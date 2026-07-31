# compman — Docker Compose Stack Manager CLI

Python CLI로 Docker/Podman Compose 스택 및 S3 기반 자동 배포를 효율적으로 관리합니다.

---

## 🛠️ Installation (설치)

### 1. 원격 원스톱 자동 설치 (자동 PATH 등록 ✨)

복잡한 PATH 설정이나 git clone 없이 터미널에서 아래 명령어 한 줄만 실행하면 **자동 설치 및 PATH 환경변수 등록**까지 일괄 처리됩니다.

```powershell
# Windows PowerShell
irm https://raw.githubusercontent.com/aimnext-dev1/compman/main/install.ps1 | iex
```

```cmd
:: Windows CMD (일반 명령 프롬프트)
curl -fsSL https://raw.githubusercontent.com/aimnext-dev1/compman/main/install.cmd -o %TEMP%\install.cmd && call %TEMP%\install.cmd
```

```bash
# Linux / macOS (Bash/Zsh)
curl -fsSL https://raw.githubusercontent.com/aimnext-dev1/compman/main/install.sh | sh
```

> ⚠️ **설치 후 반드시 터미널을 새로 열어야** PATH가 적용됩니다.  
> 설치 스크립트는 기존 pip/Python Scripts 경로에 남아있는 구버전 compman을 자동으로 제거하고, `~/.local/bin`을 User PATH 최상단에 배치합니다.

### 2. 패키지 관리자 직접 설치

```bash
# uv 사용 시 (가장 빠르고 권장)
uv tool install git+https://github.com/aimnext-dev1/compman.git

# pipx 사용 시 (자동으로 PATH 등록됨)
pipx install git+https://github.com/aimnext-dev1/compman.git
```

### 3. 로컬 소스에서 설치

```bash
uv tool install .
# 또는 개발 연결 설치: pip install -e .
```

### 4. CLI 자체 셀프 업그레이드

```bash
compman upgrade
```

---

## 🌐 Multi-Language Support (다국어 지원)

`compman`은 **영어(English)**와 **한국어(Korean)** 도움말 및 가이드 메시지를 모두 지원합니다.

### 1. 언어 조회 및 설정 명령어 (`compman lang`)
```bash
# 현재 언어 설정 및 환경변수 가이드 조회
compman lang

# 세션 언어를 한국어로 설정
compman lang ko

# 세션 언어를 영어로 설정
compman lang en
```

### 2. CLI 옵션 사용 (`--lang` / `-l`)
```bash
compman --lang ko --help
compman -l ko service --help
compman -l ko stack up
```

### 3. 환경 변수 설정 (`COMPMAN_LANG`)
```bash
# Windows PowerShell
$env:COMPMAN_LANG="ko"

# Windows CMD
set COMPMAN_LANG=ko

# Linux / macOS
export COMPMAN_LANG=ko
```

---

## 🚀 프로젝트 초기화 & 제네레이터 (`compman init`)

`compman init`을 실행하면 방향키(↑/↓) 대화형 메뉴로 3가지 초기화 모드를 제공하며, 직접 플래그로도 실행 가능합니다.

```bash
# 1. 대화형 선택 메뉴 실행 (스켈레톤 / S3 URL / 테스트 Seed)
compman init

# 2. 모드 1: 기본 compman.yml 스켈레톤 생성
compman init --skeleton

# 3. 모드 2: S3 URL로부터 패키지 수신 및 프로젝트 생성
compman init --s3 s3://my-bucket/app.tar.gz --build

# 4. 모드 3: 테스트용 Seed 프로젝트 생성 (project/ 폴더)
compman init --seed -o project -p 8080 -a
```

> 💡 **프로젝트명 자동 정규화**: 실행 디렉터리 이름이 자동으로 Docker 네이밍 규칙에 맞게 변환됩니다.  
> 예) `Desktop` → `desktop`, `My Project` → `my-project`, `Hello World!` → `hello-world`  
> `compman init`, `compman deploy`에도 동일하게 적용됩니다.

---

## 🚀 S3 배포와 컨테이너 재생성 업데이트 (`deploy` & `update`)

```bash
# 1. S3 경로 지정 첫 배포 (compman.yml에 deploy 경로 자동 저장 & project/ 소스 분리)
compman deploy --path s3://my-bucket/app.tar.gz

# 2. S3 소스 수신 + Docker 이미지 자동 빌드
compman deploy --build

# 3. S3 최신 수신 + Docker 이미지 빌드 + 컨테이너 강제 재생성
compman update
```

> `update`는 Compose `up -d --force-recreate`를 실행합니다. 단일 인스턴스 서비스에서는 중단 시간이 생길 수 있으며 롤링/무중단 배포를 보장하지 않습니다.

> 💡 **로컬 S3 에뮬레이터 (Ministack / LocalStack) 지원**: `AWS_ENDPOINT_URL_S3` 또는 `AWS_ENDPOINT_URL` 환경변수를 설정하여 로컬 S3 엔드포인트에 접속할 수 있습니다.
> ```bash
> $env:AWS_ENDPOINT_URL_S3="http://localhost:4567"
> ```

---

## ⚡ Shell 자동완성 (Tab Completion)

콘솔 터미널에서 `compman` 입력 후 `Tab` 키를 누르면 서브 커맨드(`stack`, `service`, `deploy`, `update`, `volume`, `image`, `seed`, `up`, `down`, `status` 등)가 **자동완성**됩니다.

