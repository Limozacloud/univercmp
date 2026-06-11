"""
univercmp.apk — Alpine Linux (apk-tools) version ordering.

Version grammar
---------------
    version  = numblock ('.' numblock)* letter?
               ('_' suffix digits?)* ('~' hexstring)? ('-r' digits)?
    numblock = DIGIT+
    letter   = 'a'..'z'
    suffix   = 'alpha' | 'beta' | 'pre' | 'rc'
               | 'cvs'  | 'svn'  | 'git' | 'hg' | 'p'
    hexstring = HEXDIGIT+

Ordering rules
--------------
Numeric blocks compare as integers unless either block has a leading zero,
in which case they compare lexicographically (Gentoo fractional rule:
``1.05 < 1.5``, ``1.0 < 1.00``).

A trailing letter sorts above the bare number (``1.0a > 1.0``).

Suffix ranks: alpha=1 beta=2 pre=3 rc=4 <none>=5 cvs=6 svn=7 git=8 hg=9 p=10.
Ranks 1–4 are pre-release (sort below bare), 6–10 are post-release (above).

The hex hash (``~``) compares lexicographically.
Package revision (``-rN``) compares as an integer.
"""

from __future__ import annotations

__all__ = ["compare", "validate"]

# ---------------------------------------------------------------------------
# Segment kinds
# The integer value encodes ordering precedence when one side has run out of
# tokens: a *larger* kind appearing while the other side has ended means the
# ended side is newer (it did not need that extra token to be what it is).
# ---------------------------------------------------------------------------
_NUM0 = 0  # leading numeric block
_NUM = 1  # subsequent numeric block (after '.')
_ALPHA = 2  # single lowercase letter
_SUF = 3  # suffix keyword  (_alpha, _rc, _p, …)
_SUFN = 4  # digit run following a suffix keyword
_HASH = 5  # hex commit hash after '~'
_REV = 6  # package revision after '-r'
_END = 7
_BAD = 8

_SUFFIX_RANK: dict[str, int] = {
    "alpha": 1,
    "beta": 2,
    "pre": 3,
    "rc": 4,
    "cvs": 6,
    "svn": 7,
    "git": 8,
    "hg": 9,
    "p": 10,
}
_RELEASE_RANK = 5  # rank of an unsuffixed release

_HEXCHARS = frozenset("0123456789abcdef")
_LOWERCASE = frozenset("abcdefghijklmnopqrstuvwxyz")
_DIGITS = frozenset("0123456789")


class _Scanner:
    """Stateful position-advancing scanner over a version string."""

    __slots__ = ("_s", "_i", "_n", "kind", "raw", "num", "rank")

    def __init__(self, s: str) -> None:
        self._s = s
        self._i = 0
        self._n = len(s)
        self.kind = _BAD
        self.raw = ""
        self.num = 0
        self.rank = 0
        self._read_digits(_NUM0)

    def _read_digits(self, kind: int) -> None:
        start = self._i
        while self._i < self._n and self._s[self._i] in _DIGITS:
            self._i += 1
        self.raw = self._s[start : self._i]
        if self.raw:
            self.kind = kind
            self.num = int(self.raw)
        else:
            self.kind = _BAD

    def step(self) -> None:
        """Advance to the next segment."""
        if self.kind >= _END:
            return
        if self._i >= self._n:
            self.kind = _END
            return
        c = self._s[self._i]

        if c in _LOWERCASE:
            if self.kind > _NUM:
                self.kind = _BAD
                return
            self.raw = c
            self.kind = _ALPHA
            self._i += 1

        elif c == "." or c in _DIGITS:
            if c == ".":
                if self.kind > _NUM:
                    self.kind = _BAD
                    return
                self._i += 1
                self._read_digits(_NUM)
            elif self.kind in (_NUM0, _NUM):
                self._read_digits(_NUM)
            elif self.kind == _SUF:
                self._read_digits(_SUFN)
            else:
                self.kind = _BAD

        elif c == "_":
            if self.kind > _SUFN:
                self.kind = _BAD
                return
            self._i += 1
            start = self._i
            while self._i < self._n and self._s[self._i] in _LOWERCASE:
                self._i += 1
            name = self._s[start : self._i]
            rank = _SUFFIX_RANK.get(name)
            if rank is None:
                self.kind = _BAD
                return
            self.raw = name
            self.rank = rank
            self.kind = _SUF

        elif c == "~":
            if self.kind >= _HASH:
                self.kind = _BAD
                return
            self._i += 1
            start = self._i
            while self._i < self._n and self._s[self._i] in _HEXCHARS:
                self._i += 1
            self.raw = self._s[start : self._i]
            if not self.raw:
                self.kind = _BAD
                return
            self.kind = _HASH

        elif c == "-":
            if self.kind >= _REV:
                self.kind = _BAD
                return
            if not self._s.startswith("-r", self._i):
                self.kind = _BAD
                return
            self._i += 2
            self._read_digits(_REV)

        else:
            self.kind = _BAD


# ---------------------------------------------------------------------------


def _sign(a: int | str, b: int | str) -> int:
    return (a > b) - (a < b)


def _cmp_segment(a: _Scanner, b: _Scanner) -> int:
    if a.kind == _NUM:
        # leading-zero rule: lexicographic when either side has a leading zero
        if a.raw[0] == "0" or b.raw[0] == "0":
            return _sign(a.raw, b.raw)
        return _sign(a.num, b.num)
    if a.kind in (_NUM0, _SUFN, _REV):
        return _sign(a.num, b.num)
    if a.kind == _ALPHA:
        return _sign(a.raw, b.raw)
    if a.kind == _SUF:
        return _sign(a.rank, b.rank)
    return _sign(a.raw, b.raw)


def compare(src: str, dst: str, *, fuzzy: bool = False) -> int:
    """Compare two APK version strings.

    Parameters
    ----------
    src, dst:
        Version strings to compare.
    fuzzy:
        When *True* and *dst* is exhausted while *src* continues, the two
        are considered equal (prefix match).

    Returns
    -------
    int
        ``-1`` if src < dst, ``0`` if equal, ``1`` if src > dst.
    """
    a, b = _Scanner(src), _Scanner(dst)

    while a.kind == b.kind and a.kind < _END:
        r = _cmp_segment(a, b)
        if r:
            return r
        a.step()
        b.step()

    if a.kind == b.kind:
        return 0
    if b.kind == _END and fuzzy:
        return 0
    if a.kind == _SUF and a.rank < _RELEASE_RANK:
        return -1
    if b.kind == _SUF and b.rank < _RELEASE_RANK:
        return 1
    return -1 if a.kind > b.kind else 1


def validate(version: str) -> bool:
    """Return ``True`` if *version* is a syntactically valid APK version."""
    s = _Scanner(version)
    while s.kind < _END:
        s.step()
    return s.kind == _END
