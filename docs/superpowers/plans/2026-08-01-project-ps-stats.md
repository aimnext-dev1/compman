# Project-scoped `ps` and `stats` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `compman ps` and `compman stats` commands that inspect only containers belonging to the selected compman Compose project.

**Architecture:** Add a focused `compman.ops.container` module. `ps` passes directly through Compose; `stats` captures running container IDs from Compose and passes them to the detected runtime's native statistics command, avoiding provider-dependent Compose `stats` support.

**Tech Stack:** Python 3.10+, Typer, existing `Config`/`ContainerRuntime` abstractions, pytest, uv packaging, Ruff, mypy.

## Global Constraints

- `compman ps [PROFILE]` shows the selected project's running containers; `-a` / `--all` includes stopped containers.
- `compman stats [PROFILE]` prints one native runtime statistics snapshot; `-f` / `--follow` streams continuously.
- No runtime-wide mode, custom formatting, filtering, sorting, aggregation, interval, or export feature is added.
- Docker, Docker Compose, Podman Compose, `podman-compose`, and legacy `docker-compose` detection behavior remains unchanged.
- An empty project exits successfully; `stats` prints a localized informational message and must not invoke unscoped runtime statistics.
- Existing lazy CLI imports and 100% statement/branch coverage must be preserved.
- Apply a backward-compatible minor version bump from `1.2.0` to `1.3.0`.

---

### Task 1: Project container operations

**Files:**
- Create: `compman/ops/container.py`
- Test: `tests/test_ops_container.py`
- Modify: `tests/conftest.py`

**Interfaces:**
- Consumes: `resolve_compose_context(config: Config, profile: str | None) -> ComposeContext`, `ContainerRuntime.passthru_compose(...)`, `ContainerRuntime.run_compose(...)`, and `ContainerRuntime.passthru_cli(...)`.
- Produces: `ps(runtime: ContainerRuntime, config: Config, profile: str | None = None, all_containers: bool = False) -> None` and `stats(runtime: ContainerRuntime, config: Config, profile: str | None = None, follow: bool = False) -> None`.

- [ ] **Step 1: Add failing operation tests**

```python
@pytest.fixture
def config(temp_dir):
    (temp_dir / "docker-compose.yml").touch()
    return Config(name="my_stack", root_dir=temp_dir,
                  compose_files=["docker-compose.yml"])


def test_ps_uses_selected_compose_project(dummy_runtime, config):
    container.ps(dummy_runtime, config)
    assert dummy_runtime.compose_runs[-1]["args"] == ["ps"]


def test_ps_all_includes_stopped_containers(dummy_runtime, config):
    container.ps(dummy_runtime, config, all_containers=True)
    assert dummy_runtime.compose_runs[-1]["args"] == ["ps", "--all"]


def test_stats_resolves_project_ids_then_prints_snapshot(dummy_runtime, config):
    dummy_runtime.compose_stdout = "cid-one\ncid-two\n"
    container.stats(dummy_runtime, config)
    assert dummy_runtime.compose_runs[-1]["args"] == ["ps", "--quiet"]
    assert dummy_runtime.commands_run[-1] == ["stats", "--no-stream", "cid-one", "cid-two"]


def test_stats_follow_and_empty_project(dummy_runtime, config, capsys):
    dummy_runtime.compose_stdout = "cid-one\n"
    container.stats(dummy_runtime, config, follow=True)
    assert dummy_runtime.commands_run[-1] == ["stats", "cid-one"]

    dummy_runtime.compose_stdout = "\n"
    before = list(dummy_runtime.commands_run)
    container.stats(dummy_runtime, config)
    assert dummy_runtime.commands_run == before
    assert "No running containers" in capsys.readouterr().out
```

- [ ] **Step 2: Run the focused tests and confirm the missing module failure**

Run: `uv run pytest tests/test_ops_container.py -q`

Expected: collection fails because `compman.ops.container` does not exist.

- [ ] **Step 3: Make DummyRuntime captured output configurable**

