# deploy-project

Project for testing `compman deploy` with a local ministack (S3 emulator).
A full scenario: image the seed shell program with a Dockerfile → download and build it with deploy → start the container → inspect logs → stop it.

## Structure

```
deploy-project/
├── README.md                   # test procedure documentation
└── target/                     # deploy target (gitignored; outputs retained)

docker-init/                    # ministack seeding source (repo root)
├── init-bucket.sh              # creates the bucket and automatically seeds it when ministack starts
├── seed/                       # deployment content to upload to S3 (directory version)
│   ├── Dockerfile              # images the shell program
│   └── script/
│       └── app.sh              # shell program to image (prints logs indefinitely)
└── seed.tar.gz                 # archive version (wrapped in app/ → flatten test)
```

## Prerequisites

- Docker (Compose) available
- Ministack seeds itself inside the container, so the host AWS CLI is not required.
- The seed Dockerfile normalizes `app.sh` to LF during the image build even when it is CRLF in a Windows checkout.

## Test

```powershell
# 1. Start ministack (create the bucket and automatically upload both versions inside the container)
cd C:\path\to\compman
docker compose up -d
#    s3://deploy-test/                  ← directory version (Dockerfile, script/)
#    s3://deploy-test/archives/seed.tar.gz   ← archive version (uploads docker-init/seed.tar.gz, wrapped in app/)

# 2. Run deploy from target (prefix mode, config path) → creates Dockerfile and script/
#    Automatically creates compman.yml/docker-compose.yml when absent (simple mode + recorded deploy path)
cd test/deploy-project/target
$env:AWS_ACCESS_KEY_ID="test"
$env:AWS_SECRET_ACCESS_KEY="test"
$env:AWS_DEFAULT_REGION="ap-northeast-2"
$env:AWS_ENDPOINT_URL_S3="http://localhost:4566"
uv run --project C:\path\to\compman compman deploy --build --tag deploy-e2e-app
#    → automatically creates compman.yml (name: target, deploy recorded, simple mode) and docker-compose.yml (image: deploy-e2e-app)

# 2b. Archive mode (flattened when there is one top-level directory) + automatic build
uv run --project C:\path\to\compman compman deploy --path s3://deploy-test/archives/seed.tar.gz --build --tag deploy-e2e-app

# 3. Start + status + logs + stop (the generated simple mode takes no profile argument)
uv run --project C:\path\to\compman compman stack up
uv run --project C:\path\to\compman compman service status
docker logs e2e-deploy-app-1    # verify the deploy-e2e: hello output
uv run --project C:\path\to\compman compman stack down --yes

# 4. Environment injection test (profile mode) — extend the generated compman.yml:
# compman:
#   name: deploy-e2e
#   deploy: s3://deploy-test
#   compose:
#     dev:
#       file: docker-compose.yml
#       env:
#         MESSAGE: hello-from-dev
# After adding environment: - MESSAGE=${MESSAGE} to app in docker-compose.yml:
# uv run --project C:\path\to\compman compman stack up dev
# docker logs deploy-e2e-app-1   # verify deploy-e2e: hello-from-dev
# uv run --project C:\path\to\compman compman stack down --yes
#
# 4b. Secrets from AWS Secrets Manager (reference only — needs a real secret):
# Add to compman.yml:
#   secrets:
#     MESSAGE:
#       arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:app
#       key: message
# The secret value is fetched at compose-command time and merged with the
# profile env (profile wins on a collision).
# ```


## init

`compman init` creates a simple compman.yml whose name is the cwd directory name (full options are commented).

```powershell
compman init    # create compman.yml (compose: - docker-compose.yml + comments)
```

## Cleanup

- Bucket/objects: `S3_PERSIST=0` makes them disappear automatically when the container restarts; the init script reseeds them.
- target/ contents: gitignored, with outputs retained (removed only by manual deletion)
