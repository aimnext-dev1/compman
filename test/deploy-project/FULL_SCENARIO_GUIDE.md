# compman Deploy & Stack E2E Full Scenario Guide

`compman` CLI를 사용하여 S3 프로젝트 배포, `compman.yml` 자동 갱신, `project/` 디렉터리 소스 분리, Docker 이미지 빌드, 스택 기동 및 단독 명령어(`compman update`)를 통한 최신 버전 무중단 교체 배포까지 전체 시나리오를 단계별로 설명하는 가이드 문서입니다.

---

## 📋 사전 환경 구성 (Environment Setup)

테스트 및 실동작에 필요한 S3 인증 및 에뮬레이터(ministack) 환경변수를 설정합니다.

```bash
# Windows PowerShell
$env:AWS_ACCESS_KEY_ID="test"
$env:AWS_SECRET_ACCESS_KEY="test"
$env:AWS_DEFAULT_REGION="ap-northeast-2"
$env:COMPMAN_S3_ENDPOINT="http://localhost:4567"

# Linux / macOS
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="ap-northeast-2"
export COMPMAN_S3_ENDPOINT="http://localhost:4567"
```

---

## 🚀 8단계 풀 시나리오 가이드 (Full Scenario Steps)

### Step 1. 테스트 작업 디렉터리 생성 및 이동
새로운 프로젝트 디렉터리를 생성하고 이동합니다.

```bash
mkdir -p test/deploy-project/target/e2e-scenario-test
cd test/deploy-project/target/e2e-scenario-test
```

---

### Step 2. S3 경로를 지정하여 첫 배포 (`--path`)
S3 버킷 경로를 전달받아 첫 배포를 실행합니다.

```bash
compman deploy --path s3://deploy-test
```

- **출력 결과**: `Created compman.yml`, `Created docker-compose.yml`, `Deploy done.`
- **구조 특징**:
  - 루트 디렉터리: `compman.yml`, `docker-compose.yml`
  - 하위 디렉터리 (`project/`): S3 소스 파일 (`Dockerfile`, `script/` 등)
- **`compman.yml` 상태**:
  ```yaml
  compman:
    name: e2e-scenario-test
    deploy: s3://deploy-test
    dirs:
      project: project
    compose:
      - docker-compose.yml
  ```

---

### Step 3. 다른 S3 경로로 배포 경로 갱신 (`--path` 갱신)
아카이브 파일 경로로 변경하여 배포를 수행하고 `compman.yml`의 `deploy` 경로 갱신을 확인합니다.

```bash
compman deploy --path s3://deploy-test/archives/seed.tar.gz
```

- **출력 결과**: `Updated deploy in compman.yml (s3://deploy-test/archives/seed.tar.gz)`, `Deploy done.`
- **`compman.yml` 상태**: `deploy` 속성이 `s3://deploy-test/archives/seed.tar.gz`로 자동 갱신됩니다.
- **특징**: `project/` 디렉터리가 깔끔하게 비워진 후 아카이브 내용만 압축 해제됩니다.

---

### Step 4. `--path` 옵션 없이 재배포
`compman.yml`에 기록된 경로를 통해 `--path` 없이 간단히 배포합니다.

```bash
compman deploy
```

- **출력 결과**: `Deploy done.`
- **특징**: `compman.yml`의 최신 `deploy` 경로를 자동으로 인식하여 배포됩니다.

---

### Step 5. 소스 다운로드 + Docker 이미지 자동 빌드 (`--build`)
S3 소스를 다운로드하고 `project/Dockerfile`을 기반으로 Docker 이미지를 빌드합니다.

```bash
compman deploy --build
```

- **출력 결과**: `Building image 'e2e-scenario-test' in project...`, `Deploy done.`
- **생성 이미지**: `e2e-scenario-test:latest`

---

### Step 6. 컨테이너 스택 기동 및 서비스 상태 확인
빌드된 이미지를 기반으로 Docker 컨테이너를 기동하고 웹 서비스를 확인합니다.

```bash
# 1. 스택 백그라운드 기동
compman stack up

# 2. 서비스 기동 상태 및 포트 바인딩 확인
compman service status

# 3. HTTP 웹 데몬 응답 확인 (포트 18080)
curl http://localhost:18080
```

- **상태 확인**: `0.0.0.0:18080->18080/tcp` 포트 바인딩 확인 및 웹 응답 수신.

---

### Step 7. ⭐ 단독 명령어 한 줄로 최신 버전 무중단 교체 배포 (`compman update`)
젠킨스에서 S3로 신규 빌드 아티팩트를 올린 후, 서버에서 **단 한 번의 명령어**로 S3 최신 소스 수신 $\rightarrow$ 이미지 재빌드 $\rightarrow$ 기존 컨테이너 무중단 교체 기동(Recreate)을 모두 수행합니다.

```bash
compman update
```

- **실행 결과**:
  ```text
  Building image 'e2e-scenario-test' in project...
  Deploy done.
  Container e2e-scenario-test-app-1 Recreate
  Container e2e-scenario-test-app-1 Recreated
  Container e2e-scenario-test-app-1 Starting
  Container e2e-scenario-test-app-1 Started
  ```
- **특징**: 아무런 인자나 플래그 없이 단 한 줄의 커맨드로 최신 버전 교체 기동 완료!

---

### Step 8. 스택 정돈 및 제거
테스트 완료 후 기동된 컨테이너 및 네트워크 스택을 정돈합니다.

```bash
compman stack down --yes
```

- **결과**: `Container Stopped`, `Container Removed`, `Network Removed`.

---

## 📌 핵심 정리 (Key Takeaways)

| 구 분 | 명령어 | 핵심 동작 |
| :--- | :--- | :--- |
| **단독 최신 업데이트 (추천 ✨)** | **`compman update`** | **인자 없이 한 줄로 S3 최신 다운로드 + 이미지 빌드 + 기존 컨테이너 무중단 교체 기동** |
| **기본 배포** | `compman deploy --path <S3_URI>` | S3 소스를 `project/`에 다운로드 + `compman.yml`에 `deploy` 경로 자동 기록 |
| **경로 재사용** | `compman deploy` | `compman.yml`의 최신 `deploy` 경로를 참조하여 자동 배포 |
| **배포 + 빌드** | `compman deploy --build` | S3 다운로드 + `project/Dockerfile` 기반 Docker 이미지 자동 빌드 |
| **스택 기동** | `compman stack up` | 루트 `docker-compose.yml` 기반 컨테이너 기동 (이미지 변경 시 Recreate) |
| **스택 종료** | `compman stack down --yes` | 기동된 컨테이너 및 네트워크 안전 정돈 |
