#!/bin/bash
# 도커 컴포즈 볼륨을 전체 백업합니다.
# 스택이 없으면 백업할 수 없습니다.
#
# 사용방법: ./stack-backup.sh
#
# 결과물: <스택이름>.<백업날짜(yyyyMMdd)>.volume.tar.gz

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

BACKUP_HOME="../_backup"

TIMESTAMP=$(date +"%Y%m%d_%H%M")
BACKUP_NAME="$STACK_NAME.volume.$TIMESTAMP"
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

# 볼륨 백업
console_out "도커 백업을 수행합니다."

# 스택 이름이 포함된 도커 볼륨 리스트 추출
VOLUMES=$(docker volume ls --filter name=$STACK_NAME --format '{{.Name}}')
CONTAINERS=$("${COMPOSE_CMD[@]}" -p $STACK_NAME ps -a --format '{{.Name}}')

if [ -z "$VOLUMES" ]; then
    echo "백업할 볼륨이 없습니다."
    exit 1
fi

mkdir -p "$BACKUP_TARGET"

# 매핑 기록용 임시 json 파일 생성
TEMP_JSON="./temp_volume_info.json"
> "$TEMP_JSON"  # 초기화

# 각 볼륨에 대해 
for VOLUME in $VOLUMES; do
    # 각 컨테이너에서
    for CONTAINER in $CONTAINERS; do
        # 매핑 정보를 찾는다.
        SOURCE=$(docker inspect $CONTAINER | \
            jq -r --arg name "$VOLUME" '.[] | .Mounts[]? | select(.Name == $name) | .Source')
        DESTINATION=$(docker inspect $CONTAINER | \
            jq -r --arg name "$VOLUME" '.[] | .Mounts[]? | select(.Name == $name) | .Destination')
        
        # 매핑 정보를 찾은 경우에는
        if [ -n "$SOURCE" ] && [ -n "$DESTINATION" ]; then
            # 매핑 정보를 기록하고
            echo "\"$CONTAINER\":{\"volume\":\"$VOLUME\",\"destination\":\"$DESTINATION\"}," >> "$TEMP_JSON"
            # 해당 데이터를 복사해온다. (대상 폴더가 미리 존재하면 안으로 중첩 복사되므로 만들지 않는다)
            docker cp "$CONTAINER:$DESTINATION" "$BACKUP_TARGET/$VOLUME"
        fi
    done
done

# JSON 포맷에 알맞게 저장
# 마지막 줄 쉼표 제거
sed '$ s/,$//' "$TEMP_JSON" > "$TEMP_JSON.cleaned"
# 중괄호로 감싸고 최종 JSON 만들기
echo "{" > "$BACKUP_TARGET/volume-map.json"
cat "$TEMP_JSON.cleaned" >> "$BACKUP_TARGET/volume-map.json"
echo "}" >> "$BACKUP_TARGET/volume-map.json"
# 임시파일 삭제
rm "$TEMP_JSON" "$TEMP_JSON.cleaned"

console_out "백업 폴더를 압축합니다."
tar -cvzf "$BACKUP_HOME"/"$BACKUP_NAME".tar.gz -C "$BACKUP_TARGET" .

console_out "백업 폴더를 삭제합니다."
rm -rf "$BACKUP_TARGET"

console_out "볼륨 백업 성공!!!"
exit 0