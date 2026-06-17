"""Tests for univercmp.pep440 — per PEP 440 (peps.python.org/pep-0440/)."""

import pytest

from univercmp import InvalidVersionError, PackageType
from univercmp import compare as public_compare
from univercmp.pep440 import compare, validate

ORDERING: list[tuple[str, str, str]] = [
    # basic release ordering
    ("1.0", "=", "1.0"),
    ("1.0", "<", "1.1"),
    ("1.0.0", "<", "1.0.1"),
    ("1.9", "<", "1.10"),
    ("2.0", ">", "1.9.9"),
    # zero-padding equivalence
    ("1.0", "=", "1.0.0"),
    ("1.0.0", "=", "1.0.0.0"),
    # dev releases sort before everything else
    ("1.0.dev1", "<", "1.0a1"),
    ("1.0.dev1", "<", "1.0"),
    ("1.0.dev1", "<", "1.0.dev2"),
    # pre-release ordering: dev < a < b < rc < release
    ("1.0a1", "<", "1.0b1"),
    ("1.0b1", "<", "1.0rc1"),
    ("1.0rc1", "<", "1.0"),
    ("1.0a1", "<", "1.0a2"),
    # post-release sorts after release
    ("1.0", "<", "1.0.post1"),
    ("1.0.post1", "<", "1.0.post2"),
    # epoch dominates all other fields
    ("1!0.1", ">", "999.0"),
    ("2!1.0", ">", "1!999.0"),
    ("0!1.0", "<", "1!0.0.1"),
    # local versions sort after their public counterpart
    ("1.0+local.1", ">", "1.0"),
    # local labels are compared when both sides carry one
    ("1.0+local.1", "<", "1.0+local.2"),
    # normalisation: PEP 440 canonical forms
    ("1.0.0", "=", "1.0"),
    ("1.0a1", "=", "1.0alpha1"),  # packaging normalises 'alpha' → 'a'
    ("1.0b1", "=", "1.0beta1"),
    ("1.0rc1", "=", "1.0c1"),
    ("1.0.post1", "=", "1.0-1"),  # dash-separated release interpreted as post
    ("1.0.dev0", "=", "1.0-dev0"),
]

VALID_VERSIONS = [
    "1.0",
    "1.0.0",
    "1.2.3",
    "1.0a1",
    "1.0alpha1",
    "1.0b2",
    "1.0beta2",
    "1.0rc1",
    "1.0c1",
    "1.0.post1",
    "1.0.dev1",
    "1!1.0",
    "2!3.4.5",
    "1.0+local",
    "1.0+local.version.1",
    "0.0.1",
    "21.3",
    "2023.1.0",
    "v1.0",
    "1.0.0-beta",
]

INVALID_VERSIONS = [
    "",
    "not-a-version",
    "1.0.??",
    "1.0.0+",
    "hello",
    "1.0.0-",
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


def test_public_api_older() -> None:
    result = public_compare("1.0a1", "1.0", kind=PackageType.PEP440)
    assert result.older
    assert result.verdict == "older"


def test_public_api_equal() -> None:
    result = public_compare("1.0.0", "1.0", kind="pep440")
    assert result.equal
    assert result.verdict == "equal"


def test_public_api_newer() -> None:
    result = public_compare("1.0.post1", "1.0", kind=PackageType.PEP440)
    assert result.newer
    assert result.verdict == "newer"


def test_epoch_dominates() -> None:
    result = public_compare("1!0.0.1", "999.0", kind=PackageType.PEP440)
    assert result.newer


def test_invalid_version_raises() -> None:
    with pytest.raises(InvalidVersionError):
        public_compare("not-a-version", "1.0", kind="pep440")


def test_compare_raises_on_invalid() -> None:
    with pytest.raises(ValueError, match="not a valid PEP 440"):
        compare("not-a-version", "1.0")
