# Doctor and Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add read-only `compman doctor` and `compman status` commands with human and stable JSON output.

**Architecture:** `compman/diagnostics.py` collects typed reports without terminal output. `ContainerRuntime` supplies one machine-readable service-status query. Typer handlers render reports and own exit codes, leaving existing commands unchanged.

**Tech Stack:** Python 3.10+, Typer, dataclasses, stdlib JSON, pytest, Ruff, mypy.

## Global Constraints

- Preserve all existing CLI behavior.
- `doctor` exits 1 when a required check fails; warnings do not fail it.
- `status` exits 1 for invalid configuration, unavailable runtime, absent stack, or failed status query.
- `--json` writes exactly one JSON document to stdout with `schema_version: 1`.
- No port probing, live S3 calls, health waiting, backup reporting, or corrective actions.
- Maintain Windows, Linux, and macOS support and 100% statement/branch coverage.

---

### Task 1: Structured doctor report

**Files:**
- Create: `compman/diagnostics.py`
- Create: `tests/test_diagnostics.py`

**Interfaces:**
- Consumes: `load_config(config_path)`, `resolve_compose_context(config, profile)`, `detect_runtime()`.
- Produces: `CheckResult`, `DoctorReport`, and `collect_doctor(config_path: str | None, profile: str | None = None) -> DoctorReport`.

- [ ] **Step 1: Write failing model and success-path tests**

```python
def test_collect_doctor_success(tmp_path, monkeypatch, dummy_runtime):
    write_simple_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)
    report = collect_doctor(None)
    assert report.ok is True
    assert [check.id for check in report.checks[:3]] == ["config", "compose_files", "runtime"]
    assert report.to_dict()["schema_version"] == 1


def test_warning_does_not_fail_doctor(tmp_path, monkeypatch, dummy_runtime):
    write_simple_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)
    report = collect_doctor(None)
    assert report.ok is True
    assert next(c for c in report.checks if c.id == "aws").severity == "warning"
```

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest tests/test_diagnostics.py -q`

Expected: collection fails because `compman.diagnostics` does not exist.

- [ ] **Step 3: Implement minimal result types and successful collection**

```python
@dataclass(frozen=True)
class CheckResult:
    id: str
    severity: Literal["required", "warning"]
    ok: bool
    message: str

    def to_dict(self) -> dict[str, object]: ...


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[CheckResult, ...]

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks if c.severity == "required")

    def to_dict(self) -> dict[str, object]: ...
```

Collect configuration, resolved Compose files, runtime detection/connectivity using `runtime.run_cli(["info"], check=False)`, managed-directory parent writability via `os.access`, and AWS environment presence. Do not create directories during diagnosis.

- [ ] **Step 4: Add failing failure-path tests**

Cover invalid/missing config, missing Compose file, runtime detection exception, nonzero `info`, and unwritable managed-directory parent. Assert every expected failure becomes a required failed check rather than escaping.

- [ ] **Step 5: Run targeted tests and verify RED**

Run: `uv run pytest tests/test_diagnostics.py -q`

Expected: new failure-path assertions fail because exceptions or statuses are not yet normalized.

- [ ] **Step 6: Implement minimal failure normalization**

Stop checks that depend on an unavailable prerequisite, but retain already collected results. Use stable IDs: `config`, `compose_files`, `runtime`, `runtime_connection`, `managed_dirs`, `aws`.

- [ ] **Step 7: Verify and commit**

Run: `uv run pytest tests/test_diagnostics.py -q`

Expected: PASS.

```bash
git add compman/diagnostics.py tests/test_diagnostics.py
git commit -m "feat: add structured environment diagnostics"
```

---

### Task 2: Structured stack status

**Files:**
- Modify: `compman/docker.py`
- Modify: `compman/diagnostics.py`
- Modify: `tests/test_docker.py`
- Modify: `tests/test_diagnostics.py`

**Interfaces:**
- Consumes: `ContainerRuntime.run_compose`, `resolve_compose_context`.
- Produces: `ContainerRuntime.service_status(...) -> list[dict[str, object]]`, `ServiceStatus`, `StatusReport`, and `collect_status(config_path, profile) -> StatusReport`.

- [ ] **Step 1: Write a failing runtime parser test**

```python
def test_service_status_reads_compose_json(monkeypatch):
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    payload = '[{"Service":"web","Name":"app-web-1","State":"running","Status":"Up 5 seconds","Health":"healthy"}]'
    with patch.object(runtime, "run_compose", return_value=CompletedProcess([], 0, payload, "")) as run:
        rows = runtime.service_status("app", [Path("compose.yml")], {})
    assert rows[0]["service"] == "web"
    run.assert_called_once_with(
        ["ps", "-a", "--format", "json"], project="app",
        compose_files=[Path("compose.yml")], env={}, check=False,
    )
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_docker.py::test_service_status_reads_compose_json -q`

Expected: FAIL because `service_status` does not exist.

- [ ] **Step 3: Implement JSON parsing**

Normalize Docker Compose array JSON and Podman/older newline-delimited JSON into lowercase internal keys. A nonzero command result must use the existing probe-failure path. Invalid JSON raises `RuntimeError("Invalid service status JSON")`.

- [ ] **Step 4: Add failing report tests**

```python
def test_collect_status_reports_profile_and_services(profile_project, dummy_runtime, monkeypatch):
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)
    dummy_runtime.service_status = lambda *args: [{
        "service": "web", "name": "app-web-1", "state": "running",
        "status": "Up", "health": "healthy",
    }]
    report = collect_status(str(profile_project / "compman.yml"), "dev")
    assert report.ok is True
    assert report.profile == "dev"
    assert report.services[0].health == "healthy"
