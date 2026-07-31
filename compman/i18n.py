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
    "cmd.init": {
        "en": "Initialize default compman.yml config file in current directory (--force, -c/--config).",
        "ko": "현재 디렉터리에 기본 compman.yml 설정 파일을 생성합니다 (--force, -c/--config).",
    },
    "cmd.clear": {
        "en": "Prune unused Docker images and build cache.",
        "ko": "사용하지 않는 Docker 이미지 및 빌드 캐시를 정리합니다.",
    },
    "cmd.deploy": {
        "en": "Fetch application package from S3 and generate scaffold (--path, --build, --tag).",
        "ko": "S3에서 애플리케이션 패키지를 다운로드하고 필요시 스캐폴드를 자동 생성합니다 (--path, --build, --tag).",
    },
    "cmd.update": {
        "en": "Fetch S3 package (if configured), build image, and update stack ([profile], -c/--config).",
        "ko": "S3 패키지 수신(설정 시) 및 스택 컨테이너를 재빌드/업데이트합니다 ([profile], -c/--config).",
    },
    "cmd.completion": {
        "en": "Output or install shell auto-completion script ([shell], --install).",
        "ko": "Shell 자동완성(Tab-completion) 스크립트를 출력하거나 자동 등록합니다 ([shell], --install).",
    },
    "cmd.upgrade": {
        "en": "Self-upgrade compman CLI to the latest version from GitHub (--repo).",
        "ko": "compman CLI 자체를 GitHub 최신 버전으로 셀프 업그레이드합니다 (--repo).",
    },
    "cmd.stack": {
        "en": "Manage Docker Compose stack lifecycles.",
        "ko": "Docker Compose 스택 라이프사이클(up, down, update)을 관리합니다.",
    },
    "cmd.stack.up": {
        "en": "Start stack containers in detached mode ([profile], -c/--config).",
        "ko": "스택 컨테이너를 백그라운드 모드로 기동합니다 ([profile], -c/--config).",
    },
    "cmd.stack.down": {
        "en": "Stop and remove stack containers and networks (--yes, -c/--config).",
        "ko": "스택 컨테이너 및 네트워크를 정지하고 삭제합니다 (--yes, -c/--config).",
    },
    "cmd.stack.update": {
        "en": "Rebuild images and recreate stack containers ([profile], -c/--config).",
        "ko": "이미지를 재빌드하고 스택 컨테이너를 재생성합니다 ([profile], -c/--config).",
    },
    "cmd.service": {
        "en": "Manage individual services within a stack.",
        "ko": "스택 내 개별 서비스(start, stop, log, connect, status)를 관리합니다.",
    },
    "cmd.service.start": {
        "en": "Start specific or all services in the stack ([services...], -c/--config).",
        "ko": "스택 내 특정 또는 전체 서비스를 시작합니다 ([services...], -c/--config).",
    },
    "cmd.service.stop": {
        "en": "Stop specific or all services in the stack ([services...], -c/--config).",
        "ko": "스택 내 특정 또는 전체 서비스를 정지합니다 ([services...], -c/--config).",
    },
    "cmd.service.restart": {
        "en": "Restart specific or all services in the stack ([services...], -c/--config).",
        "ko": "스택 내 특정 또는 전체 서비스를 재시작합니다 ([services...], -c/--config).",
    },
    "cmd.service.status": {
        "en": "Display current status of all stack containers (-c/--config).",
        "ko": "스택 내 모든 컨테이너의 현재 상태를 표시합니다 (-c/--config).",
    },
    "cmd.service.log": {
        "en": "Display or stream logs for a service container ([name], -f/--follow, -n/--tail, -c/--config).",
        "ko": "서비스 컨테이너의 로그를 조회하거나 실시간 스트리밍합니다 ([name], -f/--follow, -n/--tail, -c/--config).",
    },
    "cmd.service.connect": {
        "en": "Open an interactive shell inside a service container ([name], -c/--config).",
        "ko": "서비스 컨테이너 내부로 대화형 쉘(bash/sh) 접속을 수행합니다 ([name], -c/--config).",
    },
    "cmd.volume": {
        "en": "Backup, restore, pull, or push Docker persistent volumes.",
        "ko": "Docker 파시스턴트 볼륨 백업, 복원, 풀, 푸시를 관리합니다.",
    },
    "cmd.volume.backup": {
        "en": "Create a compressed backup archive of stack volumes (--no-stop, -c/--config).",
        "ko": "스택 볼륨의 압축 백업 아카이브를 생성합니다 (--no-stop, -c/--config).",
    },
    "cmd.volume.restore": {
        "en": "Restore stack volumes from a backup archive timestamp (<timestamp>, --no-stop, -c/--config).",
        "ko": "백업 아카이브 타임스탬프로부터 스택 볼륨을 복원합니다 (<timestamp>, --no-stop, -c/--config).",
    },
    "cmd.volume.pull": {
        "en": "Extract volume data from containers into local directory (-c/--config).",
        "ko": "컨테이너 볼륨 데이터를 로컬 디렉터리로 추출합니다 (-c/--config).",
    },
    "cmd.volume.push": {
        "en": "Upload local volume directory data into containers (-c/--config).",
        "ko": "로컬 디렉터리 볼륨 데이터를 컨테이너로 업로드합니다 (-c/--config).",
    },
    "cmd.image": {
        "en": "Backup or restore Docker container images.",
        "ko": "Docker 컨테이너 이미지를 백업하거나 복원합니다.",
    },
    "cmd.image.backup": {
        "en": "Commit and export stack container images to tar.gz archive (--source-image, -c/--config).",
        "ko": "스택 컨테이너 이미지를 커밋하고 tar.gz 아카이브로 내보냅니다 (--source-image, -c/--config).",
    },
    "cmd.image.restore": {
        "en": "Import container images from a backup archive timestamp (<timestamp>, -c/--config).",
        "ko": "백업 아카이브 타임스탬프로부터 컨테이너 이미지를 불러옵니다 (<timestamp>, -c/--config).",
    },
    "cmd.seed": {
        "en": "Generate a sample seed project (app.py, Dockerfile, compose) (-o/--output, -a/--archive, -p/--port, --force).",
        "ko": "배포 테스트용 샘플 시드 프로젝트(app.py, Dockerfile, compose)를 생성합니다 (-o, -a, -p, --force).",
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
