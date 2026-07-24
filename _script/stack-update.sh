#!/bin/bash
# 도커 컴포즈 스택을 최신으로 업데이트합니다.
# 변경사항이 생겼을때 사용합니다.
#
# 기본 동작: 변경된 서비스의 이미지를 다시 빌드하고 컨테이너를 재생성합니다
# (compose up -d --build). 소스코드/설정 변경이 Dockerfile 빌드에 반영되는
# 구조라면 별도 설정 없이 바로 사용 가능합니다.
#
# 재시작 없이 실행 중인 컨테이너에 파일만 반영하고 싶다면 아래
# "수동 업데이트" 섹션의 주석을 해제해 사용하세요.
#
# 사용방법: ./stack-update.sh [실행환경]
#     -> 실행환경: local(DEFAULT), dev, prod

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다.
source ./common.sh

COMPOSE_HOME="../_project"

RUN_ENV_PARAM=$1
# 실행환경 파라미터가 없으면 기본값은 local
RUN_ENV=${RUN_ENV_PARAM:-"local"}

# stack.env 기준으로 -f 옵션(COMPOSE_FILES)과 ENV_FILE_PATH를 구성
resolve_compose_files "$RUN_ENV"

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker compose 스택 없으면 진행 불가능
check_project_not_exist

console_out "스택 업데이트를 시작합니다. (변경분 빌드 후 재생성)"
if [ -z "$ENV_FILE_PATH" ]; then
  "${COMPOSE_CMD[@]}" -p "$STACK_NAME" "${COMPOSE_FILES[@]}" up -d --build
else
  "${COMPOSE_CMD[@]}" -p "$STACK_NAME" --env-file "$ENV_FILE_PATH" "${COMPOSE_FILES[@]}" up -d --build
fi

# --- 수동 업데이트: 재시작 없이 파일만 컨테이너에 반영하고 싶다면 아래를 사용하세요 (선택) ---
# TARGET_CONTAINER="my_container"
# SOURCE_PATH="$COMPOSE_HOME/update-folder"
# DESTINATION_PATH="$TARGET_CONTAINER:/my/update/folder"
#
# console_out "변경사항을 컨테이너에 반영합니다: $TARGET_CONTAINER"
# docker cp "$SOURCE_PATH" "$DESTINATION_PATH"
#
# <적용할 컨테이너가 더 있다면 여기에 추가합니다.>
# ...
# --------------------------------------------------------------------------------

console_out "스택 업데이트 완료"
exit 0
