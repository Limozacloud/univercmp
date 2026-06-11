"""Command-line interface for univercmp."""

from __future__ import annotations

import argparse
import sys

from univercmp import InvalidVersionError, PackageType, __version__, compare, validate


def _kind_choices() -> list[str]:
    return [m.value for m in PackageType]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="univercmp",
        description="Compare or validate package version strings.",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    sub = p.add_subparsers(dest="command", required=True)

    # ------------------------------------------------------------------ compare
    cmp_p = sub.add_parser("compare", help="Compare two version strings.")
    cmp_p.add_argument("src", help="Source (left-hand) version.")
    cmp_p.add_argument("dst", help="Destination (right-hand) version.")
    cmp_p.add_argument(
        "--type",
        "-t",
        dest="kind",
        required=True,
        choices=_kind_choices(),
        metavar="TYPE",
        help=f"Package ecosystem. Choices: {', '.join(_kind_choices())}.",
    )
    cmp_p.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Print only the numeric result (-1, 0 or 1).",
    )

    # ----------------------------------------------------------------- validate
    val_p = sub.add_parser("validate", help="Check whether a version string is valid.")
    val_p.add_argument("version", help="Version string to validate.")
    val_p.add_argument(
        "--type",
        "-t",
        dest="kind",
        required=True,
        choices=_kind_choices(),
        metavar="TYPE",
        help=f"Package ecosystem. Choices: {', '.join(_kind_choices())}.",
    )

    return p


def main(argv: list[str] | None = None) -> int:
    """Entry point — returns an exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    match args.command:
        case "compare":
            try:
                result = compare(args.src, args.dst, kind=args.kind)
            except InvalidVersionError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2
            if args.quiet:
                print(result.order)
            else:
                sym = "<" if result.older else ("=" if result.equal else ">")
                print(f"{args.src}  {sym}  {args.dst}  ({result.verdict})")
            return 0

        case "validate":
            ok = validate(args.version, kind=args.kind)
            if not ok:
                print(
                    f"invalid: {args.version!r} is not a valid {args.kind} version",
                    file=sys.stderr,
                )
            return 0 if ok else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
