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
