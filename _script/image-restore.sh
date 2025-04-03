#!/bin/bash
# 백업한 도커 이미지를 복원합니다.
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

BACKUP_HOME="../_backup"

# 백업한날짜를 파라미터로 받음
RESTORE_DATETIME=$1
RESTORE_NAME="<스택명>.image.$RESTORE_DATETIME"

console_out "입력 날짜 포맷이 올바른지 검사합니다."
DATETIME_REGEX="^[0-9]{8}_[0-9]{4}$"  # %Y%m%d_%H%M 형식의 정규표현식
if [[ ! "$RESTORE_DATETIME" =~ $DATETIME_REGEX ]]; then
    echo "올바른 날짜 및 시간 형식이 아닙니다. 형식(년월일_시분) ex)20240131_1341"
    
    echo "===== 백업 파일 목록 ====="
    for file in "$BACKUP_HOME"/*.image.*; do
        # Get the base filename
        base_filename="$(basename "$file")"
        
        # Use regex to match and capture the desired part
        if [[ "$base_filename" =~ ^(.*)([0-9]{8}_[0-9]{4})(.*)$ ]]; then
            # Assign captured groups to variables
            prefix="${BASH_REMATCH[1]}"
            colored_part="${BASH_REMATCH[2]}"
            suffix="${BASH_REMATCH[3]}"

            # Print with colored part
            echo -e "${prefix}\033[92m${colored_part}\033[0m${suffix}"
        fi
    done
    exit 1
fi

# 날짜 유효성 검사
OS_TYPE=$(uname)

if [[ "$OS_TYPE" == "Darwin" ]]; then
    # macOS (BSD date)
    if ! date -j -f "%Y%m%d" "${RESTORE_DATETIME:0:8}" "+%Y-%m-%d" >/dev/null 2>&1; then
        echo "유효하지 않은 날짜입니다: ${RESTORE_DATETIME:0:8}"
        exit 1
    fi
else
    # 리눅스 (GNU date)
    if ! date -d "${RESTORE_DATETIME:0:8}" >/dev/null 2>&1; then
        echo "유효하지 않은 날짜입니다: ${RESTORE_DATETIME:0:8}"
        exit 1
    fi
fi

console_out "파일이 존재하는지 검사합니다."
RESTORE_FILE_PATH=$BACKUP_HOME/$RESTORE_NAME.tar.gz
if [[ ! -e "$RESTORE_FILE_PATH" ]]; then
    echo "파일이 존재하지 않습니다: $RESTORE_FILE_PATH"
    echo "===== BACKUP FILE LIST ====="
    for file in "$BACKUP_HOME"/*; do
        if [[ "$file" =~ [0-9]{8}_[0-9]{4} ]]; then
            echo -e "\033[32m$(basename "$file")\033[0m"
        fi
    done
    exit 1
fi

console_out "백업파일의 압축을 해제합니다."
RESTORE_DIR="$BACKUP_HOME/$RESTORE_NAME"
mkdir -p "$RESTORE_DIR"
tar -xvzf "$BACKUP_HOME"/"$RESTORE_NAME".tar.gz -C "$RESTORE_DIR"

console_out "백업 이미지를 불러옵니다."
for file in "$BACKUP_HOME"/"$RESTORE_NAME"/*.tar; do
    echo "Loading $file..."
    docker load -i "$file"
    rm "$file"
done

console_out "복원이 끝났으므로 백업 폴더는 삭제합니다."
rm -rf "$RESTORE_DIR"

console_out "docker-compose.yml에서 이미지를 설정한 후 스택을 시작해주세요."
console_out "이미지 복원 완료!!!"
exit 0