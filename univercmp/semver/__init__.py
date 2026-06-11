"""
univercmp.semver — Semantic Versioning 2.0.0

Specification: https://semver.org/

Version format
--------------
    MAJOR.MINOR.PATCH[-prerelease][+buildmeta]

    MAJOR, MINOR, PATCH   non-negative integers without leading zeros
    prerelease            dot-separated identifiers ``[0-9A-Za-z-]+``
    buildmeta             dot-separated identifiers ``[0-9A-Za-z-]+``
                          (ignored for precedence)

Ordering rules (spec §11)
--------------------------
1.  Build metadata has **no** effect on precedence.
2.  A pre-release version is lower than the associated normal version:
    ``1.0.0-alpha < 1.0.0``.
3.  Pre-release identifiers are compared left-to-right:

    * Both are numeric (no leading zeros) → numeric comparison.
    * Both are non-numeric → ASCII lexicographic comparison.
    * One numeric, one non-numeric → the numeric identifier is *lower*.
    * All preceding identifiers are equal but counts differ → more
      identifiers ranks higher: ``1.0.0-alpha < 1.0.0-alpha.1``.
"""

from __future__ import annotations

__all__ = ["compare", "validate", "parse"]

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------
_IDENT_RE = re.compile(r"^[0-9A-Za-z-]+$")  # pre-release and build identifiers
_NUMERIC_RE = re.compile(r"^(0|[1-9][0-9]*)$")  # no leading zeros


@dataclass(frozen=True)
class SemVer:
    """Parsed representation of a semver string."""

    major: int
    minor: int
    patch: int
    pre: tuple[str, ...]  # () means no pre-release
    build: tuple[str, ...]  # ignored for comparison


def parse(version: str) -> SemVer | None:
    """Parse *version* into a :class:`SemVer`.

    Returns ``None`` if *version* is not a valid semver string.
    """
    v = version.strip()

    # Strip build metadata first (after '+')
    build: tuple[str, ...] = ()
    if "+" in v:
        v, _, build_str = v.partition("+")
        if not build_str:
            return None
        parts = build_str.split(".")
        if not all(_IDENT_RE.match(p) and p for p in parts):
            return None
        build = tuple(parts)

    # Split pre-release (after first '-')
    pre: tuple[str, ...] = ()
    if "-" in v:
        v, _, pre_str = v.partition("-")
        if not pre_str:
            return None
        parts = pre_str.split(".")
        if not all(_IDENT_RE.match(p) and p for p in parts):
            return None
        # Numeric pre-release identifiers must not have leading zeros
        for p in parts:
            if p.isdigit() and not _NUMERIC_RE.match(p):
                return None
        pre = tuple(parts)

    # Parse MAJOR.MINOR.PATCH
    segments = v.split(".")
    if len(segments) != 3:
        return None
    nums: list[int] = []
    for seg in segments:
        if not _NUMERIC_RE.match(seg):
            return None
        nums.append(int(seg))

    return SemVer(major=nums[0], minor=nums[1], patch=nums[2], pre=pre, build=build)


def _cmp_pre_identifier(a: str, b: str) -> int:
    """Compare two individual pre-release identifiers per spec §11.4."""
    a_num = _NUMERIC_RE.match(a) is not None
    b_num = _NUMERIC_RE.match(b) is not None

    if a_num and b_num:
        ia, ib = int(a), int(b)
        return (ia > ib) - (ia < ib)
    if a_num:
        return -1  # numeric < alphanumeric
    if b_num:
        return 1  # alphanumeric > numeric
    # both alphanumeric → ASCII lexicographic
    return (a > b) - (a < b)


def _cmp_pre(a: tuple[str, ...], b: tuple[str, ...]) -> int:
    """Compare two pre-release tuples per spec §11.4."""
    for ia, ib in zip(a, b):
        r = _cmp_pre_identifier(ia, ib)
        if r:
            return r
    # all shared identifiers equal — more fields wins
    return (len(a) > len(b)) - (len(a) < len(b))


def compare(src: str, dst: str) -> int:
    """Compare two semver strings.

    Build metadata is ignored.  Raises :exc:`ValueError` if either string
    is not a valid semver.

    Returns
    -------
    int
        ``-1`` if src < dst, ``0`` if equal, ``1`` if src > dst.
    """
    a = parse(src)
    b = parse(dst)
    if a is None:
        raise ValueError(f"not a valid semver: {src!r}")
    if b is None:
        raise ValueError(f"not a valid semver: {dst!r}")

    # Compare version core
    for va, vb in ((a.major, b.major), (a.minor, b.minor), (a.patch, b.patch)):
        r = (va > vb) - (va < vb)
        if r:
            return r

    # Pre-release handling: no pre < any pre
    if a.pre == () and b.pre == ():
        return 0
    if a.pre == ():
        return 1  # release > pre-release
    if b.pre == ():
        return -1  # pre-release < release

    return _cmp_pre(a.pre, b.pre)


def validate(version: str) -> bool:
    """Return ``True`` if *version* is a valid Semantic Versioning 2.0.0 string."""
    return parse(version) is not None
