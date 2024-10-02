#!/bin/bash
# 도커 volume파일을 S3로부터 가져와 적용합니다.

# 명령어 실패 시 스크립트 즉시 종료되도록 설정
set -e

# 공통 스크립트를 가져옵니다. 
source ./_script/common.sh

# 프로젝트 폴더가 존재하는지 검사
check_project_dir_not_exist

# TODO: 배포 이전에 볼륨폴더 전체 삭제가 필요할 경우 활성화해주세요.
#rm -rf $VOLUME_HOME/*

# TODO: 경우에 따라 다른 수단으로 볼륨 가져오기를 진행할 수 있습니다.
console_out "볼륨 내용물을 가져옵니다."
aws s3 cp s3://"$S3_VOLUME_HOME"/ "$VOLUME_HOME"/ --recursive

# TODO: 경우에 따라 로직을 추가해주세요
# ...

console_out "볼륨 가져오기 완료!!!"