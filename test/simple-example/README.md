# simple-example

`compman` 단순 compose 파일 목록 예시 — profile 없이 compose up.

## 구조

```
simple-example/
├── compman.yml
└── docker-compose.yml
```

## 사용

```bash
compman stack up
compman service status
compman service stop web
compman service start web
compman stack down --yes
```

## 설명

profile이 필요 없는 단순한 경우 `compose`를 리스트로 지정합니다.
`base`나 per-profile env 없이 compose 파일만 `-f`로 전달됩니다.

```yaml
compose:
  - docker-compose.yml
```

`compose` 키를 아예 생략하면 기본값으로 `docker-compose.yml`을 찾습니다.
