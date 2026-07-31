# compman — Docker Compose Stack Manager CLI

Python CLI로 Docker/Podman Compose 스택 및 S3 기반 자동 배포를 효율적으로 관리합니다.

---

## 🛠️ Installation (설치)

### 1. GitHub 원격 한 줄 설치 (권장 ✨)

`uv` 또는 `pipx`가 설치된 임의의 컴퓨터에서 git clone 없이 단 한 줄로 설치하여 사용할 수 있습니다.

```bash
# uv 사용 시 (가장 빠르고 권장)
uv tool install git+https://github.com/aimnext-dev1/compman.git

# pipx 사용 시
pipx install git+https://github.com/aimnext-dev1/compman.git

# pip 사용 시
pip install git+https://github.com/aimnext-dev1/compman.git
```

### 2. 로컬 소스에서 설치

```bash
uv tool install .
# 또는 개발 연결 설치: pip install -e .
```

### 3. 최신 기능 버전 업데이트

```bash
uv tool upgrade compman
```

---

## 🚀 S3 배포 & 단독 업데이트 (`deploy` & `update`)

```bash
# 1. S3 경로 지정 첫 배포 (compman.yml에 deploy 경로 자동 저장 & project/ 소스 분리)
compman deploy --path s3://my-bucket/app.tar.gz

# 2. S3 소스 수신 + Docker 이미지 자동 빌드
compman deploy --build

# 3. ⭐ 단 한 줄로 S3 최신 수신 + Docker 이미지 빌드 + 무중단 컨테이너 교체 기동
compman update
```

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

---

## 📋 주요 명령어 (Commands)

```text
compman init [-c compman.yml]           # compman.yml 템플릿 생성
compman update [profile]                # ⭐ S3 최신 다운로드 + 이미지 빌드 + 컨테이너 무중단 교체
compman deploy [--path S3_URI] [--build]# S3 배포 (compman.yml 경로 자동 저장)

compman stack up [profile]              # compose up -d
compman stack down --yes                # compose down (확인 필요)
compman stack update [profile]          # compose up -d --build

compman service start [name...]         # compose start
compman service stop [name...]          # compose stop
compman service restart [name...]       # compose restart
compman service status                  # compose ps -a
compman service log [name]              # docker logs -f -n 10000
compman service connect [name]          # docker exec -it (bash→sh)

compman volume backup [--no-stop]       # 볼륨 백업
compman volume restore <YYYYMMDD_HHMM>  # 볼륨 복원
compman volume pull                     # 볼륨을 volume/ 로 복사
compman volume push                     # volume/ 를 컨테이너로 복사

compman image backup [--source-image]   # 이미지 백업 (기본: running container commit)
compman image restore <YYYYMMDD_HHMM>   # 이미지 복원

compman clear                           # docker image prune -af
```

---

## 🔍 Runtime & 프로젝트 구조

- **자동 감지 순서**: `docker compose` $\rightarrow$ `podman compose` $\rightarrow$ `podman-compose` $\rightarrow$ `docker-compose`
- **Podman 강제 지정**: `CONTAINER_RUNTIME=podman`

```text
compman/               # Python CLI 모듈
  cli.py               # click entrypoint (init, deploy, update, clear 등)
  config.py            # compman.yml loader (dirs.project, deploy)
  docker.py            # ContainerRuntime 추상화
  deploy.py            # S3 배포 및 _update_compman_deploy
  ops/                 # 비즈니스 로직 (stack, service, volume, image)
test/                  # 테스트 및 가이드 문서 (FULL_SCENARIO_GUIDE.md)
```

---

## 📦 백업 파일명 규칙

백업은 `backup/` 폴더에 저장됩니다.
- 이미지: `<스택명>.image.<YYYYMMDD_HHMM>.tar.gz`
- 볼륨: `<스택명>.volume.<YYYYMMDD_HHMM>.tar.gz`
