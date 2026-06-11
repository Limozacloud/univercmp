"""
univercmp.rpm — RPM version ordering (rpmvercmp).

Covers RHEL, AlmaLinux, Rocky Linux, Oracle Linux, CentOS, SLES, openSUSE —
all use the identical RPM algorithm.

Algorithm  (RPM documentation / NEVRA specification)
------------------------------------------------------
1.  Non-alphanumeric characters other than ``~`` and ``^`` are separators
    and are discarded.
2.  ``~`` (tilde) sorts before everything, including end-of-string.
3.  ``^`` (caret) sorts after end-of-string but before any continuation.
4.  Segments are either entirely digits or entirely ASCII letters.
    The leading character of the *a*-side segment determines the type.
5.  Numeric segments: strip leading zeros, compare by digit count, then
    lexicographically.  A numeric segment always beats an alpha segment at
    the same position.
6.  Alpha segments: plain ASCII lexicographic comparison.
"""

from __future__ import annotations

__all__ = ["compare", "compare_evr", "split_evr", "validate", "vercmp"]


def _is_alnum(c: str) -> bool:
    return c.isascii() and c.isalnum()


def _is_digit(c: str) -> bool:
    return c.isascii() and c.isdigit()


def _is_alpha(c: str) -> bool:
    return c.isascii() and c.isalpha()


def validate(version: str) -> bool:
    """Return ``True`` if *version* is a non-empty RPM-compatible string.

    RPM imposes no strict grammar on version strings — any non-empty string
    containing at least one alphanumeric character is accepted.
    """
    if not version:
        return False
    return any(c.isascii() and c.isalnum() for c in version)


def vercmp(src: str, dst: str) -> int:
    """Compare two RPM version (or release) strings — raw segment comparison.

    Does **not** parse epoch or release fields.  Use :func:`compare` or
    :func:`compare_evr` for full ``[epoch:]version[-release]`` strings.

    Returns
    -------
    int
        ``-1`` if src < dst, ``0`` if equal, ``1`` if src > dst.
    """
    if src == dst:
        return 0

    i, j = 0, 0
    la, lb = len(src), len(dst)

    while i < la or j < lb:
        # Discard separators
        while i < la and not (_is_alnum(src[i]) or src[i] in "~^"):
            i += 1
        while j < lb and not (_is_alnum(dst[j]) or dst[j] in "~^"):
            j += 1

        ca = src[i] if i < la else ""
        cb = dst[j] if j < lb else ""

        # Tilde: sorts before everything, including end-of-string
        if ca == "~" or cb == "~":
            if ca != "~":
                return 1
            if cb != "~":
                return -1
            i += 1
            j += 1
            continue

        # Caret: sorts after end-of-string, before any continuation
        if ca == "^" or cb == "^":
            if not ca:
                return -1
            if not cb:
                return 1
            if ca != "^":
                return 1
            if cb != "^":
                return -1
            i += 1
            j += 1
            continue

        # One side exhausted
        if not ca or not cb:
            break

        # Collect one all-digit or all-alpha segment; type is driven by src (a-side)
        si, sj = i, j
        if _is_digit(ca):
            isnum = True
            while i < la and _is_digit(src[i]):
                i += 1
            while j < lb and _is_digit(dst[j]):
                j += 1
        else:
            isnum = False
            while i < la and _is_alpha(src[i]):
                i += 1
            while j < lb and _is_alpha(dst[j]):
                j += 1

        seg_a = src[si:i]
        seg_b = dst[sj:j]

        # b had no segment of this type → numeric beats alpha
        if not seg_b:
            return 1 if isnum else -1

        if isnum:
            seg_a = seg_a.lstrip("0")
            seg_b = seg_b.lstrip("0")
            if len(seg_a) != len(seg_b):
                return 1 if len(seg_a) > len(seg_b) else -1

        if seg_a != seg_b:
            return 1 if seg_a > seg_b else -1

    if i >= la and j >= lb:
        return 0
    return -1 if i >= la else 1


def split_evr(evr: str) -> tuple[int, str, str]:
    """Split ``[epoch:]version[-release]`` into ``(epoch, version, release)``.

    Epoch defaults to ``0``; release defaults to ``""``.
    """
    epoch = 0
    if ":" in evr:
        head, _, evr = evr.partition(":")
        if head.isdigit():
            epoch = int(head)
    version, sep, release = evr.partition("-")
    return epoch, version, (release if sep else "")


def compare_evr(src: str, dst: str) -> int:
    """Compare two full EVR strings ``[epoch:]version[-release]``.

    Returns
    -------
    int
        ``-1`` if src < dst, ``0`` if equal, ``1`` if src > dst.
    """
    ea, va, ra = split_evr(src)
    eb, vb, rb = split_evr(dst)
    if ea != eb:
        return -1 if ea < eb else 1
    r = vercmp(va, vb)
    if r:
        return r
    if ra == rb:
        return 0
    if not ra or not rb:
        return -1 if not ra else 1
    return vercmp(ra, rb)


def compare(src: str, dst: str) -> int:
    """Compare two RPM strings, parsing epoch and release if present.

    This is the EVR-aware entry point and the function used by the public
    ``univercmp.compare()`` API.  Delegates to :func:`compare_evr`.

    Returns
    -------
    int
        ``-1`` if src < dst, ``0`` if equal, ``1`` if src > dst.
    """
    return compare_evr(src, dst)
