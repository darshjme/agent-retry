"""Tests for RetryExecutor."""

import pytest
from unittest.mock import MagicMock, patch
from agent_retry import RetryExecutor, RetryPolicy
from agent_retry.exceptions import RetryableError, AuthError, MaxRetriesExceeded


def make_flaky(fail_times: int, exc_type=RetryableError):
    """Return a callable that raises exc_type `fail_times` times then succeeds."""
    calls = {"count": 0}

    def flaky(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] <= fail_times:
            raise exc_type(f"fail #{calls['count']}")
        return "success"

    return flaky


class TestRetryExecutorBasic:
    def test_success_first_try(self):
        executor = RetryExecutor(RetryPolicy(max_attempts=3))
        result = executor.execute(lambda: "ok")
        assert result == "ok"
        assert executor.attempts_made == 1
        assert executor.total_delay == 0.0

    def test_retries_on_retryable_error(self):
        policy = RetryPolicy(max_attempts=3, base_delay=0.0, jitter=False)
        executor = RetryExecutor(policy)
        flaky = make_flaky(2)
        result = executor.execute(flaky)
        assert result == "success"
        assert executor.attempts_made == 3

    def test_raises_max_retries_exceeded(self):
        policy = RetryPolicy(max_attempts=2, base_delay=0.0, jitter=False)
        executor = RetryExecutor(policy)
        always_fail = make_flaky(99)
        with pytest.raises(MaxRetriesExceeded) as exc_info:
            executor.execute(always_fail)
        assert exc_info.value.attempts == 2
        assert executor.last_error is not None

    def test_non_retryable_raises_immediately(self):
        policy = RetryPolicy(max_attempts=5, base_delay=0.0, jitter=False)
        executor = RetryExecutor(policy)

        def bad():
            raise ValueError("bad input")

        with pytest.raises(ValueError):
            executor.execute(bad)
        assert executor.attempts_made == 1

    def test_auth_error_not_retried(self):
        policy = RetryPolicy(max_attempts=5, base_delay=0.0, jitter=False)
        executor = RetryExecutor(policy)
        flaky = make_flaky(1, exc_type=AuthError)
        with pytest.raises(AuthError):
            executor.execute(flaky)
        assert executor.attempts_made == 1

    def test_tracks_total_delay(self):
        policy = RetryPolicy(max_attempts=3, base_delay=0.01, jitter=False, backoff_factor=2.0)
        executor = RetryExecutor(policy)
        flaky = make_flaky(2)
        executor.execute(flaky)
        # delay for attempt 1 = 0.01, attempt 2 = 0.02 → total = 0.03
        assert executor.total_delay == pytest.approx(0.03, abs=0.001)

    def test_passes_args_and_kwargs(self):
        policy = RetryPolicy(max_attempts=1)
        executor = RetryExecutor(policy)
        result = executor.execute(lambda x, y=0: x + y, 3, y=4)
        assert result == 7

    def test_default_policy_used_when_none(self):
        executor = RetryExecutor()
        assert executor.policy.max_attempts == 3


class TestRetryExecutorAsync:
    def test_execute_async_success(self):
        policy = RetryPolicy(max_attempts=3, base_delay=0.0, jitter=False)
        executor = RetryExecutor(policy)
        result = executor.execute_async(lambda: "async_ok")
        assert result == "async_ok"

    def test_execute_async_retries(self):
        policy = RetryPolicy(max_attempts=3, base_delay=0.0, jitter=False)
        executor = RetryExecutor(policy)
        flaky = make_flaky(2)
        result = executor.execute_async(flaky)
        assert result == "success"
        assert executor.attempts_made == 3

    def test_execute_async_raises_max_retries(self):
        policy = RetryPolicy(max_attempts=2, base_delay=0.0, jitter=False)
        executor = RetryExecutor(policy)
        always_fail = make_flaky(99)
        with pytest.raises(MaxRetriesExceeded):
            executor.execute_async(always_fail)
