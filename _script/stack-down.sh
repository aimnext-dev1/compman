#!/bin/bash
# 도커 컴포즈 스택을 생성합니다.
# 사용방법: ./stack-compose.sh

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e

# 공통 스크립트를 가져옵니다. 
source ./_script/common.sh

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker-compose 스택 없으면 진행 불가능
check_project_not_exist

# 사용자에게 확인을 요청
console_out "스택 내의 모든 컨테이너가 삭제됩니다."
read -r -p "계속하시겠습니까? (y/n): " answer

# 사용자가 'y'를 입력했는지 확인
if [ "$answer" == "y" ] || [ "$answer" == "Y" ]; then
    # 스택 종료 로직
    console_out "스택 삭제 작업중"
    docker-compose -p "$STACK_NAME" down
    console_out "스택 삭제 완료!"
else
    console_out "스택 삭제 취소!"
fi



