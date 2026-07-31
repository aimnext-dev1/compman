# deploy-example

`compman` deploy 기능 예시 — S3에서 프로젝트 리소스를 받아와 원자적 교체.

## 동작

S3 경로(`compman.yml: deploy` 또는 `--path`) 유형에 따라 처리해 **cwd**에 원자적 교체합니다.

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

**빈 디렉토리 자동 scaffold**: `compman.yml`/`docker-compose.yml`이 없으면 deploy가 자동 생성합니다.
```yaml
# compman.yml
compman:
  name: <cwd dirname>
  deploy: s3://<사용한 경로>     # 다음 deploy는 --path 없이 동작
  compose:
    - docker-compose.yml
```
```yaml
# docker-compose.yml
services:
  app:
    image: <--tag 또는 dirname>  # --build 시 빌드된 이미지와 일치
    restart: unless-stopped
```
기존 파일은 덮어쓰지 않습니다. 빈 디렉토리에서 `compman deploy --build` → 바로 `compman stack up` 가능.
실행 중인 컨테이너는 건드리지 않습니다.

## 설정

- S3 경로: `compman.yml`의 `deploy` 키 또는 CLI `--path` override
  ```yaml
  compman:
    deploy: s3://my-bucket/app
  ```
  ```bash
  compman deploy --path s3://my-bucket/other
  ```
- 엔드포인트: `COMPMAN_S3_ENDPOINT` — 미설정 시 실제 AWS, 설정 시 해당 엔드포인트로 (로컬 ministack 테스트용, root `docker-compose.yaml` 기동 시 `http://localhost:4567`)
- 인증: 표준 `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_DEFAULT_REGION` env vars
- boto3 사용 (aws CLI 불필요)

## 사용법

```bash
compman init                        # 심플 compman.yml 생성 (name = cwd dirname, 풀 옵션은 주석)
compman deploy                     # compman.yml의 deploy 경로에서 fetch
compman deploy --path s3://...     # 경로 override
compman deploy --build --tag myapp # fetch 후 docker build -t myapp .
```

`--build` 시 태그 미지정이면 cwd 디렉토리명이 기본 태그가 됩니다.

## 주의

deploy는 fetch된 파일을 **현재 디렉토리에** 생성합니다.
repo 루트에서 실행하면 untracked 파일이 생기므로, **스크래치/타깃 디렉토리에서 실행**하세요.

실제 테스트 절차는 `test/deploy-project/` 참고.
