from __future__ import annotations

import pathlib
from unittest.mock import MagicMock

import pytest

from compman.config import Config
from compman.errors import CommandError
from compman.ops import service


def test_service_ops(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])

    service.start(dummy_runtime, cfg, ("web",))
    assert dummy_runtime.compose_runs[-1]["args"] == ["start", "web"]

    service.stop(dummy_runtime, cfg, ("web",))
    assert dummy_runtime.compose_runs[-1]["args"] == ["stop", "web"]

    service.restart(dummy_runtime, cfg, ("web",))
    assert dummy_runtime.compose_runs[-1]["args"] == ["restart", "web"]

    service.log(dummy_runtime, cfg, "web", follow=True, tail=100)
    assert dummy_runtime.commands_run[-1] == ["logs", "-f", "-n", "100", "cid123"]

    service.status(dummy_runtime, cfg)
    assert dummy_runtime.compose_runs[-1]["args"] == ["ps", "-a"]

    service.connect(dummy_runtime, cfg, "web")
    assert len(dummy_runtime.commands_run) >= 2


def test_service_log_auto_select(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    dummy_runtime.list_containers = MagicMock(return_value=["single_container"])
    service.log(dummy_runtime, cfg, service=None)
    assert dummy_runtime.commands_run[-1] == ["logs", "-n", "50", "cid123"]


def test_service_log_multiple_containers(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    dummy_runtime.list_containers = MagicMock(return_value=["c1", "c2"])
    service.log(dummy_runtime, cfg, service=None)


def test_service_log_no_containers(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    dummy_runtime.list_containers = MagicMock(return_value=[])
    with pytest.raises(CommandError):
        service.log(dummy_runtime, cfg, service=None)


def test_service_connect_auto_select(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    dummy_runtime.list_containers = MagicMock(return_value=["single_container"])
    service.connect(dummy_runtime, cfg, service=None)


def test_service_connect_not_found(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    dummy_runtime.get_container_id = MagicMock(return_value="")
    with pytest.raises(CommandError):
        service.connect(dummy_runtime, cfg, service="nonexistent")
