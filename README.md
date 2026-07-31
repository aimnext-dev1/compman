# compman — Docker Compose Stack Manager CLI

`compman`은 Docker 또는 Podman Compose 스택의 실행, 서비스 관리, 볼륨·이미지 백업과 S3 기반 배포를 하나의 CLI로 관리합니다.

## 주요 기능

- Docker Compose, Podman Compose 런타임 자동 감지
- 단일 Compose 파일과 환경별 프로필 구성 지원
- S3 prefix 또는 `.tar.gz`/`.tgz`/`.zip` 아카이브 배포
- 빈 디렉터리 배포 시 `compman.yml`과 `docker-compose.yml` 자동 생성
- 볼륨과 컨테이너 이미지의 타임스탬프 백업·복원
- 한국어·영어 도움말 및 셸 자동완성
- Windows, Linux, macOS 지원

## 요구사항

- Python 3.10 이상
- Docker Compose 또는 Podman Compose
- S3 배포 사용 시 접근 가능한 S3 호환 스토리지와 AWS 자격 증명

CI에서는 Python 3.10–3.13을 Ubuntu, macOS, Windows에서 검증합니다. Python 3.14 지원 계획과 업그레이드 판단은 [REVIEW.md](REVIEW.md)의 `Python version strategy`를 참고하세요.

## 설치

### 자동 설치

```powershell
# Windows PowerShell
irm https://raw.githubusercontent.com/aimnext-dev1/compman/main/install.ps1 | iex
```

```cmd
:: Windows CMD
curl -fsSL https://raw.githubusercontent.com/aimnext-dev1/compman/main/install.cmd -o %TEMP%\install.cmd && call %TEMP%\install.cmd
```

```bash
# Linux / macOS
curl -fsSL https://raw.githubusercontent.com/aimnext-dev1/compman/main/install.sh | sh
```

새 터미널을 연 뒤 설치를 확인합니다.

```bash
compman --version
compman --help
```

### uv 또는 pipx로 설치

```bash
uv tool install git+https://github.com/aimnext-dev1/compman.git
# 또는
pipx install git+https://github.com/aimnext-dev1/compman.git
```

저장소에서 개발 버전을 설치하려면 다음 명령을 사용합니다.

```bash
uv tool install .
```

설치된 CLI는 다음 명령으로 최신 `main` 버전으로 갱신할 수 있습니다.

```bash
compman upgrade
```

## 빠른 시작

### 기존 Compose 프로젝트

```bash
cd my-project
compman init --skeleton
compman stack up
compman service status
compman stack down --yes
```

`compman init`만 실행하면 다음 세 가지 모드를 고르는 대화형 메뉴가 표시됩니다.

```bash
compman init --skeleton                         # compman.yml 생성
compman init --s3 s3://bucket/app.tar.gz --build
compman init --seed -o project -p 18080         # 테스트 프로젝트 생성
compman init --seed -o project -a               # 테스트 프로젝트와 아카이브 생성
```

기존 파일 덮어쓰기는 `--force`를 명시해야 합니다.

### S3에서 새 프로젝트 배포

빈 작업 디렉터리에서 실행합니다.

```bash
mkdir my-app && cd my-app
compman deploy --path s3://my-bucket/releases/app.tar.gz --build --tag my-app
compman stack up
```

배포 성공 시 다음 파일 구조가 만들어집니다.

```text
my-app/
├── compman.yml
├── docker-compose.yml
└── project/              # S3에서 받은 애플리케이션 소스
```

S3 경로는 다음 두 형식을 지원합니다.

- Prefix: 경로 아래 객체를 재귀적으로 내려받고 디렉터리 구조를 보존합니다.
- Archive: `.tar.gz`, `.tgz`, `.zip`을 안전하게 추출하며 단일 최상위 폴더는 자동으로 평탄화합니다.

동일한 이름의 배포 대상만 교체되며 다른 사용자 파일은 유지됩니다. 소스 교체 단계가 실패하면 이전 트리를 복구하지만, 이후 스캐폴드 생성이나 이미지 빌드까지 포함한 완전한 트랜잭션은 아직 보장하지 않습니다.

## 설정 파일

모든 설정은 `compman.yml`의 `compman` 키 아래에 둡니다.

### 단일 Compose 구성

```yaml
compman:
  name: my-stack
  compose:
    - docker-compose.yml
```

`compose`를 생략하면 `docker-compose.yml`을 사용합니다. 여러 파일을 나열하면 선언 순서대로 `-f` 옵션에 전달합니다.

### 환경별 프로필 구성

```yaml
compman:
  name: my-stack
  compose:
    base: docker-compose.yml
    local: docker-compose.local.yml
    dev:
      file: docker-compose.dev.yml
      env:
        DATABASE_URL: dev.db.example.com
        LOG_LEVEL: debug
    prod:
      file: docker-compose.prod.yml
      env:
        DATABASE_URL: prod.db.example.com
```

프로필의 `file`은 선택 사항입니다. 생략하면 `base`, `base`도 없으면 `docker-compose.yml`을 사용하므로 하나의 Compose 파일에 환경 변수만 다르게 적용할 수 있습니다.

```bash
compman stack up dev
compman service status --profile dev
compman stack down --profile dev --yes
```

### 배포 및 관리 디렉터리

