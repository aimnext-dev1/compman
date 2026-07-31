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
```

## 사용법

```text
compman init                    # compman.yml 템플릿 생성
compman stack up [profile]      # compose up -d
compman stack down              # compose down (confirm)
compman stack update [profile]  # compose up -d --build

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

compman image backup [--source-image]   # 이미지 백업
compman image restore <YYYYMMDD_HHMM>   # 이미지 복원

compman clear                           # docker image prune -af
compman deploy [dev|prod]               # S3 배포
```

`CONTAINER_RUNTIME=podman` 환경변수로 Podman 사용 가능.

---

# dtx-docker-manager (legacy)

Shell scripts (`_script/`)와 `Makefile`로 관리하는 기존 방식. `compman`과 병행 사용 가능.

## 📁 프로젝트 구조

```text
.
├── backup/                # 볼륨 및 이미지 백업 파일 저장 (compman)
├── volume/                # 볼륨 pull/push (compman)
├── _backup/               # 볼륨 및 이미지 백업 (shell scripts)
├── _volume/               # 볼륨 pull/push (shell scripts)
├── _project/              # 실제 프로젝트 리소스 (folder 설정시)
│   └── compose/           # docker-compose 파일
├── _script/               # shell 관리 스크립트
│   ├── common.sh
│   ├── stack-*.sh
│   ├── service-*.sh
│   ├── volume-*.sh
│   └── image-*.sh
├── compman/               # Python CLI 모듈
├── deploy.sh              # S3 배포 스크립트
├── Makefile               # shell scripts 진입점
├── stack.env.example      # shell scripts 설정 예시
├── compman.yml            # compman 설정
└── README.md
```

## 초기 설정 (shell scripts)

```bash
make init          # stack.env.example → stack.env
vi stack.env        # 값 입력
```

## 기본 사용법 (shell scripts)

```bash
make up [local|dev|prod]    # 스택 생성
make down                   # 스택 제거
make status                 # 상태 조회
make volume-backup          # 볼륨 백업
make image-backup           # 이미지 백업
```

자세한 내용은 `Makefile` 참고.

---

## 백업 파일명 규칙

백업은 `backup/`(compman) 또는 `_backup/`(scripts) 폴더에 자동 저장됩니다.

- 이미지: `<스택명>.image.<YYYYMMDD_HHMM>.tar.gz`
- 볼륨: `<스택명>.volume.<YYYYMMDD_HHMM>.tar.gz`
