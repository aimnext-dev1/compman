from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

import compman.deploy
from typer.testing import CliRunner

from compman.cli import app


def test_cli_version(runner: CliRunner):
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert "compman" in res.output


def test_cli_lang(runner: CliRunner):
    res = runner.invoke(app, ["lang"])
    assert res.exit_code == 0
    assert "Active Language" in res.output

    res_ko = runner.invoke(app, ["lang", "ko"])
    assert res_ko.exit_code == 0
    assert "ko" in res_ko.output

    res_inv = runner.invoke(app, ["lang", "invalid_lang"])
    assert res_inv.exit_code != 0


def test_cli_global_lang_flag(runner: CliRunner):
    res = runner.invoke(app, ["-l", "ko", "version"])
    assert res.exit_code == 0


def test_cli_init(runner: CliRunner, temp_dir: pathlib.Path):
    res_sk = runner.invoke(app, ["init", "--skeleton"])
    assert res_sk.exit_code == 0
    assert (temp_dir / "compman.yml").exists()

    res_sk_exists = runner.invoke(app, ["init", "--skeleton"])
    assert res_sk_exists.exit_code == 0

    res_sd = runner.invoke(app, ["init", "--seed", "-o", "my_seed", "--force"])
    assert res_sd.exit_code == 0
    assert (temp_dir / "my_seed").exists()

    with patch("compman.cli._deploy"):
        res_s3 = runner.invoke(app, ["init", "--s3", "s3://b/k"])
        assert res_s3.exit_code == 0


def test_cli_init_interactive(runner: CliRunner, temp_dir: pathlib.Path):
    with patch("compman.ops.common.prompt_select", return_value=0):
        res = runner.invoke(app, ["init", "--force"])
        assert res.exit_code == 0


def test_cli_clear(runner: CliRunner, dummy_runtime):
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime):
        res = runner.invoke(app, ["clear"])
        assert res.exit_code == 0


def test_cli_deploy(runner: CliRunner, dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  deploy: s3://b/k.tar.gz\n", encoding="utf-8")
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime), patch("compman.cli._deploy"):
        res = runner.invoke(app, ["deploy", "--path", "s3://b/k.tar.gz"])
        assert res.exit_code == 0


def test_cli_update(runner: CliRunner, dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    (temp_dir / "docker-compose.yml").touch()
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime):
        res = runner.invoke(app, ["update"])
        assert res.exit_code == 0


def test_cli_stack_commands(runner: CliRunner, dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    (temp_dir / "docker-compose.yml").touch()
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime):
        res_up = runner.invoke(app, ["stack", "up"])
        assert res_up.exit_code == 0

        res_down = runner.invoke(app, ["stack", "down", "--yes"])
        assert res_down.exit_code == 0

        res_update = runner.invoke(app, ["stack", "update"])
        assert res_update.exit_code == 0


def test_cli_service_commands(runner: CliRunner, dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    (temp_dir / "docker-compose.yml").touch()
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime):
        for cmd in ["start", "stop", "restart"]:
            res = runner.invoke(app, ["service", cmd, "web"])
            assert res.exit_code == 0

        res_st = runner.invoke(app, ["service", "status"])
        assert res_st.exit_code == 0

        res_log = runner.invoke(app, ["service", "log", "web"])
        assert res_log.exit_code == 0

        res_conn = runner.invoke(app, ["service", "connect", "web"])
        assert res_conn.exit_code == 0


def test_cli_volume_commands(runner: CliRunner, dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    (temp_dir / "docker-compose.yml").touch()
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime), patch("compman.ops.volume.backup"), patch("compman.ops.volume.restore"), patch("compman.ops.volume.pull"), patch("compman.ops.volume.push"):
        res_bak = runner.invoke(app, ["volume", "backup", "--no-stop"])
        assert res_bak.exit_code == 0

        res_res = runner.invoke(app, ["volume", "restore", "20260731_1200", "--no-stop"])
        assert res_res.exit_code == 0

        res_pull = runner.invoke(app, ["volume", "pull"])
        assert res_pull.exit_code == 0

        res_push = runner.invoke(app, ["volume", "push"])
        assert res_push.exit_code == 0


def test_cli_image_commands(runner: CliRunner, dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    (temp_dir / "docker-compose.yml").touch()
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime), patch("compman.ops.image.backup"), patch("compman.ops.image.restore"):
        res_bak = runner.invoke(app, ["image", "backup", "--source-image"])
        assert res_bak.exit_code == 0

        res_res = runner.invoke(app, ["image", "restore", "20260731_1200"])
        assert res_res.exit_code == 0


def test_cli_load_error(runner: CliRunner, temp_dir: pathlib.Path):
    res = runner.invoke(app, ["stack", "up"])
    assert res.exit_code != 0


def test_cli_unknown_command_shows_root_help(runner: CliRunner):
    res = runner.invoke(app, ["unknown"])
    assert res.exit_code == 2
    assert "Usage: compman" in res.output
    assert "Commands" in res.output


def test_cli_unknown_subcommand_shows_group_help(runner: CliRunner):
    res = runner.invoke(app, ["service", "down"])
    assert res.exit_code == 2
    assert "Usage: compman service" in res.output
    assert "status" in res.output


def test_cli_upgrade(runner: CliRunner):
    with patch("subprocess.run", return_value=MagicMock(returncode=0)):
        res = runner.invoke(app, ["upgrade"])
        assert res.exit_code == 0


