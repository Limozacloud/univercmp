"""Tests for univercmp.deb — cases per deb-version(5) / Debian Policy §5.6.12."""

import pytest

from univercmp import InvalidVersionError, PackageType
from univercmp import compare as public_compare
from univercmp.deb import compare, split, validate

ORDERING: list[tuple[str, str, str]] = [
    # basics
    ("1.0", "=", "1.0"),
    ("1.0", "<", "1.1"),
    ("1.0", "<", "1.0.1"),
    ("1.10", ">", "1.9"),
    ("2.39-0ubuntu8", "<", "2.39-0ubuntu8.3"),
    # epoch beats everything
    ("1:1.0", ">", "2.0"),
    ("2:0.1", ">", "1:9.9"),
    ("0:1.0", "=", "1.0"),
    # tilde sorts before everything, even end-of-string
    ("1.0~rc1", "<", "1.0"),
    ("1.0~rc1-1", "<", "1.0-1"),
    ("1.0~beta1", "<", "1.0~rc1"),
    ("1.0~~", "<", "1.0~"),
    ("1.0~~a", "<", "1.0~"),
    ("1.0~", "<", "1.0"),
    ("2.4.41-4ubuntu3.14~ppa1", "<", "2.4.41-4ubuntu3.14"),
    # revision split at the LAST hyphen
    ("1.0-1-1", ">", "1.0-1"),
    ("1.0-1", "<", "1.0-2"),
    ("1.0-1ubuntu1", ">", "1.0-1"),
    ("1.1.1f-1ubuntu2.16", "<", "1.1.1f-1ubuntu2.20"),
    ("1.0", "<", "1.0-1"),
    # letter ordering: uppercase < lowercase < non-alnum
    ("1.0A", "<", "1.0a"),
    ("1.0a", "<", "1.0+"),
    ("1.0", "<", "1.0+b1"),
    ("1.0+dfsg-1", "<", "1.0+dfsg1-1"),
    # leading zeros in numeric parts are insignificant
    ("1.01", "=", "1.1"),
    ("1.001", "=", "1.1"),
    ("0", "=", "00"),
    # real-world security-update chains
    ("3.0.2-0ubuntu1.9", "<", "3.0.2-0ubuntu1.15"),
    ("9.20.1-1ubuntu2.3", "<", "9.20.1-1ubuntu2.3+esm1"),
    ("1.0-1+deb12u1", "<", "1.0-1+deb12u2"),
    ("1.2.3-1~bpo12+1", "<", "1.2.3-1"),
    ("1.21.1+really1.20.2-1", ">", "1.21.1-1"),
    ("5.15.0-91.101", "<", "5.15.0-100.110"),
]

VALID_VERSIONS = [
    "1.0",
    "1:1.0-1",
    "1.0-1ubuntu2.20",
    "1.0~rc1-1",
    "0",
    "2:1.0-1-1",
    "1:0:0-0",
]

INVALID_VERSIONS = [
    "",
    "abc",
    " ",
    "-1",
    "1:-1",
    "a:1.0",
    "1.0-",
    ":1.0",
    "1:",
    "1.0!1",
    "1_0",
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


def test_split_basic() -> None:
    assert split("1:1.0-1") == (1, "1.0", "1")
    assert split("1.0-1") == (0, "1.0", "1")
    assert split("1.0") == (0, "1.0", "")


def test_split_last_hyphen() -> None:
    assert split("1.0-1-2") == (0, "1.0-1", "2")


def test_public_api() -> None:
    result = public_compare("1:1.0", "2.0", kind=PackageType.DEB)
    assert result.newer
    assert result.verdict == "newer"


def test_invalid_version_raises() -> None:
    with pytest.raises(InvalidVersionError):
        public_compare("abc", "1.0", kind="deb")
