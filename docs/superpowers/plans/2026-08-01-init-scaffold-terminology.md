# Init Scaffold Terminology Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the public `compman init --skeleton` mode with `--scaffold` and use scaffold terminology throughout CLI guidance and documentation.

**Architecture:** Keep the existing initialization flow and generated files unchanged. Rename only its public option, callback variable, displayed labels, localized guidance, documentation, and regression tests; then release it as a minor version because the old option is deliberately removed.

**Tech Stack:** Python 3.10+, Typer, pytest, Ruff, mypy, uv

## Global Constraints

- Remove `--skeleton` without a compatibility alias.
- Preserve the existing generated `compman.yml` content and all non-scaffold initialization modes.
- Update English and Korean guidance together.
- Keep deploy-time `scaffold.py` and `_generate_scaffold` names unchanged.
- Verify 100% statement and branch coverage and smoke-test the built executable.

---

### Task 1: Rename the public initialization mode

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `compman/cli.py`
- Modify: `compman/i18n.py`

**Interfaces:**
- Consumes: existing `init` Typer command and `dump_default_config()` behavior
- Produces: `compman init --scaffold`; `--skeleton` becomes an unknown option

- [ ] **Step 1: Write failing CLI tests**

Change the initialization test to invoke `init --scaffold`, assert that it creates `compman.yml`, and add an invocation of `init --skeleton` that must fail with an unknown-option message. Extend interactive/help assertions to require `scaffold` and reject displayed `skeleton` terminology.

- [ ] **Step 2: Run the focused tests and verify failure**

Run:

```bash
uv run pytest tests/test_cli.py -k "init or help" -q
```

Expected: `--scaffold` is rejected because the option does not exist yet.

- [ ] **Step 3: Implement the minimal CLI and localization rename**

In `compman/cli.py`, rename the `skeleton` option parameter to `scaffold`, expose only `--scaffold`, update its help text, branch condition, menu label, and comment. In `compman/i18n.py`, replace user-facing skeleton mode labels and command examples with scaffold equivalents in both locales.

- [ ] **Step 4: Run focused tests and verify success**

Run:

```bash
uv run pytest tests/test_cli.py -k "init or help" -q
```

Expected: all selected tests pass, including rejection of `--skeleton`.

### Task 2: Publish and verify the breaking terminology change

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**
- Consumes: Task 1's `--scaffold` CLI option
- Produces: version `1.2.0` documentation and package metadata

- [ ] **Step 1: Update documentation and release metadata**

Replace `--skeleton` examples and `Skeleton` mode wording with `--scaffold` and `Scaffold`. Set the project version to `1.2.0`, refresh the lock file, and add a dated `1.2.0` CHANGELOG entry explicitly stating that `--skeleton` was replaced and is no longer accepted.

- [ ] **Step 2: Check for stale public terminology**

Run:

```bash
rg -n -i "skeleton" README.md AGENTS.md compman tests
```

Expected: only the negative compatibility regression assertion may contain `skeleton`.

- [ ] **Step 3: Run all quality gates**

Run:

```bash
uv run ruff check compman tests
uv run mypy compman
uv run pytest --cov=compman --cov-report=term-missing
```

Expected: Ruff and mypy pass; pytest reaches 100% statement and branch coverage.

- [ ] **Step 4: Build and smoke-test the installed executable**

Build the wheel, install it into an isolated environment, create its Windows executable entry point, and run:

```powershell
compman.exe -v
compman.exe -h
compman.exe init --scaffold
```

Expected: version `1.2.0`, working help, and a generated `compman.yml`; `compman.exe init --skeleton` must fail.

- [ ] **Step 5: Commit the implementation**

```bash
git add compman tests README.md AGENTS.md CHANGELOG.md pyproject.toml uv.lock docs/superpowers/plans/2026-08-01-init-scaffold-terminology.md
git commit -m "feat(init): replace skeleton mode with scaffold"
```