In `tests/conftest.py`, initialize `self.compose_stdout = "my_stack_vol_1\nmy_stack-app-1\n"` and make `run_compose()` assign `m.stdout = self.compose_stdout`. This gives tests deterministic control of Compose ID discovery without changing production behavior.

- [ ] **Step 4: Implement the minimal project-scoped operations**

```python
from __future__ import annotations

import typer

from compman.config import Config
from compman.docker import ContainerRuntime, resolve_compose_context
from compman.i18n import t


def ps(runtime: ContainerRuntime, config: Config, profile: str | None = None,
       all_containers: bool = False) -> None:
    context = resolve_compose_context(config, profile)
    args = ["ps"]
    if all_containers:
        args.append("--all")
    runtime.passthru_compose(args, project=context.project,
                             compose_files=context.files, env=context.env)


def stats(runtime: ContainerRuntime, config: Config, profile: str | None = None,
          follow: bool = False) -> None:
    context = resolve_compose_context(config, profile)
    result = runtime.run_compose(["ps", "--quiet"], project=context.project,
                                 compose_files=context.files, env=context.env)
    container_ids = result.stdout.split()
    if not container_ids:
        typer.echo(t("msg.no_running_containers"))
        return
    args = ["stats"]
    if not follow:
        args.append("--no-stream")
    runtime.passthru_cli([*args, *container_ids])
```

- [ ] **Step 5: Run operation tests**

Run: `uv run pytest tests/test_ops_container.py -q`

Expected: all tests pass.

- [ ] **Step 6: Commit the operation layer**

```bash
git add compman/ops/container.py tests/test_ops_container.py tests/conftest.py
git commit -m "feat: add project container inspection operations"
```

### Task 2: Top-level CLI commands and localized help

**Files:**
- Modify: `compman/cli.py`
- Modify: `compman/i18n.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_coverage_completion.py`

**Interfaces:**
- Consumes: Task 1's `compman.ops.container.ps(...)` and `compman.ops.container.stats(...)`.
- Produces: `compman ps [PROFILE] [-a|--all] [-c|--config PATH]` and `compman stats [PROFILE] [-f|--follow] [-c|--config PATH]`.

- [ ] **Step 1: Add failing CLI routing and help tests**

```python
def test_cli_project_ps_and_stats(runner, dummy_runtime, temp_dir):
    (temp_dir / "compman.yml").write_text(
        "compman:\n  name: app\n  compose:\n    - docker-compose.yml\n",
        encoding="utf-8",
    )
    (temp_dir / "docker-compose.yml").touch()
    dummy_runtime.compose_stdout = "cid123\n"
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime):
        assert runner.invoke(app, ["ps"]).exit_code == 0
        assert dummy_runtime.compose_runs[-1]["args"] == ["ps"]
        assert runner.invoke(app, ["ps", "--all"]).exit_code == 0
        assert dummy_runtime.compose_runs[-1]["args"] == ["ps", "--all"]
        assert runner.invoke(app, ["stats"]).exit_code == 0
        assert dummy_runtime.commands_run[-1] == ["stats", "--no-stream", "cid123"]
        assert runner.invoke(app, ["stats", "--follow"]).exit_code == 0
        assert dummy_runtime.commands_run[-1] == ["stats", "cid123"]


def test_ps_stats_help_is_localized(runner):
    assert "project containers" in strip_ansi(runner.invoke(app, ["ps", "--help"]).output)
    set_lang("ko")
    assert "프로젝트" in strip_ansi(runner.invoke(app, ["stats", "--help"]).output)
```

Also extend completion assertions so the generated PowerShell list contains both `'ps'` and `'stats'`.

- [ ] **Step 2: Run focused CLI tests and confirm command-not-found failures**

Run: `uv run pytest tests/test_cli.py tests/test_coverage_completion.py -q`

Expected: new tests fail because the top-level commands and completion entries do not exist.

