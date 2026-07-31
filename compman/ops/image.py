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

    result = runtime.run_compose(
        ["ps", "-q"], project=config.name, capture=True
    )
    container_ids = result.stdout.strip().splitlines()
    if not container_ids:
        typer.echo("💡 No running containers found in this stack to back up.")
        shutil.rmtree(backup_dir)
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
            runtime.run_cli(["rmi", tag], capture=False)

    tarball = config.backup_dir / f"{backup_name}.tar.gz"
    with tarfile.open(tarball, "w:gz") as tar:
        tar.add(backup_dir, arcname=".")
    shutil.rmtree(backup_dir)
    typer.echo(f"Image backup done: {tarball}")


import sys


def _get_key() -> str:
    if sys.platform == "win32":
        import msvcrt

        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            ch2 = msvcrt.getch()
            if ch2 == b"H":
                return "up"
            elif ch2 == b"P":
                return "down"
            return "other"
        elif ch in (b"\r", b"\n"):
            return "enter"
        elif ch == b"\x1b":
            return "esc"
        elif ch == b"\x03":
            raise KeyboardInterrupt()
        return "other"
    else:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                if rlist:
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A":
                            return "up"
                        elif ch3 == "B":
                            return "down"
                return "esc"
            elif ch in ("\r", "\n"):
                return "enter"
            elif ch == "\x03":
                raise KeyboardInterrupt()
            return "other"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def prompt_select(title: str, options: list[str], default_index: int = 0) -> int:
    if not sys.stdin.isatty():
        typer.echo(title)
        for i, opt in enumerate(options, 1):
            typer.echo(f"  [{i}] {opt}")
        choice = typer.prompt(f"Select option [1-{len(options)}]", default=str(default_index + 1))
        return int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(options) else default_index

    selected = default_index

    def render(redraw: bool = False) -> None:
        if redraw:
            sys.stdout.write(f"\033[{len(options)}A")
        for i, option in enumerate(options):
            if i == selected:
                sys.stdout.write(f"\033[K \033[36m❯ {option}\033[0m\n")
            else:
                sys.stdout.write(f"\033[K   {option}\n")
        sys.stdout.flush()

    typer.echo(f"💡 {title} (Use ↑/↓ arrow keys, Enter to select, ESC to cancel):")
    render(redraw=False)

    while True:
        try:
            key = _get_key()
            if key == "up":
                selected = (selected - 1) % len(options)
                render(redraw=True)
            elif key == "down":
                selected = (selected + 1) % len(options)
                render(redraw=True)
            elif key == "enter":
                break
            elif key == "esc":
                typer.echo("Operation cancelled.")
                raise SystemExit(0)
        except KeyboardInterrupt:
            typer.echo("")
            raise SystemExit(0)

    return selected


def select_backup_timestamp(config: Config, kind: str) -> str:
    pattern = f"{config.name}.{kind}."
    if not config.backup_dir.is_dir():
        typer.echo(f"💡 Backup directory not found at {config.backup_dir}.", err=True)
        raise SystemExit(1)

    files = sorted(config.backup_dir.glob(f"{pattern}*.tar.gz"))
    if not files:
        typer.echo(f"💡 No {kind} backup files found in {config.backup_dir}.", err=True)
        raise SystemExit(1)

    timestamps = [f.name.replace(pattern, "").replace(".tar.gz", "") for f in files]

    idx = prompt_select(
        f"Available {kind} backups",
        timestamps,
        default_index=len(timestamps) - 1,
    )
    selected = timestamps[idx]
    typer.echo(f"Selected backup: {selected}")
    return selected


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
