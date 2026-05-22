"""Command-line interface for logslice."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from logslice.fast_slicer import fast_slice
from logslice.formatter import get_formatter
from logslice.indexer import build_index
from logslice.parser import parse_timestamp
from logslice.reporter import get_reporter
from logslice.sampler import sample_lines, sample_by_timestamp
from logslice.stats import collect_stats


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Extract time-range segments from large log files.",
    )
    p.add_argument("file", help="Path to the log file")
    p.add_argument("--start", metavar="TS", help="Start timestamp (inclusive)")
    p.add_argument("--end", metavar="TS", help="End timestamp (inclusive)")
    p.add_argument(
        "--format",
        choices=["plain", "numbered", "json"],
        default="plain",
        help="Output format (default: plain)",
    )
    p.add_argument(
        "--stats",
        choices=["text", "json"],
        default=None,
        help="Print slice statistics after output",
    )
    p.add_argument(
        "--sample-step",
        metavar="N",
        type=int,
        default=None,
        help="Keep every N-th line from the slice",
    )
    p.add_argument(
        "--sample-interval",
        metavar="SECS",
        type=float,
        default=None,
        help="Keep lines whose timestamps are at least SECS apart",
    )
    p.add_argument(
        "--max-lines",
        metavar="N",
        type=int,
        default=None,
        help="Maximum number of output lines (applied after sampling)",
    )
    p.add_argument(
        "--use-index",
        action="store_true",
        help="Build an in-memory index for faster seeking",
    )
    return p


def main(argv: Optional[list] = None) -> int:  # noqa: D401
    parser = build_parser()
    args = parser.parse_args(argv)

    start_ts = parse_timestamp(args.start) if args.start else None
    end_ts = parse_timestamp(args.end) if args.end else None

    with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
        raw_lines = list(fast_slice(fh, start=start_ts, end=end_ts))

    # --- sampling -----------------------------------------------------------
    if args.sample_interval is not None:
        raw_lines = list(sample_by_timestamp(raw_lines, args.sample_interval))
    elif args.sample_step is not None:
        result = sample_lines(raw_lines, step=args.sample_step, max_lines=args.max_lines)
        raw_lines = result.lines
    elif args.max_lines is not None:
        raw_lines = raw_lines[: args.max_lines]

    # --- formatting ---------------------------------------------------------
    formatter = get_formatter(args.format)
    for chunk in formatter(raw_lines):
        sys.stdout.write(chunk)

    # --- stats --------------------------------------------------------------
    if args.stats:
        stats = collect_stats(raw_lines, start_ts, end_ts)
        reporter = get_reporter(args.stats)
        sys.stderr.write(reporter(stats) + "\n")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
