# agent-retry

> Zero-dependency Python library for resilient LLM agent calls — exponential backoff, jitter, fallback model chains, and dead letter queues.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()

---

## The Problem

LLM APIs fail. Constantly.

- Rate limits hit at 3am during your batch job
- `gpt-4` goes down during a product demo
- Network blips during long inference calls
- One model fails, the backup model just works

Most teams handle this with ad-hoc `try/except` + `time.sleep()` scattered everywhere. It's fragile, inconsistent, and hard to observe.

**agent-retry** gives you production-grade retry primitives in a single, zero-dependency package.

---

## Installation

```bash
pip install agent-retry
```

Or from source:

```bash
git clone https://github.com/darshjme-codes/agent-retry
cd agent-retry
pip install -e .
```

---

## Quick Start

### 1. Basic Retry with Exponential Backoff

```python
from agent_retry import RetryExecutor, RetryPolicy
from agent_retry.exceptions import RetryableError

policy = RetryPolicy(
    max_attempts=5,
    base_delay=1.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=True,
)
executor = RetryExecutor(policy)

def call_openai(prompt: str) -> str:
    # Your actual LLM call here
    import httpx
    resp = httpx.post("https://api.openai.com/v1/chat/completions", ...)
    if resp.status_code == 429:
        raise RetryableError("Rate limited")
    return resp.json()["choices"][0]["message"]["content"]

result = executor.execute(call_openai, "Explain quantum entanglement")
print(f"Got result after {executor.attempts_made} attempt(s)")
```

### 2. Fallback Chain (Try GPT-4 → Claude → Gemini)

```python
from agent_retry import FallbackChain

def my_llm_caller(model_id: str, prompt: str, **kwargs) -> str:
    """Your unified LLM caller."""
    if model_id == "gpt-4":
        return call_openai(model_id, prompt)
    elif model_id == "claude-3-opus":
        return call_anthropic(model_id, prompt)
    elif model_id == "gemini-pro":
        return call_gemini(model_id, prompt)

chain = FallbackChain(
    models=["gpt-4", "claude-3-opus", "gemini-pro"],
    caller=my_llm_caller,
)

result = chain.call("Summarize this document: ...")
print(f"Model used: {result['model_used']}")
print(f"Attempts needed: {result['attempts']}")
print(f"Response: {result['result']}")
```

### 3. Dead Letter Queue (Capture Permanent Failures)

```python
from agent_retry import DeadLetterQueue, RetryExecutor, RetryPolicy
from agent_retry.exceptions import MaxRetriesExceeded

dlq = DeadLetterQueue(max_size=500)
executor = RetryExecutor(RetryPolicy(max_attempts=3, base_delay=0.5))

tasks = [{"id": "task-001", "prompt": "Hello"}, ...]

for task in tasks:
    try:
        result = executor.execute(call_llm, task["prompt"])
        save_result(task["id"], result)
    except MaxRetriesExceeded as e:
        dlq.push(
            task_id=task["id"],
            func_name="call_llm",
            args={"prompt": task["prompt"]},
            error=str(e),
        )

# Later: inspect / replay failures
failed = dlq.drain()
print(f"{len(failed)} tasks permanently failed")
for item in failed:
    print(f"  [{item['task_id']}] {item['error']}")
```

---

## Real-World Scenario: Production Batch Inference Pipeline

```python
from agent_retry import RetryExecutor, RetryPolicy, FallbackChain, DeadLetterQueue
from agent_retry.exceptions import RetryableError, MaxRetriesExceeded

# Configure resilience
policy = RetryPolicy(max_attempts=4, base_delay=1.0, max_delay=20.0, jitter=True)
executor = RetryExecutor(policy)
dlq = DeadLetterQueue(max_size=1000)

# Primary + fallback models
chain = FallbackChain(
    models=["gpt-4-turbo", "claude-3-sonnet", "gemini-1.5-pro"],
    caller=unified_llm_caller,
)

# Process 10,000 documents
documents = load_documents()

for doc in documents:
    try:
        # Retry the entire fallback chain
        result = executor.execute(chain.call, doc["text"], max_tokens=500)
        store_result(doc["id"], result)
    except MaxRetriesExceeded as e:
        dlq.push(doc["id"], "chain.call", {"text": doc["text"][:100]}, str(e))

# End-of-run report
print(f"Processed: {len(documents) - dlq.size()}/{len(documents)}")
print(f"Failed (in DLQ): {dlq.size()}")
```

---

## API Reference

### `RetryPolicy`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_attempts` | int | 3 | Total attempts including the first |
| `base_delay` | float | 1.0 | Base delay in seconds |
| `max_delay` | float | 60.0 | Maximum delay cap in seconds |
| `backoff_factor` | float | 2.0 | Exponential multiplier |
| `jitter` | bool | True | Full jitter (random in [0, delay]) |

### `RetryExecutor`

- `execute(func, *args, **kwargs)` — blocking retry with `time.sleep()`
- `execute_async(func, *args, **kwargs)` — retry with threading-based sleep (interruptible)
- `attempts_made` — number of attempts on last call
- `total_delay` — total seconds slept on last call
- `last_error` — last exception seen

### `FallbackChain`

- `call(prompt, **kwargs)` → `{"model_used", "attempts", "result"}`
- `add_fallback(model_id, priority=None)` — insert model into chain
- `get_chain()` → ordered list of model IDs

### `DeadLetterQueue`

- `push(task_id, func_name, args, error)` — enqueue a failed task
- `pop()` → oldest record or `None`
- `size()` → current count
- `drain()` → all items as list, then clears queue

### Exceptions

| Exception | Retryable | Description |
|-----------|-----------|-------------|
| `RetryableError` | ✅ | Transient failure — signal for retry |
| `TimeoutError` | ✅ | Built-in Python timeout |
| `ConnectionError` | ✅ | Built-in Python connection error |
| `AuthError` | ❌ | Authentication failure |
| `ValueError` | ❌ | Bad input |
| `TypeError` | ❌ | Type error |
| `MaxRetriesExceeded` | — | Raised when all attempts exhausted |

---

## License

MIT © Darshankumar Joshi
