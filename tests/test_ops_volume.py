from __future__ import annotations

import json
import pathlib
import tarfile
from unittest.mock import MagicMock, patch

import pytest

from compman.config import Config
from compman.errors import CommandError
from compman.ops import volume


def test_volume_backup(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    with patch("tarfile.open"), patch("compman.ops.volume._inspect_mount", return_value={"container": "c1", "volume": "vol1", "destination": "/data"}):
        volume.backup(dummy_runtime, cfg, no_stop=False)
        assert len(dummy_runtime.compose_runs) >= 1

        volume.backup(dummy_runtime, cfg, no_stop=True)


def test_volume_backup_no_volumes(dummy_runtime, temp_dir: pathlib.Path):
    dummy_runtime.list_volumes = MagicMock(return_value=[])
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    volume.backup(dummy_runtime, cfg)


def test_volume_backup_not_running(dummy_runtime, temp_dir: pathlib.Path):
    dummy_runtime.stack_exists = MagicMock(return_value=False)
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    with pytest.raises(CommandError):
        volume.backup(dummy_runtime, cfg)


def test_volume_restore(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    backup_dir = cfg.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / "my_stack.volume.20260731_1200.tar.gz"

    map_file = temp_dir / "volume-map.json"
    map_file.write_text('{"container1": {"volume": "vol1", "destination": "/data"}}', encoding="utf-8")
    with tarfile.open(backup_file, "w:gz") as tar:
        tar.add(map_file, arcname="volume-map.json")

    with patch("compman.ops.common.prompt_select", return_value=0), patch("compman.ops.volume._inspect_mount", return_value={"container": "c1", "volume": "vol1", "destination": "/data"}):
        volume.restore(dummy_runtime, cfg, timestamp="20260731_1200", no_stop=False)
        volume.restore(dummy_runtime, cfg, timestamp="20260731_1200", no_stop=True)


def test_volume_restore_invalid_timestamp(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    with pytest.raises(CommandError):
        volume.restore(dummy_runtime, cfg, timestamp="invalid_ts")


def test_volume_restore_not_found(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    cfg.backup_dir.mkdir(parents=True, exist_ok=True)
    with pytest.raises(CommandError):
        volume.restore(dummy_runtime, cfg, timestamp="20260731_1200")


def test_volume_restore_not_running(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    backup_dir = cfg.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / "my_stack.volume.20260731_1200.tar.gz"
    backup_file.touch()

    dummy_runtime.stack_exists = MagicMock(return_value=False)
    with pytest.raises(CommandError):
        volume.restore(dummy_runtime, cfg, timestamp="20260731_1200")


def test_volume_pull_push(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    with patch("compman.ops.volume._inspect_mount", return_value={"container": "c1", "volume": "vol1", "destination": "/data"}):
        volume.pull(dummy_runtime, cfg)
        assert (cfg.volume_dir / "volume-map.json").exists()

        vol_dir = cfg.volume_dir / "vol1"
        vol_dir.mkdir(parents=True, exist_ok=True)
        volume.push(dummy_runtime, cfg)
        assert len(dummy_runtime.commands_run) >= 1


def test_volume_pull_no_volumes(dummy_runtime, temp_dir: pathlib.Path):
    dummy_runtime.list_volumes = MagicMock(return_value=[])
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    volume.pull(dummy_runtime, cfg)


def test_volume_pull_not_running(dummy_runtime, temp_dir: pathlib.Path):
    dummy_runtime.stack_exists = MagicMock(return_value=False)
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    with pytest.raises(CommandError):
        volume.pull(dummy_runtime, cfg)


def test_volume_push_no_map(dummy_runtime, temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    with pytest.raises(CommandError):
        volume.push(dummy_runtime, cfg)
