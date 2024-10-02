# Makefile

SCRIPT_HOME := ./_script

.PHONY: help get-config get-volume get-compose up down status start stop restart backup restore clear

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# s3 -> ec2
get-config: ## S3로부터 config파일 다운로드(수정가능)
	bash $(SCRIPT_HOME)/get-config.sh
get-compose: ## S3로부터 compose명세 다운로드(수정가능)
	bash $(SCRIPT_HOME)/get-compose.sh
get-volume: ## S3로부터 volume파일 다운로드(수정가능)
	bash $(SCRIPT_HOME)/get-volume.sh

# stack
up: ## Docker 스택을 생성
	bash $(SCRIPT_HOME)/stack-up.sh
down: ## Docker 스택을 제거
	bash $(SCRIPT_HOME)/stack-down.sh

# service
status: ## Docker 컨테이너의 상태 조회
	bash $(SCRIPT_HOME)/service-status.sh
start: ## Docker 컨테이너 시작
	bash $(SCRIPT_HOME)/service-start.sh
stop: ## Docker 컨테이너 중지
	bash $(SCRIPT_HOME)/service-stop.sh
apply: ## Docker 컨테이너 변경사항 적용
	bash $(SCRIPT_HOME)/service-apply.sh
restart: ## Docker 컨테이너 재시작
	bash $(SCRIPT_HOME)/service-restart.sh

# backup
backup: ## Docker 스택 백업
	bash $(SCRIPT_HOME)/stack-backup.sh
restore: ## 백업 파일로부터 Docker 스택정보를 복원
	bash $(SCRIPT_HOME)/stack-restore.sh

# others
clear: ## 사용하지 않는 도커 데이터 삭제
	docker system prune -f
