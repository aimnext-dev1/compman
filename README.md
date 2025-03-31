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
│   ├── common.sh
│   ├── image-backup.sh
│   ├── image-restore.sh
│   ├── service-connect.sh
│   ├── service-log.sh
│   ├── service-restart.sh
│   ├── service-start.sh
│   ├── service-status.sh
│   ├── service-stop.sh
│   ├── stack-down.sh
│   ├── stack-up.sh
│   ├── volume-backup.sh
│   └── volume-restore.sh
├── deploy.sh              # 배포 자동화용 스크립트 (선택)
├── Makefile               # 주요 명령어 집약
└── README.md
```

---
## 사용에 앞서
_script 폴더 내 각 쉘스크립트 파일에 compose시 필요한 정보를 기재해야 합니다.

### 대상 파일명 및 채워야 할 값
```text
* common.sh
    -> <루트폴더명>
    -> <스택명>
* image-backup.sh
    -> <스택명>
* image-restore.sh
    -> <스택명>
* service-connect.sh
    -> <스택명>
* service-log.sh
    -> <스택명>
* service-restart.sh
    -> <스택명>
* service-start.sh
    -> <스택명>
* service-status.sh
    -> <스택명>
* service-stop.sh
    -> <스택명>
* stack-down.sh
    -> <스택명>
* stack-up.sh
    -> <스택명>
    -> <개발환경 도커 컴포즈 명세파일명>
    -> <운영환경 도커 컴포즈 명세파일명>
    -> <로컬환경 도커 컴포즈 명세파일명>
* volume-backup.sh
    -> <스택명>
* volume-restore.sh
    -> <스택명>

```  

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
make up local
make status
make volume-backup
make volume-restore 20250331_1325
```

## 🐳 사용 요건
* Docker CLI / Docker Compose(docker-compose) 필요
* Bash 쉘 필요
* jq(JSON 파싱용) 필요