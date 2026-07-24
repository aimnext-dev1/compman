#!/bin/bash
# 도커 이미지를 백업합니다.
#
# 사용방법: ./image-backup.sh [source]
#     -> 기본(commit 모드): 컨테이너의 현재 상태(런타임 중 변경분 포함)를 커밋해 백업합니다.
#     -> source: 컨테이너가 실행중인 원본 이미지 그대로 백업합니다.
#                  런타임 변경분은 포함되지 않지만, 더 빠르고 이미지가 더 작습니다.
#
# 결과물: <스택이름>.<백업날짜(yyyyMMdd)>.image.tar.gz

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다.
source ./common.sh

BACKUP_HOME="../_backup"

SOURCE_MODE=false
if [ "$1" == "source" ]; then
    SOURCE_MODE=true
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M")
BACKUP_NAME="$STACK_NAME.image.$TIMESTAMP"
BACKUP_TARGET="$BACKUP_HOME/$BACKUP_NAME"

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker compose 스택 없으면 진행 불가능
check_project_not_exist

console_out "백업 폴더 경로가 올바른지 확인합니다."
if [ -z "$BACKUP_HOME" ] || [ -z "$BACKUP_NAME" ]; then
    echo "잘못된 백업 경로입니다. BACKUP_HOME: $BACKUP_HOME, BACKUP_NAME: $BACKUP_NAME"
    exit 1
fi

console_out "백업 폴더를 생성합니다."
mkdir "$BACKUP_TARGET"

console_out "이미지를 백업 합니다."
# 컨테이너 ID 목록 획득
CONTAINER_IDS=$("${COMPOSE_CMD[@]}" -p "$STACK_NAME" ps -q)
# 각 컨테이너 이미지 tar 파일로 저장
for CONTAINER_ID in $CONTAINER_IDS; do
    CONTAINER_NAME=$(docker inspect --format '{{.Name}}' "$CONTAINER_ID" | sed 's/^\///')
    if [ "$SOURCE_MODE" == true ]; then
        # 컨테이너가 생성된 원본 이미지를 그대로 저장 (런타임 변경분 미포함)
        IMAGE_ID=$(docker inspect --format '{{.Image}}' "$CONTAINER_ID")
        docker save -o "${BACKUP_TARGET}"/"${CONTAINER_NAME}".image.backup.tar "$IMAGE_ID"
    else
        docker commit "$CONTAINER_ID" "${CONTAINER_NAME}":backup
        docker save -o "${BACKUP_TARGET}"/"${CONTAINER_NAME}".image.backup.tar "${CONTAINER_NAME}":backup
        docker rmi "${CONTAINER_NAME}":backup
    fi
done

console_out "백업 폴더를 압축합니다."
tar -cvzf "$BACKUP_HOME"/"$BACKUP_NAME".tar.gz -C "$BACKUP_TARGET" .

console_out "백업 폴더를 삭제합니다."
rm -rf "$BACKUP_TARGET"

console_out "이미지 백업 성공!!!"
exit 0