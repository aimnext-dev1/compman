# Windows Error Output Design

## Problem

On Windows, a failed Docker command is reported correctly but is followed by an
uncaught Click `Exit` traceback. Unicode prompt decorations can also render as
mojibake in terminals whose active code page is not UTF-8.

## Scope

- Preserve the Docker error text and exit status `1`.
- Stop after the concise translated `Error:` message without a Python traceback.
- Render the interactive selection prompt with ASCII-only navigation text.
- On Windows, start Docker Desktop when an execution or build command needs the
  Docker daemon and the daemon is not ready.
- Do not change console encoding.

## Design

`HelpOnUnknownCommandGroup.main` remains the single boundary for expected
application failures. When it catches `CommandError`, `ConfigError`, or
`RuntimeError`, it prints the current user-facing error and terminates with
`SystemExit` instead of raising Click's internal `Exit` exception outside
Click's own exception-handling boundary.

`prompt_select` keeps its keyboard behavior and visual selection marker, but
its heading uses portable ASCII wording: `Use Up/Down, Enter to select, Esc to
cancel`. No terminal capability detection or process-wide encoding mutation is
introduced.

The container runtime exposes one readiness operation used only by paths that
start, recreate, or build containers: `stack up`, `update`, and deploy-time
builds. It first probes the Docker daemon. On Windows, if Docker is selected and
the probe fails, it locates and launches Docker Desktop, then polls daemon
readiness for up to 60 seconds before continuing the original operation once.
The launch is hidden and does not open an extra console window.

Read-only commands, diagnostics, backup/restore operations, and `stack down` do
not start Docker Desktop. An explicit `CONTAINER_RUNTIME=podman` selection never
starts Docker Desktop. Linux and macOS behavior remains unchanged.

## Error Behavior

Expected operational failures return their existing non-zero status and produce
no traceback. Unexpected programming errors are not caught and continue to show
normal diagnostic tracebacks.

If Docker Desktop is unavailable, cannot be launched, or does not become ready
within 60 seconds, compman exits with status `1` and a concise actionable error.
It does not retry the requested compose operation after that failure.

## Testing

- Add a CLI regression test that raises a runtime failure through the real group
  entry boundary and asserts exit status `1`, concise error output, and absence
  of `Traceback`.
- Update prompt tests to assert that the heading is ASCII-only while preserving
  arrow-key, Enter, Escape, and non-TTY behavior.
- Add runtime tests for an already-ready daemon, successful Windows Docker
  Desktop startup, missing Docker Desktop, startup timeout, explicit Podman,
  and excluded command paths.
- Add command tests proving startup is requested only for `stack up`, `update`,
  and deploy-time builds, and that the original command runs exactly once.
- Run the full pytest suite with statement and branch coverage, Ruff, and mypy.

## Non-goals

- Detecting whether a terminal supports Unicode.
- Enabling UTF-8 globally on Windows.
- Replacing Typer/Click or changing Docker runtime detection.
- Automatically starting Docker Desktop for read-only, backup, restore, or stop
  operations.
