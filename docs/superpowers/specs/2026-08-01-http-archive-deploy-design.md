# HTTP Archive Deploy Design

## Goal

Allow `compman deploy` and S3-backed `update` behavior to fetch public archives from HTTP and HTTPS URLs while preserving existing S3 prefix and archive support.

## Source support

- Accept `http://` and `https://` sources through `compman deploy --path` and `compman.yml: deploy`.
- HTTP sources must have a URL path ending in `.tar.gz`, `.tgz`, or `.zip`; query strings do not affect suffix detection.
- Keep S3 support unchanged: an `s3://` source may be a prefix or one of the supported archive formats.
- Reject unsupported schemes and non-archive HTTP URLs before attempting a download.

## Download behavior

- Use Python's standard-library `urllib`; add no runtime dependency.
- Use the platform's default TLS certificate validation and normal redirect handling.
- Apply a 30-second request timeout.
- Stream response bytes directly to a temporary archive file instead of buffering the complete response in memory.
- Do not add authentication headers, tokens, cookies, retry policy, or configurable timeouts in this release.

## Extraction and deployment

- Reuse the existing path-safe tar and zip extraction functions.
- Preserve the existing behavior that flattens a single top-level archive directory.
- Feed the extracted tree into the current managed-tree swap, scaffold generation, optional build, and update flows.
- Keep the `compman.yml` key named `deploy`; it stores either an S3 URI or an HTTP/HTTPS archive URL.

## Errors

- Report unsupported source schemes and invalid HTTP archive suffixes as validation failures.
- Report HTTP status and network failures with the source URL and deployment stage.
- Preserve existing S3-specific credential, permission, endpoint, and not-found guidance.
- Always remove temporary download and extraction files.

## Documentation and release

- Update CLI/i18n help, README, AGENTS.md, and CHANGELOG to describe S3 or HTTP archive sources accurately.
- Include this feature with the approved init terminology change in version `1.2.0`.

## Verification

- Cover HTTP and HTTPS dispatch, query strings, each supported archive type, redirects/streaming behavior through mocked responses, invalid suffixes, unsupported schemes, and download failures.
- Re-run all S3 tests to demonstrate no regression.
- Run Ruff, mypy, and pytest with 100% statement and branch coverage.
- Build and install the wheel into an isolated Windows environment, then smoke-test the generated `compman.exe`.
