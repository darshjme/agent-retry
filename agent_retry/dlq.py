"""DeadLetterQueue — captures permanently failed calls for inspection."""

import time
import uuid
from collections import deque
from typing import Any


class DeadLetterQueue:
    """
    Thread-safe dead letter queue backed by collections.deque.

    Stores records of permanently failed LLM calls for later inspection,
    replay, or alerting.

    Args:
        max_size: Maximum number of items to retain (oldest are dropped).
    """

    def __init__(self, max_size: int = 1000) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._queue: deque[dict[str, Any]] = deque(maxlen=max_size)
        self.max_size = max_size

    def push(
        self,
        task_id: str,
        func_name: str,
        args: dict,
        error: str,
    ) -> None:
        """
        Record a permanently failed task.

        Args:
            task_id:   Caller-supplied identifier for the task.
            func_name: Name of the function/callable that failed.
            args:      Serializable representation of the call arguments.
            error:     Human-readable error description.
        """
        record = {
            "id": str(uuid.uuid4()),
            "task_id": task_id,
            "func_name": func_name,
            "args": args,
            "error": error,
            "timestamp": time.time(),
        }
        self._queue.append(record)

    def pop(self) -> dict | None:
        """
        Remove and return the oldest (FIFO) record, or None if empty.
        """
        if not self._queue:
            return None
        return self._queue.popleft()

    def size(self) -> int:
        """Return the current number of items in the queue."""
        return len(self._queue)

    def drain(self) -> list[dict]:
        """
        Return all items as a list and clear the queue.
        """
        items = list(self._queue)
        self._queue.clear()
        return items
