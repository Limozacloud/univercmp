"""Tests for univercmp.apk — cases cross-validated against apk-tools."""

import pytest

from univercmp import InvalidVersionError, PackageType
from univercmp import compare as public_compare
from univercmp import validate as public_validate
from univercmp.apk import compare, validate

# (src, op, dst) — op in {"<", "=", ">"}
ORDERING: list[tuple[str, str, str]] = [
    ("1.0", "=", "1.0"),
    ("1.0", "<", "1.1"),
    ("1.1", ">", "1.0"),
    ("1.0", "<", "1.0.1"),
    ("1.0.1", ">", "1.0"),
    ("1.10", ">", "1.9"),  # numeric, not lexicographic
    ("1.0", "<", "2.0"),
    # letter suffix
    ("1.0a", ">", "1.0"),
    ("1.0a", "<", "1.0b"),
    # pre-release suffixes sort below bare release
    ("1.0_alpha", "<", "1.0"),
    ("1.0_beta", "<", "1.0"),
    ("1.0_pre", "<", "1.0"),
    ("1.0_rc1", "<", "1.0"),
    ("1.0", ">", "1.0_rc1"),
    ("1.0_alpha", "<", "1.0_beta"),
    ("1.0_beta", "<", "1.0_pre"),
    ("1.0_pre", "<", "1.0_rc"),
    ("1.0_alpha1", "<", "1.0_alpha2"),
    ("1.0_alpha2", "<", "1.0_beta1"),
    # post-release suffixes sort above bare release
    ("1.0_p1", ">", "1.0"),
    ("1.0_p1", "<", "1.0_p2"),
    ("1.0_git", ">", "1.0"),
    ("1.0_cvs", ">", "1.0"),
    ("0.1.0_alpha", "<", "0.1.3"),
    ("0.1.0_alpha", "<", "0.1.0"),
    # revisions
    ("1.0-r0", "<", "1.0-r1"),
    ("1.0-r1", ">", "1.0-r0"),
    ("1.0-r10", ">", "1.0-r9"),
    ("1.0-r0", "=", "1.0-r0"),
    # commit hash
    ("1.0~abc", "<", "1.0~abd"),
    ("1.0~abc", "=", "1.0~abc"),
    # leading zero → lexicographic (Gentoo fractional rule)
    ("1.05", "<", "1.5"),
    ("1.005", "<", "1.05"),
    ("1.0", "<", "1.00"),
    # multi-suffix
    ("1.0_alpha_pre", "<", "1.0_alpha"),
    # real-world
    ("3.0.7-r0", "<", "3.0.7-r2"),
    ("1.1.1q-r0", "<", "1.1.1t-r0"),
    ("2.36.1-r0", "<", "2.36.2-r0"),
]

VALID_VERSIONS = [
    "1.0",
    "1.0.1",
    "1.0a",
    "1.0_rc1",
    "1.0_alpha2",
    "1.0-r3",
    "1.0~deadbeef",
    "1.2.3_git20231001-r1",
    "0.5",
]

INVALID_VERSIONS = [
    "",
    "a",
    "1.0_foo",
    "1.0-x1",
    "1.0-r",
    "_alpha",
    "-r1",
    "1..0",
    "1.0_alpha_",
    "1.0~",
]

_OP = {"<": -1, "=": 0, ">": 1}


@pytest.mark.parametrize("src,op,dst", ORDERING)
def test_ordering(src: str, op: str, dst: str) -> None:
    assert compare(src, dst) == _OP[op], f"{src} {op} {dst}"


@pytest.mark.parametrize("src,op,dst", ORDERING)
def test_antisymmetry(src: str, op: str, dst: str) -> None:
    assert compare(dst, src) == -_OP[op], f"antisymmetry: {dst} vs {src}"


@pytest.mark.parametrize("v", VALID_VERSIONS)
def test_valid(v: str) -> None:
    assert validate(v), f"expected valid: {v!r}"


@pytest.mark.parametrize("v", INVALID_VERSIONS)
def test_invalid(v: str) -> None:
    assert not validate(v), f"expected invalid: {v!r}"


def test_public_api() -> None:
    result = public_compare("1.0", "1.1", kind=PackageType.APK)
    assert result.older
    assert result.order == -1
    assert result.verdict == "older"


def test_public_api_string_kind() -> None:
    result = public_compare("1.0", "1.0", kind="apk")
    assert result.equal


def test_public_validate() -> None:
    assert public_validate("1.0", kind="apk")
    assert not public_validate("1.0_foo", kind="apk")


def test_invalid_version_raises() -> None:
    with pytest.raises(InvalidVersionError):
        public_compare("1.0_foo", "1.0", kind="apk")
