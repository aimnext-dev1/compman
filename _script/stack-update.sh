#!/bin/bash
# 도커 컴포즈 스택을 최신으로 업데이트 합니다.
# 변경사항이 생겼을때 사용합니다.
# 
# 컨테이너 내 파일(소스코드, 설정 등) 변경에 대한 업데이트는 해당 스크립트를 사용합니다.
# 컨테이너의 설정 변경(docker-compose.yml)일 경우에는 down 후 up을 사용해주세요.
#
# 사용방법: ./stack-update.sh

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

console_out "스택 업데이트를 시작합니다."
# --- TODO: 프로젝트에 맞게 아래 업데이트 작업을 명세한 후 이 가드를 제거하세요. ---
echo "stack-update.sh가 아직 프로젝트에 맞게 설정되지 않았습니다. 아래 TODO를 채워주세요."
exit 1

# Example)
# TARGET_CONTAINER="my_container"
# SOURCE_PATH="$COMPOSE_HOME/update-folder"
# DESTINATION_PATH="$TARGET_CONTAINER:/my/update/folder"
#
# console_out "변경사항을 컨테이너에 반영합니다: $TARGET_CONTAINER"
# docker cp "$SOURCE_PATH" "$DESTINATION_PATH"

# <적용할 컨테이너가 더 있다면 여기에 추가합니다.>
# ...
# -----------------------------------------------

console_out "스택을 업데이트 완료"