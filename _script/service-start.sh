#!/bin/bash
# 도커 컨테이너를 시작합니다.
# 사용방법: ./service-start.sh <도커 서비스명>
#     -> <도커 서비스명>은 선택값으로 누락시 전체 서비스가 시작됩니다. 
#     -> <도커 서비스명>은 ./service-status.sh 를 통해 확인 가능합니다.


# 쉘 스크립트가 명령어 실패 시 즉시 종료되도록 설정
set -e

# 공통 스크립트를 가져옵니다. 
source ./_script/common.sh

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker-compose 스택 없으면 진행 불가능
check_project_not_exist

SERVICE_NAME_LIST=("$@")
for f in "${SERVICE_NAME_LIST[@]}"
do
    console_out "$f 서비스를 시작합니다."
done
docker-compose -p "$STACK_NAME" start "${SERVICE_NAME_LIST[@]}"

console_out "서비스 시작 완료!!!"
