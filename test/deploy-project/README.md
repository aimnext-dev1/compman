# deploy-project

`compman deploy`를 로컬 ministack(S3 에뮬레이터)으로 테스트하는 프로젝트.
seed의 shell 프로그램을 Dockerfile로 이미지화 → deploy로 내려받아 빌드 → 컨테이너 기동 → 로그 확인 → 종료하는 풀 시나리오.

## 구조

```
deploy-project/
├── README.md                   # 테스트 절차 문서
└── target/                     # deploy 실행 대상 (gitignore, 산출물 보존)

docker-init/                    # ministack 시딩 소스 (repo root)
├── init-bucket.sh              # ministack 기동 시 버킷 + seed 자동 시딩
├── seed/                       # S3에 업로드할 배포 콘텐츠 (디렉토리 버전)
│   ├── Dockerfile              # shell 프로그램을 이미지화
│   └── script/
│       └── app.sh              # 이미지화할 shell 프로그램 (로그 무한 출력)
└── seed.tar.gz                 # 압축 버전 (app/ 래핑 → flatten 테스트)
```

## 사전 조건

- docker (compose) 사용 가능
- ministack은 컨테이너 안에서 시딩하므로 호스트 aws CLI 불필요
- seed Dockerfile은 Windows checkout에서 `app.sh`가 CRLF여도 이미지 빌드 중 LF로 정규화합니다.

## 테스트

```powershell
# 1. ministack 기동 (컨테이너 안에서 bucket 생성 + 양쪽 버전 자동 업로드)
cd C:\path\to\compman
docker compose up -d
#    s3://deploy-test/                  ← 디렉토리 버전 (Dockerfile, script/)
#    s3://deploy-test/archives/seed.tar.gz   ← 압축 버전 (docker-init/seed.tar.gz 업로드, app/ 래핑)

# 2. target에서 deploy 실행 (prefix 모드, config 경로) → Dockerfile, script/ 생성
#    compman.yml/docker-compose.yml 없으면 자동 생성 (단순 모드 + deploy 경로 기록)
cd test/deploy-project/target
$env:AWS_ACCESS_KEY_ID="test"
$env:AWS_SECRET_ACCESS_KEY="test"
$env:AWS_DEFAULT_REGION="ap-northeast-2"
$env:AWS_ENDPOINT_URL_S3="http://localhost:4567"
uv run --project C:\path\to\compman compman deploy --build --tag deploy-e2e-app
#    → compman.yml (name: target, deploy 기록, simple mode), docker-compose.yml (image: deploy-e2e-app) 자동 생성

# 2b. 아카이브 모드 (최상위 폴더 1개면 평탄화) + 자동 빌드
uv run --project C:\path\to\compman compman deploy --path s3://deploy-test/archives/seed.tar.gz --build --tag deploy-e2e-app

# 3. 기동 + 상태 + 로그 + 종료 (자동 생성된 simple mode → profile 인자 없이)
uv run --project C:\path\to\compman compman stack up
uv run --project C:\path\to\compman compman service status
docker logs e2e-deploy-app-1    # deploy-e2e: hello 출력 확인
uv run --project C:\path\to\compman compman stack down --yes

# 4. env 주입 테스트 (프로필 모드) — 자동 생성된 compman.yml을 확장:
# compman:
#   name: deploy-e2e
#   deploy: s3://deploy-test
#   compose:
#     dev:
#       file: docker-compose.yml
#       env:
#         MESSAGE: hello-from-dev
# docker-compose.yml의 app에 environment: - MESSAGE=${MESSAGE} 추가 후:
# uv run --project C:\path\to\compman compman stack up dev
# docker logs deploy-e2e-app-1   # deploy-e2e: hello-from-dev 확인
# uv run --project C:\path\to\compman compman stack down --yes
```

## init

`compman init`은 cwd 디렉토리명을 name으로 하는 심플 compman.yml을 생성 (풀 옵션은 주석).

```powershell
compman init    # compman.yml 생성 (compose: - docker-compose.yml + 주석)
```

## 정리

- 버킷/객체: `S3_PERSIST=0`이므로 컨테이너 재시작 시 자동 소멸 + init 스크립트가 재시딩
- target/ 내용: gitignore 대상, 산출물 보존 (수동 삭제 시에만 제거)
