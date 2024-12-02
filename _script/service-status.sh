#!/bin/bash
# 해당 스택의 서비스 상태를 출력합니다.
#
# 사용방법: ./service-status.sh

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

STACK_NAME="<스택명>"

# docker-compose 스택 없으면 진행 불가능
check_project_not_exist

console_out "$STACK_NAME 스택 서비스 목록"
docker-compose -p "$STACK_NAME" ps -a
exit 0