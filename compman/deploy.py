from __future__ import annotations

import os
import re
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import boto3
import click
import yaml

from compman.config import ConfigError, load_config
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
            click.echo("💡 [compman deploy] compman.yml 설정 파일이 없는 빈 디렉터리입니다.", err=True)
            click.echo("", err=True)
            click.echo("다음 중 하나로 첫 배포 또는 설정을 시작해보세요:", err=True)
            click.echo("  1️⃣ S3 경로를 직접 지정하여 첫 배포:", err=True)
            click.echo("     compman deploy --path s3://<your-bucket>/path/to/app.tar.gz", err=True)
            click.echo("  2️⃣ 기본 compman.yml 설정 템플릿 생성:", err=True)
            click.echo("     compman init", err=True)
            raise SystemExit(1)

    if not s3_path:
        click.echo("💡 [compman deploy] S3 배포 경로가 지정되지 않았습니다.", err=True)
        click.echo("  • compman.yml 파일의 'deploy' 속성을 지정하거나,", err=True)
        click.echo("  • compman deploy --path s3://... 옵션으로 S3 경로를 전달해주세요.", err=True)
        raise SystemExit(1)

    project_subfolder = config.dirs.get("project", "project") if config else "project"

    endpoint = os.environ.get("COMPMAN_S3_ENDPOINT")

    root = Path.cwd()
    deploy_target = root / project_subfolder
    deploy_target.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix=".deploy_tmp_", dir=root))

    parsed = urlparse(s3_path)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")

    s3 = boto3.client("s3", endpoint_url=endpoint or None)

    try:
        project_root = _fetch(s3, bucket, key, tmp)
        _swap(project_root, deploy_target)
        image = tag or root.name.lower()
        _generate_scaffold(root, project_subfolder, s3_path, image)
        if build:
            click.echo(f"Building image '{image}' in {project_subfolder}...")
            detect_runtime().passthru_cli(["build", "-t", image, "."], cwd=deploy_target)
        click.echo("Deploy done.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _generate_scaffold(root: Path, project_subfolder: str, s3_path: str, image: str) -> None:
    compman_yml = root / "compman.yml"
    if not compman_yml.exists():
        compman_yml.write_text(
            f"compman:\n"
            f"  name: {root.name}\n"
            f"  deploy: {s3_path}\n"
            f"  dirs:\n"
            f"    project: {project_subfolder}\n"
            f"  compose:\n"
            f"    - docker-compose.yml\n",
            encoding="utf-8",
        )
        click.echo("Created compman.yml")
    else:
        _update_compman_deploy(compman_yml, s3_path)

    deploy_target = root / project_subfolder
    sub_compose = deploy_target / "docker-compose.yml"
    root_compose = root / "docker-compose.yml"

    if sub_compose.exists():
        shutil.move(str(sub_compose), str(root_compose))

    if not root_compose.exists():
        root_compose.write_text(
            f"services:\n"
            f"  app:\n"
            f"    image: {image}\n"
            f"    ports:\n"
            f"      - \"18080:18080\"\n"
            f"    restart: unless-stopped\n",
            encoding="utf-8",
        )
        click.echo("Created docker-compose.yml")


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
            click.echo(f"Updated deploy in compman.yml ({s3_path})")
            return
    except Exception:
        pass

    if isinstance(raw, dict) and "compman" in raw and isinstance(raw["compman"], dict):
        raw["compman"]["deploy"] = s3_path
        compman_yml.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
        click.echo(f"Updated deploy in compman.yml ({s3_path})")


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
    if root.exists():
        for item in list(root.iterdir()):
            if item.name in (".git", ".gitkeep"):
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            elif item.exists():
                item.unlink()
    else:
        root.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if item.name == ".gitkeep":
            continue
        dest = root / item.name
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