```yaml
compman:
  name: my-stack
  deploy: s3://my-bucket/releases/app.tar.gz
  folder: compose
  dirs:
    project: project
    backup: backup
    volume: volume
  compose:
    - docker-compose.yml
```

- `folder`: Compose 파일 기준 하위 디렉터리
- `dirs.project`: S3 배포 소스를 배치할 하위 디렉터리
- `dirs.backup`: 백업 아카이브 저장 디렉터리
- `dirs.volume`: 호스트와 볼륨 데이터를 주고받는 디렉터리
- `deploy`: `compman deploy`와 `compman update`에서 사용할 기본 S3 경로

관리 경로는 `compman.yml`이 있는 디렉터리 밖으로 벗어날 수 없습니다. `--path`는 설정된 `deploy` 값을 한 번만 재정의합니다.

## 명령어

```text
compman init [--skeleton | --s3 URI | --seed]
compman deploy [--path S3_URI] [--build] [--tag TAG]
compman update [PROFILE]
compman upgrade
compman version
compman lang [ko|en]
compman completion [powershell|bash|zsh|fish] --install

compman stack up [PROFILE]
compman stack update [PROFILE]
compman stack down [--profile PROFILE] --yes

compman service start [SERVICE...] [--profile PROFILE]
compman service stop [SERVICE...] [--profile PROFILE]
compman service restart [SERVICE...] [--profile PROFILE]
compman service status [--profile PROFILE]
compman service log [CONTAINER] [-f] [-n 50] [--profile PROFILE]
compman service connect [CONTAINER] [--profile PROFILE]

compman volume backup [--no-stop] [--profile PROFILE]
compman volume restore [TIMESTAMP] [--no-stop] [--profile PROFILE]
compman volume pull [--profile PROFILE]
compman volume push [--profile PROFILE]

compman image backup [--source-image] [--profile PROFILE]
compman image restore [TIMESTAMP] [--profile PROFILE]

compman clear
```

각 명령의 전체 옵션은 `compman <명령> --help`로 확인할 수 있습니다.

### 동작상 주의점

- `update`: `deploy`가 있으면 S3 수신 → 이미지 빌드 → 스택 실행을 수행하고, 없으면 로컬 Compose를 `up -d --build`로 갱신합니다.
- `service log`: 기본 50줄을 표시하며 `-f`로 스트리밍합니다.
- `service connect`: `bash` 접속 실패 시 `sh`를 사용합니다.
- `volume backup/restore`: 기본적으로 작업 중 스택을 내렸다가 복구합니다. `--no-stop`은 정합성 위험을 이해한 경우에만 사용하세요.
- `image backup`: 기본값은 실행 중 컨테이너 상태를 commit한 뒤 저장합니다. 원본 이미지를 저장하려면 `--source-image`를 사용합니다.
- `clear`: 선택한 런타임 전체에 `image prune -af`를 실행하므로 현재 프로젝트 밖의 미사용 이미지도 삭제할 수 있습니다.

## 백업과 복원

백업 파일은 `dirs.backup`에 저장됩니다.

```text
<stack>.volume.<YYYYMMDD_HHMMSS>[_<microseconds>].tar.gz
<stack>.image.<YYYYMMDD_HHMMSS>[_<microseconds>].tar.gz
```

타임스탬프를 생략하고 복원을 실행하면 사용 가능한 백업을 대화형으로 선택합니다. 볼륨 복원과 `volume push`는 대상에 데이터를 병합하며 대상에만 있던 파일을 삭제하지 않습니다. 이미지 복원은 이미지를 런타임에 load하지만 Compose의 `image` 태그를 자동 변경하지 않습니다.

## 런타임 선택

자동 감지 순서는 다음과 같습니다.

```text
docker compose → podman compose → podman-compose → docker-compose
```

Podman을 우선 사용하려면 환경 변수를 지정합니다.

```bash
export CONTAINER_RUNTIME=podman
# PowerShell: $env:CONTAINER_RUNTIME="podman"
```

## S3 호환 스토리지

AWS SDK 표준 환경 변수를 사용합니다.

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=ap-northeast-2
export AWS_ENDPOINT_URL_S3=http://localhost:4567   # Ministack/LocalStack 등에서 선택
```

`AWS_ENDPOINT_URL_S3`이 없으면 `AWS_ENDPOINT_URL`도 사용할 수 있습니다.

## 언어와 자동완성

```bash
compman lang ko                    # 현재 프로세스 기본 언어 설정
compman --lang en --help           # 이번 호출만 영어 사용
export COMPMAN_LANG=ko             # 셸 환경에서 기본 언어 설정

compman completion powershell --install
compman completion bash --install
compman completion zsh --install
compman completion fish --install
```

## 개발 및 검증

```bash
uv sync --dev
uv run ruff check compman tests
uv run mypy compman
uv run pytest --cov=compman --cov-report=term-missing
```

CI는 다음 항목을 검증합니다.

- Ubuntu, macOS, Windows × Python 3.10–3.13 테스트
- 문장·분기 커버리지 100%
- Ruff 및 mypy
- wheel 빌드, 격리 설치, CLI 실행
- Ministack S3 수신, Docker 이미지 빌드, Compose 실행·종료 E2E

현재 제약과 개선 백로그는 [REVIEW.md](REVIEW.md), 테스트 프로젝트 사용법은 [`test/`](test/) 아래의 각 README를 참고하세요.
