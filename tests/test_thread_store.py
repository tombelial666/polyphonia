from __future__ import annotations

from polyphonia_runtime import thread_store


def test_thread_store_roundtrip_and_listing(tmp_path) -> None:
    chats_dir = tmp_path / "chats"
    key_id = "abc123"
    thread_id = "My Thread"
    thread_store.ensure_thread_file(chats_dir, key_id, thread_id, title="Title")
    thread_store.append_thread_event(chats_dir, key_id, thread_id, {"role": "user", "text": "hello"})
    thread_store.append_thread_event(chats_dir, key_id, thread_id, {"role": "assistant", "text": "world"})

    listed = thread_store.list_threads_for_key(chats_dir, key_id)
    assert listed[0]["thread_id"] == "my-thread"

    loaded = thread_store.load_thread_events(chats_dir, key_id, thread_id)
    assert [row["role"] for row in loaded][-2:] == ["user", "assistant"]


def test_thread_openai_messages_applies_tail_and_char_limit(tmp_path) -> None:
    chats_dir = tmp_path / "chats"
    key_id = "abc123"
    thread_id = "trim-me"
    thread_store.append_thread_event(chats_dir, key_id, thread_id, {"role": "user", "text": "short"})
    thread_store.append_thread_event(chats_dir, key_id, thread_id, {"role": "assistant", "text": "a" * 30})
    thread_store.append_thread_event(chats_dir, key_id, thread_id, {"role": "user", "text": "tail"})

    messages = thread_store.thread_openai_messages(chats_dir, key_id, thread_id, max_messages=3, max_chars=35)
    assert [message["content"] for message in messages] == ["a" * 30, "tail"]
