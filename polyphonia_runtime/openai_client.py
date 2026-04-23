from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def default_openai_model(env: Any = None) -> str:
    source = env if env is not None else os.environ
    return (source.get("OPENAI_MODEL") or "gpt-4o-mini").strip()


def build_chat_body(
    *,
    system_prompt: str,
    user_text: str,
    model: str,
    goal_hint: str | None = None,
    context_block: str | None = None,
    history_messages: list[dict[str, str]] | None = None,
    temperature: float = 0.6,
    max_tokens: int = 1200,
) -> dict[str, Any]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if goal_hint:
        messages.append({"role": "system", "content": goal_hint})
    if context_block:
        messages.append({"role": "user", "content": context_block})
    messages.extend(history_messages or [])
    messages.append({"role": "user", "content": user_text})
    return {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def _http_error_detail(err: urllib.error.HTTPError, limit: int) -> str:
    try:
        return err.read().decode("utf-8", errors="replace")[:limit]
    except Exception:
        return str(err)


def ping_models(
    key: str,
    *,
    timeout: int = 25,
    read_limit: int = 16384,
    urlopen: Any = urllib.request.urlopen,
    request_ctor: Any = urllib.request.Request,
) -> dict[str, Any]:
    req = request_ctor(
        "https://api.openai.com/v1/models",
        headers={"Authorization": "Bearer " + key},
        method="GET",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            status = int(getattr(resp, "status", 200) or 200)
            _ = resp.read(read_limit)
    except urllib.error.HTTPError as err:
        return {
            "ok": False,
            "error": "http_error",
            "status": err.code,
            "message": _http_error_detail(err, 1200),
        }
    except urllib.error.URLError as err:
        return {"ok": False, "error": "network", "message": str(err.reason or err)}
    except Exception as err:
        return {"ok": False, "error": "request_failed", "message": str(err)}
    return {"ok": True, "http_status": status}


def post_chat_completion(
    key: str,
    body: dict[str, Any],
    *,
    timeout: int = 90,
    read_limit: int | None = None,
    urlopen: Any = urllib.request.urlopen,
    request_ctor: Any = urllib.request.Request,
) -> dict[str, Any]:
    req = request_ctor(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            status = int(getattr(resp, "status", 200) or 200)
            raw_bytes = resp.read() if read_limit is None else resp.read(read_limit)
            raw = raw_bytes.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as err:
        return {
            "ok": False,
            "error": "http_error",
            "status": err.code,
            "message": _http_error_detail(err, 2000),
        }
    except urllib.error.URLError as err:
        return {"ok": False, "error": "network", "message": str(err.reason or err)}
    except Exception as err:
        return {"ok": False, "error": "request_failed", "message": str(err)}
    return {"ok": True, "http_status": status, "raw": raw}


def parse_chat_completion_content(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
        content = ((data.get("choices") or [{}])[0].get("message", {}).get("content", ""))
        if not isinstance(content, str):
            content = str(content)
    except (json.JSONDecodeError, IndexError, KeyError, TypeError) as err:
        return {"ok": False, "error": "bad_response", "message": str(err)}
    return {"ok": True, "content": content}


def validate_key_with_chat_probe(
    key: str,
    *,
    model: str,
    urlopen: Any = urllib.request.urlopen,
    request_ctor: Any = urllib.request.Request,
) -> dict[str, Any]:
    ping = ping_models(key, timeout=25, read_limit=2048, urlopen=urlopen, request_ctor=request_ctor)
    if not ping.get("ok"):
        return ping
    probe = post_chat_completion(
        key,
        {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
        },
        timeout=30,
        read_limit=2048,
        urlopen=urlopen,
        request_ctor=request_ctor,
    )
    if probe.get("ok"):
        return {
            "ok": True,
            "http_status": ping.get("http_status"),
            "chat_probe_status": probe.get("http_status"),
            "model": model,
        }
    mapped_error = {
        "http_error": "chat_probe_http_error",
        "network": "chat_probe_network",
        "request_failed": "chat_probe_failed",
    }.get(str(probe.get("error") or ""), "chat_probe_failed")
    out = {
        "ok": False,
        "error": mapped_error,
        "message": str(probe.get("message") or ""),
        "model": model,
    }
    if probe.get("status") is not None:
        out["status"] = probe.get("status")
    return out