- [ ] **Step 3: Add lazy operation loading and Typer commands**

Add `_container_ops()` beside existing lazy loaders, then register:

```python
@app.command("ps", help=t("cmd.ps"))
def ps_cmd(
    profile: Annotated[Optional[str], typer.Argument()] = None,
    all_containers: Annotated[bool, typer.Option("--all", "-a", help=t("opt.all"))] = False,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    _container_ops().ps(ctx["runtime"], ctx["config"], profile, all_containers)


@app.command("stats", help=t("cmd.stats"))
def stats_cmd(
    profile: Annotated[Optional[str], typer.Argument()] = None,
    follow: Annotated[bool, typer.Option("--follow", "-f", help=t("opt.follow"))] = False,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    _container_ops().stats(ctx["runtime"], ctx["config"], profile, follow)
```

- [ ] **Step 4: Add English and Korean i18n entries and completion names**

Define exact translations:

```python
"cmd.ps": {"en": "List project containers", "ko": "프로젝트 컨테이너 목록 표시"},
"cmd.stats": {"en": "Display project container resource usage", "ko": "프로젝트 컨테이너 리소스 사용량 표시"},
"opt.all": {"en": "Include stopped containers", "ko": "중지된 컨테이너 포함"},
"opt.follow": {"en": "Stream statistics continuously", "ko": "통계를 계속 출력"},
```

Add `'ps'` and `'stats'` to `_ps_completion_snippet()` and add `compman.ops.container` to the lazy-import regression set.

- [ ] **Step 5: Run focused CLI and import tests**

Run: `uv run pytest tests/test_cli.py tests/test_coverage_completion.py -q`

Expected: all tests pass and importing `compman.cli` still does not eagerly load command-only modules.

- [ ] **Step 6: Commit the CLI surface**

```bash
git add compman/cli.py compman/i18n.py tests/test_cli.py tests/test_coverage_completion.py
git commit -m "feat: expose project ps and stats commands"
```

### Task 3: Documentation, release metadata, and discovery contracts

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `AGENTS.md`
- Modify: `docs/site/index.html`
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `tests/test_repository_urls.py`

**Interfaces:**
- Consumes: the finalized CLI syntax from Task 2.
- Produces: release `1.3.0` documentation and metadata with automated consistency checks.

- [ ] **Step 1: Update repository contract tests first**

Rename `test_package_version_is_1_2_0` to `test_package_version_is_1_3_0`, require `version = "1.3.0"` in `pyproject.toml` and `uv.lock`, require `## [1.3.0]` in `CHANGELOG.md`, and require the homepage command section to contain `compman ps` and `compman stats -f`.

- [ ] **Step 2: Run the contract test and confirm it fails on old metadata**

Run: `uv run pytest tests/test_repository_urls.py -q`

Expected: failure because the project is still version `1.2.0` and docs do not contain the new commands.

- [ ] **Step 3: Update user and maintainer documentation**

Add the following command forms to README command reference and examples:

```text
compman ps [PROFILE] [-a|--all] [-c|--config PATH]
compman stats [PROFILE] [-f|--follow] [-c|--config PATH]
```

Explain that both are project-scoped, `stats` prints one snapshot by default, `-f` streams continuously, and users should call Docker/Podman directly for global results. Add the same concise command examples to `docs/site/index.html`. Update `AGENTS.md` structure/CLI quirks and current quality-gate test count after the final test collection is known.

- [ ] **Step 4: Bump the release and lock metadata**

Set `pyproject.toml` to `version = "1.3.0"`, run `uv lock`, and add a dated `CHANGELOG.md` section:

```markdown
## [1.3.0] - 2026-08-01

### Added

- Added project-scoped `compman ps` container listings with `-a`/`--all`.
- Added project-scoped `compman stats` resource snapshots with `-f`/`--follow` streaming.
```

- [ ] **Step 5: Run repository contract tests**

Run: `uv run pytest tests/test_repository_urls.py -q`

Expected: all tests pass.

