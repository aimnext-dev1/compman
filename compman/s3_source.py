from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from compman.archive import extract_tar, extract_zip

ARCHIVE_SUFFIXES = (".tar.gz", ".tgz", ".zip")


def fetch(s3, bucket: str, key: str, tmp: Path) -> Path:
    if key.endswith(ARCHIVE_SUFFIXES):
        archive_path = tmp / key.rsplit("/", 1)[-1]
        download(s3, bucket, key, archive_path)
        extract_dir = tmp / "extract"
        extract_dir.mkdir()
        if key.endswith(".zip"):
            with zipfile.ZipFile(archive_path) as zip_source:
                extract_zip(zip_source, extract_dir)
        else:
            with tarfile.open(archive_path) as tar_source:
                extract_tar(tar_source, extract_dir)
        contents = [p for p in extract_dir.iterdir() if p.name != ".gitkeep"]
        return contents[0] if len(contents) == 1 and contents[0].is_dir() else extract_dir

    source_dir = tmp / "src"
    download_recursive(s3, bucket, key, source_dir)
    return source_dir


def download(s3, bucket: str, key: str, destination: Path) -> None:
    s3.download_file(bucket, key, str(destination))


def download_recursive(s3, bucket: str, key_prefix: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    paginator = s3.get_paginator("list_objects_v2")
    prefix = f"{key_prefix}/" if key_prefix else ""
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            relative = key[len(key_prefix) :].lstrip("/")
            target = destination / relative
            if destination.resolve() not in target.resolve().parents:
                raise ValueError(f"Unsafe S3 object path: {key}")
            target.parent.mkdir(parents=True, exist_ok=True)
            download(s3, bucket, key, target)
