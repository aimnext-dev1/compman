# Project-scoped `ps` and `stats` commands

## Goal

Add convenient container inspection commands that operate only on the Compose project selected by the current `compman.yml`. The commands must preserve compman's runtime auto-detection and profile behavior instead of exposing runtime-wide Docker or Podman state.

## Command interface

### `compman ps [PROFILE]`

- Show running containers belonging to the selected compman project.
- Accept `-a` / `--all` to include stopped containers in that project.
- Use the existing profile selection and validation rules.

### `compman stats [PROFILE]`

- Stream CPU, memory, network, and related runtime statistics for containers belonging to the selected compman project.
- Accept `--no-stream` to print one snapshot and exit.
- Use the existing profile selection and validation rules.

Neither command provides a global mode. Users who need runtime-wide information can continue to use `docker ps`, `docker stats`, or their Podman equivalents directly.

## Architecture and data flow

The CLI layer will expose two top-level Typer commands. Each command will load `compman.yml`, resolve the requested profile, compose files, environment, project name, and detected container runtime through existing helpers.

`ps` will delegate to the selected Compose implementation with `ps`, adding `--all` when requested.

`stats` will first ask Compose for the selected project's running container IDs with `ps --quiet`, then pass those IDs to the detected runtime's native `stats` command, adding `--no-stream` when requested. Docker Compose has a native `stats` subcommand, but Podman's Compose command is a wrapper around an external provider whose supported subcommands can vary. Resolving IDs through Compose and displaying statistics through `docker stats` or `podman stats` keeps project scoping while supporting every runtime path already detected by compman.

The runtime abstraction will remain responsible for building and executing Docker Compose, Podman Compose, `podman-compose`, or legacy `docker-compose` commands. No parsing or reformatting of native output will be introduced.

## Error handling

- Missing or invalid configuration, profile, Compose file, or runtime will use existing compman error handling.
- Runtime command failures will retain their exit status and readable stderr behavior.
- An empty project is not treated as a compman error. `ps` may print an empty result; `stats` will print a short informational message instead of invoking runtime-wide statistics with no container arguments.
- Interactive `stats` streaming will preserve keyboard interruption behavior from the runtime process.

## Documentation and completion

Update the root README command reference and shell completion command lists so both commands are discoverable. Update release notes and apply a minor version bump because this adds backward-compatible user-facing functionality.

## Verification

- Unit tests will cover command construction, profile handling, `ps --all`, `stats --no-stream`, container-ID discovery, and the empty-project guard.
- Existing quality gates must remain green with 100% statement and branch coverage.
- Build the distributable Windows executable and exercise `ps`, `ps --all`, and `stats --no-stream` against a real temporary Compose project.
- The streaming `stats` path will be verified through command construction/unit coverage to keep automated validation bounded.

## Non-goals

- Runtime-wide container inspection.
- Custom table formatting or statistics aggregation.
- Filtering, sorting, polling intervals, or export formats.
- Replacing the existing normalized `compman status` report or `compman service status` command.
