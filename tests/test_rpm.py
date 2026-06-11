"""Tests for univercmp.rpm — validated against rpm upstream tests/rpmvercmp.at."""

import pytest

from univercmp import PackageType
from univercmp import compare as public_compare
from univercmp.rpm import compare, compare_evr, split_evr, vercmp

# vercmp() — raw segment comparison, no EVR parsing
VERCMP_ORDERING: list[tuple[str, str, str]] = [
    # separators are interchangeable in raw vercmp
    ("1.0", "=", "1_0"),
    ("1.0", "=", "1..0"),
    ("2.0.1", "=", "2_0-1"),  # '-' is a separator in raw vercmp
]

# compare() / compare_evr() — epoch + release aware
ORDERING: list[tuple[str, str, str]] = [
    # basics
    ("1.0", "=", "1.0"),
    ("1.0", "<", "2.0"),
    ("2.0", "<", "2.0.1"),
    ("2.0.1", "<", "2.0.1a"),  # trailing alpha is newer
    ("5.5p1", "<", "5.5p2"),
    ("5.5p10", ">", "5.5p2"),
    ("10", ">", "9"),
    # numeric beats alpha
    ("1.0.111", ">", "1.0.zzz"),
    ("1.1", ">", "1.a"),
    # case sensitivity (uppercase < lowercase in ASCII)
    ("1.0.A", "<", "1.0.a"),
    # leading zeros insignificant
    ("1.01", "=", "1.1"),
    ("1.001", "=", "1.1"),
    # tilde: pre-release, sorts before everything incl. end-of-string
    ("1.0~rc1", "<", "1.0"),
    ("1.0~rc1", "<", "1.0~rc2"),
    ("1.0~~", "<", "1.0~"),
    ("1.0~rc1~git123", "<", "1.0~rc1"),
    # caret: post-release w.r.t. end-of-string, pre w.r.t. continuation
    ("1.0^git1", ">", "1.0"),
    ("1.0^git1", "<", "1.0.1"),
    ("1.0^git1", "<", "1.0^git2"),
    ("1.0~rc1^git1", "<", "1.0"),
    ("1.0^git1~pre", "<", "1.0^git1"),
    # real-world RHEL / SLES version-only strings
    ("19.el7", "<", "26.el7_9"),
    ("1.el9", "<", "1.el9_2.1"),
    ("150400.4.46.1", "<", "150500.55.31.1"),
]

EVR_ORDERING: list[tuple[str, str, str]] = [
    ("1:1.0-1.el9", ">", "2.0-1.el9"),
    ("1.0-1.el9", "<", "1:0.5-1.el9"),
    ("0:1.0-1", "=", "1.0-1"),
    ("1.0-1.el9", "<", "1.0-2.el9"),
    ("1.0-1.el9", "<", "1.0-1.el9_2"),
    ("3.0.7-25.el9_2", ">", "3.0.7-25.el9"),
    ("1.0.2k-19.el7", "<", "1.0.2k-26.el7_9"),
]

_OP = {"<": -1, "=": 0, ">": 1}


@pytest.mark.parametrize("src,op,dst", VERCMP_ORDERING)
def test_vercmp_separators(src: str, op: str, dst: str) -> None:
    assert vercmp(src, dst) == _OP[op], f"vercmp: {src} {op} {dst}"


@pytest.mark.parametrize("src,op,dst", ORDERING)
def test_ordering(src: str, op: str, dst: str) -> None:
    assert compare(src, dst) == _OP[op], f"{src} {op} {dst}"


@pytest.mark.parametrize("src,op,dst", ORDERING)
def test_antisymmetry(src: str, op: str, dst: str) -> None:
    assert compare(dst, src) == -_OP[op], f"antisymmetry: {dst} vs {src}"


def test_zero_strip_oddity() -> None:
    # "10" vs "010a": numeric parts equal after strip, b has leftover 'a' → b wins
    assert compare("10", "010a") == -1


@pytest.mark.parametrize("src,op,dst", EVR_ORDERING)
def test_evr_ordering(src: str, op: str, dst: str) -> None:
    assert compare_evr(src, dst) == _OP[op], f"evr: {src} {op} {dst}"


def test_split_evr() -> None:
    assert split_evr("1:1.0-1.el9") == (1, "1.0", "1.el9")
    assert split_evr("1.0-1.el9") == (0, "1.0", "1.el9")
    assert split_evr("0:1.0-1") == (0, "1.0", "1")
    assert split_evr("1.0") == (0, "1.0", "")


def test_public_api() -> None:
    result = public_compare("1:1.0-1.el9", "2.0-1.el9", kind=PackageType.RPM)
    assert result.newer
    assert result.order == 1