```bash
# PowerShell 자동완성 프로필 자동 등록
compman completion powershell --install

# Bash/Zsh/Fish 자동완성 등록
compman completion bash --install
compman completion zsh --install
compman completion fish --install
```

> 💡 원스톱 설치 스크립트(`install.ps1` / `install.sh`)로 설치 시 **자동완성까지 100% 자동 등록**됩니다.

---

## ⚙️ 설정 (`compman.yml`)

```yaml
compman:
  name: my-stack
  deploy: s3://my-bucket/app.tar.gz   # compman deploy --path 실행 시 자동 기록/갱신
  dirs:
    project: project                   # S3 소스 다운로드 디렉터리 (기본값: project)
    backup: backup                     # 기본값: backup
    volume: volume                     # 기본값: volume
  compose:
    - docker-compose.yml              # 기본값: docker-compose.yml
```

- `compman.yml` 및 `docker-compose.yml`은 루트 디렉터리에 위치하며, S3 다운로드 프로젝트 소스는 `project/` 디렉터리에 분리 관리됩니다.
- `compman init` 또는 `compman deploy` 시 파일이 신규 생성되면 콘솔 화면에 생성된 YAML 내용이 자동으로 출력됩니다.
- `folder`와 `dirs.*`는 `compman.yml` 기준 상대 경로이며 프로젝트 밖으로 벗어날 수 없습니다. `backup`, `volume`, `project`는 설정 루트 자체를 지정할 수도 없습니다.
- 배포는 `dirs.project` 내부 트리를 교체합니다. 파일 교체 단계는 실패 시 롤백하지만 이후 설정 생성이나 이미지 빌드 실패까지 포함한 전체 트랜잭션은 아닙니다.

---

## 📋 주요 명령어 요약 (Commands Summary)

```text
compman seed [-o DIR] [-a] [-p PORT]    # 🌱 배포 테스트용 샘플 시드 프로젝트 생성 (.tar.gz 아카이브 지원)
compman init [-c compman.yml]           # ⚙️ compman.yml 기본 템플릿 생성 (콘솔 내용 출력)
compman update [profile]                # S3 다운로드 + 이미지 빌드 + 컨테이너 강제 재생성
compman deploy [--path S3_URI] [--build]# 🚀 S3 배포 (compman.yml 경로 자동 저장)
compman upgrade                         # 🔄 compman CLI 자체를 GitHub 최신 버전으로 셀프 업그레이드

compman stack up [profile]              # compose up -d
compman stack down --yes                # compose down (확인 옵션)
compman stack update [profile]          # compose up -d --build

compman service start [name...]         # compose start
compman service stop [name...]          # compose stop
compman service restart [name...]       # compose restart
compman service status                  # compose ps -a
compman service log [container] [-f] [-n 50] # 컨테이너 로그 조회 (기본 50줄)
compman service connect [container]          # docker exec -it (bash→sh 대화형 쉘 접속)

compman volume backup [--no-stop]       # 볼륨 백업
compman volume restore <YYYYMMDD_HHMM>  # 볼륨 복원
compman volume pull                     # 볼륨을 volume/ 로 복사
compman volume push                     # volume/ 를 컨테이너로 복사

compman image backup [--source-image]   # 이미지 백업 (기본: running container commit)
compman image restore <YYYYMMDD_HHMM>   # 이미지 복원

compman clear                           # docker image prune -af
```

> `clear`는 현재 프로젝트만이 아니라 선택된 Docker/Podman 런타임 전체의 미사용 이미지를 확인 없이 삭제합니다. 운영 호스트에서는 실행 전에 영향을 확인하세요.

---

## 🔍 Runtime & 프로젝트 구조

- **자동 감지 순서**: `docker compose` $\rightarrow$ `podman compose` $\rightarrow$ `podman-compose` $\rightarrow$ `docker-compose`
- **Podman 강제 지정**: `CONTAINER_RUNTIME=podman`

```text
compman/               # Python CLI 패키지
  cli.py               # typer entrypoint (init, deploy, update, seed, upgrade 등)
  config.py            # compman.yml loader (dirs.project, deploy)
  docker.py            # ContainerRuntime 추상화
  deploy.py            # S3 배포 및 스캐폴드 생성
  i18n.py              # 영문/한글 다국어 (i18n) 번역 모듈
  ops/                 # 비즈니스 로직 (stack, service, volume, image, seed)
tests/                 # pytest 테스트 (문장/분기 커버리지 100%)
test/                  # 실행 예제 및 E2E 가이드
```

---

## 📦 백업 파일명 규칙

백업은 `backup/` 폴더에 저장됩니다.
- 이미지: `<스택명>.image.<YYYYMMDD_HHMMSS>[_<마이크로초>].tar.gz`
- 볼륨: `<스택명>.volume.<YYYYMMDD_HHMMSS>[_<마이크로초>].tar.gz`

볼륨 복원과 push는 대상 디렉터리에 병합 복사하며, 대상에만 존재하는 오래된 파일을 삭제하지 않습니다. 이미지 복원은 이미지를 런타임에 load하지만 Compose의 image 태그를 자동 변경하지 않습니다.

## 🧪 개발 및 검증

```bash
uv sync --dev
uv run ruff check compman tests
uv run mypy compman
uv run pytest --cov=compman --cov-report=term-missing
```

현재 품질 기준과 남은 개선 백로그는 [`REVIEW.md`](REVIEW.md)를 참고하세요.
