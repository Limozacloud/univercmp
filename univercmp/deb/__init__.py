"""
univercmp.deb — Debian / Ubuntu (dpkg) version ordering.

Version format  (deb-version(5) / Debian Policy §5.6.12)
---------------------------------------------------------
    [epoch ':'] upstream_version ['-' debian_revision]

    epoch              non-negative integer, default 0
    upstream_version   starts with a digit; allowed chars: [A-Za-z0-9.+~-]
                       (``-`` only when a revision is present,
                        ``:`` only when an epoch is present)
    debian_revision    allowed chars: [A-Za-z0-9.+~]

Character weight within a non-digit run
----------------------------------------
    ``~``            → -1   (sorts before everything, including end-of-string)
    digit            →  0   (signals end of non-digit run; handled separately)
    ASCII letter     →  ord(c)
    other printable  →  ord(c) + 256
    end-of-string    →  0
"""

from __future__ import annotations

__all__ = ["compare", "validate", "split"]


def split(version: str) -> tuple[int, str, str]:
    """Split a Debian version string into ``(epoch, upstream, revision)``.

    The epoch is the part before the first ``:``, defaulting to ``0``.
    The revision is the part after the *last* ``-``, defaulting to ``""``.
    """
    v = version.strip()
    epoch = 0
    if ":" in v:
        head, _, v = v.partition(":")
        if head.isdigit():
            epoch = int(head)
    upstream, sep, revision = v.rpartition("-")
    if not sep:
        return epoch, v, ""
    return epoch, upstream, revision


def _char_weight(c: str) -> int:
    if c.isdigit():
        return 0
    if c.isascii() and c.isalpha():
        return ord(c)
    if c == "~":
        return -1
    if c:
        return ord(c) + 256
    return 0


def _compare_parts(a: str, b: str) -> int:
    """Compare two upstream-version or revision fragments."""
    ia = ib = 0
    la, lb = len(a), len(b)

    while ia < la or ib < lb:
        # Phase 1 — compare a run of non-digit characters by weight
        while (ia < la and not a[ia].isdigit()) or (ib < lb and not b[ib].isdigit()):
            wa = _char_weight(a[ia]) if ia < la else 0
            wb = _char_weight(b[ib]) if ib < lb else 0
            if wa != wb:
                return -1 if wa < wb else 1
            ia += 1
            ib += 1

        # Phase 2 — skip leading zeros
        while ia < la and a[ia] == "0":
            ia += 1
        while ib < lb and b[ib] == "0":
            ib += 1

        # Phase 3 — compare digit run: longer wins; first differing digit
        # breaks ties when lengths are equal
        first_diff = 0
        while ia < la and ib < lb and a[ia].isdigit() and b[ib].isdigit():
            if not first_diff:
                first_diff = ord(a[ia]) - ord(b[ib])
            ia += 1
            ib += 1
        if ia < la and a[ia].isdigit():
            return 1
        if ib < lb and b[ib].isdigit():
            return -1
        if first_diff:
            return -1 if first_diff < 0 else 1

    return 0


def compare(src: str, dst: str) -> int:
    """Compare two Debian version strings.

    Returns
    -------
    int
        ``-1`` if src < dst, ``0`` if equal, ``1`` if src > dst.
    """
    ea, ua, ra = split(src)
    eb, ub, rb = split(dst)
    if ea != eb:
        return -1 if ea < eb else 1
    r = _compare_parts(ua, ub)
    if r:
        return r
    return _compare_parts(ra, rb)


def validate(version: str) -> bool:
    """Return ``True`` if *version* conforms to deb-version(5)."""
    v = version.strip()
    if not v:
        return False

    has_epoch = ":" in v
    if has_epoch:
        head, _, v = v.partition(":")
        if not head.isdigit():
            return False
        if not v:
            return False

    upstream, sep, revision_str = v.rpartition("-")
    revision: str | None = revision_str if sep else None
    if not sep:
        upstream = v

    if not upstream or not upstream[0].isdigit():
        return False

    allowed_up = "+~." + ("-" if sep else "") + (":" if has_epoch else "")
    allowed_rev = "+~."

    for c in upstream:
        if not (c.isascii() and (c.isalnum() or c in allowed_up)):
            return False
    if revision is not None:
        if not revision:
            return False
        for c in revision:
            if not (c.isascii() and (c.isalnum() or c in allowed_rev)):
                return False
    return True