def test_cli_completion(runner: CliRunner):
    res = runner.invoke(app, ["completion", "powershell"])
    assert res.exit_code == 0
    assert "Register-ArgumentCompleter" in res.output

    res_install = runner.invoke(app, ["completion", "powershell", "--install"])
    assert res_install.exit_code == 0


def test_cli_completion_bash(runner: CliRunner):
    res = runner.invoke(app, ["completion", "bash"])
    assert res.exit_code == 0
    assert "_COMPMAN_COMPLETE" in res.output


def test_cli_completion_zsh(runner: CliRunner):
    res = runner.invoke(app, ["completion", "zsh"])
    assert res.exit_code == 0
    assert "_COMPMAN_COMPLETE" in res.output


def test_cli_completion_fish(runner: CliRunner):
    res = runner.invoke(app, ["completion", "fish"])
    assert res.exit_code == 0
    assert "_COMPMAN_COMPLETE" in res.output


def test_cli_completion_install_bash(runner: CliRunner, temp_dir: pathlib.Path):
    mock_home = MagicMock()
    rc = temp_dir / ".bashrc"
    with patch("pathlib.Path.home", return_value=temp_dir), patch("pathlib.Path.read_text", side_effect=FileNotFoundError if not rc.exists() else None):
        try:
            res = runner.invoke(app, ["completion", "bash", "--install"])
        except FileNotFoundError:
            res = runner.invoke(app, ["completion", "bash", "--install"])
        assert res.exit_code == 0


def test_cli_completion_install_zsh(runner: CliRunner, temp_dir: pathlib.Path):
    with patch("pathlib.Path.home", return_value=temp_dir):
        res = runner.invoke(app, ["completion", "zsh", "--install"])
        assert res.exit_code == 0


def test_cli_completion_install_fish(runner: CliRunner, temp_dir: pathlib.Path):
    with patch("pathlib.Path.home", return_value=temp_dir):
        res = runner.invoke(app, ["completion", "fish", "--install"])
        assert res.exit_code == 0


def test_cli_completion_install_ps_error(runner: CliRunner):
    with patch("subprocess.check_output", side_effect=Exception("mock fail")):
        res = runner.invoke(app, ["completion", "powershell", "--install"])
        assert res.exit_code == 0


def test_cli_init_s3_interactive(runner: CliRunner, temp_dir: pathlib.Path):
    with patch("compman.ops.common.prompt_select", return_value=1), patch("typer.prompt", return_value="s3://b/k"), patch("compman.cli._deploy"):
        res = runner.invoke(app, ["init"])
        assert res.exit_code == 0


def test_cli_update_deploy_path(runner: CliRunner, dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  deploy: s3://b/k.tar.gz\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    (temp_dir / "docker-compose.yml").touch()
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime), patch("compman.cli._deploy"):
        res = runner.invoke(app, ["update"])
        assert res.exit_code == 0


def test_cli_stack_down_no_yes_abort(runner: CliRunner, dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    (temp_dir / "docker-compose.yml").touch()
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime):
        res = runner.invoke(app, ["stack", "down"], input="y\n")
        assert res.exit_code == 0


def test_cli_root_no_subcommand(runner: CliRunner):
    res = runner.invoke(app, [])
    assert res.exit_code == 2


def test_cli_upgrade_uv_fail_pip_success(runner: CliRunner):
    mock_uv = MagicMock(returncode=1, stderr="uv fail")
    mock_pip = MagicMock(returncode=0)
    with patch("shutil.which", return_value="/fake/uv"), patch("subprocess.run", side_effect=[mock_uv, mock_pip]):
        res = runner.invoke(app, ["upgrade"])
        assert res.exit_code == 0


def test_cli_upgrade_pip_success(runner: CliRunner):
    m = MagicMock(returncode=0)
    with patch("shutil.which", return_value=None), patch("subprocess.run", return_value=m):
        res = runner.invoke(app, ["upgrade"])
        assert res.exit_code == 0


def test_cli_upgrade_pip_fail(runner: CliRunner):
    m = MagicMock(returncode=1)
    with patch("shutil.which", return_value=None), patch("subprocess.run", return_value=m):
        res = runner.invoke(app, ["upgrade"])
        assert res.exit_code != 0


def test_cli_version_pkg_not_found(runner: CliRunner):
    with patch("compman.cli._pkg_version", side_effect=Exception):
        res = runner.invoke(app, ["version"])
        assert res.exit_code == 1


def test_cli_lang_callback_set(runner: CliRunner):
    res = runner.invoke(app, ["-l", "en", "version"])
    assert res.exit_code == 0


def test_cli_load_runtime_error(runner: CliRunner, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    with patch("compman.docker.detect_runtime", side_effect=RuntimeError("no runtime")):
        res = runner.invoke(app, ["stack", "up"])
        assert res.exit_code != 0


def test_cli_upgrade_uv_fail_pip_fail(runner: CliRunner):
    mock_fail = MagicMock(returncode=1)
    with patch("shutil.which", return_value="/fake/uv"), patch("subprocess.run", return_value=mock_fail):
        res = runner.invoke(app, ["upgrade"])
        assert res.exit_code != 0


def test_cli_service_no_services(runner: CliRunner, dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    (temp_dir / "docker-compose.yml").touch()
    with patch("compman.cli.detect_runtime", return_value=dummy_runtime):
        for cmd in ["start", "stop", "restart"]:
            res = runner.invoke(app, ["service", cmd])
            assert res.exit_code == 0
