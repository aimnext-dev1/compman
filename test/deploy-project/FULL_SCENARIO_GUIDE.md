# compman Deploy & Stack E2E Full Scenario Guide

This guide covers S3 project deployment with the `compman` CLI, automatic `compman.yml` updates, separating source into the `project/` directory, building Docker images, starting the stack, and recreating containers through `compman update`.

---

## 📋 Environment Setup

Set the environment variables for the S3 credentials and emulator (ministack) needed for testing and operation.

```bash
# Windows PowerShell
$env:AWS_ACCESS_KEY_ID="test"
$env:AWS_SECRET_ACCESS_KEY="test"
$env:AWS_DEFAULT_REGION="ap-northeast-2"
$env:AWS_ENDPOINT_URL_S3="http://localhost:4566"

# Linux / macOS
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="ap-northeast-2"
export AWS_ENDPOINT_URL_S3="http://localhost:4566"
```

---

## 🚀 Eight-Step Full Scenario Guide

### Step 1. Create and enter a test working directory
Create and enter a new project directory.

```bash
mkdir -p test/deploy-project/target/e2e-scenario-test
cd test/deploy-project/target/e2e-scenario-test
```

---

### Step 2. First deployment with an S3 path (`--path`)
Pass the S3 bucket path and run the first deployment.

```bash
compman deploy --path s3://deploy-test
```

- **Output**: `Created compman.yml`, `Created docker-compose.yml`, `Deploy done.`
- **Structure**:
  - Root directory: `compman.yml`, `docker-compose.yml`
  - Subdirectory (`project/`): S3 source files (`Dockerfile`, `script/`, and so on)
- **`compman.yml` state**:
  ```yaml
  compman:
    name: e2e-scenario-test
    deploy: s3://deploy-test
    dirs:
      project: project
    compose:
      default:
        file: docker-compose.yml
  ```

---

### Step 3. Update the deployment path to another S3 path (update `--path`)
Deploy from an archive path and confirm that the `deploy` path in `compman.yml` is updated.

```bash
compman deploy --path s3://deploy-test/archives/seed.tar.gz
```

- **Output**: `Updated deploy in compman.yml (s3://deploy-test/archives/seed.tar.gz)`, `Deploy done.`
- **`compman.yml` state**: the `deploy` property is automatically updated to `s3://deploy-test/archives/seed.tar.gz`.
- **Behavior**: the `project/` directory is cleanly emptied, then only the archive contents are extracted.

---

### Step 4. Redeploy without the `--path` option
Deploy simply without `--path` by using the path recorded in `compman.yml`.

```bash
compman deploy
```

- **Output**: `Deploy done.`
- **Behavior**: deployment automatically uses the latest `deploy` path in `compman.yml`.

---

### Step 5. Download source + automatically build the Docker image (`--build`)
Download S3 source and build a Docker image based on `project/Dockerfile`.

```bash
compman deploy --build
```

- **Output**: `Building image 'e2e-scenario-test' in project...`, `Deploy done.`
- **Created image**: `e2e-scenario-test:latest`

---

### Step 6. Start the container stack and check service status
Start Docker containers from the built image and verify the web service.

```bash
# 1. Start the stack in the background
compman stack up

# 2. Check service status and port binding
compman service status

# 3. Check the HTTP web-daemon response (port 18080)
curl http://localhost:18080
```

- **Status check**: verify the `0.0.0.0:18080->18080/tcp` port binding and receive the web response.

---

### Step 7. Redeploy the latest version with a single command (`compman update`)
After Jenkins uploads a new build artifact to S3, the server receives the latest S3 source $\rightarrow$ rebuilds the image $\rightarrow$ force-recreates the existing container. Single-instance deployments may have downtime.

```bash
compman update
```

- **Result**:
  ```text
  Building image 'e2e-scenario-test' in project...
  Deploy done.
  Container e2e-scenario-test-app-1 Recreate
  Container e2e-scenario-test-app-1 Recreated
  Container e2e-scenario-test-app-1 Starting
  Container e2e-scenario-test-app-1 Started
  ```
- **Behavior**: the latest version is replaced and started with one command and no arguments or flags.

---

### Step 8. Clean up and remove the stack
After testing, clean up the running containers and network stack.

```bash
compman stack down --yes
```

- **Result**: `Container Stopped`, `Container Removed`, `Network Removed`.

---

## 🔐 Injecting Environment Variables from AWS Secrets Manager

compman can inject environment variables from AWS Secrets Manager for any compose
context via the top-level `secrets` key. Secrets are referenced with
`${secrets:NAME}` markers inside profile `env` values. Reference only —
ministack does not emulate Secrets Manager, so run this against real AWS.

```yaml
compman:
  name: my-app
  compose:
    default:
      file: docker-compose.yml
      env:
        DATABASE_URL: postgres://${secrets:DATABASE_URL}@db.example.com
  secrets:
    DATABASE_URL:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: dtx/db/url
    DB_PASSWORD:
      arn: arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db
      key: dtx/db/password
```

- Each entry maps a marker name to `{ arn, key }`. At compose-command time the
  secret's JSON `SecretString` is fetched and the referenced `key`'s value is
  substituted into `${secrets:NAME}` markers.
- The same ARN is fetched once per command invocation.
- A profile `secrets` block merges over the top-level one (profile wins on a
  name clash). Secrets are never passed to compose as standalone variables.
- Credentials and region use the standard AWS environment variables
  (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`).

---

## 📌 Key Takeaways

| Category | Command | Core behavior |
| :--- | :--- | :--- |
| **Standalone latest update** | **`compman update`** | **Download the latest S3 source + build the image + force-recreate existing containers** |
| **Basic deployment** | `compman deploy --path <S3_URI>` | Download S3 source to `project/` + automatically record the `deploy` path in `compman.yml` |
| **Reuse path** | `compman deploy` | Automatically deploy using the latest `deploy` path in `compman.yml` |
| **Deploy + build** | `compman deploy --build` | Download from S3 + automatically build a Docker image based on `project/Dockerfile` |
| **Start stack** | `compman stack up` | Start containers based on the root `docker-compose.yml` (recreate when the image changes) |
| **Stop stack** | `compman stack down --yes` | Safely clean up running containers and networks |
| **Secrets injection** | `compman.secrets` in `compman.yml` | Inject env vars from AWS Secrets Manager at compose-command time via `${secrets:NAME}` markers; profile `secrets` overrides top-level |
