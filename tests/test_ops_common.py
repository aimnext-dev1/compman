from __future__ import annotations

import pathlib
import sys
from unittest.mock import MagicMock, patch

import pytest

from compman.config import Config
from compman.ops import common


def test_select_backup_timestamp_single(temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    backup_dir = cfg.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_file = backup_dir / "my_stack.volume.20260731_1200.tar.gz"
    backup_file.touch()

    with patch("compman.ops.common.prompt_select", return_value=0):
        ts = common.select_backup_timestamp(cfg, "volume")
        assert ts == "20260731_1200"


def test_select_backup_timestamp_none(temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    with pytest.raises(SystemExit):
        common.select_backup_timestamp(cfg, "volume")


def test_select_backup_timestamp_empty_dir(temp_dir: pathlib.Path):
    cfg = Config(name="my_stack", compose_files=["docker-compose.yml"])
    cfg.backup_dir.mkdir(parents=True, exist_ok=True)
    with pytest.raises(SystemExit):
        common.select_backup_timestamp(cfg, "volume")


def test_prompt_select_non_tty(temp_dir: pathlib.Path):
    with patch("sys.stdin.isatty", return_value=False), patch("typer.prompt", return_value="1"):
        res = common.prompt_select("Title", ["Option 1", "Option 2"])
        assert res == 0

    with patch("sys.stdin.isatty", return_value=False), patch("typer.prompt", return_value="invalid"):
        res_invalid = common.prompt_select("Title", ["Option 1", "Option 2"], default_index=0)
        assert res_invalid == 0


def test_prompt_select_interactive_arrows(temp_dir: pathlib.Path):
    with patch("sys.stdin.isatty", return_value=True), patch("compman.ops.common.get_key", side_effect=["down", "up", "enter"]):
        res = common.prompt_select("Title", ["Option 1", "Option 2"])
        assert res == 0


def test_prompt_select_interactive_esc(temp_dir: pathlib.Path):
    with patch("sys.stdin.isatty", return_value=True), patch("compman.ops.common.get_key", return_value="esc"):
        with pytest.raises(SystemExit):
            common.prompt_select("Title", ["Option 1", "Option 2"])


def test_prompt_select_interactive_sigint(temp_dir: pathlib.Path):
    with patch("sys.stdin.isatty", return_value=True), patch("compman.ops.common.get_key", side_effect=KeyboardInterrupt):
        with pytest.raises(SystemExit):
            common.prompt_select("Title", ["Option 1", "Option 2"])


def test_get_key_posix():
    mock_termios = MagicMock()
    mock_tty = MagicMock()
    mock_select = MagicMock()
    with patch.dict("sys.modules", {"termios": mock_termios, "tty": mock_tty, "select": mock_select}):
        with patch("sys.platform", "linux"), patch("sys.stdin.fileno", return_value=0):
            with patch("sys.stdin.read", return_value="\r"):
                assert common.get_key() == "enter"

            with patch("sys.stdin.read", return_value="\x03"):
                with pytest.raises(KeyboardInterrupt):
                    common.get_key()

            with patch("sys.stdin.read", side_effect=["\x1b", "[", "A"]), patch("select.select", return_value=([True], [], [])):
                assert common.get_key() == "up"

            with patch("sys.stdin.read", side_effect=["\x1b", "[", "B"]), patch("select.select", return_value=([True], [], [])):
                assert common.get_key() == "down"

            with patch("sys.stdin.read", side_effect=["\x1b"]), patch("select.select", return_value=([], [], [])):
                assert common.get_key() == "esc"


def test_get_key_win32():
    with patch("sys.platform", "win32"), patch("msvcrt.getch", side_effect=[b"\r"]):
        assert common.get_key() == "enter"

    with patch("sys.platform", "win32"), patch("msvcrt.getch", side_effect=[b"\xe0", b"H"]):
        assert common.get_key() == "up"

    with patch("sys.platform", "win32"), patch("msvcrt.getch", side_effect=[b"\xe0", b"P"]):
        assert common.get_key() == "down"

    with patch("sys.platform", "win32"), patch("msvcrt.getch", side_effect=[b"\xe0", b"X"]):
        assert common.get_key() == "other"

    with patch("sys.platform", "win32"), patch("msvcrt.getch", side_effect=[b"\x1b"]):
        assert common.get_key() == "esc"

    with patch("sys.platform", "win32"), patch("msvcrt.getch", side_effect=[b"\x03"]):
        with pytest.raises(KeyboardInterrupt):
            common.get_key()
