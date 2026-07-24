#!/bin/bash
# 도커 컴포즈 스택을 생성합니다.
#
# 사용방법: ./stack-compose.sh

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh


# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker compose 스택 없으면 진행 불가능
check_project_not_exist

# 사용자에게 확인을 요청
console_out "스택 내의 모든 컨테이너가 삭제됩니다."
read -p "스택을 정말 삭제하시겠습니까? (y/n): " confirm
if [[ "$confirm" != "y" ]]; then
    echo "취소됨"
    exit 0
fi

console_out "스택 삭제 작업중"
"${COMPOSE_CMD[@]}" -p "$STACK_NAME" down
console_out "스택 삭제 완료!"

exit 0


