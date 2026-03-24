"""FallbackChain — ordered list of fallback models/functions for LLM calls."""

from typing import Any, Callable


class FallbackChain:
    """
    Maintains an ordered chain of model IDs and tries each in priority order.

    The `caller` callable is expected to have the signature:
        caller(model_id: str, prompt: str, **kwargs) -> Any

    Args:
        models: Initial ordered list of model IDs (highest priority first).
        caller: A callable used to invoke each model.
    """

    def __init__(self, models: list[str], caller: Callable) -> None:
        if not callable(caller):
            raise TypeError("caller must be callable")
        # Store as list of (priority, model_id) — lower priority value = tried first
        self._chain: list[tuple[int, str]] = [
            (i, m) for i, m in enumerate(models)
        ]
        self.caller = caller

    def add_fallback(self, model_id: str, priority: int = None) -> None:
        """
        Insert a new model into the chain.

        Args:
            model_id: Identifier for the model to add.
            priority: Position (0-based). Appends to end if None.
                      Existing items at or after this position are shifted down.
        """
        if priority is None:
            priority = len(self._chain)
        # Shift existing priorities >= the target to make room
        self._chain = [
            (p + 1, m) if p >= priority else (p, m)
            for p, m in self._chain
        ]
        self._chain.append((priority, model_id))
        self._chain.sort(key=lambda x: x[0])

    def get_chain(self) -> list[str]:
        """Return ordered list of model IDs (highest-priority first)."""
        return [model_id for _, model_id in self._chain]

    def call(self, prompt: str, **kwargs: Any) -> dict:
        """
        Try each model in order and return the first successful result.

        Args:
            prompt: The prompt string to send to the model.
            **kwargs: Additional keyword arguments forwarded to `caller`.

        Returns:
            dict with keys:
                - "model_used": str — the model that succeeded
                - "attempts": int — how many models were tried
                - "result": Any — the raw result from the caller

        Raises:
            RuntimeError if all models fail (with all errors listed).
        """
        errors: list[str] = []
        attempts = 0

        for _, model_id in self._chain:
            attempts += 1
            try:
                result = self.caller(model_id, prompt, **kwargs)
                return {
                    "model_used": model_id,
                    "attempts": attempts,
                    "result": result,
                }
            except Exception as exc:
                errors.append(f"{model_id}: {type(exc).__name__}: {exc}")

        raise RuntimeError(
            f"All {attempts} model(s) in fallback chain failed.\n"
            + "\n".join(errors)
        )
