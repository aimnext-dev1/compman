from __future__ import annotations

import pathlib
import subprocess
import click

from compman.config import ConfigError, dump_default_config, load_config
from compman.docker import detect_runtime
from compman.ops import image, service, stack, volume
from compman.deploy import deploy as _deploy


def _load(config_path: str | None = None) -> dict:
    try:
        cfg = load_config(config_path)
    except ConfigError as e:
        click.echo(f"Config error: {e}", err=True)
        raise SystemExit(1)
    try:
        runtime = detect_runtime()
    except RuntimeError as e:
        click.echo(f"Runtime error: {e}", err=True)
        raise SystemExit(1)
    return {"config": cfg, "runtime": runtime}


# ---- root level commands ----
@click.command()
@click.option("--force", is_flag=True, help="Overwrite existing compman.yml")
@click.option("--config", "-c", default="compman.yml", help="Config file path")
def init(force: bool, config: str) -> None:
    from pathlib import Path

    path = Path(config)
    if path.is_file() and not force:
        click.echo(f"{config} already exists. Use --force to overwrite.")
        return
    path.write_text(dump_default_config(Path.cwd().name), encoding="utf-8")
    click.echo(f"{config} created. Edit it with your values.")


@click.command()
def clear() -> None:
    click.echo("Pruning unused Docker images...")
    runtime = detect_runtime()
    runtime.passthru_cli(["image", "prune", "-af"])


@click.command()
@click.option("--path", default=None, help="S3 경로 (기본: compman.yml의 deploy)")
@click.option("--build", is_flag=True, help="Fetch 후 Docker 이미지 빌드")
@click.option("--tag", default=None, help="--build 시 이미지 태그 (기본: 디렉토리명)")
def deploy(path: str | None, build: bool, tag: str | None) -> None:
    _deploy(build=build, tag=tag, s3_path=path)


@click.command()
@click.argument("profile", required=False)
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def update(profile: str | None, config: str | None) -> None:
    """Fetch latest S3, build docker image, and recreate stack container."""
    _deploy(build=True, tag=None, s3_path=None)
    ctx = _load(config)
    stack.up(ctx["runtime"], ctx["config"], profile=profile)


@click.command()
@click.argument("shell", type=click.Choice(["powershell", "bash", "zsh", "fish"]), default="powershell")
@click.option("--install", is_flag=True, help="Shell 프로필에 자동완성 설정을 등록합니다.")
def completion(shell: str, install: bool) -> None:
    """Shell 자동완성(Tab-completion) 스크립트 출력 및 자동 등록."""
    if shell == "powershell":
        snippet = (
            "\n# compman shell completion\n"
            "if (Get-Command compman -ErrorAction SilentlyContinue) {\n"
            "    $env:_COMPMAN_COMPLETE='powershell_source'\n"
            "    compman | Out-String | Invoke-Expression\n"
            "}\n"
        )
        if install:
            try:
                ps_profile = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", "echo $PROFILE"], text=True
                ).strip()
                profile_path = pathlib.Path(ps_profile)
                profile_path.parent.mkdir(parents=True, exist_ok=True)
                current_content = profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""
                if "_COMPMAN_COMPLETE" not in current_content:
                    with profile_path.open("a", encoding="utf-8") as f:
                        f.write(snippet)
                    click.echo(f"✅ PowerShell 자동완성이 등록되었습니다: {profile_path}")
                else:
                    click.echo("✅ PowerShell 프로필에 이미 자동완성이 등록되어 있습니다.")
            except Exception as e:
                click.echo(f"Error registering PowerShell completion: {e}", err=True)
        else:
            click.echo(snippet.strip())
    elif shell == "bash":
        snippet = 'eval "$(_COMPMAN_COMPLETE=bash_source compman)"'
        if install:
            rc_path = pathlib.Path.home() / ".bashrc"
            current_content = rc_path.read_text(encoding="utf-8") if rc_path.exists() else ""
            if "_COMPMAN_COMPLETE" not in current_content:
                with rc_path.open("a", encoding="utf-8") as f:
                    f.write(f"\n{snippet}\n")
                click.echo(f"✅ Bash 자동완성이 등록되었습니다: {rc_path}")
            else:
                click.echo("✅ .bashrc에 이미 자동완성이 등록되어 있습니다.")
        else:
            click.echo(snippet)
    elif shell == "zsh":
        snippet = 'eval "$(_COMPMAN_COMPLETE=zsh_source compman)"'
        if install:
            rc_path = pathlib.Path.home() / ".zshrc"
            current_content = rc_path.read_text(encoding="utf-8") if rc_path.exists() else ""
            if "_COMPMAN_COMPLETE" not in current_content:
                with rc_path.open("a", encoding="utf-8") as f:
                    f.write(f"\n{snippet}\n")
                click.echo(f"✅ Zsh 자동완성이 등록되었습니다: {rc_path}")
            else:
                click.echo("✅ .zshrc에 이미 자동완성이 등록되어 있습니다.")
        else:
            click.echo(snippet)
    elif shell == "fish":
        snippet = "_COMPMAN_COMPLETE=fish_source compman | source"
        if install:
            fish_config = pathlib.Path.home() / ".config" / "fish" / "config.fish"
            fish_config.parent.mkdir(parents=True, exist_ok=True)
            current_content = fish_config.read_text(encoding="utf-8") if fish_config.exists() else ""
            if "_COMPMAN_COMPLETE" not in current_content:
                with fish_config.open("a", encoding="utf-8") as f:
                    f.write(f"\n{snippet}\n")
                click.echo(f"✅ Fish 자동완성이 등록되었습니다: {fish_config}")
            else:
                click.echo("✅ config.fish에 이미 자동완성이 등록되어 있습니다.")
        else:
            click.echo(snippet)


