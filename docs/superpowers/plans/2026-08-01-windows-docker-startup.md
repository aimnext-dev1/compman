# Windows Docker Startup and Clean Error Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Windows CLI failures readable and offer to start Docker Desktop, defaulting to Yes, only before container start/build operations.

**Architecture:** Keep process probing and Docker Desktop launch logic in `ContainerRuntime`, with user interaction supplied as a callback so the runtime layer remains independent of Typer. Wire readiness only into stack up/update and deploy build paths. Treat expected CLI errors as process exits and render the interactive selector entirely with portable ASCII characters.

**Tech Stack:** Python 3.10+, Typer/Click, subprocess, pytest, unittest.mock, Ruff, mypy

## Global Constraints

- Package version remains `1.0.0`.
- Only Windows Docker Desktop may be offered for startup; Podman and non-Windows behavior remain unchanged.
- Interactive startup confirmation defaults to Yes; non-interactive execution never launches Docker Desktop.
- Read-only, backup, restore, and stop operations never trigger Docker Desktop startup.
- Docker readiness wait is capped at 60 seconds.
- Expected operational failures exit without a traceback.
- Preserve 100% statement and branch coverage.

---

### Task 1: Clean CLI exits and portable selector output

**Files:**
- Modify: `compman/cli.py:51-59`
- Modify: `compman/ops/common.py:63-104`
- Test: `tests/test_cli.py`
- Test: `tests/test_ops_common.py`

**Interfaces:**
- Consumes: existing `HelpOnUnknownCommandGroup.main` and `prompt_select(...)` APIs.
- Produces: expected failures terminate with `SystemExit`; selector output contains only ASCII decorations and wording.

- [ ] **Step 1: Write failing CLI and prompt regression tests**

```python
def test_runtime_error_exits_without_traceback(runner, temp_dir):
    (temp_dir / "compman.yml").write_text(
        "compman:\n  name: app\n  compose:\n    - docker-compose.yml\n",
        encoding="utf-8",
    )
    (temp_dir / "docker-compose.yml").touch()
    runtime = MagicMock()
    runtime.passthru_compose.side_effect = RuntimeError("daemon unavailable")
    with patch("compman.cli.detect_runtime", return_value=runtime):
        result = runner.invoke(app, ["update"])
    assert result.exit_code == 1
    assert "Error: daemon unavailable" in result.output
    assert "Traceback" not in result.output


def test_prompt_select_uses_ascii_output(capsys):
    with patch("sys.stdin.isatty", return_value=True), patch(
        "compman.ops.common.get_key", return_value="enter"
    ):
        assert common.prompt_select("Select mode", ["First"]) == 0
    output = capsys.readouterr().out
    assert "Use Up/Down, Enter to select, Esc to cancel" in output
    assert output.isascii()
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `uv run pytest tests/test_cli.py::test_runtime_error_exits_without_traceback tests/test_ops_common.py::test_prompt_select_uses_ascii_output -q`

Expected: FAIL because Click `Exit` escapes the handler and the selector contains Unicode decorations.

- [ ] **Step 3: Implement the minimal exit and output changes**

In `HelpOnUnknownCommandGroup.main`, replace handler-level Click exits with process exits:

```python
        except CommandError as error:
            typer.echo(error.message, err=True)
            raise SystemExit(error.code)
        except (ConfigError, RuntimeError) as error:
            typer.echo(t("msg.command_failed", error=error), err=True)
            raise SystemExit(1)
```

In `prompt_select`, use an ASCII heading and marker:

```python
    typer.echo(f"{title} (Use Up/Down, Enter to select, Esc to cancel):")
