from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import time
from unittest.mock import MagicMock, call, patch

import pytest

from compman.config import Config, ConfigError, Profile
from compman.docker import (
    ContainerRuntime,
    _die,
    _merged_env,
    _passthru,
    _run,
    detect_runtime,
    resolve_compose_files,
    resolve_simple_files,
)


def test_resolve_simple_files(temp_dir: pathlib.Path):
    comp_file = temp_dir / "docker-compose.yml"
    comp_file.touch()
    cfg = Config(name="test", compose_files=["docker-compose.yml"])
    files = resolve_simple_files(cfg)
    assert len(files) == 1
    assert files[0].name == "docker-compose.yml"

    # Missing file
    cfg_missing = Config(name="test", compose_files=["nonexistent.yml"])
    with pytest.raises(ConfigError):
        resolve_simple_files(cfg_missing)

    cfg_none = Config(name="test", compose_files=None)
    with pytest.raises(ConfigError):
        resolve_simple_files(cfg_none)


def test_resolve_compose_files(temp_dir: pathlib.Path):
    base_file = temp_dir / "base.yml"
    base_file.touch()
    dev_file = temp_dir / "dev.yml"
    dev_file.touch()

    cfg = Config(
        name="test",
        compose_base="base.yml",
        profiles={"dev": Profile(file="dev.yml", env={"ENV": "DEV"})},
    )
    files, env = resolve_compose_files(cfg, "dev")
    assert len(files) == 2
    assert env == {"ENV": "DEV"}

    # No profiles configured
    cfg_no_prof = Config(name="test", compose_files=["docker-compose.yml"])
    with pytest.raises(ConfigError):
        resolve_compose_files(cfg_no_prof, "dev")

    # Unknown profile
    with pytest.raises(ConfigError):
        resolve_compose_files(cfg, "nonexistent")

    # Missing compose file
    cfg_missing_file = Config(
        name="test",
        profiles={"dev": Profile(file="nonexistent.yml")},
    )
    with pytest.raises(ConfigError):
        resolve_compose_files(cfg_missing_file, "dev")

    # Missing base compose file
    cfg_missing_base = Config(
        name="test",
        compose_base="nonexistent_base.yml",
        profiles={"dev": Profile(file="dev.yml")},
    )
    with pytest.raises(ConfigError):
        resolve_compose_files(cfg_missing_base, "dev")


@patch("compman.docker._check_cmd")
def test_detect_runtime_docker(mock_check):
    mock_check.side_effect = [(True, "Docker version 20.10.0")]
    rt = detect_runtime()
    assert isinstance(rt, ContainerRuntime)
    assert rt.name == "docker"


@patch("compman.docker._check_cmd")
def test_detect_runtime_podman(mock_check):
    mock_check.side_effect = [(False, ""), (True, "podman version 4.0.0")]
    rt = detect_runtime()
    assert isinstance(rt, ContainerRuntime)
    assert rt.name == "podman"


@patch("compman.docker._check_cmd")
def test_detect_runtime_podman_compose(mock_check):
    mock_check.side_effect = [(False, ""), (False, ""), (True, "podman-compose 1.0.0")]
    rt = detect_runtime()
    assert isinstance(rt, ContainerRuntime)
    assert rt.name == "podman"


@patch("compman.docker._check_cmd")
def test_detect_runtime_docker_compose(mock_check):
    mock_check.side_effect = [(False, ""), (False, ""), (False, ""), (True, "docker-compose 1.29.2")]
    rt = detect_runtime()
    assert isinstance(rt, ContainerRuntime)
    assert rt.name == "docker"


@patch("compman.docker._check_cmd")
def test_detect_runtime_none_found(mock_check):
    mock_check.return_value = (False, "")
    with pytest.raises(RuntimeError):
        detect_runtime()


@patch.dict(os.environ, {"CONTAINER_RUNTIME": "podman"})
@patch("compman.docker._check_cmd")
def test_detect_runtime_override(mock_check):
    mock_check.return_value = (False, "")
    with pytest.raises(RuntimeError):
        detect_runtime()


def test_die_and_merged_env():
    cp = subprocess.CompletedProcess(args=["docker"], returncode=1, stdout="out", stderr="err")
    with pytest.raises(RuntimeError):
        _die(["docker"], cp)

    env = _merged_env({"FOO": "BAR"})
    assert env["FOO"] == "BAR"


@patch("subprocess.run")
def test_passthru_and_run(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="my_proj\n")

    res = _run(["docker", "ps"])
    assert res.returncode == 0

    code = _passthru(["docker", "ps"])
    assert code == 0


