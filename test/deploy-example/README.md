# deploy-example

`compman` deploy example — fetch project resources from S3 and replace them atomically.

## Behavior

Depending on the S3 path type (`compman.yml: deploy` or `--path`), replaces the contents of the **`dirs.project` directory**.

- **Prefix path** — download every object under the key while preserving its structure
  ```
  s3://<bucket>/app/
  ├── Dockerfile                 # → project/Dockerfile
  └── script/                    # → project/script/
  ```
- **Archive file** — download and extract a `.tar.gz`/`.tgz`/`.zip` object. Flatten it when it contains exactly one top-level directory.
  ```
  s3://<bucket>/app.tar.gz (contents: app/Dockerfile, app/script/)  → project/Dockerfile, project/script/
  ```

The existing managed directory contents are replaced with the new tree. Scaffolding separately creates or updates the root `compman.yml` and `docker-compose.yml`.

**Automatic scaffolding in an empty directory**: deploy creates `compman.yml` and `docker-compose.yml` when they do not exist.
```yaml
# compman.yml
compman:
  name: <cwd dirname>
  deploy: s3://<path-used>     # the next deploy works without --path
  compose:
    default:
      file: docker-compose.yml
```
```yaml
# docker-compose.yml
services:
  app:
    image: <--tag or dirname>  # matches the image built with --build
    restart: unless-stopped
```
Existing files are not overwritten. In an empty directory, you can run `compman deploy --build` followed directly by `compman stack up`.
Running containers are not touched.

## Configuration

- S3 path: the `deploy` key in `compman.yml`, or the CLI `--path` override
  ```yaml
  compman:
    deploy: s3://my-bucket/app
  ```
  ```bash
  compman deploy --path s3://my-bucket/other
  ```
- Endpoint: `AWS_ENDPOINT_URL_S3` or `AWS_ENDPOINT_URL` — real AWS when unset; the specified endpoint when set (for local ministack testing, `http://localhost:4566` when the root `docker-compose.yaml` is running)
- Credentials: standard `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_DEFAULT_REGION` env vars
- Uses boto3 (AWS CLI not required)

## Usage

```bash
compman init                        # create a single-profile compman.yml (name = cwd dirname; full options are commented)
compman deploy                     # fetch from the deploy path in compman.yml
compman deploy --path s3://...     # override the path
compman deploy --build --tag myapp # fetch, then docker build -t myapp .
```

When using `--build`, the cwd directory name is the default tag if no tag is provided.

## Caution

By default, deploy creates fetched files in **`project/`** under the current directory. A failed file swap rolls back, but a later scaffolding or Docker-build failure leaves the new source tree in place.
Running it from the repository root creates untracked files, so **run it in a scratch/target directory**.

See `test/deploy-project/` for the full test procedure.
