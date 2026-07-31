from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath


def extract_tar(archive: tarfile.TarFile, destination: Path) -> None:
    members = archive.getmembers()
    for member in members:
        _validate_path(destination, member.name)
        if member.issym() or member.islnk():
            raise ValueError(f"Archive links are not allowed: {member.name}")
    for member in members:
        if sys.version_info >= (3, 12):
            archive.extract(member, destination, filter="data")
        else:  # Python 3.10/3.11: paths and links already validated above.
            archive.extract(member, destination)


def extract_zip(archive: zipfile.ZipFile, destination: Path) -> None:
    for member in archive.infolist():
        _validate_path(destination, member.filename)
        archive.extract(member, destination)


def _validate_path(destination: Path, name: str) -> None:
    if not name or PurePosixPath(name).is_absolute() or PureWindowsPath(name).is_absolute():
        raise ValueError(f"Unsafe archive path: {name}")
    root = destination.resolve()
    target = (destination / name).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"Unsafe archive path: {name}")
