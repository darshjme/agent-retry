# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes    |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Email security reports to: **darshjme@gmail.com**

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

We will acknowledge receipt within 48 hours and aim to release a fix within 14 days for confirmed vulnerabilities.

## Scope

This library processes user-supplied callables and strings. Key considerations:

- **Do not pass untrusted callables** to `RetryExecutor.execute()` or `FallbackChain.call()`.
- `DeadLetterQueue` stores call arguments in memory — avoid storing sensitive data (API keys, passwords) in `args`.
- This library has zero runtime dependencies, minimizing supply-chain risk.
