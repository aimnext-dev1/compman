# CLI Startup and Release Notes Design

Created: 2026-08-01

## Goal

Make `compman` help startup avoid loading command-only Docker, S3, diagnostics,
and operations modules. Keep self-upgrades usable after a system Python is
removed, and establish a durable release-note file.

## Design

- Keep the existing Typer command tree and output unchanged.
- Move business-module imports from `compman.cli` module scope into the command
  handlers that use them. Help and version paths retain only Typer, i18n, and
  standard-library imports.
- Make uv upgrades require an uv-managed Python. Preserve the pip fallback when
  uv is unavailable.
- Add `CHANGELOG.md` and require every package version change to update it.
- Release this backward-compatible fix as 1.1.3.

## Verification

- A fresh-process import test proves command-only modules are absent after
  importing `compman.cli`.
- Upgrade command tests prove the managed-Python option is passed.
- Existing unit, coverage, lint, type, wheel, and generated-executable smoke
  gates remain mandatory.

