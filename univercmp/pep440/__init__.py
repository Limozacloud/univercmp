"""
univercmp.pep440 — Python package versioning (PEP 440)

Specification: https://peps.python.org/pep-0440/

Version format
--------------
    [N!]N(.N)*[{a|b|rc}N][.postN][.devN][+local]

    N!          epoch (optional, integer)
    N(.N)*      release segment (one or more dot-separated integers)
    a|b|rc N    pre-release: alpha, beta, release candidate
    .postN      post-release
    .devN       development release
    +local      local version label (ignored for public ordering)

Ordering rules (PEP 440 §8)
-----------------------------
1.  Epochs compare numerically; a higher epoch beats any version with a
    lower epoch regardless of the rest of the release string.
2.  Release segments are compared numerically left-to-right; shorter
    releases are zero-padded on the right.
3.  Pre-releases sort before the release: ``1.0a1 < 1.0b1 < 1.0rc1 < 1.0``.
4.  Post-releases sort after the release: ``1.0 < 1.0.post1``.
5.  Development releases sort before everything else: ``1.0.dev1 < 1.0a1``.
6.  Local version labels sort after the corresponding public version but are
    excluded when comparing two public versions.

Parsing and comparison are delegated to the ``packaging`` library, the PyPA
reference implementation of PEP 440.
"""

from __future__ import annotations

__all__ = ["compare", "validate"]

from packaging.version import InvalidVersion, Version


def validate(version: str) -> bool:
    """Return ``True`` if *version* is a valid PEP 440 version string."""
    try:
        Version(version)
        return True
    except InvalidVersion:
        return False


def compare(src: str, dst: str) -> int:
    """Compare two PEP 440 version strings.

    Raises :exc:`ValueError` if either string is not a valid PEP 440 version.

    Returns
    -------
    int
        ``-1`` if src < dst, ``0`` if equal, ``1`` if src > dst.
    """
    try:
        a = Version(src)
    except InvalidVersion as exc:
        raise ValueError(f"not a valid PEP 440 version: {src!r}") from exc
    try:
        b = Version(dst)
    except InvalidVersion as exc:
        raise ValueError(f"not a valid PEP 440 version: {dst!r}") from exc

    if a == b:
        return 0
    return -1 if a < b else 1
