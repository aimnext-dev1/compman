#!/bin/bash
# 해당 파일은 각 프로젝트의 자동화 스크립트가 공통으로 사용합니다.
# 작성자: 김승범

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e

PROJECT_HOME="../_project"

# 프로젝트 루트의 stack.env를 불러옵니다. (없으면 'make init'으로 생성)
STACK_ENV_FILE="../stack.env"
if [ ! -f "$STACK_ENV_FILE" ]; then
    echo "$STACK_ENV_FILE 파일이 없습니다. 'make init' 실행 후 값을 채워주세요."
    exit 1
fi
set -a
source "$STACK_ENV_FILE"
set +a

: "${FOLDER_NAME:?FOLDER_NAME이 stack.env에 설정되지 않았습니다.}"
: "${STACK_NAME:?STACK_NAME이 stack.env에 설정되지 않았습니다.}"

# docker compose(v2) 우선, 없으면 docker-compose(v1) 사용
if docker compose version &> /dev/null; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD=(docker-compose)
else
    echo "docker compose(v2) 또는 docker-compose(v1)를 찾을 수 없습니다."
    exit 1
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

    printf '\n\033[1;31m%s\033[0m\n' "$result_message"
}

# 함수: Docker 폴더가 존재하는지 확인
# 입력: X
# 출력: 폴더가 없는경우 스크립트 종료
check_project_dir_not_exist() {
    console_out "$FOLDER_NAME 폴더가 존재하는지 확인합니다."

    # 폴더가 존재하는지 검사
    if [ ! -d "$PROJECT_HOME" ]; then
        echo "$FOLDER_NAME 폴더는 docker 폴더내에 존재하지 않습니다."
        exit 1
    fi
}

# 함수: compose 스택 존재여부 확인
# 입력: X
# 출력: 스택이 없는 경우 스크립트 종료
check_project_not_exist() {
    console_out "$STACK_NAME 스택이 존재하는지 확인합니다."

    local is_exist=$("${COMPOSE_CMD[@]}" ls -a | awk '{print $1}' | grep "^$STACK_NAME\$")

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

    local is_exist=$("${COMPOSE_CMD[@]}" ls -a | awk '{print $1}' | grep "^$STACK_NAME\$")

    if [[ -n $is_exist ]]; then
        echo "$is_exist 스택이 이미 존재합니다. make down 후 다시 시도해주세요."
        exit 1
    fi
}

# 함수: 실행환경에 맞는 compose -f 옵션과 env-file 경로를 구성합니다.
# stack.env에 COMPOSE_BASE_FILE이 설정되어 있으면 base + 환경별 override 파일을
# -f 여러개로 조합합니다(compose 네이티브 오버레이 방식). 없으면 환경별 파일
# 하나만 단독으로 사용합니다.
# 입력: run_env(local/dev/prod)
# 출력: 전역 배열 COMPOSE_FILES, 전역 변수 ENV_FILE_PATH 설정. 지원하지 않는
#       환경이거나 명세 파일을 찾지 못하면 스크립트 종료
resolve_compose_files() {
    local run_env="$1"
    local compose_home="../_project"
    local compose_file_name env_file_path

    case "$run_env" in
        dev)   compose_file_name="$COMPOSE_FILE_DEV";   env_file_path="$ENV_FILE_DEV" ;;
        prod)  compose_file_name="$COMPOSE_FILE_PROD";  env_file_path="$ENV_FILE_PROD" ;;
        local) compose_file_name="$COMPOSE_FILE_LOCAL"; env_file_path="$ENV_FILE_LOCAL" ;;
        *)
            echo "지원하지 않는 실행환경입니다: $run_env (local, dev, prod 중 하나를 입력해주세요)"
            exit 1
            ;;
    esac

    if [ -z "$compose_file_name" ]; then
        echo "$run_env 환경의 COMPOSE_FILE_* 값이 stack.env에 설정되지 않았습니다."
        exit 1
    fi

    local compose_file
    compose_file=$(find "$compose_home" -maxdepth 1 -name "$compose_file_name" | head -n 1)
    if [ ! -f "$compose_file" ]; then
        echo "$compose_home 경로에 스택 명세 파일이 존재하지 않습니다: $compose_file_name"
        exit 1
    fi

    COMPOSE_FILES=(-f "$compose_file")

    if [ -n "$COMPOSE_BASE_FILE" ]; then
        local base_file
        base_file=$(find "$compose_home" -maxdepth 1 -name "$COMPOSE_BASE_FILE" | head -n 1)
        if [ ! -f "$base_file" ]; then
            echo "$compose_home 경로에 베이스 명세 파일이 존재하지 않습니다: $COMPOSE_BASE_FILE"
            exit 1
        fi
        COMPOSE_FILES=(-f "$base_file" -f "$compose_file")
    fi

    ENV_FILE_PATH="$env_file_path"
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