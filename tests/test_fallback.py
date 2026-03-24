"""Tests for FallbackChain."""

import pytest
from agent_retry import FallbackChain


def make_caller(fail_models: set[str]):
    """Return a caller that fails for models in fail_models."""
    def caller(model_id: str, prompt: str, **kwargs):
        if model_id in fail_models:
            raise RuntimeError(f"Model {model_id} unavailable")
        return f"response_from_{model_id}:{prompt}"
    return caller


class TestFallbackChainBasic:
    def test_first_model_success(self):
        caller = make_caller(set())
        chain = FallbackChain(["gpt-4", "gpt-3.5", "claude-3"], caller)
        result = chain.call("hello")
        assert result["model_used"] == "gpt-4"
        assert result["attempts"] == 1
        assert "gpt-4" in result["result"]

    def test_fallback_to_second(self):
        caller = make_caller({"gpt-4"})
        chain = FallbackChain(["gpt-4", "gpt-3.5", "claude-3"], caller)
        result = chain.call("hello")
        assert result["model_used"] == "gpt-3.5"
        assert result["attempts"] == 2

    def test_fallback_to_third(self):
        caller = make_caller({"gpt-4", "gpt-3.5"})
        chain = FallbackChain(["gpt-4", "gpt-3.5", "claude-3"], caller)
        result = chain.call("hello")
        assert result["model_used"] == "claude-3"
        assert result["attempts"] == 3

    def test_all_fail_raises_runtime_error(self):
        caller = make_caller({"gpt-4", "gpt-3.5", "claude-3"})
        chain = FallbackChain(["gpt-4", "gpt-3.5", "claude-3"], caller)
        with pytest.raises(RuntimeError, match="All 3 model"):
            chain.call("hello")

    def test_result_contains_required_keys(self):
        caller = make_caller(set())
        chain = FallbackChain(["model-a"], caller)
        result = chain.call("test")
        assert "model_used" in result
        assert "attempts" in result
        assert "result" in result

    def test_kwargs_forwarded(self):
        received = {}

        def caller(model_id, prompt, **kwargs):
            received.update(kwargs)
            return "ok"

        chain = FallbackChain(["m1"], caller)
        chain.call("prompt", temperature=0.7, max_tokens=100)
        assert received["temperature"] == 0.7
        assert received["max_tokens"] == 100


class TestFallbackChainAddFallback:
    def test_add_fallback_appends(self):
        caller = make_caller(set())
        chain = FallbackChain(["a", "b"], caller)
        chain.add_fallback("c")
        assert chain.get_chain() == ["a", "b", "c"]

    def test_add_fallback_with_priority(self):
        caller = make_caller(set())
        chain = FallbackChain(["a", "b"], caller)
        chain.add_fallback("top-priority", priority=0)
        c = chain.get_chain()
        assert c[0] == "top-priority"

    def test_get_chain_order(self):
        caller = make_caller(set())
        chain = FallbackChain(["x", "y", "z"], caller)
        assert chain.get_chain() == ["x", "y", "z"]

    def test_non_callable_raises(self):
        with pytest.raises(TypeError):
            FallbackChain(["m"], "not_callable")
