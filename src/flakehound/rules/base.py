"""Abstract base class and helper utilities for FlakeHound inspection rules."""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import List

from flakehound.models import Diagnostic, RuleMetadata
from flakehound.scanner import ParsedTestModule, TestUnit


class BaseRule(ABC):
    """Base interface implemented by all FlakeHound static analysis rules."""

    metadata: RuleMetadata

    @abstractmethod
    def check_test(self, module: ParsedTestModule, test: TestUnit) -> List[Diagnostic]:
        """Inspect a single TestUnit within a ParsedTestModule and return diagnostics."""

    def make_diagnostic(
        self,
        module: ParsedTestModule,
        test: TestUnit,
        node: ast.AST,
        message: str,
    ) -> Diagnostic:
        lineno = getattr(node, "lineno", test.lineno)
        col = getattr(node, "col_offset", 0)
        return Diagnostic(
            rule_id=self.metadata.rule_id,
            rule_name=self.metadata.name,
            severity=self.metadata.severity,
            file_path=str(module.file_path),
            line=lineno,
            column=col,
            test_name=test.qualified_name,
            message=message,
            remediation=self.metadata.remediation,
            code_snippet=module.get_line(lineno),
        )


def call_qualified_name(node: ast.Call) -> str:
    """Resolve a dotted call target name such as 'datetime.now' or 'time.sleep'."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = [func.attr]
        curr = func.value
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
        return ".".join(reversed(parts))
    return ""
