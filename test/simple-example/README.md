# simple-example

`compman` single-profile example — Compose up without profiles.

## Structure

```
simple-example/
├── compman.yml
└── docker-compose.yml
```

## Usage

```bash
compman stack up
compman service status
compman service stop web
compman service start web
compman stack down --yes
```

## Explanation

`compose` is required and must be a mapping of profiles. A single profile
(`default`) is enough when you do not need per-environment settings. `compose`
is never a plain list; omitting it or using a list fails with a `ConfigError`.

```yaml
compose:
  default:
    file: docker-compose.yml
```

With one configured profile, commands run without a profile argument and
select it automatically.

The top-level `secrets` key is supported the same way as in multi-profile
configs: profile `env` values reference secret values with `${secrets:NAME}`
markers. Reference only — running this requires a real secret:

```yaml
compman:
  name: my-app
  compose:
    default:
      file: docker-compose.yml
      env:
        DATABASE_URL: postgres://${secrets:DB_URL}@db.example.com
  secrets:
    DB_URL:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: dtx/db/url
```
