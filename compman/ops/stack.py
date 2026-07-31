from __future__ import annotations

import typer

from compman.config import Config
from compman.docker import ContainerRuntime, resolve_compose_context
from compman.i18n import t


def up(runtime: ContainerRuntime, config: Config, profile: str | None = None) -> None:
    context = resolve_compose_context(config, profile)
    runtime.passthru_compose(
        ["up", "-d", "--force-recreate"],
        project=context.project,
        compose_files=context.files,
        env=context.env,
    )


def down(runtime: ContainerRuntime, config: Config, profile: str | None = None) -> None:
    context = resolve_compose_context(config, profile)
    if not runtime.stack_exists(config.name, context.files, context.env):
        typer.echo(t("msg.stack_not_running", name=config.name), err=True)
        return
    runtime.passthru_compose(
        ["down"], project=context.project, compose_files=context.files, env=context.env
    )


def update(
    runtime: ContainerRuntime, config: Config, profile: str | None = None
) -> None:
    context = resolve_compose_context(config, profile)
    runtime.passthru_compose(
        ["up", "-d", "--build", "--force-recreate"],
        project=context.project,
        compose_files=context.files,
        env=context.env,
    )