# selected row inside render
                sys.stdout.write(f"\033[K > {option}\n")
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `uv run pytest tests/test_cli.py::test_runtime_error_exits_without_traceback tests/test_ops_common.py -q`

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add compman/cli.py compman/ops/common.py tests/test_cli.py tests/test_ops_common.py
git commit -m "fix: keep Windows CLI errors concise"
```

### Task 2: Docker Desktop readiness and consent boundary

**Files:**
- Modify: `compman/docker.py`
- Test: `tests/test_docker.py`

**Interfaces:**
- Consumes: `ContainerRuntime.name`, `ContainerRuntime.cli`, Windows environment variables, `Callable[[], bool]` confirmation.
- Produces: `ContainerRuntime.ensure_ready_for_start(confirm_start: Callable[[], bool], timeout: float = 60.0) -> None`.

- [ ] **Step 1: Write failing runtime tests**

Add tests covering: Docker already ready; Podman no-op; non-Windows no-op; non-TTY refusal; user refusal; default acceptance and successful polling; missing executable; launch failure; timeout. Representative accepted-start test:

```python
def test_ensure_ready_starts_docker_desktop_after_consent():
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    probes = [False, False, True]
    with patch("compman.docker.sys.platform", "win32"), patch(
        "compman.docker.sys.stdin.isatty", return_value=True
    ), patch("compman.docker._docker_daemon_ready", side_effect=probes), patch(
        "compman.docker._docker_desktop_executable", return_value=Path("Docker Desktop.exe")
    ), patch("compman.docker.subprocess.Popen") as launch, patch(
        "compman.docker.time.sleep"
    ):
        runtime.ensure_ready_for_start(lambda: True, timeout=60)
    launch.assert_called_once()
