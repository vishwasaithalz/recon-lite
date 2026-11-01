"""Command-line interface for Recon Lite."""

from __future__ import annotations

import argparse
import json
import sys

from .analyzer import analyze_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recon-lite",
        description="Analyze a local HTTP response-header file. This tool makes no network requests.",
    )
    parser.add_argument("file", help="Path to a raw HTTP header block or JSON header mapping")
    parser.add_argument("--format", choices=("text", "json"), default="text",
                        help="Output format (default: text)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = analyze_file(args.file)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
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
