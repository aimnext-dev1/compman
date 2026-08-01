# compman — Docker Compose Stack Manager CLI

`compman` manages Docker or Podman Compose stacks—including execution, service operations, volume and image backup, and S3-based deployment—from one CLI.

## Key features

- Automatically detects Docker Compose and Podman Compose runtimes
- Supports a single Compose file and environment-specific profile configurations
- Deploys from an S3 prefix or a `.tar.gz`/`.tgz`/`.zip` archive
- Automatically creates `compman.yml` and `docker-compose.yml` when deploying into an empty directory
- Creates and restores timestamped backups of volumes and container images
- Korean and English help, plus shell completion
- Supports Windows, Linux, and macOS

## Requirements

- Python 3.10 or later
- Docker Compose or Podman Compose
- For S3 deployments: accessible S3-compatible storage and AWS credentials

CI verifies Python 3.10–3.13 on Ubuntu, macOS, and Windows. See the `Python version strategy` section of [REVIEW.md](REVIEW.md) for the Python 3.14 support plan and upgrade decision.

## Installation

### Automatic installation

```powershell
# Windows PowerShell
irm https://raw.githubusercontent.com/allbegray/compman/main/install.ps1 | iex
```

```cmd
:: Windows CMD
curl -fsSL https://raw.githubusercontent.com/allbegray/compman/main/install.cmd -o %TEMP%\install.cmd && call %TEMP%\install.cmd
```

```bash
# Linux / macOS
curl -fsSL https://raw.githubusercontent.com/allbegray/compman/main/install.sh | sh
```

Open a new terminal, then verify the installation.

```bash
compman --version
compman --help
```

### Install with uv or pipx

```bash
uv tool install git+https://github.com/allbegray/compman.git
# Or
pipx install git+https://github.com/allbegray/compman.git
```

To install a development version from the repository, run:

```bash
uv tool install .
```

Update an installed CLI using uv's stored tool source with:

```bash
compman upgrade
```

This runs `uv tool upgrade compman --reinstall`.

### Recover a damaged installation

If `compman upgrade` cannot run because the installation is damaged, reinstall the
released version:

```bash
uv tool uninstall compman
uv tool install git+https://github.com/allbegray/compman.git@v1.1.1
compman --version
```

## Quick start

### Existing Compose project

```bash
cd my-project
compman init --skeleton
compman stack up
compman service status
compman stack down --yes
```

Running `compman init` without arguments displays an interactive menu with these three modes.

```bash
compman init --skeleton                         # Create compman.yml
compman init --s3 s3://bucket/app.tar.gz --build
compman init --seed -o project -p 18080         # Create a test project
compman init --seed -o project -a               # Create a test project and archive
```

Overwriting existing files requires an explicit `--force`.

### Deploy a new project from S3

Run this from an empty working directory.

```bash
mkdir my-app && cd my-app
compman deploy --path s3://my-bucket/releases/app.tar.gz --build --tag my-app
compman stack up
```

A successful deployment creates this file structure.

```text
my-app/
├── compman.yml
├── docker-compose.yml
└── project/              # Application source downloaded from S3
```

S3 paths support these two formats.

- Prefix: Recursively downloads objects beneath the path and preserves their directory structure.
- Archive: Safely extracts `.tar.gz`, `.tgz`, or `.zip`; a single top-level directory is flattened automatically.

Only the deployment target with the same name is replaced; other user files are retained. If the source-replacement step fails, the previous tree is restored. A full transaction covering later scaffold generation and image building is not yet guaranteed.

## Configuration file

Put all configuration under the `compman` key in `compman.yml`.

### Single Compose configuration

```yaml
compman:
  name: my-stack
  compose:
    - docker-compose.yml
```

When `compose` is omitted, `docker-compose.yml` is used. When multiple files are listed, they are passed as `-f` options in declaration order.

### Environment-specific profile configuration

```yaml
compman:
  name: my-stack
  compose:
    base: docker-compose.yml
    local: docker-compose.local.yml
    dev:
      file: docker-compose.dev.yml
      env:
        DATABASE_URL: dev.db.example.com
        LOG_LEVEL: debug
    prod:
      file: docker-compose.prod.yml
      env:
        DATABASE_URL: prod.db.example.com
```

The profile `file` is optional. When omitted, `base` is used; if there is no `base`, `docker-compose.yml` is used. This lets one Compose file use different environment variables per environment.

```bash
compman stack up dev
compman service status --profile dev
compman stack down --profile dev --yes
```

### Deployment and managed directories

```yaml
compman:
  name: my-stack
  deploy: s3://my-bucket/releases/app.tar.gz
  folder: compose
  dirs:
    project: project
    backup: backup
    volume: volume
  compose:
    - docker-compose.yml
```

- `folder`: Relative subdirectory containing Compose files
- `dirs.project`: Relative subdirectory for S3 deployment source
- `dirs.backup`: Directory for backup archives
- `dirs.volume`: Directory for transferring volume data to and from the host
- `deploy`: Default S3 path for `compman deploy` and `compman update`

Managed paths cannot escape the directory containing `compman.yml`. `--path` overrides the configured `deploy` value for one invocation only.

## Commands

