# FlakeHound

**FlakeHound** is a command-line static flaky-test detector, AST test-smell analyzer, and test-isolation toolkit for Python `pytest` and `unittest` suites.

Flaky tests erode CI reliability by passing on developer machines and failing intermittently in continuous integration. FlakeHound inspects Python test files statically via the standard `ast` module—without executing slow test suites—to pinpoint non-deterministic patterns before they reach main branches.

---

## Who It's For

- **Python developers and backend engineers** who want fast pre-commit or CI checks against flaky test patterns.
- **Open-source maintainers and QA engineers** diagnosing order-dependent test failures, parallel `pytest-xdist` file collisions, or timing-sensitive assertions.

---

## What It's Built With

- **Language:** Python 3.10+
- **Core Architecture:** Pure Python standard library (`ast`, `argparse`, `pathlib`, `json`, `unittest`) with **zero third-party runtime dependencies**.
- **Test Suite:** Compatible with both `pytest` and `python -m unittest`.

---

## Features

- **Fixture-aware AST inspection:** Recognizes `pytest` isolation fixtures (`tmp_path`, `tmpdir`, `monkeypatch`, `freezer`, `mocker`) and `tempfile.TemporaryDirectory` contexts to avoid false positives when state or clocks are properly isolated.
- **Built-in Flakiness Rules (`FH001` – `FH004`):**
  - `FH001` (`HIGH` / `time`): Unmocked wall-clock queries (`datetime.now()`, `time.time()`, `date.today()`) and hardcoded `time.sleep()` calls.
  - `FH002` (`MEDIUM` / `randomness`): Unseeded `random.*` calls inside test functions without `random.seed()`.
  - `FH003` (`HIGH` / `isolation`): In-place mutation of module-level mutable collections (`SHARED_LIST.append()`, `GLOBAL_DICT['k'] = v`) or raw `os.environ` writes that leak state across test runs.
  - `FH004` (`MEDIUM` / `filesystem`): Hardcoded filesystem writes (`open(..., "w")`, `Path.write_text()`) without `tmp_path` or `tempfile` isolation, risking parallel worker collisions.
- **Multiple Output Formats:** Human-readable terminal report (`text`), structured `json`, and pull-request `markdown` tables.

---

## How to Run It

### 1. Install

```bash
git clone https://github.com/Dharmogata/flakehound.git
cd flakehound
pip install -e .
```

### 2. Scan a Test Suite

```bash
# Scan a directory or a single test file
flakehound scan tests/

# Filter by minimum severity or specific rule IDs
flakehound scan tests/ --min-severity high
flakehound scan tests/ --select FH001,FH003 --format markdown

# List all available rules and remediation guidance
flakehound rules
```

### 3. Run the Test Suite

```bash
# Using pytest
pytest -v

# Or using standard library unittest (zero external packages required)
PYTHONPATH=src python -m unittest discover -s tests -v
```

---

## Planned Work Ahead (TODO & Roadmap)

FlakeHound has **200+ hours of planned development** organized across 6 upcoming engineering phases in [ROADMAP.md](ROADMAP.md):

- [ ] **Phase 2 (~35h): Extended Static Rule Catalog (`FH005`–`FH025`) & Cross-File Call Graph** (`os.chdir` leakage, unmocked socket/HTTP calls, hardcoded ports, unordered set/dict assertions, un-awaited `asyncio` tasks, `# flakehound: ignore` comments, and `pyproject.toml` config loader).
- [ ] **Phase 3 (~40h): AST Automated Refactoring & Codemod Engine (`--fix` / `--diff`)** (automatic injection of `tmp_path` and `monkeypatch` fixtures, plus `unittest.TestCase` to `pytest` assertion migration).
- [ ] **Phase 4 (~35h): Dynamic Test Isolation Runner & Order-Dependency Bisector (`flakehound bisect`)** (subprocess repeat runner, seeded random order shuffler, and $O(\log N)$ binary search to isolate state-polluting tests).
- [ ] **Phase 5 (~35h): SQLite Telemetry Store & Regression Time-Machine** (local `.flakehound.db` tracking flip-rates, duration drift, and `--baseline main` git diff scanning).
- [ ] **Phase 6 (~40h): AST Mutation Testing Engine (`flakehound mutate`)** (arithmetic/relational/boolean AST mutant generation and surviving-mutant analysis).
- [ ] **Phase 7 (~20h): CI/CD Integrations, SARIF v2.1.0 Exporter & Standalone HTML Dashboard**.

See [ROADMAP.md](ROADMAP.md) for the full breakdown.

---

## License

Released under the [MIT License](LICENSE).
