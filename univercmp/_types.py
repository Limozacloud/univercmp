from __future__ import annotations

from enum import Enum


class PackageType(str, Enum):
    """Supported package ecosystems."""

    APK = "apk"
    DEB = "deb"
    RPM = "rpm"
    SEMVER = "semver"
