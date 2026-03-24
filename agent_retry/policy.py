"""RetryPolicy — configures retry behavior with exponential backoff and jitter."""

import random
from .exceptions import RetryableError, AuthError

# Errors that should trigger a retry
_RETRYABLE_TYPES = (RetryableError, TimeoutError, ConnectionError)

# Errors that should never be retried
_NON_RETRYABLE_TYPES = (ValueError, TypeError, AuthError)


class RetryPolicy:
    """
    Defines how retries should be performed for a callable.

    Supports exponential backoff with optional full jitter.

    Args:
        max_attempts:   Maximum number of total call attempts (including the first).
        base_delay:     Base delay in seconds for the first retry.
        max_delay:      Maximum delay cap in seconds.
        backoff_factor: Multiplier applied on each successive attempt.
        jitter:         If True, applies full jitter (random value in [0, delay]).
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if backoff_factor < 1.0:
            raise ValueError("backoff_factor must be >= 1.0")

        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        Return the delay (seconds) to wait before the given retry attempt.

        Args:
            attempt: 1-based attempt number (attempt=1 → first retry).

        Returns:
            Delay in seconds (float).
        """
        if attempt <= 0:
            return 0.0
        raw = self.base_delay * (self.backoff_factor ** (attempt - 1))
        capped = min(raw, self.max_delay)
        if self.jitter:
            return random.uniform(0, capped)
        return capped

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """
        Decide whether to retry after observing `error` on attempt `attempt`.

        Args:
            attempt: The attempt number that just failed (1-based).
            error:   The exception that was raised.

        Returns:
            True if the call should be retried, False otherwise.
        """
        if attempt >= self.max_attempts:
            return False
        if isinstance(error, _NON_RETRYABLE_TYPES):
            return False
        if isinstance(error, _RETRYABLE_TYPES):
            return True
        # Default: do not retry unknown error types
        return False
