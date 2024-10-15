#!/bin/bash
# 백업한 도커 스택을 복원합니다.
#
# 이미지 복원이 필요한 경우 밑의 주석을 해제하고 사용해주세요.
# 단 이미지 복원을 함께 사용하는 경우, 완전 자동화가 아니므로 복원완료 후 수동 설정이 필요합니다.
#   1. docker-compose.yml에 image명을 복원한 이미지명으로 변경합니다.
#      이미지명 예시: <이미지명>:latest
#   2. compose 폴더 내에서 다음 명령어를 수행합니다. 
#      docker-compose -p project-<프로젝트명> -y docker-compose.yml up -d 
# 
# 사용방법: ./stack-restore.sh <백업한날짜>
#     -> 백업파일이 없으면 수행이 불가능합니다.

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

# 백업한날짜를 파라미터로 받음
ROLLBACK_DATETIME=$1

console_out "입력 날짜 포맷이 올바른지 검사합니다."
DATETIME_REGEX="^[0-9]{8}_[0-9]{4}$"  # %Y%m%d_%H%M 형식의 정규표현식
if [[ ! "$ROLLBACK_DATETIME" =~ $DATETIME_REGEX ]]; then
    echo "올바른 날짜 및 시간 형식이 아닙니다. 형식(년월일_시분) ex)20240131_1341"
    console_out "BACKUP FILE LIST"
    for file in "$BACKUP_HOME"/*; do
        if [[ "$file" =~ [0-9]{8}_[0-9]{4} ]]; then
            echo -e "\033[32m$(basename "$file")\033[0m"
        fi
    done
    exit 1
fi

console_out "파일이 존재하는지 검사합니다."
ROLLBACK_FILE_PATH=$BACKUP_HOME/$STACK_NAME.$ROLLBACK_DATETIME.tar.gz
if [[ ! -e "$ROLLBACK_FILE_PATH" ]]; then
    echo "파일이 존재하지 않습니다: $ROLLBACK_FILE_PATH"
    console_out "BACKUP FILE LIST"
    for file in "$BACKUP_HOME"/*; do
        if [[ "$file" =~ [0-9]{8}_[0-9]{4} ]]; then
            echo -e "\033[32m$(basename "$file")\033[0m"
        fi
    done
    exit 1
fi

console_out "백업파일의 압축을 해제합니다."
tar -xvzf "$BACKUP_HOME"/"$STACK_NAME"."$ROLLBACK_DATETIME".tar.gz -C "$BACKUP_HOME"
chown -R "$USER":"$GROUP" "$BACKUP_HOME"

console_out "설정 폴더에 복원내용을 적용합니다."
if [ -d "$BACKUP_HOME"/config ] ; then
    rm -rf "$CONFIG_HOME"
    mv "$BACKUP_HOME"/config "$CONFIG_HOME"
fi

console_out "컴포즈 폴더에 복원내용을 적용합니다."
if [ -d "$BACKUP_HOME"/compose ] ; then
    rm -rf "$COMPOSE_HOME"
    mv "$BACKUP_HOME"/compose "$COMPOSE_HOME"
fi

console_out "볼륨 폴더에 복원내용을 적용합니다."
if [ -d "$BACKUP_HOME"/volume ] ; then
    rm -rf "$VOLUME_HOME"
    mv "$BACKUP_HOME"/volume "$VOLUME_HOME"
fi

# ** --------------------- 이미지 복원 기능을 사용하려는 경우, 다음 주석을 활성화 ------------------------ **
#
# console_out "백업 이미지를 불러옵니다."
# for file in "$BACKUP_HOME"/*.tar; do
#     echo "Loading $file..."
#     docker load -i "$file"
#     rm "$file"
# done
#
# console_out "복원 이미지 태그를 latest로 변경합니다."
# IMAGE_NAME_LIST=$(docker images --filter "reference=*:backup" --format "{{.Repository}}:{{.Tag}}")
# for image_name in $IMAGE_NAME_LIST; do
#     new_image_name=$(echo "$image_name" | sed 's/:.*/:latest/')
#     echo "change name $image_name to $new_image_name"
#     docker tag "$image_name" "$new_image_name"
#     docker rmi "$image_name"
# done
#
# ** ---------------------------------------------------------------------------------------- **

console_out "스택 복원 완료!!!"
