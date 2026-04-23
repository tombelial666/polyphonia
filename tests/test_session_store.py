from __future__ import annotations

from polyphonia_runtime import session_store


def test_persisted_auth_roundtrip_and_forget(tmp_path) -> None:
    session_store.save_persisted_auth(tmp_path, {"openai_key": "sk-test", "claude_key": "sk-ant-test"})
    loaded = session_store.load_persisted_auth(tmp_path)
    assert loaded["openai_key"] == "sk-test"
    assert loaded["claude_key"] == "sk-ant-test"
    assert loaded["v"] == 1

    session_store.forget_persisted_auth(tmp_path, openai=True)
    after_forget = session_store.load_persisted_auth(tmp_path)
    assert "openai_key" not in after_forget
    assert after_forget["claude_key"] == "sk-ant-test"


def test_persisted_auth_drops_empty_values(tmp_path) -> None:
    session_store.save_persisted_auth(tmp_path, {"openai_key": "  ", "claude_key": ""})
    assert session_store.load_persisted_auth(tmp_path) == {"v": 1}
