# dtx-docker-manager 개선 실행계획

> 작성일: 2026-07-24
> 대상: Makefile, `_script/*.sh`, `deploy.sh`, README.md

---

## 1. 현황 요약

이 프로젝트는 docker-compose 스택을 make 명령어로 관리하는 템플릿이다.
기존에 식별된 단점 3가지에 더해, 코드 정독 결과 **실제 동작 버그 7건**과
**구조 개선 포인트 다수**를 추가로 발견했다.

### 기존 식별 단점
1. make → bash → compose 3중 레이어로 디버깅 경로가 길다
2. `<스택명>` 등 플레이스홀더를 14개 파일에 수동으로 채워야 한다 (복붙 실수 위험)
3. profiles, env 분리 등 compose 자체 기능을 재구현했다

---

## 2. 신규 발견 문제 (코드 분석 결과)

### 🔴 Critical — 동작이 깨지는 버그

| # | 위치 | 문제 |
|---|------|------|
| C1 | `common.sh:13-17` + 전체 스크립트 | `COMPOSE_CMD="docker compose"`를 `"$COMPOSE_CMD"`로 인용 실행 → 공백 포함 단일 명령어 `"docker compose"`를 찾다가 `command not found`. **docker-compose(v1)가 없는 최신 환경에서는 모든 스크립트가 실패** |
| C2 | `Makefile:4` | `make start web` 실행 시 make가 `web`을 별도 타겟으로 해석 → 스크립트는 돌지만 마지막에 `No rule to make target 'web'` 에러. 캐치올 룰(`%:`) 부재 |
| C3 | `common.sh:48-58` | `check_project_dir_not_exist`가 `[ -z "$FOLDER_NAME" ] && [ ! -d ... ]` 조건이라 FOLDER_NAME이 채워져 있으면 폴더가 없어도 통과. 사실상 검사 기능 상실 |
| C4 | `volume-backup.sh:66-67` vs `volume-restore.sh:103` | backup은 `mkdir -p` 후 `docker cp` → `$VOLUME/<목적지 폴더명>/` **중첩 디렉토리** 생성. restore는 `$VOLUME/.`을 복사 → 컨테이너 내부에 한 단계 더 깊은 경로로 복원됨 (pull/push는 mkdir 없이 복사해서 정상 — backup/restore만 불일치) |
| C5 | `stack-update.sh` | `RUN_ENV_PARAM=$1` 누락(항상 기본값). 예제용 `docker cp my_container ...`가 주석이 아닌 **실행 코드**라 수정 없이 돌리면 실패/오동작 |

### 🟡 Major — 데이터 안전성 / 정확성

| # | 위치 | 문제 |
|---|------|------|
| M1 | `volume-backup.sh`, `volume-restore.sh` | **실행 중인 컨테이너에 docker cp로 백업/복원** → DB 등 쓰기 중인 데이터는 정합성 깨질 수 있음. 백업/복원 전 서비스 stop, 완료 후 start 필요 |
| M2 | `volume-backup.sh:41`, `volume-pull.sh` | `docker volume ls --filter name=$STACK_NAME`은 **부분 일치** → 스택 `app`이 `app2`의 볼륨까지 백업. `--filter label=com.docker.compose.project=$STACK_NAME`으로 교체 필요 |
| M3 | `deploy.sh:29-40` | `rm -rf` 실행 **후** S3 다운로드 → 네트워크 실패 시 Makefile/스크립트 전부 소실된 상태로 중단. 임시 폴더에 받은 뒤 원자적 교체로 변경 필요 |
| M4 | `stack-up.sh:20-33` | `RUN_ENV`가 dev/prod/local 외 값이면 분기 없이 통과 → 빈 파일명으로 find → 엉뚱한 에러 메시지. 미지원 값 즉시 거부 필요 |
| M5 | `image-backup.sh` | `docker commit` 기반 백업은 컨테이너 런타임 변경분을 이미지에 섞고, 복원 후 compose 파일 수동 수정이 필요한 반쪽 자동화. 최소한 원본 이미지 `docker save` 방식과의 선택지 제공 검토 |

