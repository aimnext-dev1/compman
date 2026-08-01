# Changelog

Major user-visible changes to compman are recorded here, with the newest release
first.

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
