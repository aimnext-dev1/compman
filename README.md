# dtx-docker-manager

# Docker Stack Management Template 🐳

이 프로젝트는 `Docker Compose` 스택을 손쉽게 **배포/관리/백업/복원**할 수 있도록 구성된 템플릿입니다.  
직관적인 `Makefile` 명령어와 기능별로 분리된 스크립트(`_script/`)를 통해 **로컬 개발환경부터 운영환경까지 손쉽게 관리**할 수 있습니다.

---

## 📁 프로젝트 구조
```text
.
├── _backup/               # 볼륨 및 이미지 백업 파일 저장
├── _project/              # 실제 프로젝트 리소스 (코드, 설정 등)
├── _script/               # 모든 관리용 스크립트 파일
│   ├── common.sh               # 공통 기능 
│   ├── image-backup.sh         # 이미지 백업 
│   ├── image-restore.sh        # 이미지 복원 
│   ├── service-connect.sh      # 컨테이너 접속 
│   ├── service-log.sh          # 컨테이너 로그 출력
│   ├── service-restart.sh      # 컨테이너 재시작
│   ├── service-start.sh        # 컨테이너 시작
│   ├── service-status.sh       # 컨테이너 상태 확인
│   ├── service-stop.sh         # 컨테이너 중지
│   ├── stack-down.sh           # 스택 제거
│   ├── stack-up.sh             # 스택 생성
│   ├── volume-backup.sh        # 볼륨 백업
│   ├── volume-pull.sh          # 볼륨 다운로드
│   ├── volume-push.sh          # 볼륨 업로드
│   └── volume-restore.sh       # 볼륨 복원
├── deploy.sh              # 배포 자동화용 스크립트 (선택)
├── Makefile               # 주요 명령어 집약
├── stack.env.example      # 스택 설정 예시 (복사해서 stack.env로 사용)
└── README.md
```

---
## 🙌 사용에 앞서

### 사용 요건
* Docker CLI / Docker Compose(docker-compose) 필요
* Bash 쉘 필요
* jq(JSON 파싱용) 필요

### 초기 설정 (stack.env)
_script 내부 파일을 직접 수정할 필요 없이, 프로젝트 루트의 `stack.env` 파일 하나만 채우면 됩니다.

```bash
make init          # stack.env.example을 복사해 stack.env 생성 (최초 1회)
vi stack.env        # 값 입력
```

`stack.env`에 채워야 할 값:
```text
FOLDER_NAME          # _project 폴더 확인 메시지에 표시할 임의의 식별용 이름
STACK_NAME           # docker compose 프로젝트명(-p) / 백업 파일명 접두사

COMPOSE_FILE_LOCAL    # 로컬환경 도커 컴포즈 명세파일명 (_project/compose 기준)
COMPOSE_FILE_DEV      # 개발환경 도커 컴포즈 명세파일명
COMPOSE_FILE_PROD     # 운영환경 도커 컴포즈 명세파일명

ENV_FILE_LOCAL        # (선택) 로컬환경 환경변수 파일 경로
ENV_FILE_DEV          # (선택) 개발환경 환경변수 파일 경로
ENV_FILE_PROD         # (선택) 운영환경 환경변수 파일 경로
```

> `stack.env`는 `.gitignore`에 포함되어 있어 커밋되지 않으며, `deploy.sh`가 `_script`를 재배포해도 값이 보존됩니다.

---

## 🛠️ 기본 사용법

### 🔹 스택 실행 / 제거

```bash
make up [환경]       # ex) make up local
make down
```

### 🔹 서비스 제어
```bash
make start <서비스명(선택)>       # 비워놓을 경우 전체 시작
make stop <서비스명(선택)>        # 비워놓을 경우 전체 중지
make restart <서비스명(선택)>     # 비워놓을 경우 전체 재시작
make status
make log <서비스명>
make connect <서비스명>
```

### 🔹 백업 / 복원
```bash
make volume-backup
make volume-restore <백업시간>   # 예: make volume-restore 20250331_1325

make image-backup
make image-restore <백업시간>    # 예: make image-restore 20250331_1325
```

### 🔹 볼륨 변경사항 적용
```bash
make volume-pull
# 다운로드 받은 폴더 위치에 변경사항을 적용 
# ...
make volume-push
```

### 🔹 기타
```bash
make clear          # 미사용 이미지/컨테이너/볼륨 정리
make help           # 명령어 도움말 출력
```

## 🧩 백업 파일명 규칙

백업은 _backup/ 폴더에 자동 저장되며, 다음 규칙으로 이름이 생성됩니다:

### 이미지 백업
> <스택이름>.image.<백업날짜_시간>.tar.gz
> 예: iot-db.20250331_1325.tar.gz

### 볼륨 백업
> <스택이름>.volume.<백업날짜_시간>.tar.gz
> 예: iot-db.volume.20250331_1325.tar.gz

## 🧪 예시
```bash
make init
# stack.env 값 입력 후
make up local
make status
make volume-backup
make volume-restore 20250331_1325
```