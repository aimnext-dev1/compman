#!/bin/bash

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e
# 현재 스크립트가 있는 경로를 기준으로 합니다.
cd "$(dirname "$0")"
# 공통 스크립트를 가져옵니다. 
source ./common.sh

CONFIG_HOME="../_project/config"
CONFIG_HOME_SRC="<설정원본위치>"
CONFIG_HOME_DST="<설정이동위치>"

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# TODO: 배포 이전에 설정폴더 전체 삭제가 필요할 경우 활성화해주세요.
#rm -rf $CONFIG_HOME/*

# TODO: 경우에 따라 다른 수단으로 배포를 진행할 수 있습니다.
console_out "설정 내용물을 가져옵니다."
# aws s3 cp s3://"$CONFIG_HOME_SRC"/ "$CONFIG_HOME_DST"/ --recursive

# TODO: 경우에 따라 로직을 추가해주세요
# ...

console_out "설정 가져오기 완료!!!"
