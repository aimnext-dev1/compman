from __future__ import annotations

import click

from compman.config import Config
from compman.docker import ContainerRuntime, resolve_compose_files, resolve_simple_files
from compman.i18n import t


def up(runtime: ContainerRuntime, config: Config, profile: str | None = None) -> None:
    if config.has_profiles():
        if not profile:
            profile = next(iter(config.profiles))
            click.echo(f"No profile specified, using: {profile}")
        files, env = resolve_compose_files(config, profile)
        runtime.passthru_compose(
            ["up", "-d"], project=config.name, compose_files=files, env=env,
        )
    else:
        files = resolve_simple_files(config)
        runtime.passthru_compose(
            ["up", "-d"], project=config.name, compose_files=files,
        )


def down(runtime: ContainerRuntime, config: Config) -> None:
    if not runtime.stack_exists(config.name):
        click.echo(t("msg.stack_not_running", name=config.name), err=True)
        return
    runtime.passthru_compose(["down"], project=config.name)


def update(
    runtime: ContainerRuntime, config: Config, profile: str | None = None
) -> None:
    if not runtime.stack_exists(config.name):
        click.echo(t("msg.stack_not_running", name=config.name), err=True)
        return
    if config.has_profiles():
        if not profile:
            profile = next(iter(config.profiles))
            click.echo(f"No profile specified, using: {profile}")
        files, env = resolve_compose_files(config, profile)
        runtime.passthru_compose(
            ["up", "-d", "--build"],
            project=config.name,
            compose_files=files,
            env=env,
        )
    else:
        files = resolve_simple_files(config)
        runtime.passthru_compose(
            ["up", "-d", "--build"],
            project=config.name,
            compose_files=files,
        )
