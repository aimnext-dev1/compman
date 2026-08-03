from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

from compman.config import Config, Profile
from compman.ops import stack
from compman.ops.common import ensure_runtime_ready


def test_ensure_runtime_ready_prompts_to_start_docker_desktop(dummy_runtime):
    dummy_runtime.ensure_ready_for_start = MagicMock()

    with patch("compman.ops.common.typer.confirm", return_value=False) as confirm:
        ensure_runtime_ready(dummy_runtime)
        confirm_start = dummy_runtime.ensure_ready_for_start.call_args.args[0]
        assert confirm_start() is False

    dummy_runtime.ensure_ready_for_start.assert_called_once()
    confirm.assert_called_once_with(
        "Docker Desktop is not running. Start it now?", default=True, abort=False
    )


def test_stack_up_checks_readiness_immediately_before_compose(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.yml").touch()
    cfg = Config(name="my_stack", profiles={"default": Profile(file="docker-compose.yml")})
    calls: list[str] = []
    original_passthru = dummy_runtime.passthru_compose

    def passthru(*args, **kwargs):
        calls.append("compose")
        return original_passthru(*args, **kwargs)

    dummy_runtime.ensure_ready_for_start = MagicMock(side_effect=lambda callback: calls.append("ready"))
    dummy_runtime.passthru_compose = MagicMock(side_effect=passthru)

    stack.up(dummy_runtime, cfg)

    assert calls == ["ready", "compose"]
    dummy_runtime.ensure_ready_for_start.assert_called_once()
    dummy_runtime.passthru_compose.assert_called_once()
    assert len(dummy_runtime.compose_runs) == 1
    assert dummy_runtime.compose_runs[0]["args"] == ["up", "-d", "--force-recreate"]


def test_stack_update_checks_readiness_immediately_before_compose(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.yml").touch()
    cfg = Config(name="my_stack", profiles={"default": Profile(file="docker-compose.yml")})
    calls: list[str] = []
    original_passthru = dummy_runtime.passthru_compose

    def passthru(*args, **kwargs):
        calls.append("compose")
        return original_passthru(*args, **kwargs)

    dummy_runtime.ensure_ready_for_start = MagicMock(side_effect=lambda callback: calls.append("ready"))
    dummy_runtime.passthru_compose = MagicMock(side_effect=passthru)

    stack.update(dummy_runtime, cfg)

    assert calls == ["ready", "compose"]
    dummy_runtime.ensure_ready_for_start.assert_called_once()
    dummy_runtime.passthru_compose.assert_called_once()
    assert len(dummy_runtime.compose_runs) == 1
    assert dummy_runtime.compose_runs[0]["args"] == ["up", "-d", "--build", "--force-recreate"]


def test_stack_up_simple(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.yml").touch()
    cfg = Config(name="my_stack", profiles={"default": Profile(file="docker-compose.yml")})
    stack.up(dummy_runtime, cfg)
    assert len(dummy_runtime.compose_runs) == 1
    assert dummy_runtime.compose_runs[0]["args"] == ["up", "-d", "--force-recreate"]


def test_stack_up_profiles(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.dev.yml").touch()
    cfg = Config(
        name="my_stack",
        profiles={"dev": Profile(file="docker-compose.dev.yml")},
    )
    stack.up(dummy_runtime, cfg, profile="dev")
    assert len(dummy_runtime.compose_runs) == 1
    assert dummy_runtime.compose_runs[0]["args"] == ["up", "-d", "--force-recreate"]


def test_stack_profile_context(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(
        name="my_stack",
        profiles={"dev": Profile(file="docker-compose.dev.yml", env={"MODE": "dev"})},
    )
    stack.up(dummy_runtime, cfg, profile="dev")
    run = dummy_runtime.compose_runs[0]
    assert run["compose_files"] == (temp_dir / "docker-compose.dev.yml",)
    assert run["env"] == {"MODE": "dev"}


def test_stack_up_profiles_default(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.dev.yml").touch()
    cfg = Config(
        name="my_stack",
        profiles={"dev": Profile(file="docker-compose.dev.yml")},
    )
    stack.up(dummy_runtime, cfg, profile=None)
    assert len(dummy_runtime.compose_runs) == 1


def test_stack_down(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.yml").touch()
    cfg = Config(name="my_stack", profiles={"default": Profile(file="docker-compose.yml")})
    dummy_runtime.ensure_ready_for_start = MagicMock()
    stack.down(dummy_runtime, cfg)
    assert len(dummy_runtime.compose_runs) == 1
    assert dummy_runtime.compose_runs[0]["args"] == ["down"]
    dummy_runtime.ensure_ready_for_start.assert_not_called()


def test_stack_down_not_running(dummy_runtime, temp_dir: pathlib.Path):
    dummy_runtime.ensure_ready_for_start = MagicMock()
    dummy_runtime.stack_exists = MagicMock(return_value=False)
    cfg = Config(name="my_stack", profiles={"default": Profile(file="docker-compose.yml")})
    stack.down(dummy_runtime, cfg)
    assert len(dummy_runtime.compose_runs) == 0
    dummy_runtime.ensure_ready_for_start.assert_not_called()


def test_stack_update_simple(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.yml").touch()
    cfg = Config(name="my_stack", profiles={"default": Profile(file="docker-compose.yml")})
    stack.update(dummy_runtime, cfg)
    assert len(dummy_runtime.compose_runs) == 1
    assert dummy_runtime.compose_runs[0]["args"] == ["up", "-d", "--build", "--force-recreate"]


def test_stack_update_profiles(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.dev.yml").touch()
    cfg = Config(
        name="my_stack",
        profiles={"dev": Profile(file="docker-compose.dev.yml")},
    )
    stack.update(dummy_runtime, cfg, profile="dev")
    assert len(dummy_runtime.compose_runs) == 1
    assert dummy_runtime.compose_runs[0]["args"] == ["up", "-d", "--build", "--force-recreate"]


def test_stack_update_profiles_default(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.dev.yml").touch()
    cfg = Config(
        name="my_stack",
        profiles={"dev": Profile(file="docker-compose.dev.yml")},
    )
    stack.update(dummy_runtime, cfg, profile=None)
    assert len(dummy_runtime.compose_runs) == 1
