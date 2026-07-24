#!/bin/bash
# 도커 프로젝트 배포를 위한 스크립트입니다.
# 실행중인 자기 자신을 덮어쓰기를 방지하기 위해 독립된 스크립트로 작성합니다.
#
# 다운로드를 임시 폴더에 받은 뒤 성공한 경우에만 실제 경로로 교체합니다.
# (중간에 네트워크 실패 등이 나도 기존 파일이 훼손되지 않습니다.)
#
# 사용방법: ./deploy.sh [dev|prod]

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"

RUN_ENV_PARAM=$1
# 실행환경 파라미터가 없으면 기본값은 dev
# project-deploy는 인프라 환경에서만 실행되므로, dev로 설정합니다.
RUN_ENV=${RUN_ENV_PARAM:-"dev"}

if [ "$RUN_ENV" == "dev" ]; then
  S3_BUCKET_PROJECT_PATH="<개발환경 배포할 프로젝트 S3 경로>"
elif [ "$RUN_ENV" == "prod" ]; then
  S3_BUCKET_PROJECT_PATH="<운영환경 배포할 프로젝트 S3 경로>"
else
  echo "지원하지 않는 실행환경입니다: $RUN_ENV (dev, prod 중 하나를 입력해주세요)"
  exit 1
fi

TMP_DIR=$(mktemp -d "./.deploy_tmp.XXXXXX")
# 스크립트가 어떤 경로로 끝나든(성공/실패) 임시 폴더는 정리
trap 'rm -rf "$TMP_DIR"' EXIT

# 1. 임시 폴더로 전부 내려받는다 (실패시 set -e로 여기서 즉시 중단, 기존 파일은 그대로 유지됨)
aws s3 cp "$S3_BUCKET_PROJECT_PATH/Makefile" "$TMP_DIR/Makefile"

mkdir -p "$TMP_DIR/_project_compose"
aws s3 cp --recursive "$S3_BUCKET_PROJECT_PATH/_project/compose" "$TMP_DIR/_project_compose"

## _project/config 다운로드(필요한 경우 주석 해제 후 사용)
#mkdir -p "$TMP_DIR/_project_config"
#aws s3 cp --recursive "$S3_BUCKET_PROJECT_PATH/_project/config" "$TMP_DIR/_project_config"

## _project/volume 다운로드(필요한 경우 주석 해제 후 사용)
#mkdir -p "$TMP_DIR/_project_volume"
#aws s3 cp --recursive "$S3_BUCKET_PROJECT_PATH/_project/volume" "$TMP_DIR/_project_volume"

mkdir -p "$TMP_DIR/_script"
aws s3 cp --recursive "$S3_BUCKET_PROJECT_PATH/_script" "$TMP_DIR/_script"

# 2. 모든 다운로드가 성공한 경우에만 실제 경로로 교체한다
mv "$TMP_DIR/Makefile" ./Makefile

rm -rf _project/compose
mv "$TMP_DIR/_project_compose" _project/compose

## _project/config 교체(필요한 경우 주석 해제 후 사용)
#rm -rf _project/config
#mv "$TMP_DIR/_project_config" _project/config

## _project/volume 교체(필요한 경우 주석 해제 후 사용)
#rm -rf _project/volume
#mv "$TMP_DIR/_project_volume" _project/volume

rm -rf _script
mv "$TMP_DIR/_script" _script

#
# (배포 과정이 더 필요한 경우 스크립트를 추가하여 사용하세요)
#

echo "배포 성공!"
exit 0
