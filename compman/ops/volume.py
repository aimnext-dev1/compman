from __future__ import annotations

import json
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

import typer

from compman.config import Config
from compman.docker import ContainerRuntime


def backup(
    runtime: ContainerRuntime,
    config: Config,
    no_stop: bool = False,
) -> None:
    if not runtime.stack_exists(config.name):
        typer.echo(f"💡 Stack '{config.name}' is not currently running. Run 'compman stack up' first.", err=True)
        raise SystemExit(1)
    volumes = runtime.list_volumes(config.name)
    if not volumes:
        typer.echo("💡 No volumes found to back up.")
        return
    containers = runtime.list_containers(config.name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_name = f"{config.name}.volume.{timestamp}"
    backup_dir = config.backup_dir / backup_name
    backup_dir.mkdir(parents=True, exist_ok=True)

    if not no_stop:
        typer.echo("Stopping stack for consistent backup...")
        runtime.run_compose(["stop"], project=config.name, capture=False)

    mapping: list[dict[str, str]] = []
    for volume in volumes:
        for container in containers:
            info = _inspect_mount(runtime, container, volume)
            if info:
                mapping.append(info)
                target = backup_dir / volume
                runtime.run_cli(
                    ["cp", f"{container}:{info['destination']}", str(target)],
                    capture=False,
                )

    if not no_stop:
        typer.echo("Starting stack again...")
        runtime.run_compose(["start"], project=config.name, capture=False)

    map_path = backup_dir / "volume-map.json"
    merged = _merge_mapping(mapping)
    map_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")

    tarball = config.backup_dir / f"{backup_name}.tar.gz"
    with tarfile.open(tarball, "w:gz") as tar:
        tar.add(backup_dir, arcname=".")
    shutil.rmtree(backup_dir)

    typer.echo(f"Volume backup done: {tarball}")


from compman.ops.common import select_backup_timestamp


def restore(
    runtime: ContainerRuntime,
    config: Config,
    timestamp: str | None = None,
    no_stop: bool = False,
) -> None:
    if not timestamp:
        timestamp = select_backup_timestamp(config, "volume")

    _validate_timestamp(timestamp)
    backup_name = f"{config.name}.volume.{timestamp}"
    tarball = config.backup_dir / f"{backup_name}.tar.gz"
    if not tarball.is_file():
        typer.echo(f"💡 Backup not found: {tarball}", err=True)
        _list_backups(config, "volume")
        raise SystemExit(1)

    if not runtime.stack_exists(config.name):
        typer.echo(f"💡 Stack '{config.name}' is not currently running. Run 'compman stack up' first.", err=True)
        raise SystemExit(1)

    restore_dir = config.backup_dir / backup_name
    restore_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tarball, "r:gz") as tar:
        tar.extractall(restore_dir)

    map_path = restore_dir / "volume-map.json"
    if not map_path.is_file():
        typer.echo(f"volume-map.json not found in backup.", err=True)
        shutil.rmtree(restore_dir)
        raise SystemExit(1)

    mapping = json.loads(map_path.read_text(encoding="utf-8"))

    if not no_stop:
        typer.echo("Stopping stack for consistent restore...")
        runtime.run_compose(["stop"], project=config.name, capture=False)

    for container, vol_info in mapping.items():
        volume_name = vol_info["volume"]
        dest = vol_info["destination"]
        src = restore_dir / volume_name
        if not src.is_dir():
            typer.echo(f"Warning: data dir '{src}' not found, skipping {container}.")
            continue
        typer.echo(f"Restoring {container}:{dest} ...")
        runtime.run_cli(
            ["cp", f"{str(src)}/.", f"{container}:{dest}"],
            capture=False,
        )

    if not no_stop:
        typer.echo("Starting stack again...")
        runtime.run_compose(["start"], project=config.name, capture=False)

    for container, vol_info in mapping.items():
        volume_name = vol_info["volume"]
        dest = vol_info["destination"]
        src = restore_dir / volume_name
        if not src.is_dir():
            continue
        _fix_permissions(runtime, container, dest)

    shutil.rmtree(restore_dir)
    typer.echo("Volume restore done.")


