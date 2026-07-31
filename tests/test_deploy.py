from __future__ import annotations

import pathlib
import tarfile
import zipfile
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
)

from compman import deploy


def test_deploy_no_s3_path(temp_dir: pathlib.Path):
    with pytest.raises(SystemExit):
        deploy.deploy(s3_path=None)


def test_deploy_invalid_s3_path(temp_dir: pathlib.Path):
    with pytest.raises(SystemExit):
        deploy.deploy(s3_path="https://bucket/key")


def test_deploy_empty_dir_help_exit(temp_dir: pathlib.Path):
    with pytest.raises(SystemExit):
        deploy.deploy(s3_path=None)


def test_deploy_existing_config_s3(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "compman.yml").write_text("compman:\n  name: app\n  deploy: s3://b/k.tar.gz\n", encoding="utf-8")
    mock_s3 = MagicMock()
    tar_path = temp_dir / "k.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        pass
    mock_s3.download_file.side_effect = lambda b, k, dst: pathlib.Path(dst).write_bytes(tar_path.read_bytes())

    with patch("boto3.client", return_value=mock_s3), patch("compman.deploy.detect_runtime", return_value=dummy_runtime):
        deploy.deploy(build=True, tag="my_tag", s3_path=None)
        assert (temp_dir / "compman.yml").exists()


def test_deploy_zip_archive(dummy_runtime, temp_dir: pathlib.Path):
    mock_s3 = MagicMock()
    zip_path = temp_dir / "app.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test.txt", "hello")
    mock_s3.download_file.side_effect = lambda b, k, dst: pathlib.Path(dst).write_bytes(zip_path.read_bytes())

    with patch("boto3.client", return_value=mock_s3), patch("compman.deploy.detect_runtime", return_value=dummy_runtime):
        deploy.deploy(build=False, tag=None, s3_path="s3://my-bucket/app.zip")
        assert (temp_dir / "project" / "test.txt").exists()


def test_deploy_rejects_zip_path_traversal(temp_dir: pathlib.Path):
    zip_path = temp_dir / "unsafe.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../outside.txt", "unsafe")

    mock_s3 = MagicMock()
    mock_s3.download_file.side_effect = lambda b, k, dst: pathlib.Path(dst).write_bytes(zip_path.read_bytes())
    (temp_dir / "tmp").mkdir()
    with patch("boto3.client", return_value=mock_s3):
        with pytest.raises(ValueError, match="Unsafe archive path"):
            deploy._fetch(mock_s3, "bucket", "unsafe.zip", temp_dir / "tmp")

    assert not (temp_dir / "outside.txt").exists()


def test_deploy_rejects_tar_path_traversal(temp_dir: pathlib.Path):
    tar_path = temp_dir / "unsafe.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        info = tarfile.TarInfo("../outside.txt")
        info.size = len(b"unsafe")
        import io
        tar.addfile(info, io.BytesIO(b"unsafe"))

    mock_s3 = MagicMock()
    mock_s3.download_file.side_effect = lambda b, k, dst: pathlib.Path(dst).write_bytes(tar_path.read_bytes())
    (temp_dir / "tmp").mkdir()
    with pytest.raises(ValueError, match="Unsafe archive path"):
        deploy._fetch(mock_s3, "bucket", "unsafe.tar.gz", temp_dir / "tmp")

    assert not (temp_dir / "outside.txt").exists()


def test_deploy_targz_single_dir(dummy_runtime, temp_dir: pathlib.Path):
    mock_s3 = MagicMock()
    src_dir = temp_dir / "src_inner"
    src_dir.mkdir()
    (src_dir / "inner.txt").write_text("inner", encoding="utf-8")

    tar_path = temp_dir / "app.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(src_dir, arcname="src_inner")

    mock_s3.download_file.side_effect = lambda b, k, dst: pathlib.Path(dst).write_bytes(tar_path.read_bytes())

    with patch("boto3.client", return_value=mock_s3), patch("compman.deploy.detect_runtime", return_value=dummy_runtime):
        deploy.deploy(build=False, tag=None, s3_path="s3://my-bucket/app.tar.gz")
        assert (temp_dir / "project" / "inner.txt").exists()


