"""Custom exceptions for agent-retry."""


class RetryableError(Exception):
    """Raised to signal a transient error that should be retried."""
    pass


class AuthError(Exception):
    """Raised for authentication failures — NOT retryable."""
    pass


class MaxRetriesExceeded(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Max retries exceeded after {attempts} attempt(s). "
            f"Last error: {type(last_error).__name__}: {last_error}"
        )
