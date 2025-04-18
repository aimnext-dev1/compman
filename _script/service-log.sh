#!/bin/bash
# 도커 컨테이너 로그를 확인합니다.
#
# 사용방법: ./service-log.sh <도커 서비스명>
#     -> <도커 서비스명> 미입력시 컨테이너 목록을 출력합니다.

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

STACK_NAME="<스택명>"
CONTAINER_NAME=$1

# docker compose 스택 없으면 진행 불가능
check_project_not_exist

# 만약 CONTAINER_NAME이 비어있다면
if [ -z "$CONTAINER_NAME" ]; then
    echo "로그를 확인할 컨테이너명을 입력해주세요:"
    "$COMPOSE_CMD" -p $STACK_NAME ps -a --format "{{.Names}}" | awk '{print "\033[92m" $1 "\033[0m"}'
    exit 1
fi

CONTAINER_KEY=$(docker ps -a --filter "name=^$CONTAINER_NAME$" --format "{{.ID}}")

console_out "$CONTAINER_NAME 컨테이너 로그를 출력합니다."
docker logs -f -n 10000 "$CONTAINER_KEY"
exit 0