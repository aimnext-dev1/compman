# Safe Self-Upgrade Design

## Problem

On a Korean Windows code page, `compman upgrade` decodes uv's UTF-8 output as
CP949. The subprocess reader thread can fail with `UnicodeDecodeError` while the
command still reports success. The current fallback can also mutate the active
uv tool environment through its own interpreter, leaving the launcher unable to
find `pyvenv.cfg`.

## Scope

- Use uv's supported tool-upgrade command for normal uv tool installations.
- Decode captured subprocess output as UTF-8 with replacement for malformed
  bytes.
- Never report success unless an upgrade command completes with exit status 0.
- Do not run `uv pip install --python sys.executable` against the active tool
  environment.
- Preserve a pip fallback only when uv itself is unavailable.
- Release the correction as version `1.1.1`.

## Design

The default upgrade path runs `uv tool upgrade compman --reinstall`. This keeps
the tool's recorded source and installation settings while using uv's supported
upgrade workflow instead of recreating the active environment with `tool
install --reinstall`.

All upgrade subprocess calls use `capture_output=True`, `text=True`,
`encoding="utf-8"`, and `errors="replace"`. A shared small runner keeps these
arguments consistent and returns the completed process without interpreting a
reader-thread failure as success.

If uv is not found, compman runs `sys.executable -m pip install --upgrade
git+<repo>`. If uv exists but `uv tool upgrade` fails, compman reports uv's
stderr/stdout and exits with status 1; it does not attempt to modify the active
environment through uv pip.

The existing `--repo` option remains meaningful for the pip fallback and manual
recovery message. The uv tool upgrade path intentionally uses the source stored
by uv. Custom source replacement remains an explicit external reinstall action,
not an in-process self-upgrade.

## Error Behavior

- Exit 0 and print success only after a zero-return-code subprocess.
- Exit 1 with decoded diagnostic output when uv or pip fails.
- Convert missing executable errors into the pip fallback only when uv cannot
  be launched.
- Replacement decoding prevents invalid output bytes from escaping as a Python
  traceback.

## Testing

- Verify the exact default uv command and UTF-8 subprocess arguments.
- Simulate non-UTF-8 bytes and confirm replacement decoding without traceback.
- Verify uv failure exits 1 and never invokes uv pip.
- Verify missing uv invokes the pip fallback with the selected repository.
- Verify pip success and failure reporting.
- Run the full suite with 100% statement and branch coverage, Ruff, and mypy.

## Recovery Documentation

Document recovery for an already damaged installation:

Keep the recovery source unpinned so uv stores a movable Git source and future
`uv tool upgrade` commands can advance to newer releases.

```powershell
uv tool uninstall compman
uv tool install git+https://github.com/allbegray/compman.git
compman --version
```
