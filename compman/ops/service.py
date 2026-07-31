from __future__ import annotations

import typer

from compman.config import Config
from compman.docker import ContainerRuntime, resolve_compose_context
from compman.i18n import t


def start(
    runtime: ContainerRuntime, config: Config, services: tuple[str, ...], profile: str | None = None
) -> None:
    args = ["start"]
    _passthru_with_services(runtime, config, args, services, profile)


def stop(
    runtime: ContainerRuntime, config: Config, services: tuple[str, ...], profile: str | None = None
) -> None:
    args = ["stop"]
    _passthru_with_services(runtime, config, args, services, profile)


def restart(
    runtime: ContainerRuntime, config: Config, services: tuple[str, ...], profile: str | None = None
) -> None:
    args = ["restart"]
    _passthru_with_services(runtime, config, args, services, profile)


def status(runtime: ContainerRuntime, config: Config, profile: str | None = None) -> None:
    context = resolve_compose_context(config, profile)
    runtime.passthru_compose(
        ["ps", "-a"], project=context.project, compose_files=context.files, env=context.env
    )


def log(
    runtime: ContainerRuntime,
    config: Config,
    service: str | None,
    follow: bool = False,
    tail: int = 50,
    profile: str | None = None,
) -> None:
    context = resolve_compose_context(config, profile)
    if not service:
        containers = runtime.list_containers(config.name, context.files, context.env)
        if len(containers) == 0:
            typer.echo(t("msg.no_running_containers"), err=True)
            return
        if len(containers) == 1:
            service = containers[0]
            typer.echo(t("msg.auto_selected", name=service))
        else:
            typer.echo(t("msg.available_containers"))
            for c in containers:
                typer.echo(f"  {c}")
            return
    cid = runtime.get_container_id(service, config.name)
    if not cid:
        typer.echo(t("msg.container_not_found", service=service), err=True)
        return

    cmd = ["logs"]
    if follow:
        cmd.append("-f")
    cmd.extend(["-n", str(tail), cid])
    runtime.passthru_cli(cmd)


def connect(
    runtime: ContainerRuntime, config: Config, service: str | None, profile: str | None = None
) -> None:
    context = resolve_compose_context(config, profile)
    if not service:
        containers = runtime.list_containers(config.name, context.files, context.env)
        if len(containers) == 0:
            typer.echo(t("msg.no_running_containers"), err=True)
            return
        if len(containers) == 1:
            service = containers[0]
            typer.echo(t("msg.auto_selected", name=service))
        else:
            typer.echo(t("msg.specify_container"))
            for c in containers:
                typer.echo(f"  {c}")
            return
    cid = runtime.get_container_id(service, config.name)
    if not cid:
        typer.echo(t("msg.container_not_found", service=service), err=True)
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
    profile: str | None,
) -> None:
    context = resolve_compose_context(config, profile)
    if services:
        args += list(services)
        names = ", ".join(services)
        typer.echo(f"Services: {names}")
    else:
        typer.echo("All services")
    runtime.passthru_compose(
        args, project=context.project, compose_files=context.files, env=context.env
    )
