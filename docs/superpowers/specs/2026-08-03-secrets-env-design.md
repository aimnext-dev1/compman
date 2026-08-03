# Secrets Manager Env Injection — Design

## Goal

Let `compman.yml` pull environment variables from AWS Secrets Manager so secrets are
not hardcoded in the config file. Values are resolved lazily at compose-command time
and merged with the existing profile `env`.

## Config syntax

```yaml
compman:
  name: my-app

  compose:
    - docker-compose.yml

  # AWS Secrets Manager -> env variable injection
  secrets:
    DB_URL:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:app
      key: dtx/db/url
    DB_PASSWORD:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:app
      key: dtx/db/password
    API_KEY:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:app2
      key: api-key
```

- Top-level `compman.secrets`: mapping from env var name (alias) to a `{arn, key}` object.
- `arn`: Secrets Manager secret identifier (name or full ARN).
- `key`: JSON key inside the secret's `SecretString`.
- Dict form only; no string shorthand. `key` is required.
- Works in both simple and profile modes.
- Merge: `secrets` resolution result is combined with the profile `env`, profile `env` wins.
- System environment variables are NOT referenced here — docker compose already inherits them.

## Resolution semantics

- **Lazy**: resolved when a compose context is built (`resolve_compose_context`), not at
  config load. Read-only commands that need compose interpolation get the values too.
- **Failure**: missing secret, unresolvable region, non-JSON `SecretString`, or missing
  JSON key raises `ConfigError` with a concise message (no traceback).
- **Cache**: each secret is fetched at most once per command invocation, even when the
  same ARN feeds multiple env vars.
- Region: standard AWS credential/region chain (boto3 default). No region configured
  produces a clear error rather than a generic boto3 exception.

## Components

### `compman/config.py`

- New `SecretRef` dataclass: `arn: str`, `key: str`.
- `Config.secrets: dict[str, SecretRef]` field.
- `load_config` parses and validates `compman.secrets`: mapping required, each value a
  mapping with `arn`/`key` strings; otherwise `ConfigError`. Raw strings preserved —
  no resolution at load.

### `compman/env_source.py` (new)

- `resolve_secrets(refs: Mapping[str, SecretRef]) -> dict[str, str]`.
- Builds a boto3 `secretsmanager` client via the default session/region chain.
- For each unique ARN, calls `get_secret_value(SecretId=arn)`, caches the parsed JSON,
  then extracts each `key`.
- Error mapping to `ConfigError`:
  - `NoRegionError` -> region not configured
  - `ResourceNotFoundException` -> secret not found
  - `InvalidRequestException` / non-JSON `SecretString` / missing key -> bad secret format

### `compman/docker.py`

- `resolve_compose_context` (and profile path) resolves secrets and merges with profile
  `env` (profile wins) before building `ComposeContext`.

### `compman/diagnostics.py`

- `doctor` gains a `secrets` warning check: if `compman.secrets` is configured, verify
  AWS credentials + region are present (mirrors existing `_collect_aws`).

### `compman/i18n.py`

- en/ko messages for the new error and doctor-check output.

## Testing

- `tests/test_config.py`: valid/invalid `secrets` parsing.
- `tests/test_env_source.py`: mocked boto3 — resolution, per-command caching, error cases
  (region, not-found, non-JSON, missing key).
- `tests/test_docker.py`: secrets + profile `env` merge precedence.
- `tests/test_diagnostics.py`: secrets doctor check.

## Verification

- `uv run ruff check compman tests`
- `uv run mypy compman`
- `uv run pytest --cov=compman --cov-report=term-missing`
- `CHANGELOG.md` entry (bump to next version).
