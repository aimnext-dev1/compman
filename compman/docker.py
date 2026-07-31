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

    def logs(self, container: str, follow: bool = False, tail: int = 50) -> int:
        args = ["logs"]
        if follow:
            args.append("-f")
        args.extend(["-n", str(tail), container])
        return self.passthru_cli(args)

    def exec_shell(self, container: str) -> int:
        return self.passthru_cli(
            [
                "exec",
                "-it",
                container,
                "sh",
                "-c",
                "if command -v bash >/dev/null 2>&1; then exec bash; else exec sh; fi",
            ]
        )

    def inspect_container(self, container: str, check: bool = True) -> subprocess.CompletedProcess:
        return self.run_cli(["inspect", container], capture=True, check=check)

    def copy_from_container(self, container: str, source: str, destination: Path) -> None:
        self.run_cli(["cp", f"{container}:{source}", str(destination)], capture=False)

    def copy_to_container(self, source: Path | str, container: str, destination: str) -> None:
        self.run_cli(["cp", f"{source}", f"{container}:{destination}"], capture=False)

    def fix_permissions(self, container: str, destination: str) -> None:
        result = self.run_cli(
            ["exec", container, "stat", "-c", "%U %G", destination],
            capture=True,
            check=False,
        )
        if result.returncode != 0:
            return
        parts = result.stdout.strip().split()
        if len(parts) >= 2:
            self.run_cli(
                ["exec", "-u", "root", container, "chown", "-R", f"{parts[0]}:{parts[1]}", destination],
                capture=False,
                check=False,
            )

    def inspect_value(self, container: str, format_string: str) -> str:
        result = self.run_cli(
            ["inspect", "--format", format_string, container], capture=True
        )
        return result.stdout.strip()

    def commit_container(self, container: str, tag: str) -> None:
        self.run_cli(["commit", container, tag], capture=False)

    def save_image(self, image: str, destination: Path) -> None:
        self.run_cli(["save", "-o", str(destination), image], capture=False)

    def remove_image(self, image: str) -> None:
        self.run_cli(["rmi", image], capture=False, check=False)

    def load_image(self, source: Path) -> None:
        self.run_cli(["load", "-i", str(source)], capture=False)

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

    def stack_exists(
        self,
        name: str,
        compose_files: Sequence[Path] | None = None,
        env: dict[str, str] | None = None,
    ) -> bool:
        result = self.run_compose(
            ["ls", "-a"], compose_files=compose_files, env=env, capture=True, check=False
        )
        _raise_probe_failure(result)
        if any(line.split(maxsplit=1)[0] == name for line in result.stdout.splitlines() if line.strip()):
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

    def list_containers(
        self,
        project: str,
        compose_files: Sequence[Path] | None = None,
        env: dict[str, str] | None = None,
    ) -> list[str]:
        result = self.run_compose(
            ["ps", "-a", "--format", "{{.Names}}"],
            project=project,
            compose_files=compose_files,
            env=env,
            check=False,
        )
        _raise_probe_failure(result)
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
        _raise_probe_failure(result)
        return [v for v in result.stdout.strip().splitlines() if v]

    def get_container_id(self, name: str, project: str | None = None) -> str:
        filters = [f"name=^{name}$"]
        if project:
            filters.append(f"label=com.docker.compose.project={project}")
        result = self.run_cli(
            [
                "ps",
                "-a",
                *sum((["--filter", value] for value in filters), []),
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


def _raise_probe_failure(result: subprocess.CompletedProcess) -> None:
    code = getattr(result, "returncode", 0)
    if isinstance(code, int) and code != 0:
        _die(getattr(result, "args", ["container runtime"]), result)


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


@dataclass(frozen=True)
class ComposeContext:
    project: str
    files: tuple[Path, ...]
    env: dict[str, str]


def resolve_compose_context(config: Config, profile: str | None = None) -> ComposeContext:
    if config.has_profiles():
        if profile is None:
            profile = next(iter(config.profiles))
        if config.source_path:
            files, env = resolve_compose_files(config, profile)
        else:
            prof = config.profiles[profile]
            file_name = prof.file or config.compose_base or "docker-compose.yml"
            files = [config.project_dir / file_name]
            env = dict(prof.env)
    else:
        if profile:
            raise ConfigError("No profiles configured. Remove profile argument.")
        if config.source_path:
            files = resolve_simple_files(config)
        else:
            files = [config.project_dir / name for name in (config.compose_files or [])]
        env = {}
    return ComposeContext(config.name, tuple(files), env)


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