@patch("subprocess.run", side_effect=FileNotFoundError)
def test_run_file_not_found(mock_run):
    with pytest.raises(RuntimeError):
        _run(["nonexistent_cmd"])

    with pytest.raises(RuntimeError):
        _passthru(["nonexistent_cmd"])


@patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="", stderr="failed"))
def test_passthru_failure_is_raised(mock_run):
    with pytest.raises(RuntimeError, match="Command failed"):
        _passthru(["docker", "compose", "up"])


@patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["docker", "compose", "up"], 3600))
def test_passthru_timeout_is_raised(mock_run):
    with pytest.raises(RuntimeError, match="timed out"):
        _passthru(["docker", "compose", "up"])


def test_container_runtime_methods():
    rt = ContainerRuntime(name="docker", cli=["docker"], compose=["docker", "compose"])

    with (
        patch.object(rt, "run_compose") as mock_compose,
        patch.object(rt, "run_cli") as mock_cli,
        patch.object(rt, "passthru_cli") as mock_passthru_cli,
        patch.object(rt, "passthru_compose") as mock_passthru_compose,
    ):
        mock_compose.return_value = MagicMock(returncode=0, stdout="container1\n")
        mock_cli.side_effect = [
            MagicMock(returncode=0, stdout="container1\n"),
            MagicMock(returncode=0, stdout="vol1\n"),
            MagicMock(returncode=0, stdout="cid123\n"),
        ]

        assert rt.stack_exists("container1")
        assert rt.list_containers("my_proj") == ["container1"]
        assert rt.list_volumes("my_proj") == ["vol1"]
        assert rt.get_container_id("my_proj", "my_stack") == "cid123"

        rt.passthru_cli(["ps"])
        rt.passthru_compose(["ps"], project="my_proj")
        mock_passthru_cli.assert_called_once_with(["ps"])
        mock_passthru_compose.assert_called_once_with(["ps"], project="my_proj")


@pytest.mark.parametrize(
    ("runtime_name", "cli", "compose"),
    [
        ("docker", ["docker"], ["docker", "compose"]),
        ("podman", ["podman"], ["podman", "compose"]),
        ("podman", ["podman"], ["podman-compose"]),
    ],
)
def test_stack_exists_uses_provider_independent_engine_query(runtime_name, cli, compose):
    runtime = ContainerRuntime(runtime_name, cli, compose)
    result = subprocess.CompletedProcess(cli + ["ps"], 0, "app-web-1\n", "")

    with (
        patch.object(runtime, "run_cli", return_value=result) as run_cli,
        patch.object(runtime, "run_compose") as run_compose,
    ):
        assert runtime.stack_exists("app", [pathlib.Path("compose.yml")], {"MODE": "test"})

    run_compose.assert_not_called()
    run_cli.assert_called_once_with(
        [
            "ps",
            "-a",
            "--filter",
            "label=com.docker.compose.project=app",
            "--format",
            "{{.Names}}",
        ],
        check=False,
    )


def test_stack_exists_rejects_failed_engine_query():
    runtime = ContainerRuntime("podman", ["podman"], ["podman-compose"])
    result = subprocess.CompletedProcess(["podman", "ps"], 125, "", "offline")

    with patch.object(runtime, "run_cli", return_value=result):
        with pytest.raises(RuntimeError, match="Command failed"):
            runtime.stack_exists("app")


def test_service_status_reads_compose_json(monkeypatch):
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    payload = (
        '[{"Service":"web","Name":"app-web-1","State":"running",'
        '"Status":"Up 5 seconds","Health":"healthy"}]'
    )
    with patch.object(
        runtime, "run_compose", return_value=subprocess.CompletedProcess([], 0, payload, "")
    ) as run:
        rows = runtime.service_status("app", [pathlib.Path("compose.yml")], {})

    assert rows[0]["service"] == "web"
    run.assert_called_once_with(
        ["ps", "-a", "--format", "json"],
        project="app",
        compose_files=[pathlib.Path("compose.yml")],
        env={},
        check=False,
    )


def test_service_status_normalizes_real_docker_compose_schema():
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    payload = (
        '[{"Command":"nginx","ExitCode":0,"Health":"healthy",'
        '"Name":"app-web-1","Service":"web","State":"running"}]'
    )
    with patch.object(
        runtime, "run_compose", return_value=subprocess.CompletedProcess([], 0, payload, "")
    ):
        rows = runtime.service_status("app", [], {})

    assert rows == [
        {
            "service": "web",
            "container": "app-web-1",
            "state": "running",
            "status": "running (exit 0)",
            "health": "healthy",
        }
    ]


