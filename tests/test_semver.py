"""Tests for univercmp.semver — per Semantic Versioning 2.0.0 (semver.org)."""

import pytest

from univercmp import InvalidVersionError, PackageType
from univercmp import compare as public_compare
from univercmp.semver import compare, parse, validate

ORDERING: list[tuple[str, str, str]] = [
    # core version ordering
    ("1.0.0", "=", "1.0.0"),
    ("1.0.0", "<", "1.0.1"),
    ("1.0.0", "<", "1.1.0"),
    ("1.0.0", "<", "2.0.0"),
    ("1.9.0", "<", "1.10.0"),
    ("1.0.10", ">", "1.0.9"),
    # pre-release < release
    ("1.0.0-alpha", "<", "1.0.0"),
    ("1.0.0-alpha.1", "<", "1.0.0"),
    ("1.0.0-0.3.7", "<", "1.0.0"),
    # pre-release ordering (spec §11.4)
    ("1.0.0-alpha", "<", "1.0.0-alpha.1"),  # more fields wins
    ("1.0.0-alpha.1", "<", "1.0.0-alpha.beta"),  # numeric < alphanumeric
    ("1.0.0-alpha.beta", "<", "1.0.0-beta"),
    ("1.0.0-beta", "<", "1.0.0-beta.2"),
    ("1.0.0-beta.2", "<", "1.0.0-beta.11"),  # numeric: 2 < 11
    ("1.0.0-beta.11", "<", "1.0.0-rc.1"),
    ("1.0.0-rc.1", "<", "1.0.0"),
    # build metadata ignored for precedence
    ("1.0.0+build.1", "=", "1.0.0"),
    ("1.0.0+001", "=", "1.0.0+002"),
    ("1.0.0-beta+exp.sha.5114f85", "=", "1.0.0-beta+20231231"),
    # leading zeros in numeric segments forbidden
    # (tested via validate, not ordering)
    # real-world style
    ("0.1.0", "<", "0.2.0"),
    ("2.0.0-rc.1", "<", "2.0.0"),
    ("1.0.0-alpha", "<", "1.0.0-alpha.1"),
    ("1.2.3-1", "<", "1.2.3-2"),  # numeric pre-release
    ("1.2.3-1", "<", "1.2.3-a"),  # numeric < alphanumeric
]

VALID_VERSIONS = [
    "0.0.0",
    "1.0.0",
    "1.2.3",
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-0.3.7",
    "1.0.0-x.7.z.92",
    "1.0.0+build.1",
    "1.0.0-beta+exp.sha.5114f85",
    "1.0.0+21AF26D3--117B344092BD",
    "999.999.999",
]

INVALID_VERSIONS = [
    "",
    "1",
    "1.2",
    "1.2.3.4",
    "01.2.3",  # leading zero in major
    "1.02.3",  # leading zero in minor
    "1.2.03",  # leading zero in patch
    "1.0.0-",  # empty pre-release
    "1.0.0+",  # empty build
    "1.0.0-01",  # leading zero in numeric pre-release identifier
    "1.0.0-.1",  # empty pre-release identifier
    "1.0.0-alpha..1",  # empty pre-release identifier
    "-1.0.0",
    "1.0.0-alpha@1",  # invalid character
    "v1.0.0",  # 'v' prefix not part of spec
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


def test_parse_basic() -> None:
    sv = parse("1.2.3-alpha.1+build.42")
    assert sv is not None
    assert sv.major == 1
    assert sv.minor == 2
    assert sv.patch == 3
    assert sv.pre == ("alpha", "1")
    assert sv.build == ("build", "42")


def test_parse_no_pre_or_build() -> None:
    sv = parse("1.0.0")
    assert sv is not None
    assert sv.pre == ()
    assert sv.build == ()


def test_build_ignored_in_public_api() -> None:
    a = public_compare("1.0.0+build.1", "1.0.0+build.2", kind=PackageType.SEMVER)
    assert a.equal


def test_public_api() -> None:
    result = public_compare("1.0.0-alpha", "1.0.0", kind="semver")
    assert result.older
    assert result.verdict == "older"


def test_invalid_version_raises() -> None:
    with pytest.raises(InvalidVersionError):
        public_compare("v1.0.0", "1.0.0", kind="semver")
