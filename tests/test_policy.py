"""Tests for RetryPolicy."""

import pytest
from agent_retry import RetryPolicy
from agent_retry.exceptions import RetryableError, AuthError


class TestRetryPolicyInit:
    def test_defaults(self):
        p = RetryPolicy()
        assert p.max_attempts == 3
        assert p.base_delay == 1.0
        assert p.max_delay == 60.0
        assert p.backoff_factor == 2.0
        assert p.jitter is True

    def test_custom_values(self):
        p = RetryPolicy(max_attempts=5, base_delay=0.5, max_delay=30.0,
                        backoff_factor=3.0, jitter=False)
        assert p.max_attempts == 5
        assert p.base_delay == 0.5
        assert p.max_delay == 30.0

    def test_invalid_max_attempts(self):
        with pytest.raises(ValueError, match="max_attempts"):
            RetryPolicy(max_attempts=0)

    def test_invalid_base_delay(self):
        with pytest.raises(ValueError, match="base_delay"):
            RetryPolicy(base_delay=-1.0)

    def test_invalid_max_delay(self):
        with pytest.raises(ValueError, match="max_delay"):
            RetryPolicy(base_delay=10.0, max_delay=5.0)

    def test_invalid_backoff_factor(self):
        with pytest.raises(ValueError, match="backoff_factor"):
            RetryPolicy(backoff_factor=0.5)


class TestRetryPolicyGetDelay:
    def test_no_jitter_exponential(self):
        p = RetryPolicy(base_delay=1.0, backoff_factor=2.0, jitter=False, max_delay=100.0)
        assert p.get_delay(1) == 1.0
        assert p.get_delay(2) == 2.0
        assert p.get_delay(3) == 4.0
        assert p.get_delay(4) == 8.0

    def test_max_delay_cap(self):
        p = RetryPolicy(base_delay=1.0, backoff_factor=2.0, jitter=False, max_delay=5.0)
        assert p.get_delay(10) == 5.0

    def test_jitter_within_range(self):
        p = RetryPolicy(base_delay=1.0, backoff_factor=2.0, jitter=True, max_delay=100.0)
        for _ in range(50):
            d = p.get_delay(2)
            assert 0.0 <= d <= 2.0

    def test_zero_attempt_returns_zero(self):
        p = RetryPolicy()
        assert p.get_delay(0) == 0.0


class TestRetryPolicyShouldRetry:
    def setup_method(self):
        self.p = RetryPolicy(max_attempts=3)

    def test_retryable_error_retries(self):
        assert self.p.should_retry(1, RetryableError("transient")) is True

    def test_timeout_error_retries(self):
        assert self.p.should_retry(1, TimeoutError("timeout")) is True

    def test_connection_error_retries(self):
        assert self.p.should_retry(1, ConnectionError("conn")) is True

    def test_value_error_no_retry(self):
        assert self.p.should_retry(1, ValueError("bad value")) is False

    def test_type_error_no_retry(self):
        assert self.p.should_retry(1, TypeError("bad type")) is False

    def test_auth_error_no_retry(self):
        assert self.p.should_retry(1, AuthError("unauthorized")) is False

    def test_max_attempts_exhausted(self):
        assert self.p.should_retry(3, RetryableError("still failing")) is False

    def test_unknown_error_no_retry(self):
        assert self.p.should_retry(1, RuntimeError("unknown")) is False
