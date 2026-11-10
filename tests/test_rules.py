"""Unit tests for built-in FlakeHound static analysis rules FH001-FH004."""

import tempfile
import unittest
from pathlib import Path

from flakehound.engine import AnalysisEngine
from flakehound.models import Severity


class TestBuiltInRules(unittest.TestCase):
    def test_fh001_detects_unmocked_time_and_sleep(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test_timing.py"
            test_file.write_text(
                """
import time
from datetime import datetime

def test_flaky_clock():
    now = datetime.now()
    time.sleep(0.5)
    assert now is not None

def test_mocked_clock(freezer):
    now = datetime.now()
    assert now is not None
""",
                encoding="utf-8",
            )

            report = AnalysisEngine(select_ids={"FH001"}).scan_path(test_file)
            self.assertEqual(report.total_issues, 2)
            self.assertTrue(all(d.rule_id == "FH001" for d in report.diagnostics))
            self.assertTrue(all(d.test_name == "test_flaky_clock" for d in report.diagnostics))

    def test_fh002_detects_unseeded_random_and_allows_seeded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test_rng.py"
            test_file.write_text(
                """
import random

def test_unseeded():
    val = random.randint(1, 100)
    assert val >= 1

def test_seeded():
    random.seed(1234)
    val = random.randint(1, 100)
    assert val >= 1
""",
                encoding="utf-8",
            )

            report = AnalysisEngine(select_ids={"FH002"}).scan_path(test_file)
            self.assertEqual(report.total_issues, 1)
            self.assertEqual(report.diagnostics[0].test_name, "test_unseeded")
            self.assertEqual(report.diagnostics[0].rule_id, "FH002")

    def test_fh003_detects_global_mutation_and_os_environ(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test_state.py"
            test_file.write_text(
                """
import os

GLOBAL_ITEMS = []

def test_mutates_global():
    GLOBAL_ITEMS.append("leaked")
    os.environ["API_MODE"] = "prod"
    assert len(GLOBAL_ITEMS) > 0

def test_local_shadow_is_safe():
    GLOBAL_ITEMS = []
    GLOBAL_ITEMS.append("safe")
    assert len(GLOBAL_ITEMS) == 1
""",
                encoding="utf-8",
            )

            report = AnalysisEngine(select_ids={"FH003"}).scan_path(test_file)
            self.assertEqual(report.total_issues, 2)
            self.assertTrue(all(d.test_name == "test_mutates_global" for d in report.diagnostics))

    def test_fh004_detects_file_writes_without_tmp_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test_io.py"
            test_file.write_text(
                """
from pathlib import Path

def test_unsafe_write():
    with open("result.txt", "w") as f:
        f.write("hello")
    Path("out.json").write_text("{}")

def test_safe_write_with_fixture(tmp_path):
    target = tmp_path / "result.txt"
    target.write_text("hello")
    assert target.exists()
""",
                encoding="utf-8",
            )

            report = AnalysisEngine(select_ids={"FH004"}).scan_path(test_file)
            self.assertEqual(report.total_issues, 2)
            self.assertTrue(all(d.test_name == "test_unsafe_write" for d in report.diagnostics))

    def test_engine_min_severity_filtering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test_mixed.py"
            test_file.write_text(
                """
import random
import time

def test_mixed_hazards():
    time.sleep(1)
    random.choice([1, 2, 3])
""",
                encoding="utf-8",
            )

            high_only = AnalysisEngine(min_severity=Severity.HIGH).scan_path(test_file)
            self.assertEqual(high_only.total_issues, 1)
            self.assertEqual(high_only.diagnostics[0].rule_id, "FH001")


if __name__ == "__main__":
    unittest.main()
