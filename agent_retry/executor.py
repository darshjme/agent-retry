"""RetryExecutor — executes callables with a RetryPolicy."""

import time
import threading
from typing import Any, Callable

from .policy import RetryPolicy
from .exceptions import MaxRetriesExceeded


class RetryExecutor:
    """
    Wraps a callable and executes it with automatic retry logic.

    Tracks per-invocation statistics: attempts_made, total_delay, last_error.

    Args:
        policy: RetryPolicy instance. Defaults to RetryPolicy() if None.
    """

    def __init__(self, policy: RetryPolicy = None) -> None:
        self.policy = policy or RetryPolicy()
        self.attempts_made: int = 0
        self.total_delay: float = 0.0
        self.last_error: Exception | None = None

    def _reset_stats(self) -> None:
        self.attempts_made = 0
        self.total_delay = 0.0
        self.last_error = None

    def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Call `func(*args, **kwargs)`, retrying on retryable errors.

        Returns the function's return value on success.
        Raises MaxRetriesExceeded if all attempts fail.
        Raises non-retryable exceptions immediately.
        """
        self._reset_stats()
        attempt = 0

        while True:
            attempt += 1
            self.attempts_made = attempt
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                self.last_error = exc
                if not self.policy.should_retry(attempt, exc):
                    if attempt >= self.policy.max_attempts:
                        raise MaxRetriesExceeded(attempt, exc) from exc
                    # Non-retryable error — re-raise immediately
                    raise
                delay = self.policy.get_delay(attempt)
                self.total_delay += delay
                time.sleep(delay)

    def execute_async(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Same as execute() but the inter-retry sleep is performed on a background
        thread so that the calling thread can be interrupted (e.g. via
        threading.Event or KeyboardInterrupt).

        Still blocks the caller until completion (synchronous return value).
        """
        self._reset_stats()
        attempt = 0
        result_holder: list[Any] = [None]
        error_holder: list[Exception | None] = [None]

        while True:
            attempt += 1
            self.attempts_made = attempt
            try:
                result = func(*args, **kwargs)
                result_holder[0] = result
                return result
            except Exception as exc:
                self.last_error = exc
                error_holder[0] = exc
                if not self.policy.should_retry(attempt, exc):
                    if attempt >= self.policy.max_attempts:
                        raise MaxRetriesExceeded(attempt, exc) from exc
                    raise

                delay = self.policy.get_delay(attempt)
                self.total_delay += delay

                # Sleep on a daemon thread so it can be interrupted
                done_event = threading.Event()

                def _sleep():
                    time.sleep(delay)
                    done_event.set()

                t = threading.Thread(target=_sleep, daemon=True)
                t.start()
                done_event.wait()
