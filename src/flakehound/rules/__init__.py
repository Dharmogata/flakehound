"""Built-in static analysis rules for FlakeHound."""

from typing import Dict, List, Type

from flakehound.rules.base import BaseRule
from flakehound.rules.fh001_time import UnmockedTimeRule
from flakehound.rules.fh002_random import UnseededRandomRule
from flakehound.rules.fh003_global import GlobalStateMutationRule
from flakehound.rules.fh004_io import HardcodedFileWriteRule

BUILTIN_RULE_CLASSES: List[Type[BaseRule]] = [
    UnmockedTimeRule,
    UnseededRandomRule,
    GlobalStateMutationRule,
    HardcodedFileWriteRule,
]


def get_default_rules() -> List[BaseRule]:
    """Instantiate all built-in FlakeHound analysis rules."""
    return [cls() for cls in BUILTIN_RULE_CLASSES]


def get_rule_map() -> Dict[str, BaseRule]:
    """Return a mapping of rule_id -> rule instance."""
    return {rule.metadata.rule_id: rule for rule in get_default_rules()}


__all__ = [
    "BaseRule",
    "UnmockedTimeRule",
    "UnseededRandomRule",
    "GlobalStateMutationRule",
    "HardcodedFileWriteRule",
    "BUILTIN_RULE_CLASSES",
    "get_default_rules",
    "get_rule_map",
]
