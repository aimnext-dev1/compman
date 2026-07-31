from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import click


S3_PATHS = {
    "dev": "",  # TODO: fill dev S3 path
    "prod": "",  # TODO: fill prod S3 path
}


def deploy(env: str) -> None:
    s3_path = S3_PATHS.get(env)
    if not s3_path:
        click.echo(f"S3 path not configured for environment '{env}'.", err=True)
        click.echo("Edit S3_PATHS in compman/deploy.py")
        raise SystemExit(1)

    root = Path.cwd()
    tmp = Path(tempfile.mkdtemp(prefix=".deploy_tmp_", dir=root))

    try:
        _aws_cp(f"{s3_path}/Makefile", str(tmp / "Makefile"))
        _aws_cp_recursive(f"{s3_path}/_script", str(tmp / "_script"))
        _aws_cp_recursive(f"{s3_path}/_project/compose", str(tmp / "_project_compose"))

        # atomic swap
        shutil.move(str(tmp / "Makefile"), str(root / "Makefile"))
        shutil.rmtree(str(root / "_script"), ignore_errors=True)
        shutil.move(str(tmp / "_script"), str(root / "_script"))
        shutil.rmtree(str(root / "_project" / "compose"), ignore_errors=True)
        (root / "_project" / "compose").mkdir(parents=True, exist_ok=True)
        for item in (tmp / "_project_compose").iterdir():
            shutil.move(str(item), str(root / "_project" / "compose" / item.name))

        click.echo("Deploy done.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _aws_cp(src: str, dst: str) -> None:
    r = subprocess.run(["aws", "s3", "cp", src, dst], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"aws s3 cp failed:\n{r.stderr}")


def _aws_cp_recursive(src: str, dst: str) -> None:
    r = subprocess.run(
        ["aws", "s3", "cp", "--recursive", src, dst],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"aws s3 cp --recursive failed:\n{r.stderr}")
