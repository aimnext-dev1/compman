# profile-example

`compman` profile example — manage Compose files and environment variables by environment.

## Structure

```
profile-example/
├── compman.yml
├── docker-compose.local.yml
├── docker-compose.dev.yml
└── docker-compose.prod.yml
```

## Usage

```bash
# local profile (profile name only; no environment variables)
compman stack up local

# dev profile (Compose file + automatic environment-variable injection)
compman stack up dev

# prod profile
compman stack up prod

# Check status
compman service status

# Remove the stack
compman stack down --yes
```

## Explanation

Each key under `compose` in `compman.yml` is a profile name.
A `string` value specifies only a Compose file; an `object` value specifies `file` and `env` together.

```yaml
compose:
  local: docker-compose.local.yml                   # file only
  dev:
    file: docker-compose.dev.yml
    env:
      DATABASE_URL: dev.db.example.com              # automatic environment-variable injection
```

## Secrets from AWS Secrets Manager

The top-level `secrets` key injects environment variables from AWS Secrets
Manager and merges them with the profile `env` (the profile value wins on a
name collision). Reference only — running this requires real credentials:

```yaml
compman:
  name: my-app
  compose:
    base: docker-compose.yml
    dev:
      file: docker-compose.dev.yml
      env:
        DATABASE_URL: dev.db.example.com
  secrets:
    DB_PASSWORD:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: password
```
