from __future__ import annotations

import typer

from compman.config import Config
from compman.docker import ComposeContext, ContainerRuntime, resolve_compose_context
from compman.errors import CommandError
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
    container = _resolve_container(runtime, config, service, context)
    if not container:
        return
    runtime.logs(container, follow=follow, tail=tail)


def connect(
    runtime: ContainerRuntime, config: Config, service: str | None, profile: str | None = None
) -> None:
    context = resolve_compose_context(config, profile)
    container = _resolve_container(runtime, config, service, context, connect=True)
    if not container:
        return
    runtime.exec_shell(container)


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
        typer.echo(t("msg.services_list", names=names))
    else:
        typer.echo(t("msg.all_services"))
    runtime.passthru_compose(
        args, project=context.project, compose_files=context.files, env=context.env
    )


def _resolve_container(
    runtime: ContainerRuntime,
    config: Config,
    service: str | None,
    context: ComposeContext,
    connect: bool = False,
) -> str | None:
    if service:
        result = runtime.run_compose(
            ["ps", "-q", service],
            project=context.project,
            compose_files=context.files,
            env=context.env,
            check=False,
        )
        containers = result.stdout.strip().splitlines()
        if not containers:
            raise CommandError(t("msg.no_running_containers"))
        if len(containers) == 1:
            resolved = containers[0]
            typer.echo(t("msg.resolved_container", service=service, container=resolved))
            return resolved
        raise CommandError(t("msg.scaled_service_ambiguous", service=service, count=len(containers)))
    containers = runtime.list_containers(config.name, context.files, context.env)
    if not containers:
        raise CommandError(t("msg.no_running_containers"))
    if len(containers) == 1:
        service = containers[0]
        typer.echo(t("msg.auto_selected", name=service))
        return service
    typer.echo(t("msg.specify_container" if connect else "msg.available_containers"))
    for container in containers:
        typer.echo(f"  {container}")
    return None
