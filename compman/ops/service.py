from __future__ import annotations

import click

from compman.config import Config
from compman.docker import ContainerRuntime


def start(
    runtime: ContainerRuntime, config: Config, services: tuple[str, ...]
) -> None:
    args = ["start"]
    _passthru_with_services(runtime, config, args, services)


def stop(
    runtime: ContainerRuntime, config: Config, services: tuple[str, ...]
) -> None:
    args = ["stop"]
    _passthru_with_services(runtime, config, args, services)


def restart(
    runtime: ContainerRuntime, config: Config, services: tuple[str, ...]
) -> None:
    args = ["restart"]
    _passthru_with_services(runtime, config, args, services)


def status(runtime: ContainerRuntime, config: Config) -> None:
    runtime.passthru_compose(["ps", "-a"], project=config.name)


def log(
    runtime: ContainerRuntime,
    config: Config,
    service: str | None,
    follow: bool = False,
    tail: int = 50,
) -> None:
    if not service:
        containers = runtime.list_containers(config.name)
        if len(containers) == 0:
            click.echo("💡 No running containers found in this stack. Run 'compman stack up' first.", err=True)
            return
        if len(containers) == 1:
            service = containers[0]
            click.echo(f"Auto-selected: {service}")
        else:
            click.echo("Available containers:")
            for c in containers:
                click.echo(f"  {c}")
            return
    cid = runtime.get_container_id(service)
    if not cid:
        click.echo(f"💡 Container '{service}' not found. Run 'compman service status' to check running containers.", err=True)
        return

    cmd = ["logs"]
    if follow:
        cmd.append("-f")
    cmd.extend(["-n", str(tail), cid])
    runtime.passthru_cli(cmd)


def connect(runtime: ContainerRuntime, config: Config, service: str | None) -> None:
    if not service:
        containers = runtime.list_containers(config.name)
        if len(containers) == 0:
            click.echo("💡 No running containers found in this stack. Run 'compman stack up' first.", err=True)
            return
        if len(containers) == 1:
            service = containers[0]
            click.echo(f"Auto-selected: {service}")
        else:
            click.echo("Specify a container name:")
            for c in containers:
                click.echo(f"  {c}")
            return
    cid = runtime.get_container_id(service)
    if not cid:
        click.echo(f"💡 Container '{service}' not found. Run 'compman service status' to check running containers.", err=True)
        return
    runtime.passthru_cli([
        "exec",
        "-it",
        cid,
        "sh",
        "-c",
        "if command -v bash >/dev/null 2>&1; then exec bash; else exec sh; fi",
    ])


def _passthru_with_services(
    runtime: ContainerRuntime,
    config: Config,
    args: list[str],
    services: tuple[str, ...],
) -> None:
    if services:
        args += list(services)
        names = ", ".join(services)
        click.echo(f"Services: {names}")
    else:
        click.echo("All services")
    runtime.passthru_compose(args, project=config.name)
