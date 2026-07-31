from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Profile:
    file: str
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class Config:
    name: str
    folder: str | None = None
    dirs: dict[str, str] = field(
        default_factory=lambda: {"backup": "backup", "volume": "volume"}
    )
    compose_base: str | None = None
    compose_files: list[str] | None = None
    profiles: dict[str, Profile] = field(default_factory=dict)

    @property
    def project_dir(self) -> Path:
        base = Path.cwd()
        return base / "_project" if self.folder else base

    @property
    def backup_dir(self) -> Path:
        return Path.cwd() / self.dirs.get("backup", "backup")

    @property
    def volume_dir(self) -> Path:
        return Path.cwd() / self.dirs.get("volume", "volume")

    def has_profiles(self) -> bool:
        return bool(self.profiles)

    def has_simple_files(self) -> bool:
        return self.compose_files is not None


def load_config(config_path: str | None = None) -> Config:
    path = Path(config_path) if config_path else Path.cwd() / "compman.yml"
    if not path.is_file():
        raise ConfigError(
            f"{path} not found. Run 'compman init' first."
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not raw or not isinstance(raw, dict):
        raise ConfigError("Invalid config file: not a YAML mapping.")
    root = raw.get("compman")
    if not root or not isinstance(root, dict):
        raise ConfigError("'compman' key not found or not a mapping.")

    name = root.get("name")
    if not name:
        raise ConfigError("'compman.name' is required.")

    folder = root.get("folder")
    raw_dirs = root.get("dirs", {})
    dirs = {
        "backup": str(raw_dirs.get("backup", "backup")),
        "volume": str(raw_dirs.get("volume", "volume")),
    }

    compose_base: str | None = None
    compose_files: list[str] | None = None
    profiles: dict[str, Profile] = {}

    raw_compose = root.get("compose")
    if raw_compose is None:
        compose_files = ["docker-compose.yml"]
    elif isinstance(raw_compose, list):
        compose_files = [str(f) for f in raw_compose]
    elif isinstance(raw_compose, dict):
        for key, val in raw_compose.items():
            if key == "base":
                compose_base = str(val)
            elif isinstance(val, str):
                profiles[key] = Profile(file=str(val))
            elif isinstance(val, dict):
                f = val.get("file")
                if not f:
                    raise ConfigError(f"'compose.{key}.file' is required.")
                profiles[key] = Profile(
                    file=str(f),
                    env={str(k): str(v) for k, v in val.get("env", {}).items()},
                )
            else:
                raise ConfigError(
                    f"Invalid value for 'compose.{key}': expected string or object."
                )
    else:
        raise ConfigError(
            "'compose' must be a list, dict, or omitted."
        )

    return Config(
        name=name,
        folder=folder,
        dirs=dirs,
        compose_base=compose_base,
        compose_files=compose_files,
        profiles=profiles,
    )


def dump_default_config() -> str:
    return """compman:
  name: my-stack
  # folder: my-project               # optional: _project/ subdirectory
  dirs:
    backup: backup
    volume: volume
  compose:
    # base: docker-compose.yml       # optional: shared base file
    # local: docker-compose.local.yml
    # dev:
    #   file: docker-compose.dev.yml
    #   env:
    #     DATABASE_URL: dev.example.com:5432
    # prod:
    #   file: docker-compose.prod.yml
    #   env:
    #     DATABASE_URL: prod.example.com:5432
"""


class ConfigError(Exception):
    pass
