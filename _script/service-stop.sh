#!/bin/bash
# 도커 컨테이너를 중지합니다.
#
# 사용방법: ./service-stop.sh <도커 서비스명>
#     -> <도커 서비스명>은 선택값으로 누락시 전체 서비스가 중지됩니다. 
#     -> <도커 서비스명>은 ./service-status.sh 를 통해 확인 가능합니다.

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

STACK_NAME="<스택명>"
SERVICE_NAME_LIST=("$@")

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker-compose 스택 없으면 진행 불가능
check_project_not_exist

if [ "${#SERVICE_NAME_LIST[@]}" -eq 0 ]; then
    console_out "모든 서비스를 중지합니다."
    docker-compose -p "$STACK_NAME" stop
else
    for f in "${SERVICE_NAME_LIST[@]}"; do
        console_out "$f 서비스를 중지합니다."
    done
    docker-compose -p "$STACK_NAME" stop "${SERVICE_NAME_LIST[@]}"
fi

console_out "서비스 중지 완료!!!"
exit 0