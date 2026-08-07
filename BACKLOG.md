# Critical Review and Improvement Backlog

Reviewed against the current implementation and 100% statement/branch test suite.

## High priority

### Make deploy transactional across swap, scaffold, and build

The managed source-tree swap can roll back its own failure. However, scaffold generation and `docker build` run after the new tree is installed. If either fails, the command exits unsuccessfully while the new source and possibly updated `compman.yml` remain.

Recommended design: retain the previous tree until build succeeds, generate scaffold changes in temporary files, then commit all filesystem changes together. Document and test rollback of source, config, Compose file, and image-tag state.

### Define replacement semantics for volume restore and push

Restore currently copies files into an existing mounted destination. Files that exist only in the destination survive, so the result may differ from the backup. This is safe against accidental deletion but is not a byte-for-byte restore.

Recommended design: keep merge as the default for compatibility, add an explicit `--replace` mode with confirmation, and implement deletion inside a narrowly validated mount destination.

### Scope destructive global cleanup

`compman clear` runs the runtime-wide equivalent of `docker image prune -af`, affecting images unrelated to the current stack and without confirmation.

Recommended design: require `--yes`, clearly label the global scope, and consider a stack-scoped cleanup command based on Compose labels.

## Medium priority

### Separate service names from container names

`service start/stop/restart` accept Compose service names, while `service log/connect` resolve exact runtime container names. The shared `name` terminology is ambiguous and scaled services are not handled ergonomically.

Recommended design: resolve service names via `compose ps -q SERVICE`, support an instance selector for scaled services, and display both service and container names.

### Add deploy integrity controls

S3 downloads rely on transport and AWS SDK validation but have no user-configured artifact checksum, signature, object-version pin, or maximum extracted size/count. A trusted-but-compromised bucket can deliver an unexpectedly large or altered artifact.

Recommended design: optional SHA-256/object version configuration, archive size/member limits, and provenance output during deploy.

### Improve release engineering

Version `1.0.0` marks the first stable release. Dependencies still have no direct lower bounds, and no documented changelog or release process exists.

Recommended design: tag-derived versions, release notes/changelog, dependency policy, reproducible wheel verification, and publishing automation.

### Split large modules and coverage-only tests

`cli.py` and `i18n.py` are large, and `tests/test_missing_coverage.py` plus `test_coverage_completion.py` group unrelated cases. Full coverage is valuable, but intent becomes harder to locate.

Recommended design: move commands into domain modules, store translations as validated resources, and relocate edge tests beside the module they specify while retaining the 100% gate.

## Lower priority

- Add structured/debug logging and preserve underlying exception chains for support diagnostics.
- Add timeouts and cancellation guidance for long Docker operations as configurable values.
- Validate configuration against an explicit schema and publish a versioned config format.
- Add documentation checks for commands, examples, broken links, and Markdown consistency.
- Remove the test-suite `runpy` import warning by testing the CLI entry point in an isolated subprocess.

## Python version strategy

As of July 2026, Python 3.14 is the latest stable feature line and Python 3.10 reaches end of support in October 2026. The project metadata still supports `>=3.10`, while CI currently tests through 3.13.

Recommended sequence:

1. Add stable Python 3.14 to the CI matrix and use it for quality/packaging jobs.
2. Keep 3.10 compatibility only if existing deployment hosts require it.
3. Before October 2026, raise the minimum to 3.11 or preferably 3.12 after checking target OS availability.
4. Do not enable the experimental JIT or adopt the free-threaded build merely for this CLI; its work is dominated by subprocess, filesystem, Docker, and network waits rather than CPU-bound Python threads.
5. Consider Python 3.14's standard-library Zstandard support only as a versioned, opt-in backup format. Retain `.tar.gz` read compatibility.

The local `uv` installation available during this review resolved `--python 3.14` to an old 3.14.0a6 interpreter rather than current stable 3.14.6, so it was not accepted as a valid stable-3.14 compatibility test. CI should pin/request a stable 3.14 release explicitly.
