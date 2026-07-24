# Makefile

SCRIPT_HOME := ./_script
PARAMS := $(wordlist 2, $(words $(MAKECMDGOALS)), $(MAKECMDGOALS))

# 추가 인자를 make 타겟으로 오인해 "No rule to make target"이 나지 않도록 흡수
%:
	@:

.DEFAULT_GOAL := help

.PHONY: help init up down update status start stop restart connect log \
        volume-pull volume-push volume-backup volume-restore \
        image-backup image-restore clear

# make 입력시 명령어 설명 출력
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# setup
init: ## stack.env 생성 (최초 1회, 이미 있으면 건드리지 않음)
	@if [ -f stack.env ]; then \
		echo "stack.env가 이미 존재합니다. 건드리지 않았습니다."; \
	else \
		cp stack.env.example stack.env; \
		echo "stack.env를 생성했습니다. 값을 채운 후 다시 실행해주세요."; \
	fi

# stack
up: ## Docker 스택을 생성 / 실행환경: local(DEFAULT), dev, prod
	bash $(SCRIPT_HOME)/stack-up.sh $(PARAMS)
down: ## Docker 스택을 제거
	bash $(SCRIPT_HOME)/stack-down.sh
update: ## Docker 스택을 업데이트
	bash $(SCRIPT_HOME)/stack-update.sh

# service
status: ## Docker 컨테이너의 상태 조회
	bash $(SCRIPT_HOME)/service-status.sh
start: ## Docker 컨테이너 시작 (서비스명 여러개 지정 가능, 비우면 전체)
	bash $(SCRIPT_HOME)/service-start.sh $(PARAMS)
stop: ## Docker 컨테이너 중지 (서비스명 여러개 지정 가능, 비우면 전체)
	bash $(SCRIPT_HOME)/service-stop.sh $(PARAMS)
restart: ## Docker 컨테이너 재시작 (서비스명 여러개 지정 가능, 비우면 전체)
	bash $(SCRIPT_HOME)/service-restart.sh $(PARAMS)
connect: ## Docker 컨테이너 접속
	bash $(SCRIPT_HOME)/service-connect.sh $(PARAMS)
log: ## Docker 컨테이너 로그 조회
	bash $(SCRIPT_HOME)/service-log.sh $(PARAMS)

# volume
volume-pull: ## Docker 볼륨 다운로드
	bash $(SCRIPT_HOME)/volume-pull.sh
volume-push: ## Docker 볼륨 업로드
	bash $(SCRIPT_HOME)/volume-push.sh

# backup
volume-backup: ## Docker 볼륨 백업
	bash $(SCRIPT_HOME)/volume-backup.sh
volume-restore: ## 백업 파일로부터 Docker 볼륨을 복원
	bash $(SCRIPT_HOME)/volume-restore.sh $(PARAMS)
image-backup: ## Docker 이미지 백업
	bash $(SCRIPT_HOME)/image-backup.sh
image-restore: ## 백업 파일로부터 Docker 이미지를 복원
	bash $(SCRIPT_HOME)/image-restore.sh $(PARAMS)

# others
clear: ## 사용하지 않는 도커 이미지 전체 삭제 (docker image prune -af)
	docker image prune -af