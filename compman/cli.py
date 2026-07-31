from __future__ import annotations

import os
import pathlib
import shutil
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
        click.echo(f"💡 compman.yml config file not found ({e})", err=True)
        click.echo("", err=True)
        click.echo("Start by running one of the following commands:", err=True)
        click.echo("  • compman init                              (Generate default compman.yml)", err=True)
        click.echo("  • compman deploy --path s3://<your-bucket>  (Deploy directly with S3 path)", err=True)
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
    content = dump_default_config(Path.cwd().name)
    path.write_text(content, encoding="utf-8")
    click.echo(f"{config} created:\n----------------------------------------\n{content.strip()}\n----------------------------------------")


@click.command()
def clear() -> None:
    click.echo("Pruning unused Docker images...")
    runtime = detect_runtime()
    runtime.passthru_cli(["image", "prune", "-af"])


@click.command()
@click.option("--path", default=None, help="S3 URI path (default: 'deploy' in compman.yml)")
@click.option("--build", is_flag=True, help="Build Docker image after fetching")
@click.option("--tag", default=None, help="Image tag when building (default: directory name)")
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
@click.option("--install", is_flag=True, help="Automatically install completion script into shell profile.")
def completion(shell: str, install: bool) -> None:
    """Output or install shell auto-completion script."""
    if shell == "powershell":
        snippet = (
            "\n# compman shell completion\n"
            "Register-ArgumentCompleter -Native -CommandName compman -ScriptBlock {\n"
            "    param($wordToComplete, $commandAst, $cursorPosition)\n"
            "    $subcommands = @('init', 'clear', 'deploy', 'update', 'upgrade', 'completion', 'stack', 'service', 'volume', 'image')\n"
            "    $words = $commandAst.ToString().Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries)\n"
            "    if ($words.Count -le 2) {\n"
            "        $subcommands | Where-Object { $_ -like \"$wordToComplete*\" } | ForEach-Object {\n"
            "            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)\n"
            "        }\n"
            "    } elseif ($words[1] -eq 'stack') {\n"
            "        @('up', 'down', 'update') | Where-Object { $_ -like \"$wordToComplete*\" } | ForEach-Object {\n"
            "            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)\n"
            "        }\n"
            "    } elseif ($words[1] -eq 'service') {\n"
            "        @('start', 'stop', 'restart', 'status', 'log', 'connect') | Where-Object { $_ -like \"$wordToComplete*\" } | ForEach-Object {\n"
            "            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)\n"
            "        }\n"
            "    } elseif ($words[1] -eq 'volume') {\n"
            "        @('backup', 'restore', 'pull', 'push') | Where-Object { $_ -like \"$wordToComplete*\" } | ForEach-Object {\n"
            "            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)\n"
            "        }\n"
            "    } elseif ($words[1] -eq 'image') {\n"
            "        @('backup', 'restore') | Where-Object { $_ -like \"$wordToComplete*\" } | ForEach-Object {\n"
            "            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)\n"
            "        }\n"
            "    }\n"
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
                # Replace old broken snippet if present
                if "compman shell completion" in current_content:
                    lines = current_content.splitlines()
                    new_lines = [l for l in lines if "_COMPMAN_COMPLETE" not in l and "compman | Out-String" not in l]
                    current_content = "\n".join(new_lines)
                if "Register-ArgumentCompleter -Native -CommandName compman" not in current_content:
                    with profile_path.open("w", encoding="utf-8") as f:
                        f.write(current_content.strip() + "\n" + snippet)
                    click.echo(f"✅ Registered PowerShell auto-completion script in {profile_path}")
                else:
                    click.echo("✅ PowerShell profile already has auto-completion registered.")
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
                click.echo(f"✅ Registered Bash auto-completion script in {rc_path}")
            else:
                click.echo("✅ .bashrc already has auto-completion registered.")
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
                click.echo(f"✅ Registered Zsh auto-completion script in {rc_path}")
            else:
                click.echo("✅ .zshrc already has auto-completion registered.")
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
                click.echo(f"✅ Registered Fish auto-completion script in {fish_config}")
            else:
                click.echo("✅ config.fish already has auto-completion registered.")
        else:
            click.echo(snippet)


def _find_uv() -> str:
    path = shutil.which("uv") or shutil.which("uv.exe")
    if path:
        return path

    home = pathlib.Path.home()
    local_app_data = pathlib.Path(os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local")))

    candidates = [
        home / "AppData" / "Roaming" / "Python" / "Scripts" / "uv.exe",
        home / ".local" / "bin" / "uv.exe",
        home / ".local" / "bin" / "uv",
        home / ".cargo" / "bin" / "uv.exe",
        home / ".cargo" / "bin" / "uv",
        local_app_data / "Programs" / "uv" / "uv.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return "uv"


@click.command()
@click.option("--repo", default="https://github.com/aimnext-dev1/compman.git", help="Git repository URL")
def upgrade(repo: str) -> None:
    """Self-upgrade compman CLI to the latest version from GitHub."""
    import sys

    click.echo(f"🚀 Upgrading compman CLI from {repo}...")

    uv_cmd = _find_uv()
    cmd = [uv_cmd, "tool", "install", "--reinstall", f"git+{repo}"]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            click.echo("✅ compman CLI upgraded successfully!")
            return
        else:
            pip_res = subprocess.run([uv_cmd, "pip", "install", "--python", sys.executable, f"git+{repo}"], capture_output=True, text=True)
            if pip_res.returncode == 0:
                click.echo("✅ compman CLI upgraded successfully!")
                return
            click.echo(f"Error upgrading compman: {res.stderr or res.stdout}", err=True)
            raise SystemExit(1)
    except FileNotFoundError:
        pip_cmd = [sys.executable, "-m", "pip", "install", "--upgrade", f"git+{repo}"]
        res = subprocess.run(pip_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            click.echo("✅ compman CLI upgraded successfully!")
            return
        click.echo(f"Error upgrading compman: {res.stderr or res.stdout}", err=True)
        raise SystemExit(1)


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
