from __future__ import annotations

import os
import re
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path
from pathlib import PurePosixPath, PureWindowsPath
from urllib.parse import urlparse

import boto3
import typer
import yaml
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
)

from compman.config import ConfigError, load_config, sanitize_project_name
from compman.docker import detect_runtime


_ARCHIVE_SUFFIXES = (".tar.gz", ".tgz", ".zip")


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
            typer.echo("💡 [compman deploy] Empty directory without compman.yml config file.", err=True)
            typer.echo("", err=True)
            typer.echo("Start by running one of the following commands:", err=True)
            typer.echo("  1️⃣ Deploy directly by providing S3 path:", err=True)
            typer.echo("     compman deploy --path s3://<your-bucket>/path/to/app.tar.gz", err=True)
            typer.echo("  2️⃣ Generate default compman.yml config template:", err=True)
            typer.echo("     compman init", err=True)
            raise SystemExit(1)

    if not s3_path:
        typer.echo("💡 [compman deploy] S3 deployment path is not configured.", err=True)
        typer.echo("  • Specify 'deploy' field in compman.yml, or", err=True)
        typer.echo("  • Pass S3 path via option: compman deploy --path s3://...", err=True)
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


def _generate_scaffold(root: Path, project_subfolder: str, s3_path: str, image: str) -> None:
    compman_yml = root / "compman.yml"
    if not compman_yml.exists():
        content = (
            f"compman:\n"
            f"  name: {sanitize_project_name(root.name)}\n"
            f"  deploy: {s3_path}\n"
            f"  dirs:\n"
            f"    project: {project_subfolder}\n"
            f"  compose:\n"
            f"    - docker-compose.yml\n"
        )
        compman_yml.write_text(content, encoding="utf-8")
        typer.echo("Created compman.yml:")
        typer.echo(f"----------------------------------------\n{content.strip()}\n----------------------------------------")
    else:
        _update_compman_deploy(compman_yml, s3_path)

    deploy_target = root / project_subfolder
    sub_compose = deploy_target / "docker-compose.yml"
    root_compose = root / "docker-compose.yml"

    if sub_compose.exists():
        shutil.move(str(sub_compose), str(root_compose))

    if not root_compose.exists():
        compose_content = (
            f"services:\n"
            f"  app:\n"
            f"    image: {image}\n"
            f"    ports:\n"
            f"      - \"127.0.0.1:18080:18080\"\n"
            f"    restart: unless-stopped\n"
        )
        root_compose.write_text(compose_content, encoding="utf-8")
        typer.echo("Created docker-compose.yml:")
        typer.echo(f"----------------------------------------\n{compose_content.strip()}\n----------------------------------------")


def _update_compman_deploy(compman_yml: Path, s3_path: str) -> None:
    content = compman_yml.read_text(encoding="utf-8-sig")
    try:
        raw = yaml.safe_load(content)
    except Exception:
        raw = None

    if isinstance(raw, dict) and isinstance(raw.get("compman"), dict):
        if raw["compman"].get("deploy") == s3_path:
            return  # Already up to date

    lines = content.splitlines(keepends=True)
    updated = False
    new_lines = []
    in_compman = False
    compman_indent = 0

    for line in lines:
        stripped = line.strip()
        if re.match(r"^compman\s*:", line):
            in_compman = True
            compman_indent = len(line) - len(line.lstrip())
            new_lines.append(line)
            continue

        if in_compman:
            current_indent = len(line) - len(line.lstrip())
            if stripped and not stripped.startswith("#") and current_indent <= compman_indent:
                in_compman = False
            elif re.match(r"^\s*deploy\s*:", line):
                indent = " " * (len(line) - len(line.lstrip()))
                new_lines.append(f"{indent}deploy: {s3_path}\n")
                updated = True
                continue
        new_lines.append(line)

    if not updated:
        final_lines = []
        inserted = False
        in_compman = False
        for line in lines:
            final_lines.append(line)
            if not inserted and re.match(r"^compman\s*:", line):
                in_compman = True
                continue
            if in_compman and not inserted:
                if line.strip() and not line.strip().startswith("#"):
                    indent = " " * (len(line) - len(line.lstrip()))
                    final_lines.append(f"{indent}deploy: {s3_path}\n")
                    inserted = True
                    in_compman = False
        if not inserted:
            final_lines.append(f"  deploy: {s3_path}\n")
        lines = final_lines
    else:
        lines = new_lines

    new_content = "".join(lines)

    try:
        check_raw = yaml.safe_load(new_content)
        if isinstance(check_raw, dict) and check_raw.get("compman", {}).get("deploy") == s3_path:
            compman_yml.write_text(new_content, encoding="utf-8")
            typer.echo(f"Updated deploy in compman.yml ({s3_path}):")
            typer.echo(f"----------------------------------------\n{new_content.strip()}\n----------------------------------------")
            return
    except Exception:
        pass

    if isinstance(raw, dict) and "compman" in raw and isinstance(raw["compman"], dict):
        raw["compman"]["deploy"] = s3_path
        dumped = yaml.safe_dump(raw, sort_keys=False, allow_unicode=True)
        compman_yml.write_text(dumped, encoding="utf-8")
        typer.echo(f"Updated deploy in compman.yml ({s3_path}):")
        typer.echo(f"----------------------------------------\n{dumped.strip()}\n----------------------------------------")


