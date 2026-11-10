"""Unit tests for the FlakeHound AST test scanner (compatible with pytest and unittest)."""

import tempfile
import unittest
from pathlib import Path

from flakehound.scanner import discover_test_files, parse_test_module


class TestScanner(unittest.TestCase):
    def test_parse_module_discovers_functions_and_methods(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample = Path(tmp_dir) / "test_sample.py"
            sample.write_text(
                """
import os

SHARED_CACHE = []
CONFIG_MAP = {"debug": True}

def helper_func():
    return 42

def test_top_level(monkeypatch, tmp_path):
    assert helper_func() == 42

class TestSuite:
    def test_method_level(self, freezer):
        assert True
""",
                encoding="utf-8",
            )

            parsed = parse_test_module(sample)
            self.assertIsNotNone(parsed)
            assert parsed is not None
            self.assertIn("SHARED_CACHE", parsed.module_mutables)
            self.assertIn("CONFIG_MAP", parsed.module_mutables)
            self.assertEqual(len(parsed.test_units), 2)

            top_unit = parsed.test_units[0]
            self.assertEqual(top_unit.qualified_name, "test_top_level")
            self.assertEqual(top_unit.fixture_args, {"monkeypatch", "tmp_path"})

            method_unit = parsed.test_units[1]
            self.assertEqual(method_unit.qualified_name, "TestSuite::test_method_level")
            self.assertEqual(method_unit.fixture_args, {"freezer"})

    def test_discover_test_files_filters_non_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "test_alpha.py").write_text("def test_a(): pass\n", encoding="utf-8")
            (root / "beta_test.py").write_text("def test_b(): pass\n", encoding="utf-8")
            (root / "utils.py").write_text("def helper(): pass\n", encoding="utf-8")

            found = [p.name for p in discover_test_files(root)]
            self.assertEqual(found, ["beta_test.py", "test_alpha.py"])


if __name__ == "__main__":
    unittest.main()
