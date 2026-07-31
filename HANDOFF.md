# compman Handoff

## Current state

- Python package entry point: `compman.cli:app`
- Supported Python metadata: `>=3.10`
- Tested CI matrix: Python 3.10-3.13 on Ubuntu, macOS, and Windows
- Runtime dependencies: Typer, PyYAML, boto3, botocore
- Runtime detection: Docker Compose, Podman Compose, `podman-compose`, then `docker-compose`
- Test suite: 183 tests with 100% statement and branch coverage
- Static checks: Ruff and mypy
- CI also includes wheel smoke testing and a Docker/Ministack deployment integration job

Do not record a branch name, commit hash, Actions run ID, or clean-worktree claim here; those values become stale immediately. Use `git status`, `git log -1`, and the repository Actions page when handing off a specific revision.

## Verification

```bash
uv sync --dev
uv run ruff check compman tests
uv run mypy compman
uv run pytest --cov=compman --cov-report=term-missing
uv build
```

Coverage is enforced at 100% for both statements and branches.

## Important behavior

- `compman update` fetches, builds, and force-recreates containers. It is not guaranteed zero-downtime.
- Deploy replaces the managed `dirs.project` tree. The tree swap rolls back on swap failure, but a later scaffold or image-build failure does not restore the previous source tree.
- Managed `folder`/`dirs.*` paths cannot escape the directory containing `compman.yml`; destructive managed paths cannot equal that root.
- Volume maps use a list so one container can retain multiple mounts. Legacy one-volume-per-container maps remain readable.
- Volume restore/push copies into existing destinations and does not delete stale destination files.
- Image restore loads image archives but does not rewrite Compose image tags.

## Recommended next work

See `REVIEW.md`. Highest value items are full deploy transaction rollback, safer confirmation/scoping for `clear`, and explicit replacement semantics for volume restore.
