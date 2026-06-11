from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompareResult:
    """The outcome of a version comparison.

    Attributes
    ----------
    order:
        ``-1`` — src is older than dst.
        ``0``  — src and dst are equal.
        ``1``  — src is newer than dst.
    """

    order: int

    @property
    def older(self) -> bool:
        return self.order < 0

    @property
    def newer(self) -> bool:
        return self.order > 0

    @property
    def equal(self) -> bool:
        return self.order == 0

    @property
    def verdict(self) -> str:
        """Human-readable verdict: ``"older"``, ``"equal"``, or ``"newer"``."""
        match self.order:
            case -1:
                return "older"
            case 0:
                return "equal"
            case 1:
                return "newer"
            case _:
                raise ValueError(f"unexpected order value: {self.order!r}")

    def __int__(self) -> int:
        return self.order

    def __repr__(self) -> str:
        return f"CompareResult(order={self.order}, verdict={self.verdict!r})"
