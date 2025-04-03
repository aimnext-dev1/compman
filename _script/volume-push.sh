#!/bin/bash

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

VOLUME_HOME="../_volume"
STACK_NAME="<스택명>"

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker-compose 스택 없으면 진행 불가능
check_project_not_exist

console_out "볼륨 데이터를 복원합니다."
VOLUME_MAP_FILE="$VOLUME_HOME/volume-map.json"

if [ -f "$VOLUME_MAP_FILE" ]; then
    # JSON을 한 줄씩 key-value 쌍으로 파싱
    jq -r 'to_entries[] | "\(.key) \(.value.volume) \(.value.destination)"' "$VOLUME_MAP_FILE" | while read -r CONTAINER VOLUME DESTINATION; do        
        echo "컨테이너 $CONTAINER 의 복원할 볼륨: $VOLUME → $DESTINATION"

        # 복사할 데이터가 있는지 확인
        if [ ! -d "$VOLUME_HOME/$VOLUME" ]; then
            echo "경고: 복원 데이터 디렉토리가 없습니다: $VOLUME_HOME/$VOLUME"
            continue
        fi

        docker cp "$VOLUME_HOME/$VOLUME/." "$CONTAINER:$DESTINATION"
    done
fi

console_out "볼륨 복원 완료!!!"
exit 0