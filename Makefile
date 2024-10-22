# Makefile

SCRIPT_HOME := ./_script
PARAM := $(word 2, $(MAKECMDGOALS))

.PHONY: help up down status start stop restart backup restore clear connect log

# make 입력시 명령어 설명 출력
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# stack
up: ## Docker 스택을 생성
	bash $(SCRIPT_HOME)/stack-up.sh
down: ## Docker 스택을 제거
	bash $(SCRIPT_HOME)/stack-down.sh

# service
status: ## Docker 컨테이너의 상태 조회
	bash $(SCRIPT_HOME)/service-status.sh
start: ## Docker 컨테이너 시작
	bash $(SCRIPT_HOME)/service-start.sh $(PARAM)
stop: ## Docker 컨테이너 중지
	bash $(SCRIPT_HOME)/service-stop.sh $(PARAM)
restart: ## Docker 컨테이너 재시작
	bash $(SCRIPT_HOME)/service-restart.sh $(PARAM)
connect: ## Docker 컨테이너 접속
	bash $(SCRIPT_HOME)/service-connect.sh
log: ## Docker 컨테이너 로그 조회
	bash $(SCRIPT_HOME)/service-log.sh

# backup
backup: ## Docker 스택 백업
	bash $(SCRIPT_HOME)/stack-backup.sh
restore: ## 백업 파일로부터 Docker 스택정보를 복원
	bash $(SCRIPT_HOME)/stack-restore.sh $(PARAM)

# others
clear: ## 사용하지 않는 도커 데이터 삭제
	docker system prune -f