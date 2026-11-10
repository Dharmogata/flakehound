"""FH004: Detect hardcoded filesystem writes in tests without tmp_path/tmpdir fixtures."""

from __future__ import annotations

import ast
from typing import List

from flakehound.models import Diagnostic, RuleMetadata, Severity
from flakehound.rules.base import BaseRule, call_qualified_name
from flakehound.scanner import ParsedTestModule, TestUnit

TEMP_FIXTURES = {"tmp_path", "tmpdir", "tmp_path_factory", "tmpdir_factory", "fs"}
TEMPFILE_CALLS = {
    "tempfile.TemporaryDirectory",
    "TemporaryDirectory",
    "tempfile.NamedTemporaryFile",
    "NamedTemporaryFile",
    "tempfile.mkdtemp",
    "mkdtemp",
}
WRITE_MODES = {"w", "wb", "a", "ab", "x", "xb", "w+", "r+", "a+"}
PATH_WRITE_METHODS = {"write_text", "write_bytes", "mkdir", "unlink", "rmdir"}


class HardcodedFileWriteRule(BaseRule):
    """Detects filesystem writes to static paths without temporary directory fixtures."""

    metadata = RuleMetadata(
        rule_id="FH004",
        name="hardcoded-file-write",
        severity=Severity.MEDIUM,
        category="filesystem",
        summary="Filesystem write in test without 'tmp_path' or 'tempfile' isolation.",
        remediation=(
            "Accept the 'tmp_path' pytest fixture or use 'tempfile.TemporaryDirectory()' "
            "so parallel test workers do not collide on static paths."
        ),
    )

    def check_test(self, module: ParsedTestModule, test: TestUnit) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        if test.fixture_args & TEMP_FIXTURES:
            return diagnostics

        all_calls = [n for n in ast.walk(test.node) if isinstance(n, ast.Call)]
        if any(call_qualified_name(c) in TEMPFILE_CALLS for c in all_calls):
            return diagnostics

        for node in all_calls:

            qname = call_qualified_name(node)
            if qname in {"open", "io.open", "pathlib.Path.open"} and self._is_write_open(node):
                diagnostics.append(
                    self.make_diagnostic(
                        module,
                        test,
                        node,
                        "File opened in write mode without 'tmp_path' fixture risks parallel test collisions.",
                    )
                )
            elif isinstance(node.func, ast.Attribute) and node.func.attr in PATH_WRITE_METHODS:
                diagnostics.append(
                    self.make_diagnostic(
                        module,
                        test,
                        node,
                        f"Filesystem write method '.{node.func.attr}()' called in test without 'tmp_path' fixture.",
                    )
                )

        return diagnostics

    @staticmethod
    def _is_write_open(node: ast.Call) -> bool:
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
            return any(m in node.args[1].value for m in ("w", "a", "x", "+"))
        for kw in node.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value in WRITE_MODES or any(m in kw.value.value for m in ("w", "a", "x", "+"))
        return False
