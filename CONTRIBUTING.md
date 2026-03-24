# Contributing to agent-retry

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/darshjme-codes/agent-retry
cd agent-retry
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Code Style

- Follow PEP 8.
- Type-annotate all public functions and methods.
- Keep zero runtime dependencies — stdlib only.

## Pull Request Guidelines

1. Fork the repository and create a feature branch.
2. Write or update tests for any changed behavior.
3. Ensure `python -m pytest tests/ -v` passes with no failures.
4. Include a summary of changes in the PR description.
5. Reference any related issues.

## Reporting Issues

Open a GitHub issue with:
- Python version
- Minimal reproducible example
- Expected vs actual behavior

## License

By contributing, you agree your contributions will be licensed under the MIT License.
