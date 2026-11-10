"""FH001: Detect unmocked wall-clock time queries and hardcoded sleeps in tests."""

from __future__ import annotations

import ast
from typing import List

from flakehound.models import Diagnostic, RuleMetadata, Severity
from flakehound.rules.base import BaseRule, call_qualified_name
from flakehound.scanner import ParsedTestModule, TestUnit

TIME_FIXTURES = {"freezer", "frozen_time", "time_machine", "monkeypatch", "mocker"}
TIME_DECORATORS = {"freeze_time", "freezegun.freeze_time", "time_machine.travel"}

UNMOCKED_CLOCK_CALLS = {
    "datetime.now",
    "datetime.datetime.now",
    "datetime.utcnow",
    "datetime.datetime.utcnow",
    "date.today",
    "datetime.date.today",
    "time.time",
}

SLEEP_CALLS = {
    "time.sleep",
    "sleep",
    "asyncio.sleep",
}


class UnmockedTimeRule(BaseRule):
    """Detects wall-clock calls and sleeps that cause timing-related test flakiness."""

    metadata = RuleMetadata(
        rule_id="FH001",
        name="unmocked-time-or-sleep",
        severity=Severity.HIGH,
        category="time",
        summary="Unmocked wall-clock query or hardcoded sleep inside test function.",
        remediation=(
            "Freeze time with 'freezegun'/'time_machine' or mock clock functions via 'monkeypatch', "
            "and replace 'time.sleep()' with deterministic event/condition synchronization."
        ),
    )

    def check_test(self, module: ParsedTestModule, test: TestUnit) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        has_time_fixture = bool(test.fixture_args & TIME_FIXTURES)
        has_time_decorator = any(
            any(td in dec for td in TIME_DECORATORS) for dec in test.decorators
        )

        for node in ast.walk(test.node):
            if not isinstance(node, ast.Call):
                continue
            qname = call_qualified_name(node)
            if qname in SLEEP_CALLS:
                diagnostics.append(
                    self.make_diagnostic(
                        module,
                        test,
                        node,
                        f"Hardcoded '{qname}()' call introduces timing sensitivity and slowdowns.",
                    )
                )
            elif qname in UNMOCKED_CLOCK_CALLS and not (has_time_fixture or has_time_decorator):
                diagnostics.append(
                    self.make_diagnostic(
                        module,
                        test,
                        node,
                        f"Unmocked wall-clock call '{qname}()' can fail across timezone or midnight boundaries.",
                    )
                )

        return diagnostics
