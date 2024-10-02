#!/bin/bash
# 도커 컴포즈 스택을 생성합니다.
# 사용방법: ./stack-compose.sh

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e

COMPOSE_HOME="<컴포즈폴더경로(/_project/_compose)>"

STACK_NAME="<스택명>"
COMPOSE_FILE_NAME="<도커컴포즈명세파일명>"

# 공통 스크립트를 가져옵니다. 
source ./_script/common.sh

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker-compose 스택 있으면 진행 불가능
check_project_exist

console_out "스택 명세 파일이 존재하는지 검사합니다."
COMPOSE_FILE=$(find "$COMPOSE_HOME" -maxdepth 1 -name "$COMPOSE_FILE_NAME" | head -n 1)

# 파일이 존재하는지 확인
if [ -z "$COMPOSE_FILE" ]; then
  echo "$COMPOSE_HOME 경로에 스택 명세 파일이 존재하지 않습니다."
  console_out "스택 생성 실패!!!"
  exit 1
fi

console_out "스택을 생성합니다."
docker-compose -p "$STACK_NAME" -f "$COMPOSE_FILE" up -d

console_out "스택 생성 성공!!!"
