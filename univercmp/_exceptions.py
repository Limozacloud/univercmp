from __future__ import annotations


class InvalidVersionError(ValueError):
    """Raised when a version string is not valid for the given package type."""
