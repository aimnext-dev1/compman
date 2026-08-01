from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from compman.archive_source import ARCHIVE_SUFFIXES, extract_archive, has_archive_suffix


def fetch(url: str, tmp: Path) -> Path:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid HTTP source: {url}")
    if not has_archive_suffix(parsed.path):
        raise ValueError(f"HTTP source must be a .tar.gz, .tgz, or .zip archive: {url}")

    lower_path = parsed.path.lower()
    suffix = next(suffix for suffix in ARCHIVE_SUFFIXES if lower_path.endswith(suffix))
    archive_path = tmp / f"source{suffix}"
    with urlopen(url, timeout=30) as response, archive_path.open("wb") as destination:
        shutil.copyfileobj(response, destination)

    return extract_archive(archive_path, tmp / "extract")
