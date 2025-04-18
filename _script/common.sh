#!/bin/bash
# 해당 파일은 각 프로젝트의 자동화 스크립트가 공통으로 사용합니다.
# 작성자: 김승범

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e

FOLDER_NAME="<루트폴더명>"
PROJECT_HOME="../_project"
STACK_NAME="<스택이름>"

# docker-compose가 설치되어 있는지 확인
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# 함수: 잘 보이는 로그 출력
# 입력: 출력할 문자열
# 출력: 빨간 로그 출력
#   출력 예시: *** This is log message ***
console_out() {
    local separator_char="*"
    local separator_length=3
    local message="$1"

    # 구분 문자열 생성(시작)
    local result_message=""
    for ((i = 0; i < separator_length; i++)); do
        result_message="${result_message}${separator_char}"
    done

    # 메시지 삽업
    result_message="${result_message} ${message} "

    # 구분 문자열 생성(끝)
    for ((i = 0; i < separator_length; i++)); do
        result_message="${result_message}${separator_char}"
    done

    echo -e "\n\e[1;31m$result_message\e[0m"
}

# 함수: Docker 폴더가 존재하는지 확인
# 입력: X
# 출력: 폴더가 없는경우 스크립트 종료
check_project_dir_not_exist() {
    console_out "$FOLDER_NAME 폴더가 존재하는지 확인합니다."

    local is_exist="$PROJECT_HOME"

    # 폴더가 존재하는지 검사
    if [ -z "$FOLDER_NAME" ] && [ ! -d "$is_exist" ]; then
        echo "$FOLDER_NAME" 폴더는 docker 폴더내에 존재하지 않습니다.
        exit 1
    fi
}

# 함수: compose 스택 존재여부 확인
# 입력: X
# 출력: 스택이 없는 경우 스크립트 종료
check_project_not_exist() {
    console_out "$STACK_NAME 스택이 존재하는지 확인합니다."

    local is_exist=$("$COMPOSE_CMD" ls -a | awk '{print $1}' | grep "^$STACK_NAME\$")

    if [[ -z $is_exist ]]; then
        echo "스택이 없습니다. make up 후 다시 시도해주세요."
        exit 1
    fi
}

# 함수: compose 스택 미존재여부 확인
# 입력: X
# 출력: 스택이 있는 경우 스크립트 종료
check_project_exist() {
    console_out "$STACK_NAME 스택이 없는지 확인합니다."

    local is_exist=$("$COMPOSE_CMD" ls -a | awk '{print $1}' | grep "^$STACK_NAME\$")

    if [[ -n $is_exist ]]; then
        echo "$is_exist 스택이 이미 존재합니다. make down 후 다시 시도해주세요."
        exit 1
    fi
}

# 함수: aws secrets manager에서 값을 가져옵니다.
# 입력: arn(AWS 리소스 식별값)
# 출력: 해당 arn의 비밀값 정보들
get_secrets_from_aws() {
    local arn="$1"
    aws secretsmanager get-secret-value --secret-id "$arn" --query SecretString --output text
}

# 함수: json에서 키에 해당하는 값을 가져옵니다.
# 입력: json(json 데이터), key(가져올 키값)
# 출력: key에 해당하는 값
get_value_from_json() {
    local json="$1"
    local key="$2"
    echo "$json" | jq -r --arg key "$key" '.[$key]'
}