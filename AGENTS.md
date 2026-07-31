# compman — Docker Compose Stack Manager CLI

## Quick start

```bash
uv tool install .      # install CLI
compman --help         # verify
```

## Structure

```
compman/               # Python package
  cli.py               # click entrypoint: compman.cli:cli
  config.py            # compman.yml loader (Config dataclass)
  docker.py            # ContainerRuntime abstraction, compose file resolution
  deploy.py            # S3 deploy (paths hardcoded, currently empty)
  ops/                 # business logic per domain
    stack.py, service.py, volume.py, image.py
test/                  # example configs only, NOT test suites
```

## Commands

- Build/running is `uv`-based (`pyproject.toml` has `[tool.uv] package = true`).
- Python >=3.10, deps: click, pyyaml.
- No tests, no CI, no linter/formatter/typechecker config.
- No Makefile (legacy shell scripts in `_script/` use `make`, but compman CLI does not).

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
- Optional `folder` key → compose files live under `_project/`.
- Optional `base` key → prepended as `-f` before profile compose files.

## Runtime

- Auto-detects Docker then Podman. Override: `CONTAINER_RUNTIME=podman`.
- Detection order: `docker compose` → `podman compose` → `podman-compose` → `docker-compose`.

## CLI quirks

- `stack down` requires `--yes` confirmation (click `confirmation_option`).
- `stack up/update` with profile mode requires valid profile name; without profiles, takes no argument.
- `image backup` defaults to committing runtime container state; `--source-image` flag saves the original image instead.
- `volume backup/restore` optional `--no-stop` flag skips stack teardown.
- `service log` runs `docker logs -f -n 10000` (follow, last 10k lines).
- `service connect` runs `docker exec -it` with bash fallback to sh.
- `deploy` requires AWS CLI + configured S3 paths in `deploy.py:S3_PATHS` (currently empty strings).

## Backup naming

```
<stackname>.volume.<YYYYMMDD_HHMM>.tar.gz
<stackname>.image.<YYYYMMDD_HHMM>.tar.gz
```

## Legacy

Shell scripts in `_script/` + `Makefile` are the old system. Can coexist with compman but compman is the primary CLI.
`stack.env` is for the legacy shell system only, not used by compman.