```

Also cover default-first-profile resolution, simple-mode rejection of a profile, absent stack, failed query, empty service list, and JSON key stability.

- [ ] **Step 5: Run tests and verify RED**

Run: `uv run pytest tests/test_docker.py tests/test_diagnostics.py -q`

Expected: report tests fail because status types and collector do not exist.

- [ ] **Step 6: Implement status types and collector**

```python
@dataclass(frozen=True)
class ServiceStatus:
    service: str
    container: str
    state: str
    status: str
    health: str | None


@dataclass(frozen=True)
class StatusReport:
    ok: bool
    runtime: str | None
    stack: str | None
    profile: str | None
    compose_files: tuple[str, ...]
    services: tuple[ServiceStatus, ...]
    error: str | None = None
```

Use `runtime.stack_exists` before `service_status`. Resolve the effective first profile explicitly so the report exposes it.

- [ ] **Step 7: Verify and commit**

Run: `uv run pytest tests/test_docker.py tests/test_diagnostics.py -q`

Expected: PASS.

```bash
git add compman/docker.py compman/diagnostics.py tests/test_docker.py tests/test_diagnostics.py
git commit -m "feat: collect structured stack status"
```

---

### Task 3: CLI commands and renderers

**Files:**
- Modify: `compman/cli.py`
- Modify: `compman/i18n.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `collect_doctor`, `collect_status`, and each report's `to_dict()`.
- Produces: top-level `doctor` and `status` Typer commands.

- [ ] **Step 1: Write failing CLI contract tests**

```python
def test_doctor_json_is_single_document(runner, monkeypatch):
    report = DoctorReport((CheckResult("config", "required", True, "valid"),))
    monkeypatch.setattr("compman.cli.collect_doctor", lambda *_: report)
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["ok"] is True


def test_doctor_failure_exits_one(runner, monkeypatch):
    report = DoctorReport((CheckResult("config", "required", False, "missing"),))
    monkeypatch.setattr("compman.cli.collect_doctor", lambda *_: report)
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "✗" in result.stdout
```

Add equivalent text/JSON/success/failure tests for `status`, including `--profile` and `--config` forwarding. Assert JSON stdout contains no prefix or progress line.

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_cli.py -k 'doctor or top_level_status' -q`

Expected: FAIL because commands are not registered.

- [ ] **Step 3: Add minimal commands and renderers**

Use `json.dumps(report.to_dict(), ensure_ascii=False)` for JSON. Human doctor markers are `✓` for passed required checks, `!` for warnings, and `✗` for failed required checks. Human status prints one header followed by one line per service. Raise `typer.Exit(1)` only after rendering a failed report.

Add English and Korean help keys `cmd.doctor`, `cmd.status`, and option key `opt.json`. Add both commands to the PowerShell completion list.

- [ ] **Step 4: Verify and commit**

Run: `uv run pytest tests/test_cli.py -q`

Expected: PASS.

```bash
git add compman/cli.py compman/i18n.py tests/test_cli.py
git commit -m "feat: expose doctor and status commands"
```

---

### Task 4: Documentation and complete verification

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `tests/test_diagnostics.py` only if coverage identifies an untested legitimate branch.

**Interfaces:**
- Consumes: final CLI behavior.
- Produces: documented command examples and verified quality gates.

- [ ] **Step 1: Update documentation**

Document:

```bash
compman doctor
compman doctor --json
compman status [--profile PROFILE]
compman status --json
```

State exit-code behavior and that missing AWS environment configuration is a non-failing warning. Update command inventory and test count only after the final test run gives the exact count.

- [ ] **Step 2: Run complete quality gates**

```bash
uv run ruff check compman tests
uv run mypy compman
uv run pytest --cov=compman --cov-report=term-missing
```

Expected: Ruff and mypy pass; pytest passes with 100% statement and branch coverage.

- [ ] **Step 3: Run real Docker smoke verification**

Using the existing repository integration fixture/guide, start the test Compose stack, then run:

```bash
uv run compman doctor
uv run compman status
uv run compman status --json
```

Parse the last command as JSON and confirm at least one service entry. Tear down using the documented integration cleanup command even when verification fails.

- [ ] **Step 4: Review the final diff and commit**

Confirm no unrelated files changed and no generated Docker, coverage, cache, or agent artifacts are tracked.

```bash
git add README.md AGENTS.md tests/test_diagnostics.py
git commit -m "docs: document diagnostics commands"
```
