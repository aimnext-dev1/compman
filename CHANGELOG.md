# Changelog

Major user-visible changes to compman are recorded here, with the newest release
first.

## [1.3.0] - 2026-08-01

### Added

- Added project-scoped `compman ps` container listings with `-a`/`--all`.
- Added project-scoped `compman stats` resource snapshots with `-f`/`--follow`
  streaming.

## [1.2.0] - 2026-08-01

### Changed

- Replaced `compman init --skeleton` with `compman init --scaffold` and updated
  interactive and localized guidance to use scaffold terminology. The removed
  `--skeleton` option is no longer accepted.

### Added

- Added public HTTP and HTTPS `.tar.gz`, `.tgz`, and `.zip` deployment sources
  alongside existing S3 prefix and archive support.
- Added a dependency-free project homepage deployed through GitHub Pages at
  `https://allbegray.github.io/compman/`.
- Licensed compman under the MIT License.

## [1.1.6] - 2026-08-01

### Added

- Added a GitHub Actions workflow that creates an annotated version tag after a
  successful CI run for a push to `main`.
- Added release guards for CHANGELOG consistency, duplicate tags, and tag
  collisions, and prevented tag pushes from starting duplicate CI runs.

## [1.1.5] - 2026-08-01

### Added

- Added `-z`/`--level` (1-9) to volume and image backups for controlling gzip
  speed versus archive size. The default level is 6.

## [1.1.4] - 2026-08-01

### Added

- Added `compman -v` as a short alias for `compman --version`.
- Added `-h` as a short alias for `--help` on the root command and command groups.

## [1.1.3] - 2026-08-01

### Changed

- Reduced CLI help startup work by loading Docker, S3, diagnostics, YAML, and
  operation modules only when their commands need them.
- Removed duplicate configuration loading and container-runtime detection from
  the S3-backed `update` path.
- Made `compman upgrade` use an uv-managed Python 3.13 runtime so removing or
  replacing a system Python installation does not break the upgraded CLI.
- Clarified that the recommended audience works in environments where a web GUI
  is unavailable, rather than implying that users do not know how to use one.
- Added this changelog as the canonical source for release notes on every version
  update.

## [1.1.2] - 2026-08-01

### Fixed

- Made captured container output and localized console text safe on Windows
  code pages, including Korean help output.
- Prevented status and upgrade output from raising Unicode decoding tracebacks.
