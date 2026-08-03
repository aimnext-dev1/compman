# Case 06 — AWS Secrets Manager injection

Inject environment variables from AWS Secrets Manager so secrets never live in
`compman.yml`. This case is simple mode.

## `compman.yml`

```yaml
compman:
  name: my-stack
  compose:
    - docker-compose.yml
  secrets:
    DB_URL:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: dtx/db/url
    DB_PASSWORD:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: dtx/db/password
```

- Each entry maps an env var name to `{ arn, key }`.
- `key` names a JSON key inside the secret's `SecretString`; slash keys like
  `dtx/db/url` are supported.
- The same ARN is fetched once per command invocation.

## Secret shape

The `db` secret's `SecretString` is JSON:

```json
{
  "dtx/db/url": "db.example.com",
  "dtx/db/password": "s3cret"
}
```

## `docker-compose.yml`

Consume the injected values with `${VAR}` interpolation:

```yaml
services:
  app:
    image: my-app
    environment:
      - DB_URL=${DB_URL}
      - DB_PASSWORD=${DB_PASSWORD}
```

## Credentials

Use the standard AWS environment variables; `compman doctor` warns when secrets
are configured but credentials or region are missing.

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="ap-northeast-2"
```

## Commands

```bash
compman stack up
```

A missing secret, unresolvable region, non-JSON body, or missing `key` fails
the command with a clear error before compose runs.
