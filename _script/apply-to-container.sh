#!/bin/bash
# 도커 컨테이너에 파일을 적용합니다. (ex. 설정파일 등)
#
# 사용방법: ./apply-to-container.sh
#     -> 적용 로직은 사용자 직접 작성해야 합니다.

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

# 적용할 설정파일 경로
CONFIG_FILE_ON_HOST="<설정파일경로(호스트)>"
CONFIG_FILE_ON_CONTAINER="<설정파일경로(컨테이너)>"

CONTAINER_NAME="<컨테이너명>"
CONTAINER_KEY=$(docker ps -a | grep $CONTAINER_NAME | xargs | awk '{print $1}')

# 값 변경
# TODO: 프로젝트에 따라 알맞게 수정
# # 예시) AWS Secret Manager를 통해 가져온 값으로 변경
# # config 폴더의 설정파일 경로(latest)
# CONFIG_FILE="/home/ec2-user/docker/dtx-docker-manager/_project/config/settings.yml"

# SECRETS_MANAGER_ARN="arn:aws:secretsmanager:ap-northeast-2:547035688495:secret:dev/aws/cloudwatch/access-e4F9bo"
# SECRETS=$(get_secrets_from_aws "$SECRETS_MANAGER_ARN")

# KEY_ACCESS_KEY="aws/cloudwatch/accesskey"
# KEY_SECRET_KEY="aws/cloudwatch/secretkey"

# console_out "키값을 가져옵니다."
# VALUE_ACCESS_KEY=$(get_value_from_json "$SECRETS" "$KEY_ACCESS_KEY")
# VALUE_SECRET_KEY=$(get_value_from_json "$SECRETS" "$KEY_SECRET_KEY")

# console_out "값을 설정합니다.."
# sed -i "s|var.access_key_id: '.*'|var.access_key_id: '$VALUE_ACCESS_KEY'|" "$CONFIG_FILE"
# sed -i "s|var.secret_access_key: '.*'|var.secret_access_key: '$VALUE_SECRET_KEY'|" "$CONFIG_FILE"

console_out "수정한 설정파일을 컨테이너로 전달합니다."
docker cp "$CONFIG_FILE_ON_HOST" "$CONTAINER_KEY":$CONFIG_FILE_ON_CONTAINER

console_out "설정 적용 성공!!!"