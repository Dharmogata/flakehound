"""FH003: Detect module-level state mutation and raw os.environ writes in tests."""

from __future__ import annotations

import ast
from typing import List, Set

from flakehound.models import Diagnostic, RuleMetadata, Severity
from flakehound.rules.base import BaseRule, call_qualified_name
from flakehound.scanner import ParsedTestModule, TestUnit

MUTATING_METHODS = {
    "append",
    "extend",
    "insert",
    "pop",
    "remove",
    "clear",
    "update",
    "setdefault",
    "add",
    "discard",
}


class GlobalStateMutationRule(BaseRule):
    """Detects mutations to module-level collections or os.environ that leak across tests."""

    metadata = RuleMetadata(
        rule_id="FH003",
        name="global-state-mutation",
        severity=Severity.HIGH,
        category="isolation",
        summary="In-place mutation of module-level state or os.environ inside test.",
        remediation=(
            "Use 'monkeypatch.setitem()', 'monkeypatch.setenv()', or fresh per-test fixtures "
            "instead of mutating module-level collections or 'os.environ' directly."
        ),
    )

    def check_test(self, module: ParsedTestModule, test: TestUnit) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        local_vars: Set[str] = set(test.fixture_args)

        for node in ast.walk(test.node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        local_vars.add(target.id)

        for node in ast.walk(test.node):
            # 1. Check method calls like SHARED_LIST.append(...) or os.environ.update(...)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                method = node.func.attr
                owner = node.func.value
                if (
                    isinstance(owner, ast.Name)
                    and owner.id in module.module_mutables
                    and owner.id not in local_vars
                    and method in MUTATING_METHODS
                ):
                    diagnostics.append(
                        self.make_diagnostic(
                            module,
                            test,
                            node,
                            f"Test mutates module-level state '{owner.id}.{method}()', causing test-order dependency.",
                        )
                    )
                elif call_qualified_name(node) in {"os.environ.update", "os.environ.pop", "os.environ.clear"}:
                    diagnostics.append(
                        self.make_diagnostic(
                            module,
                            test,
                            node,
                            "Direct mutation of 'os.environ' leaks environment variables to subsequent tests.",
                        )
                    )

            # 2. Check subscript assignments like SHARED_DICT['k'] = v or os.environ['k'] = v
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Subscript):
                        val = target.value
                        if (
                            isinstance(val, ast.Name)
                            and val.id in module.module_mutables
                            and val.id not in local_vars
                        ):
                            diagnostics.append(
                                self.make_diagnostic(
                                    module,
                                    test,
                                    node,
                                    f"Subscript assignment to module-level collection '{val.id}' leaks state across tests.",
                                )
                            )
                        elif (
                            isinstance(val, ast.Attribute)
                            and isinstance(val.value, ast.Name)
                            and val.value.id == "os"
                            and val.attr == "environ"
                        ):
                            diagnostics.append(
                                self.make_diagnostic(
                                    module,
                                    test,
                                    node,
                                    "Direct assignment to 'os.environ[...]' without 'monkeypatch.setenv()' pollutes process state.",
                                )
                            )

        return diagnostics
