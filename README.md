# compman — Docker Compose Stack Manager

Python CLI로 Docker/Podman Compose 스택을 관리합니다.

## 설치

```bash
uv tool install .
compman --help
```

## 설정 (`compman.yml`)

```yaml
compman:
  name: my-stack
  # folder: my-project               # 선택: _project/ 디렉토리 사용시
  dirs:
    backup: backup                    # 선택, 기본값: backup
    volume: volume                    # 선택, 기본값: volume
  compose:
    # base: docker-compose.yml       # 선택: 모든 profile에 공통 적용
    # local: docker-compose.local.yml
    # dev:
    #   file: docker-compose.dev.yml
    #   env:
    #     DATABASE_URL: dev.example.com:5432
    # prod:
    #   file: docker-compose.prod.yml
    #   env:
    #     DATABASE_URL: prod.example.com:5432
```

`compose` 생략 시 기본값 `docker-compose.yml`. 리스트로 지정하면 단순 모드, dict로 지정하면 profile 모드.
`folder` 설정 시 compose 파일은 `_project/` 아래에서 찾습니다. `base` 설정 시 profile 파일 앞에 `-f`로 추가됩니다.

## 사용법

```text
compman init [-c compman.yml]           # compman.yml 템플릿 생성
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
compman deploy [dev|prod]               # S3 배포 (deploy.py 설정 필요)
```

모든 명령어에 `-c <path>` 옵션으로 compman.yml 경로 지정 가능.

## Runtime

- 자동 감지 순서: `docker compose` → `podman compose` → `podman-compose` → `docker-compose`
- `CONTAINER_RUNTIME=podman` 환경변수로 Podman 강제 지정

## 프로젝트 구조

```
compman/               # Python CLI 모듈
  cli.py               # click entrypoint
  config.py            # compman.yml loader
  docker.py            # ContainerRuntime 추상화
  deploy.py            # S3 배포
  ops/                 # 비즈니스 로직
    stack.py, service.py, volume.py, image.py
test/                  # 예제 config (테스트 아님)
```

## 백업 파일명 규칙

백업은 `backup/` 폴더에 저장됩니다.

- 이미지: `<스택명>.image.<YYYYMMDD_HHMM>.tar.gz`
- 볼륨: `<스택명>.volume.<YYYYMMDD_HHMM>.tar.gz`
