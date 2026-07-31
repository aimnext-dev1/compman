from __future__ import annotations

import pathlib
import pytest
import yaml

from compman.config import (
    Config,
    ConfigError,
    dump_default_config,
    load_config,
    sanitize_project_name,
)


def test_sanitize_project_name():
    assert sanitize_project_name("My Project!") == "my-project"
    assert sanitize_project_name("Desktop-App_123") == "desktop-app_123"
    assert sanitize_project_name("!!!") == "compman-app"
    assert sanitize_project_name("") == "compman-app"


def test_dump_default_config():
    content = dump_default_config("my-app")
    assert "name: my-app" in content
    assert "compose:" in content


def test_config_properties(temp_dir: pathlib.Path):
    cfg = Config(name="test", folder="sub", dirs={"backup": "bak", "volume": "vol", "project": "proj"})
    assert cfg.project_dir == temp_dir / "_project"
    assert cfg.backup_dir == temp_dir / "bak"
    assert cfg.volume_dir == temp_dir / "vol"
    assert cfg.deploy_dir == temp_dir / "proj"


def test_load_config_simple(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text(
        "compman:\n"
        "  name: test-app\n"
        "  compose:\n"
        "    - docker-compose.yml\n",
        encoding="utf-8",
    )
    cfg = load_config(str(config_file))
    assert cfg.name == "test-app"
    assert not cfg.has_profiles()
    assert cfg.compose_files == ["docker-compose.yml"]


def test_load_config_profiles(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text(
        "compman:\n"
        "  name: test-app\n"
        "  base: docker-compose.base.yml\n"
        "  compose:\n"
        "    dev:\n"
        "      file: docker-compose.dev.yml\n"
        "      env:\n"
        "        FOO: BAR\n",
        encoding="utf-8",
    )
    cfg = load_config(str(config_file))
    assert cfg.has_profiles()
    assert "dev" in cfg.profiles
    assert cfg.profiles["dev"].file == "docker-compose.dev.yml"
    assert cfg.profiles["dev"].env == {"FOO": "BAR"}


def test_load_config_single_compose_str(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text(
        "compman:\n"
        "  name: test-app\n"
        "  compose: docker-compose.yml\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_config(str(config_file))


def test_load_config_profile_string_only(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text(
        "compman:\n"
        "  name: test-app\n"
        "  compose:\n"
        "    dev: docker-compose.dev.yml\n",
        encoding="utf-8",
    )
    cfg = load_config(str(config_file))
    assert cfg.profiles["dev"].file == "docker-compose.dev.yml"


def test_load_config_missing_file(temp_dir: pathlib.Path):
    with pytest.raises(ConfigError):
        load_config(str(temp_dir / "nonexistent.yml"))


def test_load_config_invalid_yaml(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text("invalid: : [", encoding="utf-8")
    with pytest.raises((ConfigError, yaml.YAMLError)):
        load_config(str(config_file))


def test_load_config_missing_root_key(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text("other: foo", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(str(config_file))


def test_load_config_default_name(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text("compman:\n  name: default-test\n", encoding="utf-8")
    cfg = load_config(str(config_file))
    assert cfg.name == "default-test"


def test_load_config_deploy_not_string(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text("compman:\n  name: app\n  deploy: 123\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(str(config_file))


def test_load_config_compose_invalid_type(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text("compman:\n  name: app\n  compose: 42\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(str(config_file))


def test_load_config_compose_invalid_profile_value(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text("compman:\n  name: app\n  compose:\n    dev: 123\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(str(config_file))


def test_load_config_no_name_uses_cwd(temp_dir: pathlib.Path):
    config_file = temp_dir / "compman.yml"
    config_file.write_text("compman:\n  compose:\n    - docker-compose.yml\n", encoding="utf-8")
    cfg = load_config(str(config_file))
    assert cfg.name == sanitize_project_name(temp_dir.name)
    assert cfg.compose_files == ["docker-compose.yml"]
