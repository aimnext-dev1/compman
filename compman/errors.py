from __future__ import annotations


class CommandError(Exception):
    """User-facing command failure handled by CLI boundary."""

    def __init__(self, message: str, code: int = 1) -> None:
        self.message = message
        self.code = code
        super().__init__(message)