```

Non-interactive and declined tests assert `RuntimeError` and that `Popen` is not called. Timeout uses a patched monotonic sequence and asserts an actionable `RuntimeError` mentioning 60 seconds.

- [ ] **Step 2: Run runtime tests and verify RED**

Run: `uv run pytest tests/test_docker.py -q`

Expected: FAIL because `ensure_ready_for_start` and its helpers do not exist.

- [ ] **Step 3: Implement readiness, executable lookup, launch, and bounded polling**

Add imports for `sys`, `time`, `shutil`, and `Callable`. Implement the public method with these gates:

```python
    def ensure_ready_for_start(
        self, confirm_start: Callable[[], bool], timeout: float = 60.0
    ) -> None:
        if self.name != "docker" or sys.platform != "win32":
            return
        if _docker_daemon_ready(self):
            return
        if not sys.stdin.isatty():
            raise RuntimeError("Docker Desktop is not running. Start it manually and retry.")
        if not confirm_start():
            raise RuntimeError("Docker Desktop was not started. Start it manually and retry.")
        executable = _docker_desktop_executable()
        if executable is None:
            raise RuntimeError("Docker Desktop executable was not found.")
        try:
            subprocess.Popen([str(executable)], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except OSError as error:
            raise RuntimeError(f"Could not start Docker Desktop: {error}") from error
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if _docker_daemon_ready(self):
                return
            time.sleep(1)
        raise RuntimeError(f"Docker Desktop did not become ready within {int(timeout)} seconds.")
```

`_docker_daemon_ready` runs `docker info` with capture and a short timeout, returning only a boolean. `_docker_desktop_executable` checks `shutil.which("Docker Desktop.exe")` and then `%ProgramFiles%\Docker\Docker\Docker Desktop.exe`, returning the first existing `Path`.

- [ ] **Step 4: Run runtime tests and verify GREEN**

Run: `uv run pytest tests/test_docker.py -q`

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add compman/docker.py tests/test_docker.py
git commit -m "feat: offer Docker Desktop startup on Windows"
```

### Task 3: Wire readiness only to execution and build paths

**Files:**
- Modify: `compman/ops/common.py`
- Modify: `compman/ops/stack.py`
- Modify: `compman/deploy.py`
- Test: `tests/test_ops_stack.py`
- Test: `tests/test_deploy.py`

**Interfaces:**
- Consumes: `ContainerRuntime.ensure_ready_for_start(...)` from Task 2.
- Produces: `ensure_runtime_ready(runtime: ContainerRuntime) -> None`, using `typer.confirm(..., default=True)`.

- [ ] **Step 1: Write failing wiring tests**

```python
def test_stack_up_ensures_runtime_ready(dummy_runtime, temp_dir):
    (temp_dir / "docker-compose.yml").touch()
    dummy_runtime.ensure_ready_for_start = MagicMock()
    stack.up(dummy_runtime, Config(name="app", compose_files=["docker-compose.yml"]))
    dummy_runtime.ensure_ready_for_start.assert_called_once()


def test_stack_down_does_not_ensure_runtime_ready(dummy_runtime, temp_dir):
    dummy_runtime.ensure_ready_for_start = MagicMock()
    dummy_runtime.stack_exists = MagicMock(return_value=False)
    stack.down(dummy_runtime, Config(name="app", compose_files=["docker-compose.yml"]))
    dummy_runtime.ensure_ready_for_start.assert_not_called()
```

Add equivalent assertions for `stack.update`, deploy with `build=True`, and deploy with `build=False`. The accepted callback test patches `typer.confirm`, invokes the callback passed to the runtime, and asserts `default=True` and the exact Docker Desktop prompt.

- [ ] **Step 2: Run wiring tests and verify RED**

Run: `uv run pytest tests/test_ops_stack.py tests/test_deploy.py -q`

Expected: FAIL because readiness is not called.

- [ ] **Step 3: Implement the shared confirmation adapter and wire selected paths**

In `compman/ops/common.py`:

```python
def ensure_runtime_ready(runtime: ContainerRuntime) -> None:
    runtime.ensure_ready_for_start(
        lambda: typer.confirm(
            "Docker Desktop is not running. Start it now?",
            default=True,
            abort=False,
        )
    )
```

Call `ensure_runtime_ready(runtime)` immediately before compose execution in `stack.up` and `stack.update`. In deploy's `if build:` block, store `runtime = detect_runtime()`, call `ensure_runtime_ready(runtime)`, then invoke `runtime.passthru_cli(...)`. Do not add readiness calls elsewhere.

- [ ] **Step 4: Run wiring tests and verify GREEN**

Run: `uv run pytest tests/test_ops_stack.py tests/test_deploy.py -q`

Expected: PASS and the compose/build command is called exactly once.

- [ ] **Step 5: Commit Task 3**

```bash
git add compman/ops/common.py compman/ops/stack.py compman/deploy.py tests/test_ops_stack.py tests/test_deploy.py
git commit -m "feat: gate Docker startup behind user consent"
```

### Task 4: Full verification and documentation synchronization

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Test: repository-wide quality gates

**Interfaces:**
- Consumes: completed behavior from Tasks 1-3.
- Produces: user-facing Windows behavior documentation and verified release state.

- [ ] **Step 1: Update documentation**

Document that start/build commands on Windows probe Docker Desktop, prompt with default Yes when it is stopped, wait up to 60 seconds after acceptance, and never auto-launch in non-interactive environments. State that other commands and Podman do not trigger startup.

- [ ] **Step 2: Run formatting and static analysis**

Run: `uv run ruff check compman tests`

Expected: exit `0`.

Run: `uv run mypy compman`

Expected: exit `0`.

- [ ] **Step 3: Run the full test and coverage gate**

Run: `uv run pytest --cov=compman --cov-report=term-missing --cov-fail-under=100`

Expected: all tests pass with 100% statement and branch coverage under the repository configuration.

- [ ] **Step 4: Run repository hygiene checks**

Run: `git diff --check`

Expected: exit `0`.

Run: `rg -n "[가-힣]" AGENTS.md README.md compman tests`

Expected: matches only in `compman/i18n.py`, `tests/test_i18n.py`, and intentional Korean assertions in `tests/test_cli.py`.

- [ ] **Step 5: Commit documentation**

```bash
git add AGENTS.md README.md
git commit -m "docs: explain optional Docker Desktop startup"
```
