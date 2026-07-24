#!/bin/bash

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

VOLUME_HOME="../_volume"


# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker compose 스택 없으면 진행 불가능
check_project_not_exist

# 볼륨 백업
console_out "볼륨 Pull을 수행합니다."

# 이 스택이 관리하는(컴포즈 라벨 기준) 볼륨/컨테이너만 추출 (이름 부분일치로 인한 다른 스택 침범 방지)
VOLUMES=$(docker volume ls --filter "label=com.docker.compose.project=$STACK_NAME" --format '{{.Name}}')
CONTAINERS=$("${COMPOSE_CMD[@]}" -p "$STACK_NAME" ps -a --format '{{.Name}}')

if [ -z "$VOLUMES" ]; then
    echo "Pull할 볼륨이 없습니다."
    exit 1
fi

if [ -d "$VOLUME_HOME" ]; then
    echo "이미 pull받은 볼륨 폴더가 존재합니다. 삭제합니다."
    rm -rf "$VOLUME_HOME"
fi
mkdir -p "$VOLUME_HOME"

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
            # 해당 데이터를 복사해온다.
            docker cp "$CONTAINER:$DESTINATION" "$VOLUME_HOME/$VOLUME"
        fi
    done
done

# jsonl을 "컨테이너명": {volume, destination} 형태의 단일 JSON 객체로 병합
jq -s 'map({(.container): {volume: .volume, destination: .destination}}) | add // {}' \
    "$TEMP_JSON" > "$VOLUME_HOME/volume-map.json"
rm "$TEMP_JSON"

console_out "볼륨 Pull 성공!!!"
exit 0