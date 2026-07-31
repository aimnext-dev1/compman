# Doctor and Status Commands

## Scope

Add two read-only top-level commands without changing existing command behavior:

- `compman doctor [--json]` validates the local compman environment.
- `compman status [--profile PROFILE] [--config PATH] [--json]` summarizes the selected stack and its services.

Port probing, live S3 requests, health waiting, backup reporting, and corrective actions are excluded.

## Command behavior

`doctor` reports checks for configuration loading, resolved Compose file existence, container runtime detection, runtime connectivity, managed-directory writability, and optional AWS environment configuration. A required check failure produces exit code 1. Missing optional AWS settings produce warnings and do not affect the exit code.

`status` reports the runtime, stack name, selected profile, resolved Compose files, and service/container state. A missing stack or failed status query produces exit code 1.

Human output uses concise success, warning, and failure markers. With `--json`, stdout contains exactly one JSON document; diagnostics belong in that document rather than mixed terminal output.

## Design

A new diagnostics module owns structured result collection. It has no Typer output calls. Small dataclasses represent individual checks and the two command reports. CLI handlers only load inputs, select text or JSON rendering, print the result, and map report success to an exit code.

Existing `Config`, Compose resolution, and `ContainerRuntime` APIs remain the source of truth. Runtime connectivity uses a bounded read-only runtime command. Service status uses machine-readable runtime output when available instead of parsing the current human-oriented `service status` output.

The JSON contract is versioned at the document root with `schema_version: 1`. Check entries include stable identifiers, severity, success state, and a human-readable message. Status service entries use stable fields for name, container, state, status, and health when available.

## Error handling

Expected configuration and runtime failures become structured failed checks. Unexpected programming errors continue through the existing CLI error boundary. JSON mode must not leak progress text to stdout.

Warnings never make `doctor` fail. `doctor` exits 1 when at least one required check fails. `status` exits 1 when configuration/runtime loading fails, the stack is absent, or service status cannot be obtained.

## Testing

Development follows test-first red-green-refactor cycles. Tests cover text and JSON output, schema stability, exit codes, warning semantics, simple and profile Compose resolution, missing files, runtime detection/connectivity failures, absent stacks, and representative service states.

All existing tests must remain green. Ruff, mypy, and 100% statement/branch coverage remain required. Real Docker integration verification exercises successful `doctor`, text `status`, and JSON parsing against the repository test stack.
