#!/bin/bash
# 도커 컴포즈 스택을 전체 백업합니다.
# 사용방법: ./stack-backup.sh
# 결과물: <스택이름>.<백업날짜(yyyyMMdd)>.tar.gz

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

USER="<유저명>"
GROUP="<그룹명>"

BACKUP_HOME="../_backup"
CONFIG_HOME="../_project/config"
COMPOSE_HOME="../_project/compose"
VOLUME_HOME="../_project/volume"

STACK_NAME="<스택명>"
BACKUP_NAME="<스택명>.$(date +"%Y%m%d_%H%M")"
BACKUP_TARGET="../_backup/<스택명>.$(date +"%Y%m%d_%H%M")"

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker-compose 스택 없으면 진행 불가능
check_project_not_exist

console_out "백업 폴더 경로가 올바른지 확인합니다."
if [ -z "$BACKUP_HOME" ] || [ -z "$BACKUP_NAME" ]; then
    echo "잘못된 백업 경로입니다. BACKUP_HOME: $BACKUP_HOME, BACKUP_NAME: $BACKUP_NAME"
    exit 1
fi

console_out "백업 폴더를 생성합니다."
mkdir "$BACKUP_TARGET"

console_out "설정 폴더를 백업 폴더에 복사합니다."
cp -R "$CONFIG_HOME" "$BACKUP_TARGET"
console_out "컴포즈 폴더를 백업 폴더에 복사합니다."
cp -R "$COMPOSE_HOME" "$BACKUP_TARGET" 
console_out "폴륨 폴더를 백업 폴더에 복사합니다."
cp -R "$VOLUME_HOME" "$BACKUP_TARGET"

console_out "이미지를 백업 합니다."
# 컨테이너 ID 목록 획득
CONTAINER_IDS=$(docker-compose -p "$STACK_NAME" ps -q)
# 각 컨테이너 이미지 tar 파일로 저장
for CONTAINER_ID in $CONTAINER_IDS; do
    CONTAINER_NAME=$(docker inspect --format '{{.Name}}' "$CONTAINER_ID" | sed 's/^\///')
    docker commit "$CONTAINER_ID" "${CONTAINER_NAME}":backup
    docker save -o "${BACKUP_TARGET}"/"${CONTAINER_NAME}".image.backup.tar "${CONTAINER_NAME}":backup
    docker rmi "${CONTAINER_NAME}":backup
done

console_out "백업 폴더를 압축합니다."
tar -cvzf "$BACKUP_HOME"/"$BACKUP_NAME".tar.gz -C "$BACKUP_TARGET" .
chown -R "$USER":"$GROUP" "$BACKUP_HOME"

console_out "백업 폴더를 삭제합니다."
rm -rf "$BACKUP_TARGET"

console_out "스택 백업 성공!!!"
