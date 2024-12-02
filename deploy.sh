#!/bin/bash
# 도커 프로젝트 배포를 위한 스크립트입니다.
# 실행중인 자기 자신을 덮어쓰기를 방지하기 위해 독립된 스크립트로 작성합니다.
#
# 사용방법: ./deploy.sh

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
fi

# 1. Makefile 덮어쓰기
aws s3 cp "$S3_BUCKET_PROJECT_PATH/Makefile" ./Makefile

# 2. _project 덮어쓰기
## _project/compose 덮어쓰기(필수)
rm -rf _project/compose/*
aws s3 cp --recursive "$S3_BUCKET_PROJECT_PATH/_project/compose" ./_project/compose

## _project/config  덮어쓰기(필요한 경우 주석 해제 후 사용)
#rm -rf _project/config/*
#aws s3 cp --recursive "$S3_BUCKET_PROJECT_PATH/_project/config" ./_project/config

## _project/volume  덮어쓰기(필요한 경우 주석 해제 후 사용)
#rm -rf _project/volume/*
#aws s3 cp --recursive "$S3_BUCKET_PROJECT_PATH/_project/volume" ./_project/volume

# 3. _script 덮어쓰기
rm -rf _script/*
aws s3 cp --recursive "$S3_BUCKET_PROJECT_PATH/_script" ./_script

#
# (배포 과정이 더 필요한 경우 스크립트를 추가하여 사용하세요)
#

# deploy.sh 스크립트 덮어쓰기
echo "배포 성공!"
exit 0