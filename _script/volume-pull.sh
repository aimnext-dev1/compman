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

# 스택 이름이 포함된 도커 볼륨 리스트 추출
VOLUMES=$(docker volume ls --filter name=$STACK_NAME --format '{{.Name}}')
CONTAINERS=$("${COMPOSE_CMD[@]}" -p $STACK_NAME ps -a --format '{{.Name}}')

if [ -z "$VOLUMES" ]; then
    echo "Pull할 볼륨이 없습니다."
    exit 1
fi

if [ -d "$VOLUME_HOME" ]; then
    echo "이미 pull받은 볼륨 폴더가 존재합니다. 삭제합니다."
    rm -rf "$VOLUME_HOME"
fi
mkdir -p "$VOLUME_HOME"

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
            # 해당 데이터를 복사해온다.
            docker cp "$CONTAINER:$DESTINATION" "$VOLUME_HOME/$VOLUME"
        fi
    done
done

# JSON 포맷에 알맞게 저장
# 마지막 줄 쉼표 제거
sed '$ s/,$//' "$TEMP_JSON" > "$TEMP_JSON.cleaned"
# 중괄호로 감싸고 최종 JSON 만들기
echo "{" > "$VOLUME_HOME/volume-map.json"
cat "$TEMP_JSON.cleaned" >> "$VOLUME_HOME/volume-map.json"
echo "}" >> "$VOLUME_HOME/volume-map.json"
# 임시파일 삭제
rm "$TEMP_JSON" "$TEMP_JSON.cleaned"

console_out "볼륨 Pull 성공!!!"
exit 0