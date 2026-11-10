"""Core analysis engine orchestrating test discovery and rule execution."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Set

from flakehound.models import Diagnostic, ScanReport, Severity
from flakehound.rules import BaseRule, get_default_rules
from flakehound.scanner import discover_test_files, parse_test_module

SEVERITY_RANK = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
}


class AnalysisEngine:
    """Executes configured FlakeHound rules across discovered pytest modules."""

    def __init__(
        self,
        rules: Optional[Iterable[BaseRule]] = None,
        select_ids: Optional[Set[str]] = None,
        ignore_ids: Optional[Set[str]] = None,
        min_severity: Severity = Severity.LOW,
    ) -> None:
        all_rules = list(rules) if rules is not None else get_default_rules()
        self.active_rules: List[BaseRule] = []
        for rule in all_rules:
            rid = rule.metadata.rule_id.upper()
            if select_ids and rid not in {s.upper() for s in select_ids}:
                continue
            if ignore_ids and rid in {i.upper() for i in ignore_ids}:
                continue
            if SEVERITY_RANK[rule.metadata.severity] < SEVERITY_RANK[min_severity]:
                continue
            self.active_rules.append(rule)

    def scan_path(self, target: Path) -> ScanReport:
        """Scan a file or directory and return an aggregated ScanReport."""
        report = ScanReport(target_path=str(target))
        files = discover_test_files(target)

        for file_path in files:
            parsed = parse_test_module(file_path)
            if parsed is None:
                continue
            report.files_scanned += 1
            report.tests_inspected += len(parsed.test_units)

            file_diagnostics: List[Diagnostic] = []
            for test_unit in parsed.test_units:
                for rule in self.active_rules:
                    file_diagnostics.extend(rule.check_test(parsed, test_unit))

            file_diagnostics.sort(key=lambda d: (d.line, d.column, d.rule_id))
            report.diagnostics.extend(file_diagnostics)

        return report