def test_update_compman_deploy(temp_dir: pathlib.Path):
    compman_yml = temp_dir / "compman.yml"
    compman_yml.write_text("compman:\n  name: app\n  deploy: s3://old/path\n", encoding="utf-8")

    deploy._update_compman_deploy(compman_yml, "s3://new/path")
    assert "s3://new/path" in compman_yml.read_text(encoding="utf-8")

    # Already matching
    deploy._update_compman_deploy(compman_yml, "s3://new/path")

    # Invalid yaml fallback
    compman_yml.write_text("compman:\n  name: app\n", encoding="utf-8")
    deploy._update_compman_deploy(compman_yml, "s3://new2/path")
    assert "s3://new2/path" in compman_yml.read_text(encoding="utf-8")


def test_deploy_prefix_download(dummy_runtime, temp_dir: pathlib.Path):
    mock_s3 = MagicMock()
    mock_s3.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": "my-prefix/file1.txt"}, {"Key": "my-prefix/sub/file2.txt"}]}
    ]
    def download(_bucket, key, destination):
        pathlib.Path(destination).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(destination).write_text(key, encoding="utf-8")

    mock_s3.download_file = MagicMock(side_effect=download)

    with patch("boto3.client", return_value=mock_s3), patch("compman.deploy.detect_runtime", return_value=dummy_runtime):
        deploy.deploy(s3_path="s3://my-bucket/my-prefix")
        assert (temp_dir / "project" / "file1.txt").exists()


def test_deploy_prefix_rejects_path_traversal(temp_dir: pathlib.Path):
    mock_s3 = MagicMock()
    mock_s3.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": "my-prefix/../outside.txt"}]}
    ]
    with pytest.raises(ValueError, match="Unsafe S3 object path"):
        deploy._download_recursive(mock_s3, "bucket", "my-prefix", temp_dir / "project")


def test_deploy_swap_existing(dummy_runtime, temp_dir: pathlib.Path):
    (temp_dir / "project").mkdir(exist_ok=True)
    (temp_dir / "project" / "old_file.txt").write_text("old", encoding="utf-8")

    mock_s3 = MagicMock()
    src_dir = temp_dir / "_src_inner"
    src_dir.mkdir()
    (src_dir / "new_file.txt").write_text("new", encoding="utf-8")

    tar_path = temp_dir / "app.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(src_dir, arcname="_src_inner")

    mock_s3.download_file.side_effect = lambda b, k, dst: pathlib.Path(dst).write_bytes(tar_path.read_bytes())

    with patch("boto3.client", return_value=mock_s3), patch("compman.deploy.detect_runtime", return_value=dummy_runtime):
        deploy.deploy(s3_path="s3://my-bucket/app.tar.gz")
        assert (temp_dir / "project" / "new_file.txt").exists()


def test_generate_scaffold_sub_compose(dummy_runtime, temp_dir: pathlib.Path):
    project_dir = temp_dir / "project"
    project_dir.mkdir()
    sub_compose = project_dir / "docker-compose.yml"
    sub_compose.write_text("services:\n  app:\n    image: old\n", encoding="utf-8")

    deploy._generate_scaffold(temp_dir, "project", "s3://b/k", "my_image")
    assert not sub_compose.exists()
    root_compose = temp_dir / "docker-compose.yml"
    assert root_compose.exists()


def test_update_compman_deploy_fallback_insert(temp_dir: pathlib.Path):
    compman_yml = temp_dir / "compman.yml"
    compman_yml.write_text("compman:\n  name: app\n", encoding="utf-8")

    deploy._update_compman_deploy(compman_yml, "s3://new3/path")
    assert "s3://new3/path" in compman_yml.read_text(encoding="utf-8")


def test_handle_s3_errors():
    with pytest.raises(SystemExit):
        deploy._handle_s3_error(NoCredentialsError(), "s3://b/k")

    with pytest.raises(SystemExit):
        deploy._handle_s3_error(PartialCredentialsError(provider="env", cred_var="AWS_SECRET_ACCESS_KEY"), "s3://b/k")

    with pytest.raises(SystemExit):
        deploy._handle_s3_error(ClientError({"Error": {"Code": "403"}}, "GetObject"), "s3://b/k")

    with pytest.raises(SystemExit):
        deploy._handle_s3_error(ClientError({"Error": {"Code": "404"}}, "GetObject"), "s3://b/k")

    with pytest.raises(SystemExit):
        deploy._handle_s3_error(ClientError({"Error": {"Code": "500"}}, "GetObject"), "s3://b/k")

    with pytest.raises(SystemExit):
        deploy._handle_s3_error(EndpointConnectionError(endpoint_url="http://localhost"), "s3://b/k")

    with pytest.raises(SystemExit):
        deploy._handle_s3_error(RuntimeError("generic error"), "s3://b/k")
