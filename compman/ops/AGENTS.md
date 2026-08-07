# compman/ops — Business Logic Layer

**Generated:** 2026-08-07 · **Commit:** e8ccb76 · **Branch:** main

## OVERVIEW
Per-domain business logic behind CLI commands. `cli.py` holds thin typer signatures; every command dispatches here via `_*_ops()` lazy importers.

## STRUCTURE
One module per command group + shared helpers:

```
ops/
  stack.py     # stack up / down / update
  service.py   # service start / stop / restart / status / log / connect
  container.py # project-scoped ps / stats
  volume.py    # volume backup / restore / pull / push
  image.py     # image backup / restore
  seed.py      # generate_seed — `init --seed` test project
  common.py    # shared: ensure_runtime_ready, get_key, prompt_select,
               #         select_backup_timestamp, stack_paused
```

## WHERE TO LOOK

| Task | File |
|------|------|
| Backup/restore consistency | `volume.py`, `image.py` + `common.stack_paused` contextmanager |
| Interactive selection menu | `common.prompt_select` / `common.get_key` (raw terminal, no rich) |
| Pick a backup timestamp | `common.select_backup_timestamp` |
| Docker Desktop startup gate | `common.ensure_runtime_ready` -> `docker.py: ensure_ready_for_start` |
| Test seed project generation | `seed.py` |

## CONVENTIONS

- Module-level functions taking `(runtime, config, profile)` — no classes, no state.
- User-facing failures raise `CommandError(t("msg.*", ...))`; the CLI boundary (`HelpOnUnknownCommandGroup.main`) renders them concisely with the exit code.
- All runtime interaction via `ContainerRuntime` (`run_compose`, `passthru_cli`, `passthru_compose`); never raw `subprocess` here.
- Volume/image backup wraps the operation in `stack_paused(...)` unless `--no-stop`; restart failure after an operation error is a warning, not a crash.
- `get_key()` is cross-platform (msvcrt on win32, termios elsewhere) — keep platform branches symmetrical.

## ANTI-PATTERNS

- No `typer.echo` for errors in ops — raise `CommandError`; keep rendering in the CLI layer.
- Don't add a new domain module without a `tests/test_ops_<domain>.py` mirror — 100% branch coverage is enforced.
- `common.py` is the shared layer — new cross-cutting helpers live there, not in a domain module.
