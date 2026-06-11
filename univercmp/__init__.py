"""
univercmp — cross-platform package version comparison.

Supported ecosystems
--------------------
+-----------------+--------------------------------------------+
| PackageType.APK | Alpine Linux (apk-tools)                   |
| PackageType.DEB | Debian / Ubuntu (dpkg)                     |
| PackageType.RPM | RHEL, AlmaLinux, Rocky, CentOS, SLES, …   |
+-----------------+--------------------------------------------+

Quick start
-----------
::

    from univercmp import compare, PackageType

    result = compare("1.0", "1.1", kind=PackageType.RPM)
    result.verdict   # "older"
    result.order     # -1
    result.older     # True

    # Direct submodule access (no validation wrapper)
    from univercmp.rpm import compare as rpm_cmp
    rpm_cmp("1.0", "1.1")  # -1

CLI
---
::

    univercmp compare 1.0 1.1 --type rpm
    univercmp validate 1.0_foo --type apk
"""

from __future__ import annotations

__all__ = [
    "compare",
    "validate",
    "CompareResult",
    "PackageType",
    "InvalidVersionError",
]
import types
from importlib.metadata import version as _version

__version__ = _version("univercmp")

from univercmp import apk, deb, rpm, semver
from univercmp._exceptions import InvalidVersionError
from univercmp._result import CompareResult
from univercmp._types import PackageType


def _backend(kind: PackageType | str) -> types.ModuleType:
    match PackageType(kind):
        case PackageType.APK:
            return apk
        case PackageType.DEB:
            return deb
        case PackageType.RPM:
            return rpm
        case PackageType.SEMVER:
            return semver


def compare(src: str, dst: str, *, kind: PackageType | str) -> CompareResult:
    """Compare *src* against *dst* using the ordering for *kind*.

    Parameters
    ----------
    src, dst:
        Version strings to compare.
    kind:
        Package ecosystem — a :class:`PackageType` member or its string
        value (``"apk"``, ``"deb"``, ``"rpm"``).

    Returns
    -------
    CompareResult
        ``result.order`` is ``-1`` (src older), ``0`` (equal),
        or ``1`` (src newer).

    Raises
    ------
    InvalidVersionError
        If either version string is not valid for the given *kind*.
    ValueError
        If *kind* is not a recognised package type.
    """
    backend = _backend(kind)
    for label, v in (("src", src), ("dst", dst)):
        if not backend.validate(v):
            raise InvalidVersionError(
                f"{label} {v!r} is not a valid {PackageType(kind).value} version"
            )
    return CompareResult(backend.compare(src, dst))


def validate(version: str, *, kind: PackageType | str) -> bool:
    """Return ``True`` if *version* is syntactically valid for *kind*.

    Parameters
    ----------
    version:
        Version string to check.
    kind:
        Package ecosystem — a :class:`PackageType` member or its string value.

    Returns
    -------
    bool
        ``True`` if valid, ``False`` otherwise.
    """
    return _backend(kind).validate(version)
