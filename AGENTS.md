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
- Profile `file` is optional: omitted → fallback to `base` or `docker-compose.yml`.
  Useful when all profiles share one compose file with different env vars only.

## Runtime

- Auto-detects Docker then Podman. Override: `CONTAINER_RUNTIME=podman`.
- Detection order: `docker compose` → `podman compose` → `podman-compose` → `docker-compose`.

## CLI quirks

- `stack down` requires `--yes` confirmation (click `confirmation_option`).
- `stack up/update` with profile mode requires valid profile name; without profiles, takes no argument.
- `image backup` defaults to committing runtime container state; `--source-image` flag saves the original image instead.
- `volume backup/restore` optional `--no-stop` flag skips stack teardown.
- `service log` displays last 50 lines by default (`docker logs -n 50`), supports `-f`/`--follow` to stream and `-n`/`--tail N` for line count.
- `service connect` runs `docker exec -it` with bash fallback to sh.
- `deploy` uses boto3 (no AWS CLI needed). S3 source path comes from `compman.yml: deploy` (single value, no per-profile) or `--path` override. `AWS_ENDPOINT_URL_S3` or `AWS_ENDPOINT_URL` env redirects the S3 client (e.g. local ministack at `http://localhost:4567`). Creds via standard `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_DEFAULT_REGION` env vars.
- Deploy key can be a **prefix path** (everything under it is downloaded, structure preserved) or an **archive file** (`.tar.gz`/`.tgz`/`.zip`, downloaded + extracted; a single top-level dir is flattened). Fetched tree replaces same-named entries in cwd (atomic swap, user files kept). If `compman.yml`/`docker-compose.yml` are missing, deploy auto-generates them (simple-mode `compman.yml` with the used S3 path recorded; `docker-compose.yml` referencing the build image tag) — so `compman deploy --build` then `compman stack up` works in an empty dir. Optional `--build` runs `docker build -t TAG .` after fetch (`--tag` defaults to cwd dirname). Run from scratch dir, not repo root — creates untracked files. Test setup: root `docker-compose.yaml` runs `ministack-compman` on port `4567`; `docker-init/` holds the seed sources — `init-bucket.sh` auto-seeds bucket `deploy-test` with the dir (`seed/`) and committed archive (`seed.tar.gz`, app-wrapped) versions; deploy into `test/deploy-project/target/`.

## Backup naming

```
<stackname>.volume.<YYYYMMDD_HHMM>.tar.gz
<stackname>.image.<YYYYMMDD_HHMM>.tar.gz
```

## Legacy

Shell scripts in `_script/` + `Makefile` are the old system. Can coexist with compman but compman is the primary CLI.
`stack.env` is for the legacy shell system only, not used by compman.
