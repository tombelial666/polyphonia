from __future__ import annotations

import io
import urllib.error

from polyphonia_runtime import openai_client


def test_build_chat_body_orders_system_context_history_and_user() -> None:
    body = openai_client.build_chat_body(
        system_prompt="sys",
        goal_hint="goal",
        context_block="ctx",
        history_messages=[{"role": "assistant", "content": "prev"}],
        user_text="now",
        model="gpt-4o-mini",
    )
    assert [message["role"] for message in body["messages"]] == ["system", "system", "user", "assistant", "user"]
    assert body["messages"][-1]["content"] == "now"


def test_parse_chat_completion_content_coerces_non_string() -> None:
    out = openai_client.parse_chat_completion_content('{"choices":[{"message":{"content":123}}]}')
    assert out == {"ok": True, "content": "123"}


def test_validate_key_with_chat_probe_maps_http_error() -> None:
    class Resp:
        status = 200

        def read(self, n: int = -1) -> bytes:
            return b'{"data":[]}'

    class Ctx:
        def __enter__(self):
            return Resp()

        def __exit__(self, *args):
            return None

    body = b'{"error":{"message":"quota","code":"insufficient_quota"}}'
    err = urllib.error.HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=429,
        msg="Too Many Requests",
        hdrs=None,
        fp=io.BytesIO(body),
    )

    def _urlopen(req, timeout=0):  # noqa: ANN001
        if req.full_url.endswith("/v1/models"):
            return Ctx()
        raise err

    out = openai_client.validate_key_with_chat_probe("sk-test", model="gpt-4o-mini", urlopen=_urlopen)
    assert out["ok"] is False
    assert out["error"] == "chat_probe_http_error"
    assert out["status"] == 429
    assert "insufficient_quota" in out["message"]
