# deploy-project

`compman deploy`를 로컬 ministack(S3 에뮬레이터)으로 테스트하는 프로젝트.
seed의 shell 프로그램을 Dockerfile로 이미지화 → deploy로 내려받아 빌드 → 컨테이너 기동 → 로그 확인 → 종료하는 풀 시나리오.

## 구조

```
deploy-project/
├── README.md
├── setup-s3.ps1              # ministack에 버킷 생성 + seed 업로드 (--delete)
├── seed/                     # S3에 업로드할 배포 콘텐츠
│   ├── Dockerfile            # shell 프로그램을 이미지화
│   └── script/
│       └── app.sh            # 이미지화할 shell 프로그램 (로그 무한 출력)
└── target/                   # deploy 실행 대상 (gitignore, 산출물 보존)
```

## 사전 조건

- ministack 실행 중 (`localhost:4566`, creds `test`/`test`)
- aws CLI 설치 (seed 업로드용 — deploy 자체는 boto3 사용)
- docker 사용 가능

## 테스트

```powershell
# 1. ministack 상태 확인
docker ps --filter name=ministack

# 2. 버킷 생성 + seed 업로드 (S3에 이전 잔재 있으면 --delete로 정리)
powershell -File setup-s3.ps1

# 3. target에서 deploy 실행 (prefix 모드) → Dockerfile, script/app.sh 생성
cd target
$env:AWS_ACCESS_KEY_ID="test"
$env:AWS_SECRET_ACCESS_KEY="test"
$env:AWS_DEFAULT_REGION="ap-northeast-2"
$env:COMPMAN_S3_ENDPOINT="http://localhost:4566"
$env:COMPMAN_S3_PATH_DEV="s3://deploy-test"
uv run --project C:\path\to\compman compman deploy dev

# 3b. 아카이브 모드 (tar.gz/zip, 최상위 폴더 1개면 평탄화)
#   seed/app/ 아래에 Dockerfile+script를 묶어 seed.tar.gz 생성 후 업로드
#   tar -C seed -czf seed.tar.gz app
#   aws s3 cp seed.tar.gz s3://deploy-test/seed.tar.gz --checksum-algorithm SHA256
#   $env:COMPMAN_S3_PATH_DEV="s3://deploy-test/seed.tar.gz"
#   uv run --project C:\path\to\compman compman deploy dev --build --tag deploy-e2e-app   # fetch 후 자동 빌드

# 4. 이미지 빌드 (아카이브에서 --build 안 쓴 경우)
docker build -t deploy-e2e-app .

# 5. docker-compose.yml 생성 (deploy 후 만들기)
# services:
#   app:
#     image: deploy-e2e-app
#     environment:
#       - MESSAGE=${MESSAGE}
#     restart: unless-stopped

# 6. compman.yml 생성
# compman:
#   name: deploy-e2e
#   compose:
#     dev:
#       file: docker-compose.yml
#       env:
#         MESSAGE: hello-from-dev

# 7. 기동 + 상태 + 로그 + 종료
uv run --project C:\path\to\compman compman stack up dev
uv run --project C:\path\to\compman compman service status
docker logs deploy-e2e-app-1    # deploy-e2e: hello-from-dev 출력 확인 (env 주입)
uv run --project C:\path\to\compman compman stack down --yes
```

## 정리

- 버킷/객체: `S3_PERSIST=0`이므로 ministack 재시작 시 자동 소멸
- target/ 내용: gitignore 대상, 산출물 보존 (수동 삭제 시에만 제거)
