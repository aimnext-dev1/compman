from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import re
import yaml


def sanitize_project_name(name: str) -> str:
    """Normalize a string to a valid Docker Compose project name.

    Docker Compose project names must match [a-z0-9_-], start with [a-z0-9],
    and be entirely lowercase.
    """
    if not name:
        return "compman-app"
    s = str(name).lower()
    s = re.sub(r"[^a-z0-9_-]", "-", s)
    s = re.sub(r"^[^a-z0-9]+", "", s)
    s = s.strip("-_")
    return s or "compman-app"


@dataclass
class Profile:
    file: str | None = None
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class Config:
    name: str
    root_dir: Path = field(default_factory=Path.cwd)
    source_path: Path | None = None
    folder: str | None = None
    dirs: dict[str, str] = field(
        default_factory=lambda: {"backup": "backup", "volume": "volume", "project": "project"}
    )
    compose_base: str | None = None
    compose_files: list[str] | None = None
    profiles: dict[str, Profile] = field(default_factory=dict)
    deploy: str | None = None

    @property
    def project_dir(self) -> Path:
        return self.root_dir / self.folder if self.folder else self.root_dir

    @property
    def backup_dir(self) -> Path:
        return self.root_dir / self.dirs.get("backup", "backup")

    @property
    def volume_dir(self) -> Path:
        return self.root_dir / self.dirs.get("volume", "volume")

    @property
    def deploy_dir(self) -> Path:
        return self.root_dir / self.dirs.get("project", "project")

    def has_profiles(self) -> bool:
        return bool(self.profiles)

    def has_simple_files(self) -> bool:
        return self.compose_files is not None


def load_config(config_path: str | None = None) -> Config:
    path = (Path(config_path) if config_path else Path.cwd() / "compman.yml").resolve()
    if not path.is_file():
        raise ConfigError(
            f"{path} not found. Run 'compman init' first."
        )
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}") from e
    if not raw or not isinstance(raw, dict):
        raise ConfigError("Invalid config file: not a YAML mapping.")
    root = raw.get("compman")
    if not root or not isinstance(root, dict):
        raise ConfigError("'compman' key not found or not a mapping.")

    raw_name = root.get("name") or path.parent.name
    name = sanitize_project_name(str(raw_name))

    folder = root.get("folder")
    if folder is not None and not isinstance(folder, str):
        raise ConfigError("'folder' must be a string.")
    raw_dirs = root.get("dirs", {})
    if not isinstance(raw_dirs, dict):
        raise ConfigError("'dirs' must be a mapping.")
    dirs = {
        "backup": str(raw_dirs.get("backup", "backup")),
        "volume": str(raw_dirs.get("volume", "volume")),
        "project": str(raw_dirs.get("project", "project")),
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
                raw_env = val.get("env", {})
                if not isinstance(raw_env, dict):
                    raise ConfigError(f"'compose.{key}.env' must be a mapping.")
                profiles[key] = Profile(
                    file=str(f) if f else None,
                    env={str(k): str(v) for k, v in raw_env.items()},
                )
            else:
                raise ConfigError(
                    f"Invalid value for 'compose.{key}': expected string or object."
                )
    else:
        raise ConfigError(
            "'compose' must be a list, dict, or omitted."
        )

    raw_deploy = root.get("deploy")
    if raw_deploy is not None and not isinstance(raw_deploy, str):
        raise ConfigError("'deploy' must be a string (e.g. 's3://bucket/app').")

    return Config(
        name=name,
        root_dir=path.parent,
        source_path=path,
        folder=folder,
        dirs=dirs,
        compose_base=compose_base,
        compose_files=compose_files,
        profiles=profiles,
        deploy=raw_deploy,
    )


def dump_default_config(name: str) -> str:
    sanitized = sanitize_project_name(name)
    return f"""compman:
  name: {sanitized}
  compose:
    - docker-compose.yml
  # --- optional features ---
  # folder: my-project             # _project/ subdirectory
  # deploy: s3://bucket/app        # deploy source (--path overrides)
  # dirs:
  #   backup: backup
  #   volume: volume
  # profile mode (alternative to the compose list above):
  # compose:
  #   base: docker-compose.yml
  #   local: docker-compose.local.yml
  #   dev:
  #     file: docker-compose.dev.yml
  #     env:
  #       DATABASE_URL: dev.example.com:5432
  #   prod:
  #     file: docker-compose.prod.yml
  #     env:
  #       DATABASE_URL: prod.example.com:5432
"""


class ConfigError(Exception):
    pass
