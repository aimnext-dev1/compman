# HTTP Archive Deploy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add public HTTP/HTTPS archive sources to deploy and update without changing existing S3 behavior.

**Architecture:** Extract shared archive recognition and safe extraction into a source-neutral module. Add a standard-library HTTP downloader, then dispatch by URI scheme in the existing deploy orchestrator while leaving configuration and managed-tree replacement unchanged.

**Tech Stack:** Python 3.10+, urllib, tarfile, zipfile, Typer, pytest, Ruff, mypy, uv

## Global Constraints

- HTTP and HTTPS accept only `.tar.gz`, `.tgz`, and `.zip` URL paths.
- Query strings do not affect archive suffix detection.
- HTTP downloads use standard TLS verification, redirects, a 30-second timeout, and streamed file writes.
- No new dependency, authentication option, retry policy, or configurable timeout.
- Existing S3 prefix and archive behavior remains unchanged.
- Temporary files are always removed by the deploy orchestrator.

---

### Task 1: Share source-neutral archive extraction

**Files:**
- Create: `compman/archive_source.py`
- Modify: `compman/s3_source.py`
- Test: `tests/test_deploy.py`

**Interfaces:**
- Produces: `ARCHIVE_SUFFIXES`, `has_archive_suffix(path: str) -> bool`, and `extract_archive(archive_path: Path, extract_dir: Path) -> Path`
- Consumes: existing `extract_tar()` and `extract_zip()` path-safety functions

- [ ] **Step 1: Write tests for archive suffix recognition and top-level flattening**

Add assertions for `.tar.gz`, `.tgz`, `.zip`, case-insensitive matching, unsupported suffixes, and returning either a single extracted directory or the extraction directory.

- [ ] **Step 2: Run focused tests and verify failure**

```bash
uv run pytest tests/test_deploy.py -k "archive_source" -q
```

Expected: import failure because `compman.archive_source` does not exist.

- [ ] **Step 3: Implement the shared module and migrate S3 fetch**

Move suffix recognition and tar/zip extraction selection out of `s3_source.py`. Keep S3 recursive-prefix logic intact and call `extract_archive()` only after downloading an archive.

- [ ] **Step 4: Run S3 and archive tests**

```bash
uv run pytest tests/test_deploy.py -q
```

Expected: all existing and new deploy tests pass.

### Task 2: Download public HTTP archives

**Files:**
- Create: `compman/http_source.py`
- Test: `tests/test_deploy.py`

**Interfaces:**
- Consumes: `has_archive_suffix()` and `extract_archive()` from Task 1
- Produces: `fetch(url: str, tmp: Path) -> Path`

- [ ] **Step 1: Write failing HTTP source tests**

Mock `urlopen` with a context-managed byte response. Assert timeout `30`, streamed archive extraction, query-string suffix handling, HTTP and HTTPS acceptance, and rejection of a non-archive URL before download.

- [ ] **Step 2: Run focused tests and verify failure**

```bash
uv run pytest tests/test_deploy.py -k "http_source" -q
```

Expected: import failure because `compman.http_source` does not exist.

- [ ] **Step 3: Implement the minimal HTTP fetcher**

Validate the parsed scheme and path suffix, create a safe temporary filename, call `urllib.request.urlopen(url, timeout=30)`, stream with `shutil.copyfileobj`, and return `extract_archive()` output.

- [ ] **Step 4: Run HTTP source tests and verify success**

```bash
uv run pytest tests/test_deploy.py -k "http_source" -q
```

Expected: all selected tests pass.

### Task 3: Dispatch deploy sources and update user guidance

**Files:**
- Modify: `compman/deploy.py`
- Modify: `compman/cli.py`
- Modify: `compman/i18n.py`
- Modify: `compman/config.py`
- Modify: `tests/test_deploy.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_coverage_completion.py`
- Modify: `tests/test_missing_coverage.py`

**Interfaces:**
- Consumes: `http_source.fetch()` and existing `s3_source.fetch()`
- Produces: scheme-dispatched `deploy --path` and configured `update` behavior

- [ ] **Step 1: Write failing dispatch and error tests**

Test HTTP and HTTPS dispatch without creating a boto3 client, unsupported schemes, HTTP non-archive validation, HTTP download failure stage text, and unchanged S3 dispatch.

- [ ] **Step 2: Run focused tests and verify failure**

```bash
uv run pytest tests/test_deploy.py tests/test_cli.py -k "http or invalid_s3_path or deploy" -q
```

Expected: HTTP archive deployment is rejected by the S3-only validator.

- [ ] **Step 3: Implement scheme dispatch and neutral terminology**

Parse the configured source once. For `s3`, preserve boto3 handling; for `http` or `https`, call the HTTP fetcher; otherwise raise an unsupported-source error. Change user-facing `S3 path` wording to `deploy source` where both forms are accepted, while retaining S3-specific error guidance.

- [ ] **Step 4: Run focused deployment tests**

```bash
uv run pytest tests/test_deploy.py tests/test_cli.py tests/test_coverage_completion.py tests/test_missing_coverage.py -q
```

Expected: selected test files pass.

### Task 4: Document, verify, build, and release

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `CHANGELOG.md`
- Modify: `tests/test_repository_urls.py` if repository-wide wording checks require adjustment

**Interfaces:**
- Consumes: Tasks 1-3 behavior and the existing version `1.2.0` release metadata
- Produces: complete user and maintainer documentation for S3 and HTTP archive sources

- [ ] **Step 1: Update documentation and release notes**

Document HTTP/HTTPS public archives, allowed suffixes, example configuration and commands, unchanged S3 prefix support, and the lack of HTTP authentication options. Add the feature to the existing `1.2.0` CHANGELOG entry.

- [ ] **Step 2: Run all quality gates**

```bash
uv run ruff check compman tests
uv run mypy compman
uv run pytest --cov=compman --cov-report=term-missing
```

Expected: Ruff and mypy pass and pytest reaches 100% statement and branch coverage.

- [ ] **Step 3: Build and smoke-test the Windows executable**

Build the wheel, install it into an isolated Windows virtual environment, and run the generated `compman.exe` with `-v`, `-h`, `init --scaffold`, and invalid `init --skeleton`. Use a local HTTP server fixture or test archive to confirm the built executable deploys an HTTP zip without making an external network request.

- [ ] **Step 4: Commit the combined release**

```bash
git add compman tests README.md AGENTS.md CHANGELOG.md pyproject.toml uv.lock docs/superpowers/plans
git commit -m "feat(deploy): support HTTP archive sources"
```
