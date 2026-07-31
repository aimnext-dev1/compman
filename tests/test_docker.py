from __future__ import annotations

import os
import pathlib
import subprocess
from unittest.mock import MagicMock, patch

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
