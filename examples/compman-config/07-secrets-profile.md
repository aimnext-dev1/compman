# Case 07 — Secrets combined with profiles

`secrets` works in profile mode too. The resolved secret values merge with the
profile `env`; on a name collision the **profile value wins**.

## `compman.yml`

```yaml
compman:
  name: my-stack
  compose:
    base: docker-compose.yml
    dev:
      file: docker-compose.dev.yml
      env:
        LOG_LEVEL: debug
    prod:
      file: docker-compose.prod.yml
      env:
        LOG_LEVEL: warn
  secrets:
    DATABASE_URL:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: dtx/db/url
    DB_PASSWORD:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: dtx/db/password
```

Both profiles receive `DATABASE_URL` and `DB_PASSWORD` from Secrets Manager,
plus their own `LOG_LEVEL`. The profile `env` never overrides secrets here
because the names do not collide.

## Overriding a secret from a profile

Set the same env var name in a profile `env` to replace the secret value for
that profile only:

```yaml
compman:
  name: my-stack
  compose:
    dev:
      file: docker-compose.dev.yml
      env:
        DB_PASSWORD: dev-only-password   # wins over the secret for dev
    prod:
      file: docker-compose.prod.yml
  secrets:
    DB_PASSWORD:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: dtx/db/password
```

## `docker-compose.yml`

```yaml
services:
  app:
    image: my-app
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DB_PASSWORD=${DB_PASSWORD}
      - LOG_LEVEL=${LOG_LEVEL}
```

## Commands

```bash
compman stack up dev
compman stack up prod
```

## Resolution order

1. Secrets are fetched from AWS Secrets Manager (once per ARN per command).
2. The profile `env` is merged on top; a profile value overrides a secret of
   the same name.
3. Host environment variables pass through to docker compose as usual.
