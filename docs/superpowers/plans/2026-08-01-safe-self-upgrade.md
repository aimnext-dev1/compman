# Safe Self-Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `compman upgrade` safe on Windows code pages and prevent self-upgrade from corrupting its active uv tool environment.

**Architecture:** Replace in-process tool reinstallation with uv's supported `tool upgrade` workflow. Centralize subprocess text decoding in a small helper, retain pip only when uv cannot launch, and make every success/failure path explicit and testable.

**Tech Stack:** Python 3.10+, Typer, subprocess, uv, pytest, unittest.mock, Ruff, mypy

## Global Constraints

- Default uv command is exactly `uv tool upgrade compman --reinstall`.
- Captured output uses UTF-8 with replacement decoding.
- uv command failure exits 1 and never invokes `uv pip install --python sys.executable`.
- pip fallback runs only when uv raises `FileNotFoundError`.
- Package release version is `1.1.1`.
- Preserve English-first policy and 100% statement/branch coverage.

---

### Task 1: Safe upgrade command and regression tests

**Files:**
- Modify: `compman/cli.py:361-394`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_missing_coverage.py`

**Interfaces:**
- Produces: `_run_upgrade_command(cmd: list[str]) -> subprocess.CompletedProcess[str]` with fixed UTF-8 decoding.
- Consumes: `_find_uv()`, `sys.executable`, existing translated upgrade messages.

- [ ] **Step 1: Write failing behavior tests**

Add tests asserting:

```python
run.assert_called_once_with(
    ["/fake/uv", "tool", "upgrade", "compman", "--reinstall"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
```

Add a uv-failure test asserting exit 1, decoded error output, and only one subprocess call. Add missing-uv pip success/failure tests asserting `[sys.executable, "-m", "pip", "install", "--upgrade", f"git+{repo}"]`. Simulate malformed bytes through a fake result or real short Python subprocess and assert no `UnicodeDecodeError`/traceback.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_missing_coverage.py -k upgrade -q`

Expected: failures show the old `tool install --reinstall` command, missing encoding arguments, and unsafe uv-pip fallback.

- [ ] **Step 3: Implement minimal safe flow**

```python
def _run_upgrade_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
```

Use `[uv_cmd, "tool", "upgrade", "compman", "--reinstall"]`. On non-zero return, render `stderr or stdout` and exit 1. Catch only `FileNotFoundError` to invoke the pip command through the same helper; render its result and return/exit accordingly. Remove the uv-pip fallback entirely.

- [ ] **Step 4: Run affected suites and static checks**

Run: `.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_missing_coverage.py -q`

Run: `.venv\Scripts\python.exe -m ruff check compman/cli.py tests/test_cli.py tests/test_missing_coverage.py`

Run: `.venv\Scripts\python.exe -m mypy compman/cli.py`

Expected: all pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add compman/cli.py tests/test_cli.py tests/test_missing_coverage.py
git commit -m "fix: make self-upgrade safe on Windows"
```

### Task 2: Recovery documentation and 1.1.1 version

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `tests/test_repository_urls.py`

**Interfaces:**
- Consumes: Task 1 behavior.
- Produces: documented recovery command and package version `1.1.1`.

- [ ] **Step 1: Update documentation and version regression**

Document the supported uv upgrade behavior and broken-install recovery:

Use an unpinned Git source so uv records a source that future `uv tool upgrade`
commands can move forward.

```powershell
uv tool uninstall compman
uv tool install git+https://github.com/allbegray/compman.git
compman --version
```

Change project/lock/AGENTS version values and repository regression assertions from `1.1.0` to `1.1.1`.

- [ ] **Step 2: Run focused documentation/version tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_repository_urls.py -q`

Run: `git diff --check`

Expected: all pass and no Hangul appears outside allowed i18n/test resources.

- [ ] **Step 3: Commit Task 2**

```bash
git add README.md AGENTS.md pyproject.toml uv.lock tests/test_repository_urls.py
git commit -m "chore: prepare 1.1.1 recovery release"
```

### Task 3: Full release verification

**Files:**
- Test: repository-wide quality gates

**Interfaces:**
- Consumes: Tasks 1-2 completed tree.
- Produces: merge/tag-ready `1.1.1` state.

- [ ] **Step 1: Run full coverage gate**

Run: `.venv\Scripts\python.exe -m pytest --cov=compman --cov-report=term-missing --cov-fail-under=100`

Expected: all tests pass with 100% statement and branch coverage.

- [ ] **Step 2: Run static and hygiene gates**

Run: `.venv\Scripts\python.exe -m ruff check compman tests`

Run: `.venv\Scripts\python.exe -m mypy compman`

Run: `git diff --check`

Expected: all exit 0; Hangul scan matches only allowed localization resources/tests.

- [ ] **Step 3: Verify release identity**

Confirm `pyproject.toml`, the compman entry in `uv.lock`, `AGENTS.md`, and version regression tests all contain `1.1.1`; confirm local and remote `v1.1.1` do not already exist before tagging.
