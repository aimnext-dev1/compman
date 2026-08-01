# Windows Error Output Design

## Problem

On Windows, a failed Docker command is reported correctly but is followed by an
uncaught Click `Exit` traceback. Unicode prompt decorations can also render as
mojibake in terminals whose active code page is not UTF-8.

## Scope

- Preserve the Docker error text and exit status `1`.
- Stop after the concise translated `Error:` message without a Python traceback.
- Render the interactive selection prompt with ASCII-only navigation text.
- Do not start Docker Desktop, retry Docker commands, or change console encoding.

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

## Error Behavior

Expected operational failures return their existing non-zero status and produce
no traceback. Unexpected programming errors are not caught and continue to show
normal diagnostic tracebacks.

## Testing

- Add a CLI regression test that raises a runtime failure through the real group
  entry boundary and asserts exit status `1`, concise error output, and absence
  of `Traceback`.
- Update prompt tests to assert that the heading is ASCII-only while preserving
  arrow-key, Enter, Escape, and non-TTY behavior.
- Run the full pytest suite with statement and branch coverage, Ruff, and mypy.

## Non-goals

- Detecting whether a terminal supports Unicode.
- Enabling UTF-8 globally on Windows.
- Replacing Typer/Click or changing Docker runtime detection.
