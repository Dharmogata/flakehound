"""Unit tests for the FlakeHound CLI and report formatters."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from flakehound.cli import main


class TestCLI(unittest.TestCase):
    def test_cli_rules_command(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["rules"])
        self.assertEqual(exit_code, 0)
        out = stdout.getvalue()
        self.assertIn("FH001", out)
        self.assertIn("FH004", out)

    def test_cli_scan_json_and_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            flaky_test = Path(tmp_dir) / "test_example.py"
            flaky_test.write_text(
                """
import time

def test_slow():
    time.sleep(0.1)
""",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code_fail = main(["scan", str(flaky_test), "--format", "json"])
            self.assertEqual(code_fail, 1)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["total_issues"], 1)
            self.assertEqual(payload["diagnostics"][0]["rule_id"], "FH001")

            stdout_md = io.StringIO()
            with contextlib.redirect_stdout(stdout_md):
                code_zero = main(["scan", str(flaky_test), "--exit-zero", "--format", "markdown"])
            self.assertEqual(code_zero, 0)
            md_out = stdout_md.getvalue()
            self.assertIn("## FlakeHound Scan Report", md_out)
            self.assertIn("`FH001`", md_out)

    def test_cli_nonexistent_path_returns_error_code(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(["scan", "does_not_exist_12345.py"])
        self.assertEqual(code, 2)
        self.assertIn("does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
