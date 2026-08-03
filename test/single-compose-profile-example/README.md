# single-compose-profile-example

`compman` single Compose-file + profile example — manage only environment variables by profile.

## Structure

```
single-compose-profile-example/
├── compman.yml
└── docker-compose.yml
```

## Usage

```bash
compman stack up dev      # docker compose -f docker-compose.yml -p single-compose-app up -d
compman service status
compman stack down --yes

compman stack up prod     # docker compose -f docker-compose.yml -p single-compose-app up -d
compman stack down --yes
```

## Explanation

When `file` is omitted for a profile, it defaults to `docker-compose.yml`.
You can share the same Compose file while injecting different environment variables for each profile.

```yaml
compose:
  dev:
    env:
      DATABASE_URL: dev.example.com
      LOG_LEVEL: debug
  prod:
    env:
      DATABASE_URL: prod.example.com
      LOG_LEVEL: warn
```

### Secrets from AWS Secrets Manager

The top-level `secrets` key injects environment variables from AWS Secrets
Manager for the shared Compose file. It merges with the profile `env`, and the
profile value wins on a name collision. Reference only — running this requires
real credentials:

```yaml
compman:
  name: single-compose-app
  compose:
    dev:
      env:
        LOG_LEVEL: debug
    prod:
      env:
        LOG_LEVEL: warn
  secrets:
    DATABASE_URL:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: dtx/db/url
```
