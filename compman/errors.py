from __future__ import annotations


class CommandError(SystemExit):
    """User-facing command failure handled by CLI boundary."""

    def __init__(self, message: str, code: int = 1) -> None:
        self.message = message
        super().__init__(code)
