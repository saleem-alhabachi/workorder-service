# app/domain/exceptions.py
from __future__ import annotations


class InvalidStatusTransitionError(Exception):
    """Raised when an invalid status transition is attempted on a work order."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