@click.command()
@click.option("--repo", default="https://github.com/aimnext-dev1/compman.git", help="Git repository URL")
def upgrade(repo: str) -> None:
    """compman CLI 자체를 GitHub 최신 버전으로 셀프 업그레이드합니다."""
    click.echo(f"🚀 Upgrading compman CLI from {repo}...")
    
    cmd_uv = ["uv", "tool", "install", "--reinstall", f"git+{repo}"]
    cmd_pip = ["pip", "install", "--upgrade", f"git+{repo}"]
    
    try:
        res = subprocess.run(cmd_uv, capture_output=True, text=True)
        if res.returncode == 0:
            click.echo("✅ compman CLI upgrade complete!")
            return
    except FileNotFoundError:
        pass

    try:
        res = subprocess.run(cmd_pip, capture_output=True, text=True)
        if res.returncode == 0:
            click.echo("✅ compman CLI upgrade complete!")
            return
        else:
            click.echo(f"Error upgrading compman: {res.stderr}", err=True)
    except FileNotFoundError:
        click.echo("Error: Neither 'uv' nor 'pip' command found in PATH.", err=True)


# ---- main group ----
@click.group()
def cli() -> None:
    pass


cli.add_command(init)
cli.add_command(clear)
cli.add_command(deploy)
cli.add_command(update)
cli.add_command(completion)
cli.add_command(upgrade)


# ---- stack ----
@cli.group()
def stack_cmd() -> None:
    pass


@stack_cmd.command()
@click.argument("profile", required=False)
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def up(profile: str | None, config: str | None) -> None:
    ctx = _load(config)
    stack.up(ctx["runtime"], ctx["config"], profile)


@stack_cmd.command()
@click.confirmation_option(prompt="Remove the entire stack?")
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def down(config: str | None) -> None:
    ctx = _load(config)
    stack.down(ctx["runtime"], ctx["config"])


@stack_cmd.command()
@click.argument("profile", required=False)
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def update(profile: str | None, config: str | None) -> None:
    ctx = _load(config)
    stack.update(ctx["runtime"], ctx["config"], profile)


# ---- service ----
@cli.group()
def service_cmd() -> None:
    pass


@service_cmd.command()
@click.argument("services", nargs=-1)
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def start(services: tuple[str, ...], config: str | None) -> None:
    ctx = _load(config)
    service.start(ctx["runtime"], ctx["config"], services)


@service_cmd.command()
@click.argument("services", nargs=-1)
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def stop(services: tuple[str, ...], config: str | None) -> None:
    ctx = _load(config)
    service.stop(ctx["runtime"], ctx["config"], services)


@service_cmd.command()
@click.argument("services", nargs=-1)
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def restart(services: tuple[str, ...], config: str | None) -> None:
    ctx = _load(config)
    service.restart(ctx["runtime"], ctx["config"], services)


@service_cmd.command()
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def status(config: str | None) -> None:
    ctx = _load(config)
    service.status(ctx["runtime"], ctx["config"])


@service_cmd.command()
@click.argument("name", required=False)
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def log(name: str | None, config: str | None) -> None:
    ctx = _load(config)
    service.log(ctx["runtime"], ctx["config"], name)


@service_cmd.command()
@click.argument("name", required=False)
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def connect(name: str | None, config: str | None) -> None:
    ctx = _load(config)
    service.connect(ctx["runtime"], ctx["config"], name)


# ---- volume ----
@cli.group()
def volume_cmd() -> None:
    pass


@volume_cmd.command()
@click.option("--no-stop", is_flag=True, help="Don't stop stack during backup")
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def backup(no_stop: bool, config: str | None) -> None:
    ctx = _load(config)
    volume.backup(ctx["runtime"], ctx["config"], no_stop=no_stop)


@volume_cmd.command()
@click.argument("timestamp")
@click.option("--no-stop", is_flag=True, help="Don't stop stack during restore")
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def restore(timestamp: str, no_stop: bool, config: str | None) -> None:
    ctx = _load(config)
    volume.restore(ctx["runtime"], ctx["config"], timestamp, no_stop=no_stop)


@volume_cmd.command()
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def pull(config: str | None) -> None:
    ctx = _load(config)
    volume.pull(ctx["runtime"], ctx["config"])


@volume_cmd.command()
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def push(config: str | None) -> None:
    ctx = _load(config)
    volume.push(ctx["runtime"], ctx["config"])


# ---- image ----
@cli.group()
def image_cmd() -> None:
    pass


@image_cmd.command("backup")
@click.option("--source-image", is_flag=True, help="Backup original image instead of committing runtime state")
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def img_backup(source_image: bool, config: str | None) -> None:
    ctx = _load(config)
    image.backup(ctx["runtime"], ctx["config"], source_mode=source_image)


@image_cmd.command("restore")
@click.argument("timestamp")
@click.option("--config", "-c", default=None, help="Path to compman.yml")
def img_restore(timestamp: str, config: str | None) -> None:
    ctx = _load(config)
    image.restore(ctx["runtime"], ctx["config"], timestamp)


if __name__ == "__main__":
    cli()
