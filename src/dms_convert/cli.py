"""Command-line interface."""

from __future__ import annotations

import argparse
import re
import sys

from .core import format_coordinate, parse_coordinate

_NEGATIVE = re.compile(r"-[0-9.]")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="dms-convert",
        description="Convert lat/lon pairs between decimal degrees, DMS and degrees-decimal-minutes.",
    )
    p.add_argument("coords", nargs="*", help='coordinate pairs, e.g. "40 26 46 N 79 58 56 W" (stdin if omitted)')
    p.add_argument("-t", "--to", choices=["dd", "dms", "ddm"], default="dd", help="output format (default: dd)")
    p.add_argument("-p", "--precision", type=int, help="decimals of the last unit")
    argv = sys.argv[1:] if argv is None else list(argv)
    # A leading space keeps argparse from treating "-40.5, 10" as an option;
    # the parser ignores surrounding whitespace.
    argv = [" " + a if _NEGATIVE.match(a) else a for a in argv]
    args = p.parse_args(argv)
    if args.precision is not None and not 0 <= args.precision <= 12:
        p.error("--precision must be between 0 and 12")

    inputs = args.coords or [ln for ln in sys.stdin.read().splitlines() if ln.strip()]
    if not inputs:
        p.error("no coordinates given")
    status = 0
    for text in inputs:
        text = text.strip()
        try:
            print(format_coordinate(*parse_coordinate(text), args.to, args.precision))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
