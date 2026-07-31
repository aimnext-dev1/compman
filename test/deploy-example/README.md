# deploy-example

`compman` deploy 기능 예시 — S3에서 프로젝트 리소스를 받아와 원자적 교체.

## 동작

S3 key(`COMPMAN_S3_PATH_<ENV>` 값) 유형에 따라 처리해 **cwd**에 원자적 교체합니다.

- **prefix 경로** — key 아래 모든 객체를 구조 보존 다운로드
  ```
  s3://<bucket>/app/
  ├── Dockerfile                 # → cwd/Dockerfile
  └── script/                    # → cwd/script/
  ```
- **아카이브 파일** — `.tar.gz`/`.tgz`/`.zip` 객체를 다운로드해 추출. 최상위 폴더가 하나뿐이면 평탄화
  ```
  s3://<bucket>/app.tar.gz (내부: app/Dockerfile, app/script/)  → cwd/Dockerfile, cwd/script/
  ```

교체는 fetch된 항목만 덮어씁니다 (cwd의 사용자 파일 `compman.yml`, `docker-compose.yml` 등은 보존).

`compman.yml`은 읽지 않습니다. 실행 중인 컨테이너는 건드리지 않습니다.

## 설정

- S3 경로: `compman/deploy.py`의 `S3_PATHS` 또는 env override
  - `COMPMAN_S3_PATH_<ENV>` (예: `COMPMAN_S3_PATH_DEV=s3://my-bucket/prod`)
- 엔드포인트: `COMPMAN_S3_ENDPOINT` — 미설정 시 실제 AWS, 설정 시 해당 엔드포인트로 (로컬 ministack 테스트용)
- 인증: 표준 `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_DEFAULT_REGION` env vars
- boto3 사용 (aws CLI 불필요)

## 사용법

```bash
compman deploy [dev|prod]                     # S3에서 소스 fetch (prefix or 아카이브)
compman deploy dev --build --tag myapp        # fetch 후 docker build -t myapp .
```

`--build` 시 태그 미지정이면 cwd 디렉토리명이 기본 태그가 됩니다.

## 주의

deploy는 fetch된 파일을 **현재 디렉토리에** 생성합니다.
repo 루트에서 실행하면 untracked 파일이 생기므로, **스크래치/타깃 디렉토리에서 실행**하세요.

실제 테스트 절차는 `test/deploy-project/` 참고.
