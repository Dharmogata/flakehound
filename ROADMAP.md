# FlakeHound Engineering Roadmap (200+ Hours)

This document outlines the multi-phase software engineering roadmap for **FlakeHound**, evolving from a static AST flaky-test detector into a full-featured Python test intelligence, automated refactoring (Codemod), order-dependency bisection, and mutation testing platform.

---

## Phase 1: Core Static AST Engine & Foundational Rules (Completed - v0.1.0)
- [x] Core diagnostic data models (`Diagnostic`, `RuleMetadata`, `ScanReport`).
- [x] AST test function, class method, fixture parameter, and module-level mutable collector.
- [x] Foundational rules `FH001` (time/sleep), `FH002` (unseeded random), `FH003` (global state mutation), `FH004` (hardcoded file writes).
- [x] CLI (`scan`, `rules`) with `--select`, `--ignore`, `--min-severity`, and `text`/`json`/`markdown` formatters.

---

## Phase 2: Extended Static Rule Catalog & Cross-File Call Graph (~35 Hours)
- [ ] **Rule `FH005` (`os.chdir` leakage):** Detect working directory changes without `monkeypatch.chdir()` or context restoration.
- [ ] **Rule `FH006` (Network & Socket leakage):** Detect unmocked `urllib.request`, `socket.connect`, `requests.*`, and `httpx.*` calls inside unit tests.
- [ ] **Rule `FH007` (Hardcoded TCP/UDP ports):** Detect hardcoded port numbers in test servers that collide under parallel execution.
- [ ] **Rule `FH008` (Unordered collection assertions):** Detect string/JSON equality assertions over `set` or un-sorted `dict.keys()` projections.
- [ ] **Rule `FH009` (Asyncio task leakage):** Detect un-awaited coroutines and `asyncio.create_task()` calls without cleanup.
- [ ] **Rule `FH010` (Thread/Process cleanup):** Detect `threading.Thread.start()` or `multiprocessing.Process.start()` without `.join(timeout=...)`.
- [ ] **Rule `FH011` – `FH025`:** Database session rollback omissions, environment variable leakage in `setUp`, floating-point exact equality (`==` instead of `pytest.approx`), and broad `except Exception: pass` blocks in tests.
- [ ] **Cross-File Helper Call Graph (`callgraph.py`):** Trace helper functions imported from `tests/helpers.py` or `conftest.py` to detect indirect flakiness hazards up to $k$ call hops deep.
- [ ] **Inline Suppression Comments (`# flakehound: ignore[FH001]`):** Tokenize source comments to support line-level and block-level suppressions, plus `--report-unused-ignores`.
- [ ] **`pyproject.toml` Configuration Loader (`config.py`):** Parse `[tool.flakehound]` settings for per-directory rule overrides, custom fixture whitelists, and exclude globs.

---

## Phase 3: AST Automated Refactoring & Codemod Engine (`--fix`) (~40 Hours)
- [ ] **Lossless Source Patching Engine (`fixer.py`):** Line/column span replacement and unified diff generation (`flakehound scan --diff` and `flakehound scan --fix`).
- [ ] **Autofix for `FH004`:** Automatically inject `tmp_path` into the test function signature and rewrite hardcoded `open("foo.txt", "w")` calls to `open(tmp_path / "foo.txt", "w")`.
- [ ] **Autofix for `FH003` (`os.environ`):** Automatically inject `monkeypatch` into test parameters and rewrite `os.environ["KEY"] = "VAL"` to `monkeypatch.setenv("KEY", "VAL")`.
- [ ] **Autofix for Floating-Point Assertions:** Rewrite `assert a == 0.1 + 0.2` into `assert a == pytest.approx(0.1 + 0.2)`.
- [ ] **`unittest.TestCase` to `pytest` Codemod Suite:** Automated AST migration converting `self.assertEqual`, `self.assertTrue`, `self.assertRaises` into idiomatic `pytest` assertions.

---

## Phase 4: Dynamic Test Isolation Runner & Order-Dependency Bisector (~35 Hours)
- [ ] **Subprocess Test Runner (`runner.py`):** Execute discovered test items in isolated subprocesses with configurable repeat counts (`flakehound verify --repeat 10`).
- [ ] **Random Order Shuffler (`flakehound shuffle`):** Execute test modules and functions under deterministic PRNG seeds to uncover hidden state pollution.
- [ ] **Delta-Debugging Bisector (`flakehound bisect <failing_test>`):** Given a test that passes in isolation but fails after the full suite, automatically run binary search ($O(\log N)$ subset execution) to identify the exact minimal polluting predecessor test.
- [ ] **Filesystem & Environment Diff Auditor:** Snapshot `os.environ`, `sys.modules`, working directory, and open file descriptors before and after each test execution.

---

## Phase 5: SQLite Telemetry Store & Regression Time-Machine (~35 Hours)
- [ ] **Local SQLite Storage Engine (`storage/db.py`):** Schema for storing historical scan results, dynamic test run durations, pass/fail transitions, and git commit SHAs.
- [ ] **Flakiness Score Calculator (`storage/analytics.py`):** Compute rolling flip-rate, failure entropy, and P95 duration drift per test across commit history.
- [ ] **Baseline Snapshot Comparison (`flakehound scan --baseline main`):** Report only newly introduced flaky test hazards in dirty working trees or feature branches (`git diff` integration).

---

## Phase 6: AST Mutation Testing Engine (`flakehound mutate`) (~40 Hours)
- [ ] **AST Mutant Generator (`mutator/operators.py`):** Arithmetic, relational (`<` ↔ `<=`, `==` ↔ `!=`), boolean, and return-value mutation operators for target application code.
- [ ] **Test-to-Source Coverage Mapper:** Run only the relevant subset of tests covering the mutated source lines.
- [ ] **Mutation Score & Surviving Mutant Reporter:** Identify weak tests that pass even when underlying business logic is mutated.

---

## Phase 7: CI/CD Integrations, SARIF Exporter & Interactive Reports (~20 Hours)
- [ ] **SARIF v2.1.0 Exporter:** Native integration with GitHub Code Scanning alerts.
- [ ] **JUnit XML Enricher & Standalone HTML Dashboard:** Self-contained single-file HTML report with filterable diagnostics and historical charts.
- [ ] **Plugin Architecture:** Entry-point discovery allowing teams to register custom organization-specific AST test rules.