def _fetch(s3, bucket: str, key: str, tmp: Path) -> Path:
    if key.endswith(_ARCHIVE_SUFFIXES):
        archive = tmp / key.rsplit("/", 1)[-1]
        _download(s3, bucket, key, archive)
        extract_dir = tmp / "extract"
        extract_dir.mkdir()
        if key.endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                for member in zf.infolist():
                    _validate_archive_path(extract_dir, member.filename)
                    zf.extract(member, extract_dir)
        else:
            with tarfile.open(archive) as tf:
                for member in tf.getmembers():
                    _validate_archive_path(extract_dir, member.name)
                    if member.issym() or member.islnk():
                        raise ValueError(f"Archive links are not allowed: {member.name}")
                tf.extractall(extract_dir, filter="data")
        contents = [p for p in extract_dir.iterdir() if p.name != ".gitkeep"]
        if len(contents) == 1 and contents[0].is_dir():
            return contents[0]
        return extract_dir

    src = tmp / "src"
    _download_recursive(s3, bucket, key, src)
    return src


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


def _validate_archive_path(root: Path, name: str) -> None:
    if not name or PurePosixPath(name).is_absolute() or PureWindowsPath(name).is_absolute():
        raise ValueError(f"Unsafe archive path: {name}")
    target = (root / name).resolve()
    if target != root.resolve() and root.resolve() not in target.parents:
        raise ValueError(f"Unsafe archive path: {name}")


def _handle_s3_error(e: Exception, s3_path: str) -> None:
    typer.echo(f"💡 [compman deploy] Failed to download from {s3_path}", err=True)
    typer.echo("", err=True)

    if isinstance(e, (NoCredentialsError, PartialCredentialsError)):
        typer.echo("Error: AWS credentials were not found or are incomplete.", err=True)
        typer.echo("", err=True)
        typer.echo("Guide - Please set your AWS credentials using environment variables:", err=True)
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
            typer.echo(f"Error 403 (Access Denied): Access to '{s3_path}' was forbidden.", err=True)
            typer.echo("", err=True)
            typer.echo("Guide - Troubleshooting 403 Forbidden:", err=True)
            typer.echo("  1️⃣ Ensure AWS credentials have 's3:GetObject' and 's3:ListBucket' permissions.", err=True)
            typer.echo("  2️⃣ Verify S3 bucket name and key path are correct.", err=True)
            typer.echo("  3️⃣ If using local S3 (e.g. ministack), check AWS_ENDPOINT_URL_S3 or AWS_ENDPOINT_URL.", err=True)
        elif err_code in ("404", "NoSuchBucket", "NoSuchKey", "NotFound"):
            typer.echo(f"Error 404 (Not Found): Bucket or file does not exist: '{s3_path}'", err=True)
            typer.echo("", err=True)
            typer.echo("Guide - Troubleshooting 404 Not Found:", err=True)
            typer.echo("  1️⃣ Verify bucket name and file/archive path on S3.", err=True)
            typer.echo("  2️⃣ Check for typos in s3://bucket/path", err=True)
        else:
            typer.echo(f"S3 Client Error ({err_code}): {err_msg}", err=True)

    elif isinstance(e, EndpointConnectionError):
        typer.echo(f"Network Error: Unable to connect to S3 endpoint.", err=True)
        typer.echo("", err=True)
        typer.echo("Guide - Troubleshooting connection error:", err=True)
        typer.echo("  1️⃣ Check internet connection.", err=True)
        typer.echo("  2️⃣ If using local S3 (e.g. ministack), check AWS_ENDPOINT_URL_S3 or AWS_ENDPOINT_URL.", err=True)

    else:
        typer.echo(f"Download Error: {e}", err=True)

    raise SystemExit(1)


def _download(s3, bucket: str, key: str, dst: Path) -> None:
    s3.download_file(bucket, key, str(dst))


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