```text
compman init [--skeleton | --s3 URI | --seed]
compman deploy [--path S3_URI] [--build] [--tag TAG]
compman update [PROFILE]
compman doctor [--profile PROFILE] [-c|--config PATH] [--json]
compman status [--profile PROFILE] [-c|--config PATH] [--json]
compman upgrade
compman version
compman lang [ko|en]
compman completion [powershell|bash|zsh|fish] --install

compman stack up [PROFILE]
compman stack update [PROFILE]
compman stack down [--profile PROFILE] --yes

compman service start [SERVICE...] [--profile PROFILE]
compman service stop [SERVICE...] [--profile PROFILE]
compman service restart [SERVICE...] [--profile PROFILE]
compman service status [--profile PROFILE]
compman service log [CONTAINER] [-f] [-n 50] [--profile PROFILE]
compman service connect [CONTAINER] [--profile PROFILE]

compman volume backup [--no-stop] [--profile PROFILE]
compman volume restore [TIMESTAMP] [--no-stop] [--profile PROFILE]
compman volume pull [--profile PROFILE]
compman volume push [--profile PROFILE]

compman image backup [--source-image] [--profile PROFILE]
compman image restore [TIMESTAMP] [--profile PROFILE]

compman clear
```

View all options for a command with `compman <command> --help`.

### Behavioral notes

- `update`: When `deploy` is configured, it downloads from S3, builds images, and starts the stack. Otherwise, it updates the local Compose project with `up -d --build`.
- `service log`: Displays the last 50 lines by default and streams output with `-f`.
- `service connect`: Falls back to `sh` if connecting with `bash` fails.
- `volume backup/restore`: By default, brings the stack down during the operation and restores it afterward. Use `--no-stop` only when you understand the consistency risk.
- `image backup`: By default, commits and saves the state of the running container. Use `--source-image` to save the original image.
- `clear`: Runs `image prune -af` for the selected runtime, so it can delete unused images outside the current project.

## Diagnostics and status

```bash
compman doctor
compman doctor --json
compman doctor --config /path/to/compman.yml
compman doctor -c /path/to/compman.yml
compman status
compman status --profile PROFILE
compman status --json
compman status --config /path/to/compman.yml
compman status -c /path/to/compman.yml
```

`doctor` checks configuration, Compose files, container-runtime availability and connectivity, managed directories, and AWS credentials. `status` displays the service state of the running stack. `--json` outputs structured JSON suitable for automation.

If a required `doctor` check fails, it returns exit code `1`. `status` returns exit code `1` when the target stack does not exist or status retrieval itself fails. If the stack exists and retrieval succeeds, it returns exit code `0` even if every service is stopped or exited. Missing AWS environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) are non-failing warnings, so `doctor` returns exit code `0` if all other required checks pass.

## Backup and restore

Backup files are stored in `dirs.backup`.

```text
<stack>.volume.<YYYYMMDD_HHMMSS>[_<microseconds>].tar.gz
<stack>.image.<YYYYMMDD_HHMMSS>[_<microseconds>].tar.gz
```

When restoring without a timestamp, choose an available backup interactively. Volume restore and `volume push` merge data into the target; they do not delete files that exist only at the target. Image restore loads the image into the runtime but does not automatically change the Compose `image` tag.

## Runtime selection

The automatic detection order is:

```text
docker compose → podman compose → podman-compose → docker-compose
```

To prefer Podman, set an environment variable.

```bash
export CONTAINER_RUNTIME=podman
# PowerShell: $env:CONTAINER_RUNTIME="podman"
```

### Windows Docker Desktop readiness

On Windows when Docker is the selected runtime, compman checks Docker Desktop before `compman stack up`, `compman update`, `compman stack update`, and a `compman deploy --build` image build. If Docker Desktop is not ready in an interactive terminal, it asks:

```text
Docker Desktop is not running. Start it now? [Y/n]
```

Press Enter (or answer `Y`) to start Docker Desktop. compman waits up to 60 seconds for it to become ready before continuing. Answering `N` exits with guidance to start Docker Desktop manually and retry.

In non-interactive execution, compman never starts Docker Desktop; it exits with a concise error instead. This check does not run for Podman, read-only commands, backup/restore, or stop/down paths.

Expected operational failures, including Docker Desktop readiness failures, are printed as concise messages without Python tracebacks.

## S3-compatible storage

Uses standard AWS SDK environment variables.

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=ap-northeast-2
export AWS_ENDPOINT_URL_S3=http://localhost:4566   # Default Ministack/LocalStack port
```

If `AWS_ENDPOINT_URL_S3` is absent, `AWS_ENDPOINT_URL` can also be used.

## Language and shell completion

```bash
compman lang ko                    # Set the default language for the current process
compman --lang en --help           # Use English for this invocation only
export COMPMAN_LANG=ko             # Set the default language in the shell environment

compman completion powershell --install
compman completion bash --install
compman completion zsh --install
compman completion fish --install
```

## Development and verification

```bash
uv sync --dev
uv run ruff check compman tests
uv run mypy compman
uv run pytest --cov=compman --cov-report=term-missing
```

CI verifies:

- Ubuntu, macOS, and Windows × Python 3.10–3.13 tests
- 100% statement and branch coverage
- Ruff and mypy
- Wheel build, isolated installation, and CLI execution
- Ministack S3 download, Docker image build, and Compose start/stop E2E

For current constraints and the improvement backlog, see [REVIEW.md](REVIEW.md). For test-project usage, see each README under [`test/`](test/).
