"""Threaded local chat storage keyed by OpenAI key fingerprint."""

from __future__ import annotations

import json
from pathlib import Path

import phrygian_app


def test_openai_identity_exposes_key_fingerprint(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    out = json.loads(api.get_openai_identity())
    assert out["ok"] is True
    assert out["source"] in ("env", "session")
    assert len(out["key_id"]) == 64
    assert out["key_id"] == phrygian_app._openai_key_id("sk-test-key")


def test_openai_threads_roundtrip(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(phrygian_app, "get_base", lambda: str(tmp_path))
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    key_id = "abc123"

    created = json.loads(api.new_openai_thread(json.dumps({"key_id": key_id, "title": "My first thread"})))
    assert created["ok"] is True
    thread_id = created["thread_id"]

    lst = json.loads(api.list_openai_threads(json.dumps({"key_id": key_id})))
    assert lst["ok"] is True
    assert any(t["thread_id"] == thread_id for t in lst["threads"])

    phrygian_app._append_thread_event(key_id, thread_id, {"role": "user", "text": "hello"})
    phrygian_app._append_thread_event(key_id, thread_id, {"role": "assistant", "text": "world"})

    loaded = json.loads(api.load_openai_thread(json.dumps({"key_id": key_id, "thread_id": thread_id})))
    assert loaded["ok"] is True
    assert loaded["thread_id"] == thread_id
    assert [m["role"] for m in loaded["messages"]][-2:] == ["user", "gpt"]


def test_openai_chat_uses_thread_history(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(phrygian_app, "get_base", lambda: str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    key_id = phrygian_app._openai_key_id("sk-test")
    thread_id = "history-thread"

    phrygian_app._append_thread_event(key_id, thread_id, {"role": "user", "text": "prev-user"})
    phrygian_app._append_thread_event(key_id, thread_id, {"role": "assistant", "text": "prev-assistant"})

    seen_messages: list[dict[str, str]] = []

    class _Resp:
        status = 200

        def read(self) -> bytes:
            return b'{"choices":[{"message":{"content":"ok"}}]}'

    class _Ctx:
        def __enter__(self):
            return _Resp()

        def __exit__(self, *args):
            return None

    def _urlopen(req, timeout=0):  # noqa: ANN001
        body = json.loads(req.data.decode("utf-8"))
        seen_messages.extend(body.get("messages") or [])
        return _Ctx()

    monkeypatch.setattr(phrygian_app.urllib.request, "urlopen", _urlopen)

    out = json.loads(
        api.openai_chat(
            json.dumps(
                {
                    "thread_id": thread_id,
                    "user_text": "new-user",
                    "include_context": True,
                    "context_json": {
                        "instrument": "guitar",
                        "tuning": "standard",
                        "capo": "2",
                        "scaleContext": {"rootName": "C", "scaleName": "major", "scaleNoteNames": ["C", "D", "E"]},
                    },
                }
            )
        )
    )
    assert out["ok"] is True
    assert out["thread_id"] == thread_id
    contents = [m.get("content", "") for m in seen_messages]
    assert any("prev-user" in c for c in contents)
    assert any("prev-assistant" in c for c in contents)
    assert any("Polyphonia deterministic context" in c for c in contents)

