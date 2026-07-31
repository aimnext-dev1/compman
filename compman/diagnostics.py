from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from compman.config import Config, load_config
from compman.docker import ContainerRuntime, detect_runtime, resolve_compose_context


@dataclass(frozen=True)
class CheckResult:
    id: str
    severity: Literal["required", "warning"]
    ok: bool
    message: str

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "severity": self.severity, "ok": self.ok, "message": self.message}


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[CheckResult, ...]

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks if check.severity == "required")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "ok": self.ok,
            "checks": [check.to_dict() for check in self.checks],
        }


def collect_doctor(config_path: str | None, profile: str | None = None) -> DoctorReport:
    checks: list[CheckResult] = []
    config = _collect_config(config_path, checks)
    if config is not None:
        _collect_compose_files(config, profile, checks)
    runtime = _collect_runtime(checks)
    if runtime is not None:
        _collect_runtime_connection(runtime, checks)
    if config is not None:
        _collect_managed_dirs(config, checks)
    _collect_aws(checks)
    return DoctorReport(tuple(checks))


def _collect_config(config_path: str | None, checks: list[CheckResult]) -> Config | None:
    try:
        config = load_config(config_path)
    except Exception as exc:
        checks.append(CheckResult("config", "required", False, str(exc)))
        return None
    checks.append(CheckResult("config", "required", True, f"Loaded configuration for {config.name}."))
    return config


def _collect_compose_files(config: Config, profile: str | None, checks: list[CheckResult]) -> None:
    try:
        context = resolve_compose_context(config, profile)
    except Exception as exc:
        checks.append(CheckResult("compose_files", "required", False, str(exc)))
        return
    checks.append(
        CheckResult(
            "compose_files",
            "required",
            True,
            f"Resolved {len(context.files)} Compose file(s).",
        )
    )


def _collect_runtime(checks: list[CheckResult]) -> ContainerRuntime | None:
    try:
        runtime = detect_runtime()
    except Exception as exc:
        checks.append(CheckResult("runtime", "required", False, str(exc)))
        return None
    checks.append(CheckResult("runtime", "required", True, f"Detected {runtime.name} runtime."))
    return runtime


def _collect_runtime_connection(runtime: ContainerRuntime, checks: list[CheckResult]) -> None:
    try:
        result = runtime.run_cli(["info"], check=False)
    except Exception as exc:
        checks.append(CheckResult("runtime_connection", "required", False, str(exc)))
        return
    if result.returncode != 0:
        checks.append(
            CheckResult("runtime_connection", "required", False, f"Runtime info failed (exit={result.returncode}).")
        )
        return
    checks.append(CheckResult("runtime_connection", "required", True, "Runtime connection succeeded."))


def _collect_managed_dirs(config: Config, checks: list[CheckResult]) -> None:
    try:
        directories = (config.backup_dir, config.volume_dir, config.deploy_dir)
        unwritable = [directory.parent for directory in directories if not os.access(directory.parent, os.W_OK)]
    except Exception as exc:
        checks.append(CheckResult("managed_dirs", "required", False, str(exc)))
        return
    if unwritable:
        checks.append(
            CheckResult("managed_dirs", "required", False, f"Managed directory parent is not writable: {unwritable[0]}")
        )
        return
    checks.append(CheckResult("managed_dirs", "required", True, "Managed directory parents are writable."))


def _collect_aws(checks: list[CheckResult]) -> None:
    credentials_present = bool(os.environ.get("AWS_ACCESS_KEY_ID")) and bool(
        os.environ.get("AWS_SECRET_ACCESS_KEY")
    )
    message = "AWS credentials are available." if credentials_present else "AWS credentials are not configured."
    checks.append(CheckResult("aws", "warning", credentials_present, message))
