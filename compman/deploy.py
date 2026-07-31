from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import boto3
import typer
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
)

from compman.config import ConfigError, load_config, sanitize_project_name
from compman.docker import detect_runtime
from compman.i18n import t
from compman.s3_source import download as _download  # noqa: F401
from compman.s3_source import download_recursive as _download_recursive  # noqa: F401
from compman.s3_source import fetch as _fetch
from compman.scaffold import generate as _generate_scaffold
from compman.scaffold import update_deploy as _update_compman_deploy  # noqa: F401


def deploy(build: bool = False, tag: str | None = None, s3_path: str | None = None) -> None:
    config = None
    if (Path.cwd() / "compman.yml").exists():
        try:
            config = load_config()
        except ConfigError:
            pass

    if not s3_path and config:
        s3_path = config.deploy

    if not s3_path and not config:
        try:
            s3_path = load_config().deploy
        except ConfigError:
            typer.echo(t("msg.empty_dir_deploy"), err=True)
            typer.echo("", err=True)
            typer.echo(t("msg.empty_dir_start"), err=True)
            typer.echo(t("msg.deploy_direct_hint"), err=True)
            typer.echo("     compman deploy --path s3://<your-bucket>/path/to/app.tar.gz", err=True)
            typer.echo(t("msg.config_hint"), err=True)
            typer.echo("     compman init", err=True)
            raise SystemExit(1)

    if not s3_path:
        typer.echo(t("msg.deploy_path_not_configured"), err=True)
        typer.echo(t("msg.deploy_path_hint1"), err=True)
        typer.echo(t("msg.deploy_path_hint2"), err=True)
        raise SystemExit(1)

    project_subfolder = config.dirs.get("project", "project") if config else "project"

    endpoint = os.environ.get("AWS_ENDPOINT_URL_S3") or os.environ.get("AWS_ENDPOINT_URL")

    root = Path.cwd()
    deploy_target = root / project_subfolder
    deploy_target.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix=".deploy_tmp_", dir=root))

    parsed = urlparse(s3_path)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")

    try:
        if parsed.scheme != "s3" or not bucket or not key:
            raise ValueError(f"Invalid S3 path: {s3_path}")
        try:
            s3 = boto3.client("s3", endpoint_url=endpoint or None)
            project_root = _fetch(s3, bucket, key, tmp)
        except (ClientError, EndpointConnectionError, NoCredentialsError, PartialCredentialsError) as e:
            _handle_s3_error(e, s3_path)
        _swap(project_root, deploy_target)
        image = tag or sanitize_project_name(root.name)
        _generate_scaffold(root, project_subfolder, s3_path, image)
        if build:
            typer.echo(f"Building image '{image}' in {project_subfolder}...")
            detect_runtime().passthru_cli(["build", "-t", image, "."], cwd=deploy_target)
        typer.echo("Deploy done.")
    except Exception as e:
        _handle_s3_error(e, s3_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _swap(src: Path, root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix=f".{root.name}.swap-", dir=root.parent))
    moved_old: list[str] = []
    moved_new: list[str] = []
    try:
        for item in list(root.iterdir()):
            if item.name in (".git", ".gitkeep"):
                continue
            shutil.move(str(item), str(backup / item.name))
            moved_old.append(item.name)

        for item in src.iterdir():
            if item.name == ".gitkeep":
                continue
            shutil.move(str(item), str(root / item.name))
            moved_new.append(item.name)
    except Exception:
        for name in moved_new:
            dest = root / name
            if dest.is_dir() and not dest.is_symlink():
                shutil.rmtree(dest)
            elif dest.exists():
                dest.unlink()
        for name in moved_old:
            shutil.move(str(backup / name), str(root / name))
        raise
    finally:
        shutil.rmtree(backup, ignore_errors=True)


def _handle_s3_error(e: Exception, s3_path: str) -> None:
    typer.echo(t("msg.s3_failed", path=s3_path), err=True)
    if isinstance(e, (NoCredentialsError, PartialCredentialsError)):
        typer.echo(t("msg.s3_no_creds"), err=True)
        typer.echo("  • Windows PowerShell:", err=True)
        typer.echo('      $env:AWS_ACCESS_KEY_ID="your-key-id"', err=True)
        typer.echo('      $env:AWS_SECRET_ACCESS_KEY="your-secret-key"', err=True)
        typer.echo('      $env:AWS_DEFAULT_REGION="ap-northeast-2"', err=True)
        typer.echo("  • Windows CMD:", err=True)
        typer.echo("      set AWS_ACCESS_KEY_ID=your-key-id", err=True)
        typer.echo("      set AWS_SECRET_ACCESS_KEY=your-secret-key", err=True)
        typer.echo("      set AWS_DEFAULT_REGION=ap-northeast-2", err=True)
        typer.echo("  • Or configure credentials in ~/.aws/credentials", err=True)

    elif isinstance(e, ClientError):
        err_code = str(e.response.get("Error", {}).get("Code", ""))
        err_msg = str(e.response.get("Error", {}).get("Message", e))
        if err_code in ("403", "AccessDenied", "Forbidden"):
            typer.echo(t("msg.s3_403", path=s3_path), err=True)
            typer.echo("  1️⃣ Ensure AWS credentials have 's3:GetObject' and 's3:ListBucket' permissions.", err=True)
            typer.echo("  2️⃣ Verify S3 bucket name and key path are correct.", err=True)
            typer.echo("  3️⃣ If using local S3 (e.g. ministack), check AWS_ENDPOINT_URL_S3 or AWS_ENDPOINT_URL.", err=True)
        elif err_code in ("404", "NoSuchBucket", "NoSuchKey", "NotFound"):
            typer.echo(t("msg.s3_404", path=s3_path), err=True)
            typer.echo("  1️⃣ Verify bucket name and file/archive path on S3.", err=True)
            typer.echo("  2️⃣ Check for typos in s3://bucket/path", err=True)
        else:
            typer.echo(f"S3 Client Error ({err_code}): {err_msg}", err=True)

    elif isinstance(e, EndpointConnectionError):
        typer.echo(t("msg.s3_network"), err=True)
        typer.echo("", err=True)
        typer.echo("Guide - Troubleshooting connection error:", err=True)
        typer.echo("  1️⃣ Check internet connection.", err=True)
        typer.echo("  2️⃣ If using local S3 (e.g. ministack), check AWS_ENDPOINT_URL_S3 or AWS_ENDPOINT_URL.", err=True)

    else:
        typer.echo(f"Download Error: {e}", err=True)

    raise SystemExit(1)
