"""AST test collector that discovers test functions, fixtures, and module-level state."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

ASTFunction = Union[ast.FunctionDef, ast.AsyncFunctionDef]


@dataclass
class TestUnit:
    """Represents a single discovered test function or method within a module."""

    name: str
    qualified_name: str
    node: ASTFunction
    lineno: int
    end_lineno: int
    fixture_args: Set[str] = field(default_factory=set)
    decorators: List[str] = field(default_factory=list)
    class_name: Optional[str] = None


@dataclass
class ParsedTestModule:
    """Container for a parsed Python test file and its AST metadata."""

    file_path: Path
    source: str
    lines: List[str]
    tree: ast.Module
    test_units: List[TestUnit] = field(default_factory=list)
    module_mutables: Dict[str, int] = field(default_factory=dict)
    imports: Set[str] = field(default_factory=set)

    def get_line(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""


def _decorator_name(dec: ast.expr) -> str:
    if isinstance(dec, ast.Name):
        return dec.id
    if isinstance(dec, ast.Attribute):
        prefix = _decorator_name(dec.value)
        return f"{prefix}.{dec.attr}" if prefix else dec.attr
    if isinstance(dec, ast.Call):
        return _decorator_name(dec.func)
    return ""


def _is_mutable_literal_or_call(expr: Optional[ast.expr]) -> bool:
    if expr is None:
        return False
    if isinstance(expr, (ast.List, ast.Dict, ast.Set)):
        return True
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
        return expr.func.id in {"list", "dict", "set", "defaultdict", "Counter", "deque"}
    return False


def discover_test_files(target: Path) -> List[Path]:
    """Recursively discover Python test files matching pytest conventions."""
    if target.is_file():
        return [target] if target.suffix == ".py" else []

    discovered: List[Path] = []
    for path in sorted(target.rglob("*.py")):
        parts = set(path.parts)
        if any(ignored in parts for ignored in {".git", ".venv", "venv", "__pycache__", "build", "dist"}):
            continue
        name = path.name
        if name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py":
            discovered.append(path)
    return discovered


def parse_test_module(file_path: Path) -> Optional[ParsedTestModule]:
    """Parse a Python test file into a ParsedTestModule with discovered tests and globals."""
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return None

    lines = source.splitlines()
    module = ParsedTestModule(
        file_path=file_path,
        source=source,
        lines=lines,
        tree=tree,
    )

    # 1. Collect module-level imports and top-level mutable state
    for stmt in tree.body:
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                module.imports.add(alias.asname or alias.name)
        elif isinstance(stmt, ast.ImportFrom):
            for alias in stmt.names:
                module.imports.add(alias.asname or alias.name)
        elif isinstance(stmt, ast.Assign):
            if _is_mutable_literal_or_call(stmt.value):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("__"):
                        module.module_mutables[target.id] = stmt.lineno
        elif isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name) and _is_mutable_literal_or_call(stmt.value):
                module.module_mutables[stmt.target.id] = stmt.lineno

    # 2. Collect top-level and class-based test functions
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if stmt.name.startswith("test_"):
                module.test_units.append(_build_test_unit(stmt, class_name=None))
        elif isinstance(stmt, ast.ClassDef):
            for item in stmt.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                    module.test_units.append(_build_test_unit(item, class_name=stmt.name))

    return module


def _build_test_unit(node: ASTFunction, class_name: Optional[str]) -> TestUnit:
    arg_names = {arg.arg for arg in node.args.args if arg.arg not in {"self", "cls"}}
    arg_names.update(arg.arg for arg in node.args.kwonlyargs)
    decorators = [_decorator_name(d) for d in node.decorator_list]
    qualified = f"{class_name}::{node.name}" if class_name else node.name
    return TestUnit(
        name=node.name,
        qualified_name=qualified,
        node=node,
        lineno=node.lineno,
        end_lineno=getattr(node, "end_lineno", node.lineno),
        fixture_args=arg_names,
        decorators=[d for d in decorators if d],
        class_name=class_name,
    )
