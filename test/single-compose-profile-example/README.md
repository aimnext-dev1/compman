# single-compose-profile-example

`compman` 단일 compose 파일 + profile 예제 — 환경변수만 profile로 관리.

## 구조

```
single-compose-profile-example/
├── compman.yml
└── docker-compose.yml
```

## 사용

```bash
compman stack up dev      # docker compose -f docker-compose.yml -p single-compose-app up -d
compman service status
compman stack down --yes

compman stack up prod     # docker compose -f docker-compose.yml -p single-compose-app up -d
compman stack down --yes
```

## 설명

profile에 `file`을 생략하면 기본값 `docker-compose.yml`을 사용합니다.
같은 compose 파일을 공유하되 profile별 env vars만 다르게 주입할 수 있습니다.

```yaml
compose:
  dev:
    env:
      DATABASE_URL: dev.example.com
      LOG_LEVEL: debug
  prod:
    env:
      DATABASE_URL: prod.example.com
      LOG_LEVEL: warn
```
