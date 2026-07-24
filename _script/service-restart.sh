#!/bin/bash
# 도커 컨테이너를 재시작합니다.
#
# 사용방법: ./service-restart.sh <도커 서비스명>
#     -> <도커 서비스명>은 선택값으로 누락시 전체 서비스가 재시작됩니다. 
#     -> <도커 서비스명>은 ./service-status.sh 를 통해 확인 가능합니다.

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

SERVICE_NAME_LIST=("$@")

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker compose 스택 없으면 진행 불가능
check_project_not_exist

if [ "${#SERVICE_NAME_LIST[@]}" -eq 0 ]; then
    console_out "모든 서비스를 재시작합니다."
    "${COMPOSE_CMD[@]}" -p "$STACK_NAME" restart
else
    for f in "${SERVICE_NAME_LIST[@]}"; do
        console_out "$f 서비스를 재시작합니다."
    done
    "${COMPOSE_CMD[@]}" -p "$STACK_NAME" restart "${SERVICE_NAME_LIST[@]}"
fi

console_out "서비스 재시작 완료!!!"
exit 0