def pull(runtime: ContainerRuntime, config: Config) -> None:
    if not runtime.stack_exists(config.name):
        typer.echo(f"💡 Stack '{config.name}' is not currently running. Run 'compman stack up' first.", err=True)
        raise SystemExit(1)
    volumes = runtime.list_volumes(config.name)
    if not volumes:
        typer.echo("💡 No volumes found to pull.")
        return
    containers = runtime.list_containers(config.name)

    volume_dir = config.volume_dir
    if volume_dir.is_dir():
        shutil.rmtree(volume_dir)
    volume_dir.mkdir(parents=True)

    mapping: list[dict[str, str]] = []
    for volume in volumes:
        for container in containers:
            info = _inspect_mount(runtime, container, volume)
            if info:
                mapping.append(info)
                target = volume_dir / volume
                runtime.run_cli(
                    ["cp", f"{container}:{info['destination']}", str(target)],
                    capture=False,
                )

    map_path = volume_dir / "volume-map.json"
    merged = _merge_mapping(mapping)
    map_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    typer.echo("Volume pull done.")


def push(runtime: ContainerRuntime, config: Config) -> None:
    volume_dir = config.volume_dir
    map_path = volume_dir / "volume-map.json"
    if not map_path.is_file():
        typer.echo(f"💡 volume-map.json not found at {map_path}. Run 'compman volume pull' first.", err=True)
        raise SystemExit(1)
    if not runtime.stack_exists(config.name):
        typer.echo(f"💡 Stack '{config.name}' is not currently running. Run 'compman stack up' first.", err=True)
        raise SystemExit(1)

    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    for container, vol_info in mapping.items():
        volume_name = vol_info["volume"]
        dest = vol_info["destination"]
        src = volume_dir / volume_name
        if not src.is_dir():
            typer.echo(f"Warning: '{src}' not found, skipping {container}.")
            continue
        typer.echo(f"Pushing to {container}:{dest} ...")
        runtime.run_cli(
            ["cp", f"{str(src)}/.", f"{container}:{dest}"],
            capture=False,
        )
        _fix_permissions(runtime, container, dest)
    typer.echo("Volume push done.")


def _inspect_mount(
    runtime: ContainerRuntime, container: str, volume: str
) -> dict[str, str] | None:
    result = runtime.run_cli(["inspect", container], capture=True, check=False)
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    if not data:
        return None
    for mount in data[0].get("Mounts", []):
        if mount.get("Name") == volume:
            return {
                "container": container,
                "volume": volume,
                "destination": mount["Destination"],
            }
    return None


def _merge_mapping(mapping: list[dict[str, str]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in mapping:
        c = item["container"]
        result[c] = {"volume": item["volume"], "destination": item["destination"]}
    return result


def _fix_permissions(
    runtime: ContainerRuntime, container: str, dest: str
) -> None:
    typer.echo(f"Fixing permissions on {container}:{dest} ...")
    r = runtime.run_cli(
        [
            "exec",
            container,
            "stat",
            "-c",
            "%U %G",
            dest,
        ],
        capture=True,
        check=False,
    )
    if r.returncode != 0:
        return
    parts = r.stdout.strip().split()
    if len(parts) >= 2:
        user, group = parts[0], parts[1]
        runtime.run_cli(
            ["exec", "-u", "root", container, "chown", "-R", f"{user}:{group}", dest],
            capture=False,
            check=False,
        )


def _validate_timestamp(ts: str) -> None:
    try:
        datetime.strptime(ts, "%Y%m%d_%H%M")
    except ValueError:
        typer.echo(
            f"Invalid timestamp format: {ts} (expected YYYYMMDD_HHMM)", err=True
        )
        raise SystemExit(1)


def _list_backups(config: Config, kind: str) -> None:
    pattern = f"{config.name}.{kind}."
    typer.echo(f"Available {kind} backups:")
    for f in sorted(config.backup_dir.glob(f"{pattern}*.tar.gz")):
        name = f.name
        ts = name.replace(pattern, "").replace(".tar.gz", "")
        typer.echo(f"  {ts}")  # ponytail: color omitted, typer handles terminal
