"""Core data models for FlakeHound diagnostics and rule metadata."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List


class Severity(str, Enum):
    """Severity levels for detected flaky test hazards."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class RuleMetadata:
    """Metadata describing an individual FlakeHound inspection rule."""

    rule_id: str
    name: str
    severity: Severity
    category: str
    summary: str
    remediation: str


@dataclass(frozen=True)
class Diagnostic:
    """Represents a single flaky test hazard detected in a test file."""

    rule_id: str
    rule_name: str
    severity: Severity
    file_path: str
    line: int
    column: int
    test_name: str
    message: str
    remediation: str
    code_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass
class ScanReport:
    """Aggregated results of scanning a target path."""

    target_path: str
    files_scanned: int = 0
    tests_inspected: int = 0
    diagnostics: List[Diagnostic] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return len(self.diagnostics)

    def count_by_severity(self) -> Dict[str, int]:
        counts = {s.value: 0 for s in Severity}
        for diag in self.diagnostics:
            counts[diag.severity.value] += 1
        return counts

    def count_by_rule(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for diag in self.diagnostics:
            counts[diag.rule_id] = counts.get(diag.rule_id, 0) + 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_path": self.target_path,
            "files_scanned": self.files_scanned,
            "tests_inspected": self.tests_inspected,
            "total_issues": self.total_issues,
            "severity_counts": self.count_by_severity(),
            "rule_counts": self.count_by_rule(),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }
