from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
from typing import Any
import click

from compman.config import ConfigError, dump_default_config, load_config
from compman.docker import detect_runtime
from compman.ops import image, service, stack, volume
from compman.deploy import deploy as _deploy
from compman.i18n import set_lang, t


for _idx, _arg in enumerate(sys.argv):
    if _arg in ("--lang", "-l") and _idx + 1 < len(sys.argv):
        set_lang(sys.argv[_idx + 1])
        break
    elif _arg.startswith("--lang="):
        set_lang(_arg.split("=", 1)[1])
    elif _arg.startswith("-l="):
        set_lang(_arg.split("=", 1)[1])


class I18nOption(click.Option):
    def __init__(self, param_decls: Any = None, key: str | None = None, **kwargs: Any) -> None:
        self.i18n_key = key
        super().__init__(param_decls=param_decls, **kwargs)

    def get_help_record(self, ctx: click.Context) -> tuple[str, str] | None:
        record = super().get_help_record(ctx)
        if record and self.i18n_key:
            return (record[0], t(f"opt.{self.i18n_key}"))
        return record


class I18nCommand(click.Command):
    def __init__(self, name: str | None = None, key: str | None = None, **kwargs: Any) -> None:
        self.i18n_key = key or name
        super().__init__(name=name, **kwargs)

    def get_short_help_str(self, limit: int = 45) -> str:
        if self.i18n_key:
            return t(f"cmd.{self.i18n_key}")
        return super().get_short_help_str(limit)

    def format_help_text(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        text = t(f"cmd.{self.i18n_key}") if self.i18n_key else self.help
        if text:
            formatter.write_paragraph()
            with formatter.indentation():
                formatter.write_text(text)


class I18nGroup(click.Group):
    def __init__(self, name: str | None = None, key: str | None = None, **kwargs: Any) -> None:
        self.i18n_key = key or name
        super().__init__(name=name, **kwargs)

    def get_short_help_str(self, limit: int = 45) -> str:
        if self.i18n_key:
            return t(f"cmd.{self.i18n_key}")
        return super().get_short_help_str(limit)

    def format_help_text(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        text = t(f"cmd.{self.i18n_key}") if self.i18n_key else self.help
        if text:
            formatter.write_paragraph()
            with formatter.indentation():
                formatter.write_text(text)

    def command(self, *args: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("cls", I18nCommand)
        return super().command(*args, **kwargs)

    def group(self, *args: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("cls", I18nGroup)
        return super().group(*args, **kwargs)


def _load(config_path: str | None = None) -> dict:
    try:
        cfg = load_config(config_path)
    except ConfigError as e:
        click.echo(t("msg.config_not_found", err=e), err=True)
        click.echo("", err=True)
        click.echo(t("msg.start_guide"), err=True)
        click.echo(f"  • compman init                              ({t('msg.init_desc')})", err=True)
        click.echo(f"  • compman deploy --path s3://<your-bucket>  ({t('msg.deploy_desc')})", err=True)
        raise SystemExit(1)
    try:
        runtime = detect_runtime()
    except RuntimeError as e:
        click.echo(f"Runtime error: {e}", err=True)
        raise SystemExit(1)
    return {"config": cfg, "runtime": runtime}


# ---- root level commands ----
@click.command(cls=I18nCommand, key="init")
@click.option("--force", is_flag=True, cls=I18nOption, key="force")
@click.option("--config", "-c", default="compman.yml", cls=I18nOption, key="config")
def init(force: bool, config: str) -> None:
    from pathlib import Path

    path = Path(config)
    if path.is_file() and not force:
        click.echo(f"{config} already exists. Use --force to overwrite.")
        return
    content = dump_default_config(Path.cwd().name)
    path.write_text(content, encoding="utf-8")
    click.echo(f"{config} created:\n----------------------------------------\n{content.strip()}\n----------------------------------------")


@click.command(cls=I18nCommand, key="clear")
def clear() -> None:
    click.echo("Pruning unused Docker images...")
    runtime = detect_runtime()
    runtime.passthru_cli(["image", "prune", "-af"])


@click.command(cls=I18nCommand, key="deploy")
@click.option("--path", default=None, cls=I18nOption, key="path")
@click.option("--build", is_flag=True, cls=I18nOption, key="build")
@click.option("--tag", default=None, cls=I18nOption, key="tag")
def deploy(path: str | None, build: bool, tag: str | None) -> None:
    _deploy(build=build, tag=tag, s3_path=path)


@click.command(cls=I18nCommand, key="update")
@click.argument("profile", required=False)
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def update(profile: str | None, config: str | None) -> None:
    _deploy(build=True, tag=None, s3_path=None)
    ctx = _load(config)
    stack.up(ctx["runtime"], ctx["config"], profile=profile)


@click.command(cls=I18nCommand, key="completion")
@click.argument("shell", type=click.Choice(["powershell", "bash", "zsh", "fish"]), default="powershell")
@click.option("--install", is_flag=True, cls=I18nOption, key="install")
def completion(shell: str, install: bool) -> None:
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


@click.command(cls=I18nCommand, key="upgrade")
@click.option("--repo", default="https://github.com/aimnext-dev1/compman.git", cls=I18nOption, key="repo")
def upgrade(repo: str) -> None:
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
@click.group(cls=I18nGroup, key="root")
@click.option("--lang", "-l", type=click.Choice(["en", "ko"]), default=None, cls=I18nOption, key="lang")
@click.pass_context
def cli(ctx: click.Context, lang: str | None) -> None:
    if lang:
        set_lang(lang)


cli.add_command(init)
cli.add_command(clear)
cli.add_command(deploy)
cli.add_command(update)
cli.add_command(completion)
cli.add_command(upgrade)


# ---- stack ----
@cli.group("stack", cls=I18nGroup, key="stack")
def stack_cmd() -> None:
    pass


@stack_cmd.command(cls=I18nCommand, key="stack.up")
@click.argument("profile", required=False)
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def up(profile: str | None, config: str | None) -> None:
    ctx = _load(config)
    stack.up(ctx["runtime"], ctx["config"], profile)


@stack_cmd.command(cls=I18nCommand, key="stack.down")
@click.confirmation_option(prompt="Remove the entire stack?")
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def down(config: str | None) -> None:
    ctx = _load(config)
    stack.down(ctx["runtime"], ctx["config"])


@stack_cmd.command(cls=I18nCommand, key="stack.update")
@click.argument("profile", required=False)
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def update(profile: str | None, config: str | None) -> None:
    ctx = _load(config)
    stack.update(ctx["runtime"], ctx["config"], profile)


# ---- service ----
@cli.group("service", cls=I18nGroup, key="service")
def service_cmd() -> None:
    pass


@service_cmd.command(cls=I18nCommand, key="service.start")
@click.argument("services", nargs=-1)
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def start(services: tuple[str, ...], config: str | None) -> None:
    ctx = _load(config)
    service.start(ctx["runtime"], ctx["config"], services)


@service_cmd.command(cls=I18nCommand, key="service.stop")
@click.argument("services", nargs=-1)
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def stop(services: tuple[str, ...], config: str | None) -> None:
    ctx = _load(config)
    service.stop(ctx["runtime"], ctx["config"], services)


@service_cmd.command(cls=I18nCommand, key="service.restart")
@click.argument("services", nargs=-1)
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def restart(services: tuple[str, ...], config: str | None) -> None:
    ctx = _load(config)
    service.restart(ctx["runtime"], ctx["config"], services)


@service_cmd.command(cls=I18nCommand, key="service.status")
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def status(config: str | None) -> None:
    ctx = _load(config)
    service.status(ctx["runtime"], ctx["config"])


@service_cmd.command(cls=I18nCommand, key="service.log")
@click.argument("name", required=False)
@click.option("-f", "--follow", is_flag=True, cls=I18nOption, key="follow")
@click.option("-n", "--tail", default=50, cls=I18nOption, key="tail")
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def log(name: str | None, follow: bool, tail: int, config: str | None) -> None:
    ctx = _load(config)
    service.log(ctx["runtime"], ctx["config"], name, follow=follow, tail=tail)


@service_cmd.command(cls=I18nCommand, key="service.connect")
@click.argument("name", required=False)
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def connect(name: str | None, config: str | None) -> None:
    ctx = _load(config)
    service.connect(ctx["runtime"], ctx["config"], name)


# ---- volume ----
@cli.group("volume", cls=I18nGroup, key="volume")
def volume_cmd() -> None:
    pass


@volume_cmd.command(cls=I18nCommand, key="volume.backup")
@click.option("--no-stop", is_flag=True, cls=I18nOption, key="no_stop")
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def backup(no_stop: bool, config: str | None) -> None:
    ctx = _load(config)
    volume.backup(ctx["runtime"], ctx["config"], no_stop=no_stop)


@volume_cmd.command(cls=I18nCommand, key="volume.restore")
@click.argument("timestamp")
@click.option("--no-stop", is_flag=True, cls=I18nOption, key="no_stop")
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def restore(timestamp: str, no_stop: bool, config: str | None) -> None:
    ctx = _load(config)
    volume.restore(ctx["runtime"], ctx["config"], timestamp, no_stop=no_stop)


@volume_cmd.command(cls=I18nCommand, key="volume.pull")
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def pull(config: str | None) -> None:
    ctx = _load(config)
    volume.pull(ctx["runtime"], ctx["config"])


@volume_cmd.command(cls=I18nCommand, key="volume.push")
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def push(config: str | None) -> None:
    ctx = _load(config)
    volume.push(ctx["runtime"], ctx["config"])


# ---- image ----
@cli.group("image", cls=I18nGroup, key="image")
def image_cmd() -> None:
    pass


@image_cmd.command("backup", cls=I18nCommand, key="image.backup")
@click.option("--source-image", is_flag=True, cls=I18nOption, key="source_image")
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def img_backup(source_image: bool, config: str | None) -> None:
    ctx = _load(config)
    image.backup(ctx["runtime"], ctx["config"], source_mode=source_image)


@image_cmd.command("restore", cls=I18nCommand, key="image.restore")
@click.argument("timestamp")
@click.option("--config", "-c", default=None, cls=I18nOption, key="config")
def img_restore(timestamp: str, config: str | None) -> None:
    ctx = _load(config)
    image.restore(ctx["runtime"], ctx["config"], timestamp)


if __name__ == "__main__":
    cli()