### 🟢 Minor — 사용성 / 이식성

| # | 위치 | 문제 |
|---|------|------|
| m1 | `Makefile:47` | `image-restore` 도움말이 "볼륨을 복원"으로 잘못 기재 (복붙 오타) |
| m2 | `Makefile:51-53` | `clear` 설명은 "이미지/컨테이너/볼륨 정리"인데 실제는 `docker image prune -af`만 실행. `-a`는 미사용 이미지 **전부** 삭제라 과격함 — 설명과 동작 일치시켜야 함 |
| m3 | `Makefile:6` | `update`, `volume-*`, `image-*` 타겟이 `.PHONY` 누락. `.DEFAULT_GOAL := help` 미설정 |
| m4 | `service-connect.sh:44` | `/bin/bash` 고정 → alpine 등 bash 없는 이미지 접속 불가. `bash || sh` 폴백 필요 |
| m5 | `common.sh:42` | `echo -e "\e[..."` — macOS 기본 bash 3.2에서 `\e` 미해석. `printf '\033[...'`로 교체 |
| m6 | `Makefile:4` | `$(word 2, ...)`라 서비스 1개만 전달 가능. 스크립트는 배열(`"$@"`)을 지원하는데 Makefile이 병목 |
| m7 | 전체 | shellcheck 미적용, CI 부재 |

---

## 3. 개선 실행계획

### Phase 1 — 버그 수정 (즉시, 반나절)

동작을 깨뜨리는 것부터 고친다. 구조 변경 없이 최소 diff로 진행.

1. **C1**: `common.sh`에서 compose 명령을 배열로 정의하고 전 스크립트의 호출부 수정
   ```bash
   # common.sh
   if docker compose version &>/dev/null; then
       COMPOSE_CMD=(docker compose)
   elif command -v docker-compose &>/dev/null; then
       COMPOSE_CMD=(docker-compose)
   else
       echo "docker compose를 찾을 수 없습니다."; exit 1
   fi
   # 호출부: "${COMPOSE_CMD[@]}" -p "$STACK_NAME" ...
   ```
2. **C2 + m6**: Makefile에 캐치올 룰 추가, 파라미터를 `$(wordlist 2, ...)`로 확장
   ```makefile
   PARAMS := $(wordlist 2, $(words $(MAKECMDGOALS)), $(MAKECMDGOALS))
   %:
   	@:
   ```
3. **C3**: `check_project_dir_not_exist` 조건을 `[ ! -d "$PROJECT_HOME" ]` 단독 검사로 수정
4. **C4**: `volume-backup.sh`의 `mkdir -p` + `docker cp` 조합을 pull과 동일한 방식(`docker cp CONTAINER:DEST "$BACKUP_TARGET/$VOLUME"`)으로 통일 → 중첩 제거
5. **C5**: `stack-update.sh`에 `RUN_ENV_PARAM=$1` 추가, 예제 코드는 주석 처리 + "TODO를 채우지 않으면 에러로 종료" 가드 추가
6. **m1, m2, m3**: Makefile 오타/`.PHONY`/`.DEFAULT_GOAL`/clear 동작-설명 일치
7. **m4**: `docker exec -it "$ID" sh -c 'command -v bash >/dev/null && exec bash || exec sh'`
8. **m5**: `console_out`을 `printf` 기반으로 교체

### Phase 2 — 설정 중앙화 (플레이스홀더 문제 해결, 1일)

기존 단점 2번(수동 플레이스홀더)의 근본 해결.

1. **`stack.env` 단일 설정 파일 도입** (프로젝트 루트)
   ```bash
   # stack.env — 이 파일 하나만 채우면 됨
   STACK_NAME=my-stack
   COMPOSE_FILE_LOCAL=docker-compose.local.yml
   COMPOSE_FILE_DEV=docker-compose.dev.yml
   COMPOSE_FILE_PROD=docker-compose.prod.yml
   # ENV_FILE_DEV=...   # 선택
   ```
