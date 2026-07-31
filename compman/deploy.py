from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import boto3
import click

from compman.config import ConfigError, load_config
from compman.docker import detect_runtime


_ARCHIVE_SUFFIXES = (".tar.gz", ".tgz", ".zip")


def deploy(build: bool = False, tag: str | None = None, s3_path: str | None = None) -> None:
    if not s3_path:
        try:
            s3_path = load_config().deploy
        except ConfigError as e:
            click.echo(f"Config error: {e}", err=True)
            raise SystemExit(1)
    if not s3_path:
        click.echo("S3 path not configured.", err=True)
        click.echo("Set 'deploy' in compman.yml or pass --path.")
        raise SystemExit(1)

    endpoint = os.environ.get("COMPMAN_S3_ENDPOINT")

    root = Path.cwd()
    tmp = Path(tempfile.mkdtemp(prefix=".deploy_tmp_", dir=root))

    parsed = urlparse(s3_path)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")

    s3 = boto3.client("s3", endpoint_url=endpoint or None)

    try:
        project_root = _fetch(s3, bucket, key, tmp)
        _swap(project_root, root)
        image = tag or root.name.lower()
        _generate_scaffold(root, s3_path, image)
        if build:
            click.echo(f"Building image '{image}'...")
            detect_runtime().passthru_cli(["build", "-t", image, "."])
        click.echo("Deploy done.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _generate_scaffold(root: Path, s3_path: str, image: str) -> None:
    compman_yml = root / "compman.yml"
    if not compman_yml.exists():
        compman_yml.write_text(
            f"compman:\n"
            f"  name: {root.name}\n"
            f"  deploy: {s3_path}\n"
            f"  compose:\n"
            f"    - docker-compose.yml\n",
            encoding="utf-8",
        )
        click.echo("Created compman.yml")

    compose_yml = root / "docker-compose.yml"
    if not compose_yml.exists():
        compose_yml.write_text(
            f"services:\n"
            f"  app:\n"
            f"    image: {image}\n"
            f"    restart: unless-stopped\n",
            encoding="utf-8",
        )
        click.echo("Created docker-compose.yml")


def _fetch(s3, bucket: str, key: str, tmp: Path) -> Path:
    if key.endswith(_ARCHIVE_SUFFIXES):
        archive = tmp / key.rsplit("/", 1)[-1]
        _download(s3, bucket, key, archive)
        extract_dir = tmp / "extract"
        extract_dir.mkdir()
        if key.endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(extract_dir)
        else:
            with tarfile.open(archive) as tf:
                tf.extractall(extract_dir, filter="data")
        contents = [p for p in extract_dir.iterdir() if p.name != ".gitkeep"]
        if len(contents) == 1 and contents[0].is_dir():
            return contents[0]
        return extract_dir

    src = tmp / "src"
    _download_recursive(s3, bucket, key, src)
    return src


def _swap(src: Path, root: Path) -> None:
    for item in src.iterdir():
        if item.name == ".gitkeep":
            continue
        dest = root / item.name
        if dest.is_dir():
            shutil.rmtree(dest, ignore_errors=True)
        elif dest.exists():
            dest.unlink()
        shutil.move(str(item), str(dest))


def _download(s3, bucket: str, key: str, dst: Path) -> None:
    try:
        s3.download_file(bucket, key, str(dst))
    except Exception as e:
        raise RuntimeError(f"s3 download failed: {key}") from e


def _download_recursive(s3, bucket: str, key_prefix: str, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    paginator = s3.get_paginator("list_objects_v2")
    prefix_arg = f"{key_prefix}/" if key_prefix else ""
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix_arg):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            rel = key[len(key_prefix) :].lstrip("/")
            dest = dst_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            _download(s3, bucket, key, dest)
