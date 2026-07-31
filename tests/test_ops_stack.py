from __future__ import annotations

import pathlib
from unittest.mock import MagicMock

from compman.config import Config, Profile
from compman.ops import stack


def test_stack_up_simple(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.yml").touch()
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
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
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    stack.down(dummy_runtime, cfg)
    assert len(dummy_runtime.compose_runs) == 1
    assert dummy_runtime.compose_runs[0]["args"] == ["down"]


def test_stack_down_not_running(dummy_runtime, temp_dir: pathlib.Path):
    dummy_runtime.stack_exists = MagicMock(return_value=False)
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    stack.down(dummy_runtime, cfg)
    assert len(dummy_runtime.compose_runs) == 0


def test_stack_update_simple(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "docker-compose.yml").touch()
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
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