2. `common.sh`가 `stack.env`를 source하고 필수값 검증 (미설정 시 명확한 에러)
3. 각 스크립트의 중복된 `STACK_NAME="<스택명>"` 선언 **전부 삭제** — common.sh 값만 사용
4. `make init` 타겟 추가: `stack.env.example` 복사 + 값 입력 안내 → 신규 프로젝트 셋업이 파일 1개 편집으로 축소
5. README의 "채워야 할 값" 섹션을 stack.env 기준으로 재작성

### Phase 3 — 데이터 안전성 (1일)

1. **M1**: `volume-backup.sh` / `volume-restore.sh`에 stop → 작업 → start 시퀀스 추가 (`--no-stop` 옵션으로 기존 동작 유지 가능)
2. **M2**: 볼륨 조회를 compose 라벨 필터로 교체
   ```bash
   docker volume ls --filter "label=com.docker.compose.project=$STACK_NAME" --format '{{.Name}}'
   ```
3. **M3**: `deploy.sh`를 "임시 폴더 다운로드 → 성공 시 교체" 구조로 변경
4. **M4**: `stack-up.sh`에 미지원 환경값 즉시 거부 분기 추가
5. volume-backup의 임시 JSON 문자열 조립을 `jq -n` 기반 생성으로 교체 (컨테이너명에 특수문자 있어도 안전)

### Phase 4 — compose 네이티브 기능 활용 (단점 3번 대응, 선택)

재구현 코드를 줄이고 compose 표준에 위임.

1. `stack-up.sh`의 환경 분기 → `COMPOSE_FILE` / `COMPOSE_PROJECT_NAME` 환경변수 + `--env-file` 조합으로 단순화 검토
2. 환경별 오버라이드는 `docker-compose.yml` + `docker-compose.<env>.yml` **override 패턴** 권장 (README에 가이드 추가)
3. `stack-update.sh`의 docker cp 방식 대신 `compose up -d --build` / `watch` 활용 가능 여부 검토
4. **M5**: image-backup에 "원본 이미지 save" 모드 추가, commit 방식은 옵션으로 강등

### Phase 5 — 품질 인프라 (지속)

1. `shellcheck` 전 스크립트 적용 + 지적사항 수정
2. GitHub Actions CI: shellcheck + `make help` 스모크 테스트
3. bats-core 기반 최소 테스트 (플레이스홀더 미치환 감지, 날짜 검증 로직 등 순수 로직 위주)

---

## 4. 우선순위 및 예상 규모

| Phase | 내용 | 우선순위 | 예상 규모 |
|-------|------|----------|-----------|
| 1 | 버그 수정 (C1~C5, m1~m5) | ★★★ 즉시 | 반나절 |
| 2 | stack.env 설정 중앙화 | ★★★ | 1일 |
| 3 | 데이터 안전성 (M1~M4) | ★★☆ | 1일 |
| 4 | compose 네이티브 활용 | ★☆☆ 선택 | 1~2일 |
| 5 | shellcheck / CI / 테스트 | ★☆☆ 지속 | 반나절 셋업 |

**권장 순서**: Phase 1 → 2는 연달아 진행 (2가 끝나야 템플릿으로서 쓸만해짐).
Phase 3은 실데이터 백업에 쓰기 전 필수. 4, 5는 여유 시.

---

## 5. 리스크 및 참고

- Phase 2의 `stack.env` 도입은 **기존에 이 템플릿을 복사해 쓰는 프로젝트와 호환되지 않음** — 템플릿이므로 신규 프로젝트부터 적용하면 되나, 기존 배포처가 있다면 마이그레이션 안내 필요
- `deploy.sh`는 S3의 `_script`를 통째로 덮어쓰므로, Phase 2 적용 시 S3 측 원본도 함께 갱신해야 함
- Phase 3의 stop/start 시퀀스는 서비스 다운타임을 발생시키므로 README에 명시 필요
