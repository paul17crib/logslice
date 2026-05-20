"""Command-line interface for logslice."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.formatter import get_formatter
from logslice.parser import parse_timestamp
from logslice.slicer import slice_log


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Extract a time-range segment from a log file.",
    )
    p.add_argument("file", type=Path, help="Path to the log file.")
    p.add_argument(
        "--start",
        metavar="TIMESTAMP",
        default=None,
        help="Start of the time range (inclusive). Omit to start from beginning.",
    )
    p.add_argument(
        "--end",
        metavar="TIMESTAMP",
        default=None,
        help="End of the time range (inclusive). Omit to read until end of file.",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["plain", "numbered", "json"],
        default="plain",
        help="Output format (default: plain).",
    )
    p.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Write output to FILE instead of stdout.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI.

    Returns:
        Exit code (0 on success, non-zero on error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.file.exists():
        print(f"logslice: error: file not found: {args.file}", file=sys.stderr)
        return 1

    start_dt = parse_timestamp(args.start) if args.start else None
    end_dt = parse_timestamp(args.end) if args.end else None

    formatter = get_formatter(args.fmt)

    try:
        lines = slice_log(args.file, start=start_dt, end=end_dt)

        if args.fmt == "json":
            formatted = formatter(lines, start_time=start_dt, end_time=end_dt)
        else:
            formatted = formatter(lines)

        out = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
        try:
            for line in formatted:
                print(line, file=out, end="" if args.fmt != "json" else "\n")
        finally:
            if args.output:
                out.close()
    except Exception as exc:  # noqa: BLE001
        print(f"logslice: error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
