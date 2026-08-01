from __future__ import annotations

from pathlib import Path

from compman.archive_source import extract_archive, has_archive_suffix


def fetch(s3, bucket: str, key: str, tmp: Path) -> Path:
    if has_archive_suffix(key):
        archive_path = tmp / key.rsplit("/", 1)[-1]
        download(s3, bucket, key, archive_path)
        return extract_archive(archive_path, tmp / "extract")

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
