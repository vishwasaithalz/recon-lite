"""Command-line interface for Recon Lite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyzer import analyze_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recon-lite",
        description="Analyze a local HTTP response-header file. This tool makes no network requests.",
    )
    parser.add_argument("file", help="Path to a raw HTTP header block or JSON header mapping")
    parser.add_argument("--format", choices=("text", "json"), default="text",
                        help="Output format (default: text)")
    parser.add_argument("--json", action="store_true",
                        help="Shorthand for --format json, with no network access")
    parser.add_argument("--report", metavar="FILE",
                        help="Save JSON review to a NEW local file; never overwrite an existing file")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = analyze_file(args.file)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.report:
        # Exclusive mode avoids silently overwriting prior review evidence.
        # Never create directories, execute commands or make network requests.
        destination = Path(args.report).expanduser()
        try:
            with destination.open("x", encoding="utf-8") as output:
                output.write(json.dumps(report, indent=2) + "\n")
        except OSError as exc:
            print(f"error: cannot save report to '{destination}': {exc}", file=sys.stderr)
            return 2
        print(f"Saved JSON report to {destination}")
        return 0

    if args.json or args.format == "json":
        print(json.dumps(report, indent=2))
        return 0

    print("RECON LITE | HTTP RESPONSE HEADER REVIEW")
    print("=" * 44)
    print(f"Educational score: {report['score']}/100")
    print(report["score_note"])
    print(report["scope"])
    print()
    for item in report["findings"]:
        print(f"[{item['severity'].upper()}] {item['header']}: {item['status']}")
        print(f"  {item['detail']}")
        print(f"  Recommendation: {item['recommendation']}")
    print()
    print("Review findings in application context before making production changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
