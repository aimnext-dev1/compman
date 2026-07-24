#!/bin/bash
# 도커 컴포즈 스택을 생성합니다.
#
# 사용방법: ./stack-up.sh [실행환경]
#     -> 실행환경: local(DEFAULT), dev, prod

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다.
source ./common.sh

RUN_ENV_PARAM=$1
# 실행환경 파라미터가 없으면 기본값은 local
RUN_ENV=${RUN_ENV_PARAM:-"local"}

# stack.env 기준으로 -f 옵션(COMPOSE_FILES)과 ENV_FILE_PATH를 구성
resolve_compose_files "$RUN_ENV"

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker compose 스택 있으면 진행 불가능
check_project_exist

console_out "스택을 생성합니다."
# 환경변수 파일이 존재하는지 확인 후 적절한 명령어 실행
if [ -z "$ENV_FILE_PATH" ]; then
  "${COMPOSE_CMD[@]}" -p "$STACK_NAME" "${COMPOSE_FILES[@]}" up -d
else
  "${COMPOSE_CMD[@]}" -p "$STACK_NAME" --env-file "$ENV_FILE_PATH" "${COMPOSE_FILES[@]}" up -d
fi

console_out "스택 생성 성공!!!"
exit 0
