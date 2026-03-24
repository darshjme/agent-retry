"""
agent-retry: Zero-dependency Python library for resilient LLM call execution.

Provides exponential backoff, jitter, fallback model chains, and dead letter queues.
"""

from .exceptions import RetryableError, AuthError, MaxRetriesExceeded
from .policy import RetryPolicy
from .executor import RetryExecutor
from .fallback import FallbackChain
from .dlq import DeadLetterQueue

__version__ = "0.1.0"
__all__ = [
    "RetryPolicy",
    "RetryExecutor",
    "FallbackChain",
    "DeadLetterQueue",
    "RetryableError",
    "AuthError",
    "MaxRetriesExceeded",
]
