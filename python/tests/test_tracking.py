"""Tests for AKF LLM call tracking (thread-local context, record, history)."""

import threading

import pytest

from akf.tracking import (
    _record,
    clear_tracking,
    get_last_model,
    get_tracking_history,
)


@pytest.fixture(autouse=True)
def clean_tracking():
    """Clear tracking state before and after each test."""
    clear_tracking()
    yield
    clear_tracking()


class TestRecord:
    def test_stores_entry(self):
        _record("gpt-4", "openai")
        last = get_last_model()
        assert last is not None
        assert last["model"] == "gpt-4"
        assert last["provider"] == "openai"

    def test_with_tokens(self):
        _record("gpt-4", "openai", input_tokens=100, output_tokens=50)
        last = get_last_model()
        assert last["input_tokens"] == 100
        assert last["output_tokens"] == 50

    def test_has_timestamp(self):
        _record("claude-3", "anthropic")
        last = get_last_model()
        assert "timestamp" in last
        # ISO 8601 format contains T separator
        assert "T" in last["timestamp"]

    def test_none_initially(self):
        assert get_last_model() is None

    def test_most_recent(self):
        _record("gpt-4", "openai")
        _record("claude-3", "anthropic")
        last = get_last_model()
        assert last["model"] == "claude-3"
        assert last["provider"] == "anthropic"


class TestHistory:
    def test_all_calls(self):
        _record("gpt-4", "openai")
        _record("claude-3", "anthropic")
        _record("mistral-7b", "mistral")
        history = get_tracking_history()
        assert len(history) == 3
        assert history[0]["model"] == "gpt-4"
        assert history[2]["model"] == "mistral-7b"

    def test_empty(self):
        assert get_tracking_history() == []

    def test_clear(self):
        _record("gpt-4", "openai")
        _record("claude-3", "anthropic")
        clear_tracking()
        assert get_last_model() is None
        assert get_tracking_history() == []

    def test_max_limit(self):
        for i in range(110):
            _record(f"model-{i}", "test")
        history = get_tracking_history()
        assert len(history) == 100
        # Should keep the last 100
        assert history[0]["model"] == "model-10"
        assert history[-1]["model"] == "model-109"


class TestThreadIsolation:
    def test_thread_sees_empty(self):
        _record("gpt-4", "openai")
        assert get_last_model() is not None

        result = {}

        def check_in_thread():
            result["last"] = get_last_model()
            result["history"] = get_tracking_history()

        t = threading.Thread(target=check_in_thread)
        t.start()
        t.join(timeout=2)

        assert result["last"] is None
        assert result["history"] == []


class TestTrackWrapper:
    def test_track_unsupported_raises(self):
        from akf.tracking import track

        with pytest.raises(TypeError, match="Unsupported client type"):
            track("not a real client")

    def test_detect_sdk_openai(self):
        from akf.tracking import _detect_sdk

        # Create a mock that looks like an OpenAI client
        class FakeOpenAI:
            pass

        FakeOpenAI.__module__ = "openai.client"
        obj = FakeOpenAI()
        assert _detect_sdk(obj) == "openai"

    def test_detect_sdk_anthropic(self):
        from akf.tracking import _detect_sdk

        class FakeAnthropic:
            pass

        FakeAnthropic.__module__ = "anthropic.client"
        obj = FakeAnthropic()
        assert _detect_sdk(obj) == "anthropic"
