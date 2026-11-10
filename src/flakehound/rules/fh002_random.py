"""FH002: Detect unseeded pseudo-random number generation in tests."""

from __future__ import annotations

import ast
from typing import List

from flakehound.models import Diagnostic, RuleMetadata, Severity
from flakehound.rules.base import BaseRule, call_qualified_name
from flakehound.scanner import ParsedTestModule, TestUnit

RANDOM_CALLS = {
    "random.random",
    "random.randint",
    "random.choice",
    "random.choices",
    "random.sample",
    "random.shuffle",
    "random.uniform",
    "random.randrange",
}

SEED_CALLS = {
    "random.seed",
    "seed",
}


class UnseededRandomRule(BaseRule):
    """Detects random value generation in tests without an explicit seed."""

    metadata = RuleMetadata(
        rule_id="FH002",
        name="unseeded-random-call",
        severity=Severity.MEDIUM,
        category="randomness",
        summary="Unseeded random number generation inside test function.",
        remediation=(
            "Call 'random.seed(<constant>)' at the start of the test, instantiate a seeded "
            "'random.Random(42)' instance, or pass deterministic test inputs."
        ),
    )

    def check_test(self, module: ParsedTestModule, test: TestUnit) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        if "monkeypatch" in test.fixture_args or "mocker" in test.fixture_args:
            return diagnostics

        calls = [node for node in ast.walk(test.node) if isinstance(node, ast.Call)]
        has_seed = any(call_qualified_name(c) in SEED_CALLS for c in calls)
        if has_seed:
            return diagnostics

        for node in calls:
            qname = call_qualified_name(node)
            if qname in RANDOM_CALLS:
                diagnostics.append(
                    self.make_diagnostic(
                        module,
                        test,
                        node,
                        f"Call to '{qname}()' without 'random.seed()' produces non-reproducible test runs.",
                    )
                )

        return diagnostics
