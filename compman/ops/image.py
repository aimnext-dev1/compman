from __future__ import annotations

import shutil
import tarfile
from datetime import datetime
from pathlib import Path

import typer

from compman.archive import extract_tar
from compman.config import Config
from compman.docker import ContainerRuntime, resolve_compose_context
from compman.i18n import t


def backup(
    runtime: ContainerRuntime,
    config: Config,
    source_mode: bool = False,
    profile: str | None = None,
) -> None:
    context = resolve_compose_context(config, profile)
    if not runtime.stack_exists(config.name, context.files, context.env):
        typer.echo(t("msg.stack_not_running", name=config.name), err=True)
        raise SystemExit(1)

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    backup_name = f"{config.name}.image.{timestamp}"
    backup_dir = config.backup_dir / backup_name
    tarball = config.backup_dir / f"{backup_name}.tar.gz"
    if backup_dir.exists() or tarball.exists():
        timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{config.name}.image.{timestamp}"
        backup_dir = config.backup_dir / backup_name
        tarball = config.backup_dir / f"{backup_name}.tar.gz"
    backup_dir.mkdir(parents=True)
    backup_tags: list[str] = []

    try:
        result = runtime.run_compose(
            ["ps", "-q"], project=context.project, compose_files=context.files, env=context.env, capture=True
        )
        container_ids = result.stdout.strip().splitlines()
        if not container_ids:
            typer.echo(t("msg.no_running_containers"))
            return

        for cid in container_ids:
            cid = cid.strip()
            if not cid:
                continue
            container_name = runtime.inspect_value(cid, "{{.Name}}").strip("/")

            if source_mode:
                image_id = runtime.inspect_value(cid, "{{.Image}}")
                runtime.save_image(
                    image_id, backup_dir / f"{container_name}.image.backup.tar"
                )
            else:
                tag = f"{container_name}:backup"
                backup_tags.append(tag)
                runtime.commit_container(cid, tag)
                runtime.save_image(tag, backup_dir / f"{container_name}.image.backup.tar")

        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(backup_dir, arcname=".")
    except Exception:
        tarball.unlink(missing_ok=True)
        raise
    finally:
        for tag in backup_tags:
            runtime.remove_image(tag)
        shutil.rmtree(backup_dir, ignore_errors=True)

    typer.echo(f"Image backup done: {tarball}")


from compman.ops.common import prompt_select, select_backup_timestamp


def restore(
    runtime: ContainerRuntime,
    config: Config,
    timestamp: str | None = None,
    profile: str | None = None,
) -> None:
    if not timestamp:
        timestamp = select_backup_timestamp(config, "image")

    _validate_timestamp(timestamp)

    backup_name = f"{config.name}.image.{timestamp}"
    tarball = config.backup_dir / f"{backup_name}.tar.gz"
    if not tarball.is_file():
        typer.echo(t("msg.backup_not_found", tarball=tarball), err=True)
        _list_backups(config)
        raise SystemExit(1)

    restore_dir = config.backup_dir / backup_name
    restore_dir.mkdir(parents=True)
    with tarfile.open(tarball, "r:gz") as tar:
        extract_tar(tar, restore_dir)

    for tar_file in restore_dir.glob("*.tar"):
        typer.echo(f"Loading {tar_file.name} ...")
        runtime.load_image(tar_file)
        tar_file.unlink()

    shutil.rmtree(restore_dir)
    typer.echo("Image restore done. Update docker-compose.yml image tags and run 'compman stack up'.")


def _validate_timestamp(ts: str) -> None:
    if not any(
        _valid_timestamp(ts, fmt)
        for fmt in ("%Y%m%d_%H%M", "%Y%m%d_%H%M%S", "%Y%m%d_%H%M%S_%f")
    ):
        typer.echo(
            f"Invalid timestamp: {ts} (expected YYYYMMDD_HHMM[SS])", err=True
        )
        raise SystemExit(1)


def _valid_timestamp(value: str, fmt: str) -> bool:
    try:
        datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


def _list_backups(config: Config) -> None:
    typer.echo("Available image backups:")
    for f in sorted(config.backup_dir.glob(f"{config.name}.image.*.tar.gz")):
        ts = f.name.replace(f"{config.name}.image.", "").replace(".tar.gz", "")
        typer.echo(f"  {ts}")
