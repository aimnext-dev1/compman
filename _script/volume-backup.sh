#!/bin/bash
# 도커 컴포즈 볼륨을 전체 백업합니다.
# 스택이 없으면 백업할 수 없습니다.
# 데이터 정합성을 위해 백업 전 스택을 중지하고, 완료 후 다시 시작합니다.
#
# 사용방법: ./volume-backup.sh [no-stop]
#     -> no-stop: 스택을 중지하지 않고 백업합니다. (실행 중 쓰기로 정합성이 깨질 수 있음)
#
# 결과물: <스택이름>.volume.<백업날짜_시간>.tar.gz

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

NO_STOP=false
if [ "$1" == "no-stop" ]; then
    NO_STOP=true
fi

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

# 이 스택이 관리하는(컴포즈 라벨 기준) 볼륨/컨테이너만 추출 (이름 부분일치로 인한 다른 스택 침범 방지)
VOLUMES=$(docker volume ls --filter "label=com.docker.compose.project=$STACK_NAME" --format '{{.Name}}')
CONTAINERS=$("${COMPOSE_CMD[@]}" -p "$STACK_NAME" ps -a --format '{{.Name}}')

if [ -z "$VOLUMES" ]; then
    echo "백업할 볼륨이 없습니다."
    exit 1
fi

mkdir -p "$BACKUP_TARGET"

if [ "$NO_STOP" == false ]; then
    console_out "정합성 있는 백업을 위해 스택을 중지합니다."
    "${COMPOSE_CMD[@]}" -p "$STACK_NAME" stop
    # 백업 도중 실패해도 스택이 중지된 채로 남지 않도록 안전장치
    trap '"${COMPOSE_CMD[@]}" -p "$STACK_NAME" start' EXIT
fi

# 매핑 기록용 임시 jsonl 파일 생성 (한 줄에 객체 하나씩, 마지막에 jq로 병합)
TEMP_JSON="./temp_volume_info.jsonl"
> "$TEMP_JSON"  # 초기화

# 각 볼륨에 대해
for VOLUME in $VOLUMES; do
    # 각 컨테이너에서
    for CONTAINER in $CONTAINERS; do
        # 매핑 정보를 찾는다.
        SOURCE=$(docker inspect "$CONTAINER" | \
            jq -r --arg name "$VOLUME" '.[] | .Mounts[]? | select(.Name == $name) | .Source')
        DESTINATION=$(docker inspect "$CONTAINER" | \
            jq -r --arg name "$VOLUME" '.[] | .Mounts[]? | select(.Name == $name) | .Destination')

        # 매핑 정보를 찾은 경우에는
        if [ -n "$SOURCE" ] && [ -n "$DESTINATION" ]; then
            # 매핑 정보를 기록하고 (jq -n으로 특수문자 이스케이프 안전하게 생성)
            jq -n --arg container "$CONTAINER" --arg volume "$VOLUME" --arg destination "$DESTINATION" \
                '{container: $container, volume: $volume, destination: $destination}' >> "$TEMP_JSON"
            # 해당 데이터를 복사해온다. (대상 폴더가 미리 존재하면 안으로 중첩 복사되므로 만들지 않는다)
            docker cp "$CONTAINER:$DESTINATION" "$BACKUP_TARGET/$VOLUME"
        fi
    done
done

if [ "$NO_STOP" == false ]; then
    console_out "스택을 다시 시작합니다."
    "${COMPOSE_CMD[@]}" -p "$STACK_NAME" start
    trap - EXIT
fi

# jsonl을 "컨테이너명": {volume, destination} 형태의 단일 JSON 객체로 병합
jq -s 'map({(.container): {volume: .volume, destination: .destination}}) | add // {}' \
    "$TEMP_JSON" > "$BACKUP_TARGET/volume-map.json"
rm "$TEMP_JSON"

console_out "백업 폴더를 압축합니다."
tar -cvzf "$BACKUP_HOME"/"$BACKUP_NAME".tar.gz -C "$BACKUP_TARGET" .

console_out "백업 폴더를 삭제합니다."
rm -rf "$BACKUP_TARGET"

console_out "볼륨 백업 성공!!!"
exit 0
