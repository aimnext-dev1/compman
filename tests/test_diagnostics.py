from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from compman.diagnostics import collect_doctor


def write_simple_project(path: Path) -> None:
    (path / "compman.yml").write_text(
        "compman:\n"
        "  name: test-app\n"
        "  compose:\n"
        "    - docker-compose.yml\n",
        encoding="utf-8",
    )
    (path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")


def test_collect_doctor_success(tmp_path, monkeypatch, dummy_runtime):
    write_simple_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)

    report = collect_doctor(None)

    assert report.ok is True
    assert [check.id for check in report.checks[:3]] == ["config", "compose_files", "runtime"]
    assert report.to_dict()["schema_version"] == 1


def test_warning_does_not_fail_doctor(tmp_path, monkeypatch, dummy_runtime):
    write_simple_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)

    report = collect_doctor(None)

    assert report.ok is True
    assert next(check for check in report.checks if check.id == "aws").severity == "warning"


@pytest.mark.parametrize("config_contents", [None, "invalid: : ["])
def test_invalid_or_missing_config_is_a_failed_required_check(tmp_path, monkeypatch, dummy_runtime, config_contents):
    if config_contents is not None:
        (tmp_path / "compman.yml").write_text(config_contents, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)

    report = collect_doctor(None)

    config = next(check for check in report.checks if check.id == "config")
    assert config.severity == "required"
    assert config.ok is False
    assert report.ok is False


def test_missing_compose_file_is_a_failed_required_check(tmp_path, monkeypatch, dummy_runtime):
    (tmp_path / "compman.yml").write_text(
        "compman:\n  compose:\n    - docker-compose.yml\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)

    report = collect_doctor(None)

    compose = next(check for check in report.checks if check.id == "compose_files")
    assert compose.severity == "required"
    assert compose.ok is False
    assert report.ok is False


def test_runtime_detection_exception_is_a_failed_required_check(tmp_path, monkeypatch):
    write_simple_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: (_ for _ in ()).throw(RuntimeError("missing")))

    report = collect_doctor(None)

    runtime = next(check for check in report.checks if check.id == "runtime")
    assert runtime.severity == "required"
    assert runtime.ok is False
    assert report.ok is False


def test_nonzero_runtime_info_is_a_failed_required_check(tmp_path, monkeypatch, dummy_runtime):
    write_simple_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)
    monkeypatch.setattr(dummy_runtime, "run_cli", lambda *args, **kwargs: SimpleNamespace(returncode=1))

    report = collect_doctor(None)

    connection = next(check for check in report.checks if check.id == "runtime_connection")
    assert connection.severity == "required"
    assert connection.ok is False
    assert report.ok is False


def test_unwritable_managed_directory_parent_is_a_failed_required_check(tmp_path, monkeypatch, dummy_runtime):
    write_simple_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)
    monkeypatch.setattr("compman.diagnostics.os.access", lambda *args: False)

    report = collect_doctor(None)

    managed_dirs = next(check for check in report.checks if check.id == "managed_dirs")
    assert managed_dirs.severity == "required"
    assert managed_dirs.ok is False
    assert report.ok is False


def test_runtime_info_exception_is_a_failed_required_check(tmp_path, monkeypatch, dummy_runtime):
    write_simple_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)
    monkeypatch.setattr(dummy_runtime, "run_cli", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline")))

    report = collect_doctor(None)

    connection = next(check for check in report.checks if check.id == "runtime_connection")
    assert connection.ok is False
    assert report.ok is False


def test_managed_directory_access_exception_is_a_failed_required_check(tmp_path, monkeypatch, dummy_runtime):
    write_simple_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)
    monkeypatch.setattr("compman.diagnostics.os.access", lambda *args: (_ for _ in ()).throw(OSError("denied")))

    report = collect_doctor(None)

    managed_dirs = next(check for check in report.checks if check.id == "managed_dirs")
    assert managed_dirs.ok is False
    assert report.ok is False


def test_aws_credentials_are_reported_as_available(tmp_path, monkeypatch, dummy_runtime):
    write_simple_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("compman.diagnostics.detect_runtime", lambda: dummy_runtime)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    report = collect_doctor(None)

    aws = next(check for check in report.checks if check.id == "aws")
    assert aws.severity == "warning"
    assert aws.ok is True
