from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)
U = TypeVar("U")


class Result(Generic[T, E]):
    """Lightweight Result type for fallible operations."""

    __slots__ = ("_value", "_error")

    def __init__(self, value: T | None = None, error: E | None = None) -> None:
        self._value = value
        self._error = error

    @classmethod
    def ok(cls, value: T) -> Result[T, E]:
        return cls(value=value)

    @classmethod
    def err(cls, error: E) -> Result[T, E]:
        return cls(error=error)

    def is_err(self) -> bool:
        return self._error is not None

    def unwrap(self) -> T:
        if self._error is not None:
            raise self._error
        assert self._value is not None
        return self._value

    def unwrap_err(self) -> E:
        if self._error is None:
            raise ValueError("Result is Ok")
        return self._error

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        if self._error is not None:
            return Result.err(self._error)  # type: ignore[arg-type]
        return Result.ok(fn(self.unwrap()))