def test_service_status_normalizes_real_podman_schema():
    runtime = ContainerRuntime("podman", ["podman"], ["podman-compose"])
    payload = (
        '[{"ExitCode":0,"Labels":{"com.docker.compose.project":"app",'
        '"com.docker.compose.service":"worker"},"Names":["app-worker-1"],'
        '"State":"running","Status":"Up 5 minutes"}]'
    )
    with patch.object(
        runtime, "run_compose", return_value=subprocess.CompletedProcess([], 0, payload, "")
    ):
        rows = runtime.service_status("app", [], {})

    assert rows == [
        {
            "service": "worker",
            "container": "app-worker-1",
            "state": "running",
            "status": "Up 5 minutes",
            "health": None,
        }
    ]


def test_service_status_uses_exit_code_when_state_is_missing():
    runtime = ContainerRuntime("podman", ["podman"], ["podman-compose"])
    payload = '[{"ExitCode":125,"Names":["app-worker-1"]}]'
    with patch.object(
        runtime, "run_compose", return_value=subprocess.CompletedProcess([], 0, payload, "")
    ):
        rows = runtime.service_status("app", [], {})

    assert rows[0]["status"] == "exit 125"


def test_service_status_reads_newline_delimited_json():
    runtime = ContainerRuntime("podman", ["podman"], ["podman", "compose"])
    payload = '{"Service":"web","Name":"app-web-1"}\n{"Service":"db","Name":"app-db-1"}'
    with patch.object(
        runtime, "run_compose", return_value=subprocess.CompletedProcess([], 0, payload, "")):
        rows = runtime.service_status("app", [], {})

    assert rows == [
        {"service": "web", "container": "app-web-1", "state": "", "status": "", "health": None},
        {"service": "db", "container": "app-db-1", "state": "", "status": "", "health": None},
    ]


def test_service_status_reads_single_json_object():
    runtime = ContainerRuntime("podman", ["podman"], ["podman", "compose"])
    with patch.object(
        runtime, "run_compose", return_value=subprocess.CompletedProcess([], 0, '{"Service":"web"}', "")
    ):
        rows = runtime.service_status("app", [], {})

    assert rows == [{"service": "web", "container": "", "state": "", "status": "", "health": None}]


def test_service_status_returns_empty_for_blank_output():
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    with patch.object(runtime, "run_compose", return_value=subprocess.CompletedProcess([], 0, "\n", "")):
        rows = runtime.service_status("app", [], {})

    assert rows == []


def test_service_status_rejects_invalid_json():
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    with patch.object(runtime, "run_compose", return_value=subprocess.CompletedProcess([], 0, "bad json", "")):
        with pytest.raises(RuntimeError, match="Invalid service status JSON"):
            runtime.service_status("app", [], {})


def test_service_status_rejects_json_without_object_rows():
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    with patch.object(runtime, "run_compose", return_value=subprocess.CompletedProcess([], 0, "[1]", "")):
        with pytest.raises(RuntimeError, match="Invalid service status JSON"):
            runtime.service_status("app", [], {})


def test_service_status_raises_on_failed_probe():
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    result = subprocess.CompletedProcess(["docker", "compose"], 1, "", "failed")
    with patch.object(runtime, "run_compose", return_value=result):
        with pytest.raises(RuntimeError, match="Command failed"):
            runtime.service_status("app", [], {})


