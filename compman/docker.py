from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from compman.config import Config, ConfigError


@dataclass
class ContainerRuntime:
    name: str
    cli: list[str]
    compose: list[str]

    def run_cli(
        self,
        args: Sequence[str],
        capture: bool = True,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        return _run(self.cli + list(args), capture=capture, check=check)

    def run_compose(
        self,
        args: Sequence[str],
        project: str | None = None,
        compose_files: Sequence[Path] | None = None,
        env: dict[str, str] | None = None,
        capture: bool = True,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        cmd = self._compose_cmd(project, compose_files) + list(args)
        return _run(cmd, extra_env=env, capture=capture, check=check)

    def passthru_compose(
        self,
        args: Sequence[str],
        project: str | None = None,
        compose_files: Sequence[Path] | None = None,
        env: dict[str, str] | None = None,
    ) -> int:
        cmd = self._compose_cmd(project, compose_files) + list(args)
        return _passthru(cmd, extra_env=env)

    def passthru_cli(self, args: Sequence[str], cwd: Path | str | None = None) -> int:
        return _passthru(self.cli + list(args), cwd=cwd)

    def _compose_cmd(
        self,
        project: str | None,
        compose_files: Sequence[Path] | None,
    ) -> list[str]:
        cmd: list[str] = []
        cmd += self.compose
        if project:
            cmd += ["-p", project]
        if compose_files:
            for f in compose_files:
                cmd += ["-f", str(f)]
        return cmd

    def stack_exists(self, name: str) -> bool:
        result = self.run_compose(["ls", "-a"], capture=True, check=False)
        if name in result.stdout:
            return True
        r = self.run_cli(
            [
                "ps",
                "-a",
                "--filter",
                f"label=com.docker.compose.project={name}",
                "--format",
                "{{.Names}}",
            ],
            check=False,
        )
        return bool(r.stdout.strip())

    def list_containers(self, project: str) -> list[str]:
        result = self.run_compose(
            ["ps", "-a", "--format", "{{.Names}}"],
            project=project,
            check=False,
        )
        return [c for c in result.stdout.strip().splitlines() if c]

    def list_volumes(self, project: str) -> list[str]:
        result = self.run_cli(
            [
                "volume",
                "ls",
                "--filter",
                f"label=com.docker.compose.project={project}",
                "--format",
                "{{.Name}}",
            ],
            check=False,
        )
        return [v for v in result.stdout.strip().splitlines() if v]

    def get_container_id(self, name: str) -> str:
        result = self.run_cli(
            [
                "ps",
                "-a",
                "--filter",
                f"name=^{name}$",
                "--format",
                "{{.ID}}",
            ],
        )
        return result.stdout.strip()


def detect_runtime() -> ContainerRuntime:
    override = os.environ.get("CONTAINER_RUNTIME", "").lower()

    if not override or override == "docker":
        ok, _ = _check_cmd(["docker", "compose", "version"])
        if ok:
            return ContainerRuntime(
                name="docker",
                cli=["docker"],
                compose=["docker", "compose"],
            )

    if not override or override == "podman":
        ok, _ = _check_cmd(["podman", "compose", "version"])
        if ok:
            return ContainerRuntime(
                name="podman",
                cli=["podman"],
                compose=["podman", "compose"],
            )

    if not override or override == "podman":
        ok, _ = _check_cmd(["podman-compose", "--version"])
        if ok:
            return ContainerRuntime(
                name="podman",
                cli=["podman"],
                compose=["podman-compose"],
            )

    if not override or override == "docker":
        ok, _ = _check_cmd(["docker-compose", "--version"])
        if ok:
            return ContainerRuntime(
                name="docker",
                cli=["docker"],
                compose=["docker-compose"],
            )

    msg = "No container runtime found. Install Docker or Podman."
    if override:
        msg = f"Runtime '{override}' not found."
    raise RuntimeError(msg)


def _check_cmd(cmd: list[str]) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.returncode == 0, r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def _run(
    cmd: Sequence[str],
    extra_env: dict[str, str] | None = None,
    capture: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess:
    env = _merged_env(extra_env)
    kwargs: dict = {}
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    try:
        r = subprocess.run(list(cmd), env=env, **kwargs, timeout=300)
    except FileNotFoundError:
        raise RuntimeError(f"Command not found: {cmd[0]}")
    if check and r.returncode != 0:
        _die(cmd, r)
    return r


def _passthru(
    cmd: Sequence[str],
    extra_env: dict[str, str] | None = None,
    cwd: Path | str | None = None,
) -> int:
    env = _merged_env(extra_env)
    try:
        r = subprocess.run(list(cmd), env=env, cwd=cwd, timeout=3600)
    except FileNotFoundError:
        raise RuntimeError(f"Command not found: {cmd[0]}")
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"Command timed out after 3600 seconds: {' '.join(cmd)}") from e
    if r.returncode != 0:
        _die(cmd, r)
    return r.returncode


def _merged_env(extra: dict[str, str] | None) -> dict[str, str]:
    if not extra:
        merged = dict(os.environ)
    else:
        merged = {**os.environ, **extra}
    merged.pop("PYTHONPATH", None)
    return merged


def _die(cmd: Sequence[str], r: subprocess.CompletedProcess) -> None:
    msg = f"Command failed: {' '.join(cmd)} (exit={r.returncode})"
    if r.stderr:
        msg += f"\nstderr: {r.stderr.strip()}"
    if r.stdout:
        msg += f"\nstdout: {r.stdout.strip()}"
    raise RuntimeError(msg)


def resolve_compose_files(
    config: Config, profile: str
) -> tuple[list[Path], dict[str, str]]:
    if not config.has_profiles():
        raise ConfigError(f"No profiles configured. Use 'compman stack up' without env.")

    prof = config.profiles.get(profile)
    if not prof:
        known = ", ".join(config.profiles)
        raise ConfigError(f"Unknown profile: {profile}. Known: {known}")

    project_dir = config.project_dir
    file_name = prof.file or config.compose_base or "docker-compose.yml"
    compose_file = project_dir / file_name
    if not compose_file.is_file():
        raise ConfigError(f"Compose file not found: {compose_file}")

    files = [compose_file]
    if config.compose_base and prof.file:
        base = project_dir / config.compose_base
        if not base.is_file():
            raise ConfigError(f"Base compose file not found: {base}")
        files.insert(0, base)

    return files, dict(prof.env)


def resolve_simple_files(config: Config) -> list[Path]:
    if not config.has_simple_files():
        raise ConfigError("No compose files configured.")
    project_dir = config.project_dir
    files: list[Path] = []
    for name in config.compose_files:
        f = project_dir / name
        if not f.is_file():
            raise ConfigError(f"Compose file not found: {f}")
        files.append(f)
    return files
