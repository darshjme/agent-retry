# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-03-24

### Added
- `RetryPolicy` — exponential backoff with full jitter, configurable max attempts, base/max delay, and backoff factor.
- `RetryExecutor` — wraps any callable with retry logic; tracks `attempts_made`, `total_delay`, `last_error`.
- `execute_async()` — same retry behavior with interruptible threading-based sleep.
- `FallbackChain` — ordered model fallback with priority insertion and structured result dict.
- `DeadLetterQueue` — bounded FIFO queue backed by `collections.deque`; stores permanently failed tasks.
- Custom exceptions: `RetryableError`, `AuthError`, `MaxRetriesExceeded`.
- 100% zero runtime dependencies (stdlib only).
- Full test suite (20+ tests) with pytest.
