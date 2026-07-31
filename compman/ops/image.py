from __future__ import annotations

import re
import shutil
import tarfile
from datetime import datetime
from pathlib import Path

import typer

from compman.config import Config
from compman.docker import ContainerRuntime


def backup(
    runtime: ContainerRuntime,
    config: Config,
    source_mode: bool = False,
) -> None:
    if not runtime.stack_exists(config.name):
        typer.echo(f"💡 Stack '{config.name}' is not currently running. Run 'compman stack up' first.", err=True)
        raise SystemExit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_name = f"{config.name}.image.{timestamp}"
    backup_dir = config.backup_dir / backup_name
    backup_dir.mkdir(parents=True)
    tarball = config.backup_dir / f"{backup_name}.tar.gz"
    backup_tags: list[str] = []

    try:
        result = runtime.run_compose(
            ["ps", "-q"], project=config.name, capture=True
        )
        container_ids = result.stdout.strip().splitlines()
        if not container_ids:
            typer.echo("💡 No running containers found in this stack to back up.")
            return

        for cid in container_ids:
            cid = cid.strip()
            if not cid:
                continue
            r = runtime.run_cli(
                ["inspect", "--format", "{{.Name}}", cid], capture=True
            )
            container_name = r.stdout.strip().strip("/")

            if source_mode:
                r2 = runtime.run_cli(
                    ["inspect", "--format", "{{.Image}}", cid], capture=True
                )
                image_id = r2.stdout.strip()
                runtime.run_cli(
                    [
                        "save",
                        "-o",
                        str(backup_dir / f"{container_name}.image.backup.tar"),
                        image_id,
                    ],
                    capture=False,
                )
            else:
                tag = f"{container_name}:backup"
                backup_tags.append(tag)
                runtime.run_cli(["commit", cid, tag], capture=False)
                runtime.run_cli(
                    [
                        "save",
                        "-o",
                        str(backup_dir / f"{container_name}.image.backup.tar"),
                        tag,
                    ],
                    capture=False,
                )

        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(backup_dir, arcname=".")
    except Exception:
        tarball.unlink(missing_ok=True)
        raise
    finally:
        for tag in backup_tags:
            runtime.run_cli(["rmi", tag], capture=False, check=False)
        shutil.rmtree(backup_dir, ignore_errors=True)

    typer.echo(f"Image backup done: {tarball}")


from compman.ops.common import prompt_select, select_backup_timestamp


def restore(
    runtime: ContainerRuntime, config: Config, timestamp: str | None = None
) -> None:
    if not timestamp:
        timestamp = select_backup_timestamp(config, "image")

    _validate_timestamp(timestamp)

    backup_name = f"{config.name}.image.{timestamp}"
    tarball = config.backup_dir / f"{backup_name}.tar.gz"
    if not tarball.is_file():
        typer.echo(f"Backup not found: {tarball}", err=True)
        _list_backups(config)
        raise SystemExit(1)

    restore_dir = config.backup_dir / backup_name
    restore_dir.mkdir(parents=True)
    with tarfile.open(tarball, "r:gz") as tar:
        tar.extractall(restore_dir)

    for tar_file in restore_dir.glob("*.tar"):
        typer.echo(f"Loading {tar_file.name} ...")
        runtime.run_cli(["load", "-i", str(tar_file)], capture=False)
        tar_file.unlink()

    shutil.rmtree(restore_dir)
    typer.echo("Image restore done. Update docker-compose.yml image tags and run 'compman stack up'.")


def _validate_timestamp(ts: str) -> None:
    try:
        datetime.strptime(ts, "%Y%m%d_%H%M")
    except ValueError:
        typer.echo(
            f"Invalid timestamp: {ts} (expected YYYYMMDD_HHMM)", err=True
        )
        raise SystemExit(1)


def _list_backups(config: Config) -> None:
    pattern = re.escape(config.name) + r"\.image\.\d{8}_\d{4}\.tar\.gz"
    typer.echo("Available image backups:")
    for f in sorted(config.backup_dir.glob(f"{config.name}.image.*.tar.gz")):
        ts = f.name.replace(f"{config.name}.image.", "").replace(".tar.gz", "")
        typer.echo(f"  {ts}")
