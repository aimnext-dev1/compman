# CLI Startup and Release Notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce no-argument CLI startup work, harden self-upgrade Python selection, and add maintained release notes.

**Architecture:** Preserve the public Typer tree while moving command-only imports to their handlers. Force uv-managed Python for tool upgrades, and treat `CHANGELOG.md` as part of every version bump.

**Tech Stack:** Python 3.10+, Typer, uv, pytest

## Global Constraints

- Do not change command names, options, help text, or i18n behavior.
- Maintain 100% statement and branch coverage.
- Verify the built Windows executable, not only source tests.

---

### Task 1: Lazy command imports

**Files:**
- Modify: `compman/cli.py`
- Test: `tests/test_cli.py`

- [ ] Add a fresh-process test asserting `boto3`, `compman.deploy`, `compman.diagnostics`, and operation modules are not loaded by `import compman.cli`.
- [ ] Run the test and confirm it fails because those modules are eagerly imported.
- [ ] Move command-only imports into the handlers that use them.
- [ ] Run the focused test and existing CLI tests.

### Task 2: Managed-Python self-upgrade

**Files:**
- Modify: `compman/cli.py`
- Test: `tests/test_cli.py`

- [ ] Change the uv upgrade expectation to require `--managed-python` and confirm the test fails.
- [ ] Add the option to the uv command while preserving the pip fallback.
- [ ] Run focused upgrade tests.

### Task 3: Release notes and version

**Files:**
- Create: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Test: `tests/test_repository_urls.py`

- [ ] Update the version assertion to 1.1.3 and confirm it fails.
- [ ] Bump package metadata and document the release.
- [ ] Require changelog updates for subsequent version changes.

### Task 4: Verification

**Files:**
- Verify: `compman/cli.py`, `tests/`, packaging output

- [ ] Run pytest with 100% statement and branch coverage, Ruff, and mypy once after all changes.
- [ ] Build a wheel, install it into a fresh isolated uv tool environment, and smoke-test generated `compman.exe` help in English and Korean plus version, init, doctor, status, and upgrade.
- [ ] Compare fresh-process import/startup behavior with the previous eager-import structure and report measured results where the host Python installation permits valid timing.

### Task 5: Remove in-command duplicate work

**Files:**
- Modify: `compman/cli.py`
- Modify: `compman/deploy.py`
- Test: `tests/test_cli.py`

- [ ] Prove the S3-backed `update` path passes its already-loaded configuration and detected runtime to deploy.
- [ ] Reuse that context so update does not repeat YAML loading or runtime detection.
