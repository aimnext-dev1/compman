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

COMPOSE_HOME="../_project/compose"

RUN_ENV_PARAM=$1
# 실행환경 파라미터가 없으면 기본값은 local
RUN_ENV=${RUN_ENV_PARAM:-"local"}

STACK_NAME="<스택명>"
if [ "$RUN_ENV" == "dev" ]; then
  COMPOSE_FILE_NAME="<개발환경 도커 컴포즈 명세파일명>"
  # 필요한 경우 활성화 하여 사용
  #ENV_FILE_PATH="<개발환경 환경변수 파일 경로>"
elif [ "$RUN_ENV" == "prod" ]; then
  COMPOSE_FILE_NAME="<운영환경 도커 컴포즈 명세파일명>"
  # 필요한 경우 활성화 하여 사용
  #ENV_FILE_PATH="<운영환경 환경변수 파일 경로>"
elif [ "$RUN_ENV" == "local" ]; then
  COMPOSE_FILE_NAME="<로컬환경 도커 컴포즈 명세파일명>"
  # 필요한 경우 활성화 하여 사용
  #ENV_FILE_PATH="<로컬환경 환경변수 파일 경로>"
fi

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# docker-compose 스택 있으면 진행 불가능
check_project_exist

console_out "스택 명세 파일이 존재하는지 검사합니다."
COMPOSE_FILE=$(find "$COMPOSE_HOME" -maxdepth 1 -name "$COMPOSE_FILE_NAME" | head -n 1)

# 파일이 존재하는지 확인
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "$COMPOSE_HOME 경로에 스택 명세 파일이 존재하지 않습니다."
  console_out "스택 생성 실패!!!"
  exit 1
fi

console_out "스택을 생성합니다."
# 환경변수 파일이 존재하는지 확인 후 적절한 명령어 실행
if [ -z "$ENV_FILE_PATH" ]; then
  docker-compose -p "$STACK_NAME" -f "$COMPOSE_FILE" up -d
else
  docker-compose -p "$STACK_NAME" --env-file "$ENV_FILE_PATH" -f "$COMPOSE_FILE" up -d
fi

console_out "스택 생성 성공!!!"
exit 0