def test_ensure_ready_for_start_returns_when_docker_is_ready(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    confirm_start = MagicMock()

    with patch.object(runtime, "run_cli", return_value=subprocess.CompletedProcess([], 0)) as run_cli:
        runtime.ensure_ready_for_start(confirm_start)

    run_cli.assert_called_once_with(["info"], capture=True, check=False)
    confirm_start.assert_not_called()


def test_ensure_ready_for_start_skips_podman(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    runtime = ContainerRuntime("podman", ["podman"], ["podman", "compose"])
    confirm_start = MagicMock()

    with patch.object(runtime, "run_cli") as run_cli:
        runtime.ensure_ready_for_start(confirm_start)

    run_cli.assert_not_called()
    confirm_start.assert_not_called()


def test_ensure_ready_for_start_skips_non_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    confirm_start = MagicMock()

    with patch.object(runtime, "run_cli") as run_cli:
        runtime.ensure_ready_for_start(confirm_start)

    run_cli.assert_not_called()
    confirm_start.assert_not_called()


def test_ensure_ready_for_start_rejects_noninteractive_start(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    confirm_start = MagicMock()

    with (
        patch.object(runtime, "run_cli", return_value=subprocess.CompletedProcess([], 1)),
        patch.object(subprocess, "Popen") as popen,
        pytest.raises(RuntimeError, match="non-interactive"),
    ):
        runtime.ensure_ready_for_start(confirm_start)

    confirm_start.assert_not_called()
    popen.assert_not_called()


def test_ensure_ready_for_start_rejects_declined_start(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    confirm_start = MagicMock(return_value=False)

    with (
        patch.object(runtime, "run_cli", return_value=subprocess.CompletedProcess([], 1)),
        patch.object(subprocess, "Popen") as popen,
        pytest.raises(RuntimeError, match="declined"),
    ):
        runtime.ensure_ready_for_start(confirm_start)

    confirm_start.assert_called_once_with()
    popen.assert_not_called()


def test_ensure_ready_for_start_launches_desktop_and_waits_for_ready(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    confirm_start = MagicMock(return_value=True)
    desktop = r"C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"

    with (
        patch.object(
            runtime,
            "run_cli",
            side_effect=[subprocess.CompletedProcess([], 1), subprocess.CompletedProcess([], 0)],
        ) as run_cli,
        patch.object(shutil, "which", return_value=desktop),
        patch.object(subprocess, "Popen") as popen,
        patch.object(time, "monotonic", side_effect=[0.0, 0.0]),
        patch.object(time, "sleep") as sleep,
    ):
        runtime.ensure_ready_for_start(confirm_start)

    confirm_start.assert_called_once_with()
    popen.assert_called_once_with([desktop], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    sleep.assert_called_once_with(1.0)
    assert run_cli.call_count == 2


def test_ensure_ready_for_start_uses_program_files_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    desktop = tmp_path / "Docker" / "Docker" / "Docker Desktop.exe"
    desktop.parent.mkdir(parents=True)
    desktop.touch()
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])

    with (
        patch.object(
            runtime,
            "run_cli",
            side_effect=[subprocess.CompletedProcess([], 1), subprocess.CompletedProcess([], 0)],
        ),
        patch.object(shutil, "which", return_value=None),
        patch.object(subprocess, "Popen") as popen,
        patch.object(time, "monotonic", side_effect=[0.0, 0.0]),
        patch.object(time, "sleep"),
    ):
        runtime.ensure_ready_for_start(lambda: True)

    popen.assert_called_once_with([str(desktop)], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def test_ensure_ready_for_start_reports_missing_desktop_executable(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.delenv("ProgramFiles", raising=False)
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])

    with (
        patch.object(runtime, "run_cli", return_value=subprocess.CompletedProcess([], 1)),
        patch.object(shutil, "which", return_value=None),
        patch.object(subprocess, "Popen") as popen,
        pytest.raises(RuntimeError, match="executable"),
    ):
        runtime.ensure_ready_for_start(lambda: True)

    popen.assert_not_called()


def test_ensure_ready_for_start_reports_missing_program_files_executable(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])

    with (
        patch.object(runtime, "run_cli", return_value=subprocess.CompletedProcess([], 1)),
        patch.object(shutil, "which", return_value=None),
        patch.object(subprocess, "Popen") as popen,
        pytest.raises(RuntimeError, match="executable"),
    ):
        runtime.ensure_ready_for_start(lambda: True)

    popen.assert_not_called()


def test_ensure_ready_for_start_reports_desktop_launch_error(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])

    with (
        patch.object(runtime, "run_cli", return_value=subprocess.CompletedProcess([], 1)),
        patch.object(shutil, "which", return_value="Docker Desktop.exe"),
        patch.object(subprocess, "Popen", side_effect=OSError("blocked")),
        pytest.raises(RuntimeError, match="start Docker Desktop"),
    ):
        runtime.ensure_ready_for_start(lambda: True)


def test_ensure_ready_for_start_times_out_after_default_sixty_seconds(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])
    times = [0.0, *[float(second) for second in range(61)]]

    with (
        patch.object(runtime, "run_cli", return_value=subprocess.CompletedProcess([], 1)) as run_cli,
        patch.object(shutil, "which", return_value="Docker Desktop.exe"),
        patch.object(subprocess, "Popen"),
        patch.object(time, "monotonic", side_effect=times),
        patch.object(time, "sleep") as sleep,
        pytest.raises(RuntimeError, match="within 60 seconds"),
    ):
        runtime.ensure_ready_for_start(lambda: True)

    assert sleep.call_count == 60
    assert sleep.call_args_list == [call(1.0)] * 60
    assert run_cli.call_count == 61


def test_docker_is_ready_returns_false_when_info_command_fails():
    runtime = ContainerRuntime("docker", ["docker"], ["docker", "compose"])

    with patch.object(runtime, "run_cli", side_effect=RuntimeError("docker unavailable")) as run_cli:
        assert not runtime._docker_is_ready()

    run_cli.assert_called_once_with(["info"], capture=True, check=False)
