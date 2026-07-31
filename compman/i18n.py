from __future__ import annotations

import os
from typing import Any

_CURRENT_LANG: str | None = None


def get_lang() -> str:
    global _CURRENT_LANG
    if _CURRENT_LANG:
        return _CURRENT_LANG
    env_lang = os.environ.get("COMPMAN_LANG", "en").lower()
    if env_lang in ("ko", "ko_kr", "korean"):
        return "ko"
    return "en"


def set_lang(lang: str | None) -> None:
    global _CURRENT_LANG
    if lang and lang.lower() in ("en", "ko"):
        _CURRENT_LANG = lang.lower()


TRANSLATIONS: dict[str, dict[str, str]] = {
    # Command descriptions
    "cmd.root": {
        "en": (
            "Docker Compose Stack Manager CLI.\n\n"
            "Language Options:\n"
            "  • Use --lang / -l <en|ko> option for a one-time language switch.\n"
            "  • Set COMPMAN_LANG=ko environment variable for a permanent setting.\n"
            "  • Run 'compman lang' to view current language or see environment setup guides."
        ),
        "ko": (
            "Docker Compose 스택 및 배포 관리 CLI.\n\n"
            "언어 설정 방법:\n"
            "  • --lang / -l <en|ko> 옵션으로 1회성 언어 전환 가능.\n"
            "  • COMPMAN_LANG=ko 환경 변수를 설정하여 영구 언어 지정 가능.\n"
            "  • 'compman lang' 명령어로 현재 언어 상태 및 설정 방법 확인 가능."
        ),
    },
    "cmd.lang": {
        "en": (
            "Display current language or switch CLI language.\n\n"
            "Examples:\n"
            "  compman lang\n"
            "  compman lang ko\n"
            "  compman lang en"
        ),
        "ko": (
            "현재 CLI 언어 상태를 표시하거나 언어를 변경합니다.\n\n"
            "사용 예시:\n"
            "  compman lang\n"
            "  compman lang ko\n"
            "  compman lang en"
        ),
    },
    "cmd.init": {
        "en": (
            "Initialize project config, fetch S3 package, or generate seed project.\n\n"
            "Provides interactive choices:\n"
            "  1. Create skeleton config (compman.yml)\n"
            "  2. Fetch package from S3 URL\n"
            "  3. Generate test seed project\n\n"
            "Examples:\n"
            "  compman init\n"
            "  compman init --skeleton\n"
            "  compman init --s3 s3://my-bucket/app.tar.gz --build\n"
            "  compman init --seed -o project -p 8080"
        ),
        "ko": (
            "프로젝트 설정, S3 패키지 수신 또는 시드 프로젝트를 생성합니다.\n\n"
            "대화형 선택 지원:\n"
            "  1. 스켈레톤 설정 (compman.yml) 생성\n"
            "  2. S3 URL로부터 패키지 수신 및 프로젝트 생성\n"
            "  3. 테스트용 Seed 프로젝트 생성\n\n"
            "사용 예시:\n"
            "  compman init\n"
            "  compman init --skeleton\n"
            "  compman init --s3 s3://my-bucket/app.tar.gz --build\n"
            "  compman init --seed -o project -p 8080"
        ),
    },
    "cmd.clear": {
        "en": (
            "Prune unused Docker images and build cache.\n\n"
            "Frees disk space by removing dangling and unused container images.\n\n"
            "Examples:\n"
            "  compman clear"
        ),
        "ko": (
            "사용하지 않는 Docker 이미지 및 빌드 캐시를 정리합니다.\n\n"
            "dangling 및 미사용 이미지를 정리하여 디스크 공간을 확보합니다.\n\n"
            "사용 예시:\n"
            "  compman clear"
        ),
    },
    "cmd.deploy": {
        "en": (
            "Fetch application package from S3 and generate scaffold.\n\n"
            "Downloads a project directory or archive (.tar.gz/.zip) from S3, extracts it, and optionally builds the image.\n\n"
            "Examples:\n"
            "  compman deploy --path s3://my-bucket/app\n"
            "  compman deploy --path s3://my-bucket/app.tar.gz --build"
        ),
        "ko": (
            "S3에서 애플리케이션 패키지를 다운로드하고 스캐폴드를 생성합니다.\n\n"
            "S3 경로 또는 아카이브(.tar.gz/.zip)를 다운로드하여 해제하고, 필요시 이미지를 빌드합니다.\n\n"
            "사용 예시:\n"
            "  compman deploy --path s3://my-bucket/app\n"
            "  compman deploy --path s3://my-bucket/app.tar.gz --build"
        ),
    },
    "cmd.update": {
        "en": (
            "Fetch S3 package (if configured), build image, and update stack.\n\n"
            "If S3 deploy path is set in compman.yml, fetches latest package first. Otherwise, rebuilds local image and updates stack.\n\n"
            "Examples:\n"
            "  compman update\n"
            "  compman update dev"
        ),
        "ko": (
            "최신 S3 패키지를 수신(설정 시)하고 이미지 빌드 및 스택을 갱신합니다.\n\n"
            "compman.yml에 S3 경로가 설정된 경우 최신 패키지를 먼저 수신하며, 설정이 없으면 로컬 빌드로 갱신합니다.\n\n"
            "사용 예시:\n"
            "  compman update\n"
            "  compman update dev"
        ),
    },
    "cmd.completion": {
        "en": (
            "Output or install shell auto-completion script.\n\n"
            "Supports powershell, bash, zsh, and fish shells.\n\n"
            "Examples:\n"
            "  compman completion powershell\n"
            "  compman completion bash --install"
        ),
        "ko": (
            "Shell 자동완성(Tab-completion) 스크립트를 출력하거나 자동 등록합니다.\n\n"
            "powershell, bash, zsh, fish 쉘을 지원합니다.\n\n"
            "사용 예시:\n"
            "  compman completion powershell\n"
            "  compman completion bash --install"
        ),
    },
    "cmd.upgrade": {
        "en": (
            "Self-upgrade compman CLI to the latest version from GitHub.\n\n"
            "Reinstalls compman from the specified repository using uv or pip.\n\n"
            "Examples:\n"
            "  compman upgrade"
        ),
        "ko": (
            "compman CLI 자체를 GitHub 최신 버전으로 셀프 업그레이드합니다.\n\n"
            "uv 또는 pip를 통해 원격 리포지토리의 최신 버전으로 자동 재설치합니다.\n\n"
            "사용 예시:\n"
            "  compman upgrade"
        ),
    },
    "cmd.stack": {
        "en": "Manage Docker Compose stack lifecycles.",
        "ko": "Docker Compose 스택 라이프사이클(up, down, update)을 관리합니다.",
    },
    "cmd.stack.up": {
        "en": (
            "Start stack containers in detached mode.\n\n"
            "Brings up containers defined in compose files.\n\n"
            "Examples:\n"
            "  compman stack up\n"
            "  compman stack up dev"
        ),
        "ko": (
            "스택 컨테이너를 백그라운드(detached) 모드로 기동합니다.\n\n"
            "compose 파일에 정의된 서비스 컨테이너를 생성 및 실행합니다.\n\n"
            "사용 예시:\n"
            "  compman stack up\n"
            "  compman stack up dev"
        ),
    },
    "cmd.stack.down": {
        "en": (
            "Stop and remove stack containers and networks.\n\n"
            "Stops running containers and removes networks. Requires --yes confirmation or interactive prompt.\n\n"
            "Examples:\n"
            "  compman stack down\n"
            "  compman stack down --yes"
        ),
        "ko": (
            "스택 컨테이너 및 네트워크를 정지하고 삭제합니다.\n\n"
            "기동 중인 스택 전체를 정지하고 제거합니다. 대화형 확인 또는 --yes 옵션이 필요합니다.\n\n"
            "사용 예시:\n"
            "  compman stack down\n"
            "  compman stack down --yes"
        ),
    },
    "cmd.stack.update": {
        "en": (
            "Rebuild images and recreate stack containers.\n\n"
            "Forces rebuild of container images and recreates updated stack containers.\n\n"
            "Examples:\n"
            "  compman stack update\n"
            "  compman stack update prod"
        ),
        "ko": (
            "이미지를 재빌드하고 스택 컨테이너를 무중단 재생성합니다.\n\n"
            "컨테이너 이미지를 강제 재빌드하고 변경된 컨테이너를 다시 기동합니다.\n\n"
            "사용 예시:\n"
            "  compman stack update\n"
            "  compman stack update prod"
        ),
    },
    "cmd.service": {
        "en": "Manage individual services within a stack.",
        "ko": "스택 내 개별 서비스(start, stop, log, connect, status)를 관리합니다.",
    },
    "cmd.service.start": {
        "en": (
            "Start specific or all services in the stack.\n\n"
            "Examples:\n"
            "  compman service start\n"
            "  compman service start app db"
        ),
        "ko": (
            "스택 내 특정 또는 전체 서비스를 시작합니다.\n\n"
            "사용 예시:\n"
            "  compman service start\n"
            "  compman service start app db"
        ),
    },
    "cmd.service.stop": {
        "en": (
            "Stop specific or all services in the stack.\n\n"
            "Examples:\n"
            "  compman service stop\n"
            "  compman service stop app"
        ),
        "ko": (
            "스택 내 특정 또는 전체 서비스를 정지합니다.\n\n"
            "사용 예시:\n"
            "  compman service stop\n"
            "  compman service stop app"
        ),
    },
    "cmd.service.restart": {
        "en": (
            "Restart specific or all services in the stack.\n\n"
            "Examples:\n"
            "  compman service restart\n"
            "  compman service restart app"
        ),
        "ko": (
            "스택 내 특정 또는 전체 서비스를 재시작합니다.\n\n"
            "사용 예시:\n"
            "  compman service restart\n"
            "  compman service restart app"
        ),
    },
    "cmd.service.status": {
        "en": (
            "Display current status of all stack containers.\n\n"
            "Examples:\n"
            "  compman service status"
        ),
        "ko": (
            "스택 내 모든 컨테이너의 현재 상태를 표시합니다.\n\n"
            "사용 예시:\n"
            "  compman service status"
        ),
    },
    "cmd.service.log": {
        "en": (
            "Display or stream logs for a service container.\n\n"
            "Supports streaming logs (-f/--follow) and limiting line count (-n/--tail).\n\n"
            "Examples:\n"
            "  compman service log\n"
            "  compman service log app -f\n"
            "  compman service log app -n 100"
        ),
        "ko": (
            "서비스 컨테이너의 로그를 조회하거나 실시간 스트리밍합니다.\n\n"
            "실시간 로그 스트리밍(-f/--follow) 및 출력 줄 수 지정(-n/--tail)을 지원합니다.\n\n"
            "사용 예시:\n"
            "  compman service log\n"
            "  compman service log app -f\n"
            "  compman service log app -n 100"
        ),
    },
    "cmd.service.connect": {
        "en": (
            "Open an interactive shell inside a service container.\n\n"
            "Executes an interactive terminal inside the target container (bash with sh fallback).\n\n"
            "Examples:\n"
            "  compman service connect\n"
            "  compman service connect app"
        ),
        "ko": (
            "서비스 컨테이너 내부로 대화형 쉘(bash/sh) 접속을 수행합니다.\n\n"
            "대상 컨테이너 내부 터미널로 대화형 쉘 접속을 실행합니다.\n\n"
            "사용 예시:\n"
            "  compman service connect\n"
            "  compman service connect app"
        ),
    },
    "cmd.volume": {
        "en": "Backup, restore, pull, or push Docker persistent volumes.",
        "ko": "Docker 파시스턴트 볼륨 백업, 복원, 풀, 푸시를 관리합니다.",
    },
    "cmd.volume.backup": {
        "en": (
            "Create a compressed backup archive of stack volumes.\n\n"
            "Copies volume data from running containers and archives them into a timestamped .tar.gz file.\n\n"
            "Examples:\n"
            "  compman volume backup\n"
            "  compman volume backup --no-stop"
        ),
        "ko": (
            "스택 볼륨의 압축 백업 아카이브를 생성합니다.\n\n"
            "컨테이너의 파시스턴트 볼륨 데이터를 추출하고 타임스탬프 .tar.gz 아카이브 파일로 백업합니다.\n\n"
            "사용 예시:\n"
            "  compman volume backup\n"
            "  compman volume backup --no-stop"
        ),
    },
    "cmd.volume.restore": {
        "en": (
            "Restore stack volumes from a backup archive timestamp.\n\n"
            "Restores volume data from a specified timestamp archive back into container volumes.\n\n"
            "Examples:\n"
            "  compman volume restore 20260731_1732\n"
            "  compman volume restore 20260731_1732 --no-stop"
        ),
        "ko": (
            "백업 아카이브 타임스탬프로부터 스택 볼륨을 복원합니다.\n\n"
            "지정한 타임스탬프의 아카이브 데이터로부터 컨테이너 볼륨으로 데이터를 복원합니다.\n\n"
            "사용 예시:\n"
            "  compman volume restore 20260731_1732\n"
            "  compman volume restore 20260731_1732 --no-stop"
        ),
    },
    "cmd.volume.pull": {
        "en": (
            "Extract volume data from containers into local directory.\n\n"
            "Copies volume files from containers into local ./volume directory.\n\n"
            "Examples:\n"
            "  compman volume pull"
        ),
        "ko": (
            "컨테이너 볼륨 데이터를 로컬 디렉터리로 추출합니다.\n\n"
            "컨테이너 내부의 볼륨 파일들을 로컬 ./volume 디렉터리로 복사합니다.\n\n"
            "사용 예시:\n"
            "  compman volume pull"
        ),
    },
    "cmd.volume.push": {
        "en": (
            "Upload local volume directory data into containers.\n\n"
            "Uploads files from local ./volume directory into container volumes.\n\n"
            "Examples:\n"
            "  compman volume push"
        ),
        "ko": (
            "로컬 디렉터리 볼륨 데이터를 컨테이너로 업로드합니다.\n\n"
            "로컬 ./volume 디렉터리의 파일들을 컨테이너 볼륨으로 업로드합니다.\n\n"
            "사용 예시:\n"
            "  compman volume push"
        ),
    },
    "cmd.image": {
        "en": "Backup or restore Docker container images.",
        "ko": "Docker 컨테이너 이미지를 백업하거나 복원합니다.",
    },
    "cmd.image.backup": {
        "en": (
            "Commit and export stack container images to tar.gz archive.\n\n"
            "Saves runtime container state (or original image via --source-image) to a timestamped backup archive.\n\n"
            "Examples:\n"
            "  compman image backup\n"
            "  compman image backup --source-image"
        ),
        "ko": (
            "스택 컨테이너 이미지를 커밋하고 tar.gz 아카이브로 내보냅니다.\n\n"
            "현재 실행 상태 컨테이너(또는 --source-image 지정 시 원본 이미지)를 타임스탬프 백업 아카이브로 저장합니다.\n\n"
            "사용 예시:\n"
            "  compman image backup\n"
            "  compman image backup --source-image"
        ),
    },
    "cmd.image.restore": {
        "en": (
            "Import container images from a backup archive timestamp.\n\n"
            "Loads a container image from a timestamped backup archive.\n\n"
            "Examples:\n"
            "  compman image restore 20260731_1732"
        ),
        "ko": (
            "백업 아카이브 타임스탬프로부터 컨테이너 이미지를 불러옵니다.\n\n"
            "타임스탬프 백업 아카이브 파일로부터 컨테이너 이미지를 로드합니다.\n\n"
            "사용 예시:\n"
            "  compman image restore 20260731_1732"
        ),
    },

    "cmd.version": {
        "en": "Display the current compman CLI version.",
        "ko": "현재 compman CLI 버전을 표시합니다.",
    },

    # Option descriptions
    "opt.lang": {
        "en": "Language for CLI help and messages (en/ko).",
        "ko": "CLI 도움말 및 메시지 언어 설정 (en/ko).",
    },
    "opt.force": {
        "en": "Overwrite existing files",
        "ko": "기존 파일 덮어쓰기",
    },
    "opt.archive": {
        "en": "Compress generated seed files into a .tar.gz archive.",
        "ko": "생성된 시드 파일들을 .tar.gz 아카이브 파일로 압축합니다.",
    },
    "opt.output": {
        "en": "Output directory or archive base name (default: project).",
        "ko": "출력 디렉터리 또는 아카이브 기본 이름 (기본값: project).",
    },
    "opt.port": {
        "en": "Port number for the sample app (default: 18080).",
        "ko": "샘플 애플리케이션의 포트 번호 (기본값: 18080).",
    },
    "opt.config": {
        "en": "Path to compman.yml",
        "ko": "compman.yml 설정 파일 경로",
    },
    "opt.path": {
        "en": "S3 URI path (default: 'deploy' in compman.yml)",
        "ko": "S3 URI 경로 (기본값: compman.yml의 deploy 속성)",
    },
    "opt.build": {
        "en": "Build Docker image after fetching",
        "ko": "패키지 수신 후 Docker 이미지 빌드",
    },
    "opt.tag": {
        "en": "Image tag when building (default: directory name)",
        "ko": "빌드 시 이미지 태그명 (기본값: 디렉터리명)",
    },
    "opt.install": {
        "en": "Automatically install completion script into shell profile.",
        "ko": "Shell 프로필에 자동완성 스크립트를 자동 등록합니다.",
    },
    "opt.repo": {
        "en": "Git repository URL for upgrade",
        "ko": "업그레이드용 Git 저장소 URL",
    },
    "opt.no_stop": {
        "en": "Don't stop stack during backup/restore",
        "ko": "백업/복원 시 스택을 정지하지 않고 진행",
    },
    "opt.source_image": {
        "en": "Backup original image instead of committing runtime state",
        "ko": "실행 중인 상태 커밋 대신 원본 이미지를 백업",
    },
    "opt.follow": {
        "en": "Follow log output continuously.",
        "ko": "로그 출력을 실시간으로 계속 추적(스트리밍)합니다.",
    },
    "opt.tail": {
        "en": "Number of lines to show from the end of logs (default: 50).",
        "ko": "로그 출력할 마지막 라인 수 (기본값: 50).",
    },

    # Guidance & Error Messages
    "msg.config_not_found": {
        "en": "💡 compman.yml config file not found ({err})",
        "ko": "💡 compman.yml 설정 파일을 찾을 수 없습니다 ({err})",
    },
    "msg.unknown_command": {
        "en": "Error: Unknown command '{command}'.",
        "ko": "오류: 알 수 없는 명령어입니다: '{command}'",
    },
    "msg.start_guide": {
        "en": "Start by running one of the following commands:",
        "ko": "다음 명령어로 기본 설정 파일을 생성하거나 첫 배포를 진행해보세요:",
    },
    "msg.init_desc": {
        "en": "Generate default compman.yml",
        "ko": "기본 compman.yml 생성",
    },
    "msg.deploy_desc": {
        "en": "Deploy directly with S3 path",
        "ko": "S3 경로로 바로 첫 배포",
    },
    "msg.empty_dir_deploy": {
        "en": "💡 [compman deploy] Empty directory without compman.yml config file.",
        "ko": "💡 [compman deploy] compman.yml 설정 파일이 없는 빈 디렉터리입니다.",
    },
    "msg.empty_dir_start": {
        "en": "Start by running one of the following commands:",
        "ko": "다음 중 하나로 첫 배포 또는 설정을 시작해보세요:",
    },
    "msg.deploy_path_not_configured": {
        "en": "💡 [compman deploy] S3 deployment path is not configured.",
        "ko": "💡 [compman deploy] S3 배포 경로가 지정되지 않았습니다.",
    },
    "msg.deploy_path_hint1": {
        "en": "  • Specify 'deploy' field in compman.yml, or",
        "ko": "  • compman.yml 파일의 'deploy' 속성을 지정하거나,",
    },
    "msg.deploy_path_hint2": {
        "en": "  • Pass S3 path via option: compman deploy --path s3://...",
        "ko": "  • compman deploy --path s3://... 옵션으로 S3 경로를 전달해주세요.",
    },
    "msg.stack_not_running": {
        "en": "💡 Stack '{name}' is not currently running. Run 'compman stack up' to start it.",
        "ko": "💡 스택 '{name}'이(가) 현재 실행 중이지 않습니다. 'compman stack up' 커맨드로 시작하세요.",
    },
    "msg.no_running_containers": {
        "en": "💡 No running containers found in this stack. Run 'compman stack up' first.",
        "ko": "💡 실행 중인 스택 컨테이너가 없습니다. 'compman stack up' 커맨드를 먼저 실행하세요.",
    },
    "msg.container_not_found": {
        "en": "💡 Container '{service}' not found. Run 'compman service status' to check running containers.",
        "ko": "💡 컨테이너 '{service}'를 찾을 수 없습니다. 'compman service status'로 실행 중인 컨테이너를 확인하세요.",
    },
    "msg.backup_not_found": {
        "en": "💡 Backup not found: {tarball}",
        "ko": "💡 백업 파일을 찾을 수 없습니다: {tarball}",
    },
    "msg.volume_map_not_found": {
        "en": "💡 volume-map.json not found at {path}. Run 'compman volume pull' first.",
        "ko": "💡 {path} 위치에 volume-map.json이 없습니다. 'compman volume pull'을 먼저 실행하세요.",
    },
    "msg.s3_failed": {
        "en": "💡 [compman deploy] Failed to download from {path}",
        "ko": "💡 [compman deploy] {path} 다운로드 실패",
    },
    "msg.s3_no_creds": {
        "en": "Error: AWS credentials were not found or are incomplete.\n\nGuide - Please set your AWS credentials using environment variables:\n  • Windows PowerShell:\n      $env:AWS_ACCESS_KEY_ID=\"your-key-id\"\n      $env:AWS_SECRET_ACCESS_KEY=\"your-secret-key\"\n      $env:AWS_DEFAULT_REGION=\"ap-northeast-2\"\n  • Windows CMD:\n      set AWS_ACCESS_KEY_ID=your-key-id\n      set AWS_SECRET_ACCESS_KEY=your-secret-key\n      set AWS_DEFAULT_REGION=ap-northeast-2\n  • Or configure credentials in ~/.aws/credentials",
        "ko": "오류: AWS 자격 증명을 찾을 수 없거나 불완전합니다.\n\n가이드 - 환경 변수로 AWS 자격 증명을 설정하세요:\n  • Windows PowerShell:\n      $env:AWS_ACCESS_KEY_ID=\"your-key-id\"\n      $env:AWS_SECRET_ACCESS_KEY=\"your-secret-key\"\n      $env:AWS_DEFAULT_REGION=\"ap-northeast-2\"\n  • Windows CMD:\n      set AWS_ACCESS_KEY_ID=your-key-id\n      set AWS_SECRET_ACCESS_KEY=your-secret-key\n      set AWS_DEFAULT_REGION=ap-northeast-2\n  • 또는 ~/.aws/credentials 파일에 설정",
    },
    "msg.s3_403": {
        "en": "Error 403 (Access Denied): Access to '{path}' was forbidden.\n\nGuide - Troubleshooting 403 Forbidden:\n  1️⃣ Ensure AWS credentials have 's3:GetObject' and 's3:ListBucket' permissions.\n  2️⃣ Verify S3 bucket name and key path are correct.\n  3️⃣ If using local S3 (e.g. ministack), check AWS_ENDPOINT_URL_S3 or AWS_ENDPOINT_URL.",
        "ko": "오류 403 (접근 거부): '{path}' 접근 권한이 거부되었습니다.\n\n가이드 - 403 Forbidden 해결 방법:\n  1️⃣ AWS 자격 증명에 's3:GetObject' 및 's3:ListBucket' 권한이 있는지 확인하세요.\n  2️⃣ S3 버킷 이름 및 객체 경로가 정확한지 확인하세요.\n  3️⃣ 로컬 S3 에뮬레이터 사용 시 AWS_ENDPOINT_URL_S3 또는 AWS_ENDPOINT_URL 환경 변수를 확인하세요.",
    },
    "msg.s3_404": {
        "en": "Error 404 (Not Found): Bucket or file does not exist: '{path}'\n\nGuide - Troubleshooting 404 Not Found:\n  1️⃣ Verify bucket name and file/archive path on S3.\n  2️⃣ Check for typos in s3://bucket/path",
        "ko": "오류 404 (찾을 수 없음): 버킷 또는 파일이 S3에 존재하지 않습니다: '{path}'\n\n가이드 - 404 Not Found 해결 방법:\n  1️⃣ S3의 버킷 이름 및 아카이브 파일 경로를 확인하세요.\n  2️⃣ s3://bucket/path 오타 여부를 확인하세요.",
    },
    "msg.s3_network": {
        "en": "Network Error: Unable to connect to S3 endpoint.\n\nGuide - Troubleshooting connection error:\n  1️⃣ Check internet connection.\n  2️⃣ If using local S3 (e.g. ministack), check AWS_ENDPOINT_URL_S3 or AWS_ENDPOINT_URL.",
        "ko": "네트워크 오류: S3 엔드포인트에 연결할 수 없습니다.\n\n가이드 - 네트워크 연결 오류 해결 방법:\n  1️⃣ 인터넷 연결 상태를 확인하세요.\n  2️⃣ 로컬 S3 에뮬레이터 사용 시 AWS_ENDPOINT_URL_S3 또는 AWS_ENDPOINT_URL 환경 변수를 확인하세요.",
    },
    "msg.seed_created": {
        "en": "Created sample seed project: {path}/",
        "ko": "샘플 시드 프로젝트가 생성되었습니다: {path}/",
    },
    "msg.seed_archive_created": {
        "en": "Archive created: {path}",
        "ko": "아카이브 파일이 생성되었습니다: {path}",
    },
    "msg.seed_exists": {
        "en": "💡 Directory '{path}' already exists and is not empty. Use --force to overwrite.",
        "ko": "💡 디렉터리 '{path}'가 이미 존재하며 비어있지 않습니다. 덮어쓰려면 --force 옵션을 사용하세요.",
    },
}


def t(key: str, lang: str | None = None, **kwargs: Any) -> str:
    l = lang or get_lang()
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(l) or entry.get("en") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
