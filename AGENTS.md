# compman — Docker Compose Stack Manager CLI

## Quick start

```bash
uv tool install .      # install CLI
compman --help         # verify
```

## Structure

```
compman/               # Python package
  cli.py               # typer entrypoint: compman.cli:app
  config.py            # compman.yml loader (Config dataclass)
  docker.py            # ContainerRuntime abstraction, compose file resolution
  deploy.py            # S3 download, managed-tree swap, optional image build
  archive.py           # path-safe tar/zip extraction
  scaffold.py          # deploy-time compman/compose generation
  ops/                 # business logic per domain
    stack.py, service.py, volume.py, image.py, seed.py
tests/                 # pytest unit/regression suite
test/                  # runnable examples and E2E guides (not pytest tests)
```

- `compman init` provides an interactive 3-mode menu (1. Skeleton compman.yml, 2. S3 URL deploy, 3. Test seed project). Direct flags `--skeleton`, `--s3 <url>`, and `--seed` are also supported.
- Build/running is `uv`-based (`pyproject.toml` has `[tool.uv] package = true`).
- Python >=3.10; runtime deps: typer, PyYAML, boto3, botocore.
- Quality gates: 238 pytest tests, 100% statement/branch coverage, Ruff, mypy.
- CI tests Python 3.10-3.13 on Linux/macOS/Windows and has packaging and Docker/Ministack integration jobs.

## Config: `compman.yml`

Two modes:

1. **Simple** (no profiles, single compose file or list):
   ```yaml
   compose:
     - docker-compose.yml
   ```

2. **Profile-based** (per-environment compose + env vars):
   ```yaml
   compose:
     local: docker-compose.local.yml
     dev:
       file: docker-compose.dev.yml
       env:
         DATABASE_URL: dev.db.example.com
   ```

- `compose` key omitted → defaults to `docker-compose.yml`.
- Optional `folder` key → compose files live under that relative subdirectory.
- `folder` and `dirs.*` are resolved relative to the config directory. Managed backup/volume/project paths may not escape it; destructive managed directories may not equal the config root.
- Optional `base` key → prepended as `-f` before profile compose files.
- Profile `file` is optional: omitted → fallback to `base` or `docker-compose.yml`.
  Useful when all profiles share one compose file with different env vars only.

## Runtime

- Auto-detects Docker then Podman. Override: `CONTAINER_RUNTIME=podman`.
- Detection order: `docker compose` → `podman compose` → `podman-compose` → `docker-compose`.

## CLI quirks

- `stack down` requires `--yes` confirmation (`typer.confirm`).
- Profile mode defaults to the first configured profile when none is supplied; an explicit name must be valid. Simple mode rejects a profile argument.
- `image backup` defaults to committing runtime container state; `--source-image` flag saves the original image instead.
- `volume backup/restore` optional `--no-stop` flag skips stack teardown.
- `service log` displays last 50 lines by default (`docker logs -n 50`), supports `-f`/`--follow` to stream and `-n`/`--tail N` for line count.
- `service connect` runs `docker exec -it` with bash fallback to sh.
- `deploy` uses boto3 (no AWS CLI needed). S3 source path comes from `compman.yml: deploy` (single value, no per-profile) or `--path` override. `AWS_ENDPOINT_URL_S3` or `AWS_ENDPOINT_URL` env redirects the S3 client (e.g. local ministack at `http://localhost:4566`). Creds via standard `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_DEFAULT_REGION` env vars.
- Deploy accepts an S3 **prefix** or `.tar.gz`/`.tgz`/`.zip` archive. Archives reject absolute/traversal paths and links; a single top-level directory is flattened.
- The fetched tree replaces the contents of the managed `dirs.project` directory, preserving `.git` and `.gitkeep`. Root `compman.yml` and `docker-compose.yml` are scaffolded or updated separately.
- File swap rollback is atomic at the managed-tree step, but the full fetch → scaffold → build operation is not transactional: a later scaffold/build failure leaves the new source tree in place.
- `update` rebuilds and force-recreates containers; it is not a zero-downtime rolling deployment.

## Backup naming

```
<stackname>.volume.<YYYYMMDD_HHMMSS>[_<microseconds>].tar.gz
<stackname>.image.<YYYYMMDD_HHMMSS>[_<microseconds>].tar.gz
```

## Verification

```bash
uv sync --dev
uv run ruff check compman tests
uv run mypy compman
uv run pytest --cov=compman --cov-report=term-missing
```
