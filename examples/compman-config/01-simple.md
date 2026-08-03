# Case 01 — Simple mode

Single Compose file, no profiles.

## `compman.yml`

```yaml
compman:
  name: my-stack
  compose:
    - docker-compose.yml
```

The `compose` key is optional. When omitted it defaults to `docker-compose.yml`:

```yaml
compman:
  name: my-stack
```

To combine multiple Compose files, list them in order:

```yaml
compman:
  name: my-stack
  compose:
    - docker-compose.base.yml
    - docker-compose.yml
```

They are passed as `-f` options in declaration order.

## `docker-compose.yml`

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
```

## Commands

```bash
compman stack up
compman service status
compman stack down --yes
```

Simple mode rejects a profile argument (`compman stack up dev` fails).
