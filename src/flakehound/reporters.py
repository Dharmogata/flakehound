"""Output formatters for FlakeHound scan reports and rule listings."""

from __future__ import annotations

import json
from typing import Iterable, List

from flakehound.models import RuleMetadata, ScanReport


def format_text_report(report: ScanReport, show_remediation: bool = True) -> str:
    """Format a ScanReport into a human-readable terminal summary."""
    lines: List[str] = []
    lines.append(
        f"FlakeHound Scan: {report.target_path} "
        f"({report.files_scanned} files, {report.tests_inspected} tests inspected)"
    )
    lines.append("=" * 76)

    if not report.diagnostics:
        lines.append("No flaky test hazards detected.")
        return "\n".join(lines)

    for diag in report.diagnostics:
        loc = f"{diag.file_path}:{diag.line}:{diag.column}"
        lines.append(
            f"[{diag.rule_id}] ({diag.severity.value.upper()}) {loc} in {diag.test_name}"
        )
        lines.append(f"  Problem: {diag.message}")
        if diag.code_snippet:
            lines.append(f"  Code:    {diag.code_snippet}")
        if show_remediation:
            lines.append(f"  Fix:     {diag.remediation}")
        lines.append("-" * 76)

    sev_counts = report.count_by_severity()
    lines.append(
        f"Summary: {report.total_issues} issue(s) found "
        f"(high={sev_counts['high']}, medium={sev_counts['medium']}, low={sev_counts['low']})"
    )
    return "\n".join(lines)


def format_json_report(report: ScanReport) -> str:
    """Format a ScanReport as structured JSON."""
    return json.dumps(report.to_dict(), indent=2)


def format_markdown_report(report: ScanReport) -> str:
    """Format a ScanReport as a Markdown table suitable for PR comments or CI summaries."""
    lines: List[str] = [
        f"## FlakeHound Scan Report (`{report.target_path}`)",
        "",
        f"- **Files scanned:** {report.files_scanned}",
        f"- **Tests inspected:** {report.tests_inspected}",
        f"- **Total hazards:** {report.total_issues}",
        "",
    ]
    if not report.diagnostics:
        lines.append("No flaky test hazards detected.")
        return "\n".join(lines)

    lines.extend(
        [
            "| Rule | Severity | Location | Test | Message |",
            "| :--- | :---: | :--- | :--- | :--- |",
        ]
    )
    for d in report.diagnostics:
        loc = f"`{d.file_path}:{d.line}`"
        lines.append(
            f"| `{d.rule_id}` | **{d.severity.value.upper()}** | {loc} | `{d.test_name}` | {d.message} |"
        )
    return "\n".join(lines)


def format_rules_catalog(rules: Iterable[RuleMetadata]) -> str:
    """Format the list of available FlakeHound rules."""
    lines = [
        "Available FlakeHound Rules:",
        "=" * 76,
    ]
    for meta in rules:
        lines.append(
            f"{meta.rule_id} [{meta.severity.value.upper()}] ({meta.category}) - {meta.name}"
        )
        lines.append(f"  Summary:     {meta.summary}")
        lines.append(f"  Remediation: {meta.remediation}")
        lines.append("-" * 76)
    return "\n".join(lines)
