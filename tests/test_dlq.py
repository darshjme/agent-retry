"""Tests for DeadLetterQueue."""

import time
import pytest
from agent_retry import DeadLetterQueue


class TestDeadLetterQueueBasic:
    def test_push_and_size(self):
        dlq = DeadLetterQueue()
        dlq.push("t1", "my_func", {"prompt": "hello"}, "TimeoutError")
        assert dlq.size() == 1

    def test_pop_returns_record(self):
        dlq = DeadLetterQueue()
        dlq.push("t1", "func_a", {"x": 1}, "ConnectionError")
        record = dlq.pop()
        assert record is not None
        assert record["task_id"] == "t1"
        assert record["func_name"] == "func_a"
        assert record["args"] == {"x": 1}
        assert record["error"] == "ConnectionError"

    def test_pop_on_empty_returns_none(self):
        dlq = DeadLetterQueue()
        assert dlq.pop() is None

    def test_fifo_order(self):
        dlq = DeadLetterQueue()
        dlq.push("first", "f", {}, "err")
        dlq.push("second", "f", {}, "err")
        assert dlq.pop()["task_id"] == "first"
        assert dlq.pop()["task_id"] == "second"

    def test_drain_returns_all_and_clears(self):
        dlq = DeadLetterQueue()
        for i in range(5):
            dlq.push(f"t{i}", "f", {}, "err")
        items = dlq.drain()
        assert len(items) == 5
        assert dlq.size() == 0

    def test_drain_empty(self):
        dlq = DeadLetterQueue()
        assert dlq.drain() == []

    def test_max_size_respected(self):
        dlq = DeadLetterQueue(max_size=3)
        for i in range(5):
            dlq.push(f"t{i}", "f", {}, "err")
        assert dlq.size() == 3
        # Oldest 2 should have been dropped
        items = dlq.drain()
        task_ids = [item["task_id"] for item in items]
        assert "t0" not in task_ids
        assert "t1" not in task_ids
        assert "t4" in task_ids

    def test_record_has_uuid_id(self):
        dlq = DeadLetterQueue()
        dlq.push("t1", "f", {}, "err")
        record = dlq.pop()
        assert "id" in record
        assert len(record["id"]) == 36  # UUID4 format

    def test_record_has_timestamp(self):
        dlq = DeadLetterQueue()
        before = time.time()
        dlq.push("t1", "f", {}, "err")
        after = time.time()
        record = dlq.pop()
        assert before <= record["timestamp"] <= after

    def test_invalid_max_size(self):
        with pytest.raises(ValueError, match="max_size"):
            DeadLetterQueue(max_size=0)