- [ ] **Step 6: Commit documentation and release metadata**

```bash
git add README.md CHANGELOG.md AGENTS.md docs/site/index.html pyproject.toml uv.lock tests/test_repository_urls.py
git commit -m "docs: release project container monitoring"
```

### Task 4: Full quality gates and built executable validation

**Files:**
- Modify only files required by failures directly caused by Tasks 1-3.

**Interfaces:**
- Consumes: the complete `1.3.0` implementation.
- Produces: verified source, package, and real-runtime behavior.

- [ ] **Step 1: Run static quality gates**

Run: `uv run ruff check compman tests`

Expected: no Ruff errors.

Run: `uv run mypy compman`

Expected: no mypy errors.

- [ ] **Step 2: Run the complete test suite once with branch coverage**

Run: `uv run pytest --cov=compman --cov-branch --cov-report=term-missing`

Expected: all tests pass with 100% statement and branch coverage. Update the exact collected-test count in `AGENTS.md` if needed, then rerun only the documentation contract test.

- [ ] **Step 3: Build and install the packaged CLI into an isolated uv tool directory**

```powershell
$CompmanToolRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("compman-tool-" + [guid]::NewGuid())
$env:UV_TOOL_DIR = Join-Path $CompmanToolRoot "tools"
$env:UV_TOOL_BIN_DIR = Join-Path $CompmanToolRoot "bin"
uv tool install --force .
& "$env:UV_TOOL_BIN_DIR\compman.exe" -v
```

Expected: uv builds and installs the current project, and the generated Windows launcher reports `compman 1.3.0`.

- [ ] **Step 4: Exercise the built executable against a real temporary Compose project**

Create a temporary Compose project containing a lightweight long-running service, start it with the available detected runtime, and run:

```powershell
$CompmanE2ERoot = Join-Path ([System.IO.Path]::GetTempPath()) ("compman-ps-stats-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $CompmanE2ERoot
@"
compman:
  name: compman-ps-stats-e2e
  compose:
    - docker-compose.yml
"@ | Set-Content -Encoding utf8 "$CompmanE2ERoot\compman.yml"
@"
services:
  probe:
    image: alpine:3.22
    command: ["sh", "-c", "while true; do sleep 60; done"]
"@ | Set-Content -Encoding utf8 "$CompmanE2ERoot\docker-compose.yml"
docker compose -p compman-ps-stats-e2e -f "$CompmanE2ERoot\docker-compose.yml" up -d
& "$env:UV_TOOL_BIN_DIR\compman.exe" ps --config "$CompmanE2ERoot\compman.yml"
& "$env:UV_TOOL_BIN_DIR\compman.exe" ps --all --config "$CompmanE2ERoot\compman.yml"
& "$env:UV_TOOL_BIN_DIR\compman.exe" stats --config "$CompmanE2ERoot\compman.yml"
docker compose -p compman-ps-stats-e2e -f "$CompmanE2ERoot\docker-compose.yml" down
```

Expected: only that temporary project's container appears; `stats` prints one resource snapshot and exits. Stop and remove the temporary project through its Compose file after verification.

- [ ] **Step 5: Verify the empty-project guard with the built executable**

After removing the temporary container, run `& "$env:UV_TOOL_BIN_DIR\compman.exe" stats --config "$CompmanE2ERoot\compman.yml"`.

Expected: a concise no-running-containers message, exit code 0, and no global container statistics.

- [ ] **Step 6: Review and commit verification-only corrections**

Run `git diff --check`, inspect `git status --short`, and commit only corrections attributable to this feature:

```bash
git add compman/ops/container.py compman/cli.py compman/i18n.py tests/conftest.py tests/test_ops_container.py tests/test_cli.py tests/test_coverage_completion.py README.md CHANGELOG.md AGENTS.md docs/site/index.html pyproject.toml uv.lock tests/test_repository_urls.py
git commit -m "fix: harden project container monitoring"
```

Skip this commit when verification required no corrections.
