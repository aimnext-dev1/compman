#!/bin/bash
# 도커 컨테이너에 접속합니다.
#
# 사용방법: ./service-connect.sh <도커 서비스명>
#     -> <도커 서비스명> 미입력시:
#        - 컨테이너가 1개면 해당 컨테이너로 바로 접속
#        - 컨테이너가 2개 이상이면 목록을 출력

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
    CONTAINERS=()
    while IFS= read -r container_name; do
        [ -n "$container_name" ] && CONTAINERS+=("$container_name")
    done < <("$COMPOSE_CMD" -p "$STACK_NAME" ps -a --format "{{.Names}}")

    if [ "${#CONTAINERS[@]}" -eq 1 ]; then
        CONTAINER_NAME="${CONTAINERS[0]}"
        console_out "컨테이너가 1개라 자동으로 선택합니다: $CONTAINER_NAME"
    else
        echo "접속할 컨테이너명을 입력해주세요:"
        printf '%s\n' "${CONTAINERS[@]}" | awk '{print "\033[92m" $1 "\033[0m"}'
        exit 1
    fi
fi

CONTAINER_KEY=$(docker ps -a --filter "name=^$CONTAINER_NAME$" --format "{{.ID}}")

console_out "$CONTAINER_NAME 컨테이너로 접속합니다."
docker exec -it "$CONTAINER_KEY" /bin/bash
exit 0