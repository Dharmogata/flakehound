"""Command-line interface for FlakeHound."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Set

from flakehound import __version__
from flakehound.engine import AnalysisEngine
from flakehound.models import Severity
from flakehound.reporters import (
    format_json_report,
    format_markdown_report,
    format_rules_catalog,
    format_text_report,
)
from flakehound.rules import get_default_rules


def _parse_csv_ids(raw: Optional[str]) -> Optional[Set[str]]:
    if not raw:
        return None
    items = {part.strip().upper() for part in raw.split(",") if part.strip()}
    return items or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flakehound",
        description="Static flaky test detector and test isolation analyzer for pytest suites.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"flakehound {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    # flakehound scan <path>
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a test file or directory for flaky test hazards.",
    )
    scan_parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target test file or directory to inspect (default: current directory).",
    )
    scan_parser.add_argument(
        "--select",
        type=str,
        default=None,
        help="Comma-separated rule IDs to enable (e.g. FH001,FH003).",
    )
    scan_parser.add_argument(
        "--ignore",
        type=str,
        default=None,
        help="Comma-separated rule IDs to ignore (e.g. FH002).",
    )
    scan_parser.add_argument(
        "--min-severity",
        choices=["low", "medium", "high"],
        default="low",
        help="Minimum severity level to report (default: low).",
    )
    scan_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output report format (default: text).",
    )
    scan_parser.add_argument(
        "--no-remediation",
        action="store_true",
        help="Omit remediation hints from text output.",
    )
    scan_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write formatted report to the given file path instead of stdout.",
    )
    scan_parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always return exit code 0 even when issues are found.",
    )

    # flakehound rules
    subparsers.add_parser(
        "rules",
        help="List all built-in FlakeHound inspection rules and remediations.",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "rules":
        metas = [rule.metadata for rule in get_default_rules()]
        print(format_rules_catalog(metas))
        return 0

    if args.command == "scan":
        target_path = Path(args.target)
        if not target_path.exists():
            print(f"Error: target path '{target_path}' does not exist.", file=sys.stderr)
            return 2

        engine = AnalysisEngine(
            select_ids=_parse_csv_ids(args.select),
            ignore_ids=_parse_csv_ids(args.ignore),
            min_severity=Severity(args.min_severity),
        )
        report = engine.scan_path(target_path)

        if args.format == "json":
            rendered = format_json_report(report)
        elif args.format == "markdown":
            rendered = format_markdown_report(report)
        else:
            rendered = format_text_report(report, show_remediation=not args.no_remediation)

        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)

        if report.total_issues > 0 and not args.exit_zero:
            return 1
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
