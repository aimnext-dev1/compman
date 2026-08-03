# simple-example

`compman` simple Compose-file list example — Compose up without profiles.

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

For a simple setup that does not need profiles, specify `compose` as a list.
Only Compose files are passed with `-f`, without `base` or per-profile environment variables.

```yaml
compose:
  - docker-compose.yml
```

If the `compose` key is omitted entirely, it defaults to `docker-compose.yml`.

Simple mode also supports the top-level `secrets` key, which injects environment
variables from AWS Secrets Manager (same syntax as profile mode). Reference only —
running this requires a real secret:

```yaml
compman:
  name: my-app
  compose:
    - docker-compose.yml
  secrets:
    DB_URL:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: dtx/db/url
```
