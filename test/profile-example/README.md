# profile-example

`compman` profile 기능 예시 — 실행환경별 compose 파일 + env vars 관리.

## 구조

```
profile-example/
├── compman.yml
├── docker-compose.local.yml
├── docker-compose.dev.yml
└── docker-compose.prod.yml
```

## 사용

```bash
# local profile (profile명만, env 없음)
compman stack up local

# dev profile (compose 파일 + env vars 자동 주입)
compman stack up dev

# prod profile
compman stack up prod

# 상태 확인
compman service status

# 스택 제거
compman stack down
```

## 설명

`compman.yml`의 `compose` 아래 각 키가 profile명입니다.
`string` 값은 compose 파일만 지정, `object` 값은 `file` + `env`를 함께 지정합니다.

```yaml
profiles:
  local: docker-compose.local.yml                   # 파일만
  dev:
    file: docker-compose.dev.yml
    env:
      DATABASE_URL: dev.db.example.com              # env vars 자동 주입
```
