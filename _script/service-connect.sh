#!/bin/bash

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

CONTAINER_NAME="<컨테이너명>"
CONTAINER_KEY=$(docker ps -a | grep $CONTAINER_NAME | xargs | awk '{print $1}')

console_out "$CONTAINER_NAME 컨테이너로 접속합니다."
docker exec -it "$CONTAINER_KEY" /bin/bash
