from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from typing import Annotated, Optional

import typer
from typer import _click
from typer.core import TyperGroup




from compman.config import ConfigError, dump_default_config, load_config
from compman.deploy import deploy as _deploy
from compman.docker import detect_runtime
from compman.i18n import get_lang, set_lang, t
from compman.ops import image, seed, service, stack, volume


def _version_callback(value: bool) -> None:
    if value:
        try:
            v = _pkg_version("compman")
        except PackageNotFoundError:
            v = "dev"
        typer.echo(f"compman {v}")
        raise typer.Exit()


def _lang_callback(value: str | None) -> None:
    if value:
        set_lang(value)


class HelpOnUnknownCommandGroup(TyperGroup):
    def resolve_command(self, ctx: typer.Context, args: list[str]):
        try:
            return super().resolve_command(ctx, args)
        except _click.exceptions.UsageError:
            command = args[0] if args else ""
            typer.echo(t("msg.unknown_command", command=command), err=True)
            typer.echo(ctx.get_help())
            raise _click.exceptions.Exit(2)


# ---- pre-parse --lang for help text resolution ----
for _idx, _arg in enumerate(sys.argv):
    if _arg in ("--lang", "-l") and _idx + 1 < len(sys.argv):
        set_lang(sys.argv[_idx + 1])
        break
    elif _arg.startswith("--lang="):
        set_lang(_arg.split("=", 1)[1])
    elif _arg.startswith("-l="):
        set_lang(_arg.split("=", 1)[1])

app = typer.Typer(
    name="compman",
    cls=HelpOnUnknownCommandGroup,
    help=t("cmd.root"),
    no_args_is_help=True,
    invoke_without_command=True,
)

def _load(config_path: str | None = None):
    try:
        cfg = load_config(config_path)
    except ConfigError as e:
        typer.echo(t("msg.config_not_found", err=e), err=True)
        typer.echo("", err=True)
        typer.echo(t("msg.start_guide"), err=True)
        typer.echo(f"  • compman init                              ({t('msg.init_desc')})", err=True)
        typer.echo(f"  • compman deploy --path s3://<your-bucket>  ({t('msg.deploy_desc')})", err=True)
        raise typer.Exit(1)
    try:
        runtime = detect_runtime()
    except RuntimeError as e:
        typer.echo(f"Runtime error: {e}", err=True)
        raise typer.Exit(1)
    return {"config": cfg, "runtime": runtime}


# ---- Root callback ----
@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    lang: Annotated[Optional[str], typer.Option("--lang", "-l", help="Language (en/ko)")] = None,
    version: Annotated[bool, typer.Option("--version", callback=_version_callback, is_eager=True)] = False,
) -> None:
    if lang:
        set_lang(lang)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())



# ---- init ----
@app.command("init", help=t("cmd.init"))
def init_cmd(
    skeleton: Annotated[bool, typer.Option("--skeleton", help="Create default compman.yml skeleton")] = False,
    s3: Annotated[Optional[str], typer.Option("--s3", help="Fetch package from S3 URL")] = None,
    seed_mode: Annotated[bool, typer.Option("--seed", help="Generate test seed project")] = False,
    output: Annotated[str, typer.Option("-o", "--output", help=t("opt.output"))] = "project",
    archive: Annotated[bool, typer.Option("-a", "--archive", help=t("opt.archive"))] = False,
    port: Annotated[int, typer.Option("-p", "--port", help=t("opt.port"))] = 18080,
    build: Annotated[bool, typer.Option("--build", help=t("opt.build"))] = False,
    tag: Annotated[Optional[str], typer.Option("--tag", help=t("opt.tag"))] = None,
    force: Annotated[bool, typer.Option("--force", help=t("opt.force"))] = False,
    config: Annotated[str, typer.Option("--config", "-c", help=t("opt.config"))] = "compman.yml",
) -> None:
    from compman.ops.common import prompt_select

    # Direct mode routing if explicit flag passed
    if skeleton:
        choice = 0
    elif s3 is not None:
        choice = 1
    elif seed_mode or archive or port != 18080:
        choice = 2
    else:
        # Interactive mode selection
        modes = [
            "1. Create skeleton config (compman.yml)",
            "2. Fetch package from S3 URL",
            "3. Generate test seed project (app.py, Dockerfile, compose)",
        ]
        choice = prompt_select("Select initialization mode", modes, default_index=0)

    if choice == 0:
        # Mode 1: Skeleton compman.yml
        path = pathlib.Path(config)
        if path.is_file() and not force:
            typer.echo(f"{config} already exists. Use --force to overwrite.")
            return
        content = dump_default_config(pathlib.Path.cwd().name)
        path.write_text(content, encoding="utf-8")
        typer.echo(f"{config} created:\n----------------------------------------\n{content.strip()}\n----------------------------------------")

    elif choice == 1:
        # Mode 2: S3 URL
        s3_url = s3
        if not s3_url:
            s3_url = typer.prompt("Enter S3 URL (e.g. s3://bucket/path/app.tar.gz)")
        _deploy(build=build, tag=tag, s3_path=s3_url)

    elif choice == 2:
        # Mode 3: Test Seed Project
        from compman.ops import seed

        seed.generate_seed(output=output, archive=archive, port=port, force=force)


# ---- clear ----
@app.command("clear", help=t("cmd.clear"))
def clear_cmd() -> None:
    typer.echo("Pruning unused Docker images...")
    runtime = detect_runtime()
    runtime.passthru_cli(["image", "prune", "-af"])


# ---- deploy ----
@app.command("deploy", help=t("cmd.deploy"))
def deploy_cmd(
    path: Annotated[Optional[str], typer.Option("--path", help=t("opt.path"))] = None,
    build: Annotated[bool, typer.Option("--build", help=t("opt.build"))] = False,
    tag: Annotated[Optional[str], typer.Option("--tag", help=t("opt.tag"))] = None,
) -> None:
    _deploy(build=build, tag=tag, s3_path=path)


# ---- update ----
@app.command("update", help=t("cmd.update"))
def update_cmd(
    profile: Annotated[Optional[str], typer.Argument()] = None,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    cfg = ctx["config"]
    if cfg.deploy:
        _deploy(build=True, tag=None, s3_path=None)
        stack.up(ctx["runtime"], cfg, profile=profile)
    else:
        stack.update(ctx["runtime"], cfg, profile=profile)


# ---- completion ----
@app.command("completion", help=t("cmd.completion"))
def completion_cmd(
    shell: Annotated[str, typer.Argument()] = "powershell",
    install: Annotated[bool, typer.Option("--install", help=t("opt.install"))] = False,
) -> None:
    if shell == "powershell":
        snippet = _ps_completion_snippet()
        if install:
            try:
                ps_profile = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", "echo $PROFILE"], text=True
                ).strip()
                profile_path = pathlib.Path(ps_profile)
                profile_path.parent.mkdir(parents=True, exist_ok=True)
                current_content = profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""
                if "compman shell completion" in current_content:
                    lines = current_content.splitlines()
                    new_lines = [l for l in lines if "_COMPMAN_COMPLETE" not in l and "compman | Out-String" not in l]
                    current_content = "\n".join(new_lines)
                if "Register-ArgumentCompleter -Native -CommandName compman" not in current_content:
                    with profile_path.open("w", encoding="utf-8") as f:
                        f.write(current_content.strip() + "\n" + snippet)
                    typer.echo(f"Registered PowerShell auto-completion script in {profile_path}")
                else:
                    typer.echo("PowerShell profile already has auto-completion registered.")
            except Exception as e:
                typer.echo(f"Error registering PowerShell completion: {e}", err=True)
        else:
            typer.echo(snippet.strip())
    elif shell == "bash":
        snippet = 'eval "$(_COMPMAN_COMPLETE=bash_source compman)"'
        if install:
            rc_path = pathlib.Path.home() / ".bashrc"
            current_content = rc_path.read_text(encoding="utf-8") if rc_path.exists() else ""
            if "_COMPMAN_COMPLETE" not in current_content:
                with rc_path.open("a", encoding="utf-8") as f:
                    f.write(f"\n{snippet}\n")
                typer.echo(f"Registered Bash auto-completion script in {rc_path}")
            else:
                typer.echo(".bashrc already has auto-completion registered.")
        else:
            typer.echo(snippet)
    elif shell == "zsh":
        snippet = 'eval "$(_COMPMAN_COMPLETE=zsh_source compman)"'
        if install:
            rc_path = pathlib.Path.home() / ".zshrc"
            current_content = rc_path.read_text(encoding="utf-8") if rc_path.exists() else ""
            if "_COMPMAN_COMPLETE" not in current_content:
                with rc_path.open("a", encoding="utf-8") as f:
                    f.write(f"\n{snippet}\n")
                typer.echo(f"Registered Zsh auto-completion script in {rc_path}")
            else:
                typer.echo(".zshrc already has auto-completion registered.")
        else:
            typer.echo(snippet)
    elif shell == "fish":
        snippet = "_COMPMAN_COMPLETE=fish_source compman | source"
        if install:
            fish_config = pathlib.Path.home() / ".config" / "fish" / "config.fish"
            fish_config.parent.mkdir(parents=True, exist_ok=True)
            current_content = fish_config.read_text(encoding="utf-8") if fish_config.exists() else ""
            if "_COMPMAN_COMPLETE" not in current_content:
                with fish_config.open("a", encoding="utf-8") as f:
                    f.write(f"\n{snippet}\n")
                typer.echo(f"Registered Fish auto-completion script in {fish_config}")
            else:
                typer.echo("config.fish already has auto-completion registered.")
        else:
            typer.echo(snippet)


def _ps_completion_snippet() -> str:
    return (
        "\n# compman shell completion\n"
        "Register-ArgumentCompleter -Native -CommandName compman -ScriptBlock {\n"
        "    param($wordToComplete, $commandAst, $cursorPosition)\n"
        "    $subcommands = @('init', 'clear', 'deploy', 'update', 'upgrade', 'completion', 'seed', 'version', 'stack', 'service', 'volume', 'image')\n"
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


# ---- upgrade ----
@app.command("upgrade", help=t("cmd.upgrade"))
def upgrade_cmd(
    repo: Annotated[str, typer.Option("--repo", help=t("opt.repo"))] = "https://github.com/aimnext-dev1/compman.git",
) -> None:
    import sys

    typer.echo(f"Upgrading compman CLI from {repo}...")

    uv_cmd = _find_uv()
    cmd = [uv_cmd, "tool", "install", "--reinstall", f"git+{repo}"]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            typer.echo("compman CLI upgraded successfully!")
            return
        else:
            pip_res = subprocess.run([uv_cmd, "pip", "install", "--python", sys.executable, f"git+{repo}"], capture_output=True, text=True)
            if pip_res.returncode == 0:
                typer.echo("compman CLI upgraded successfully!")
                return
            typer.echo(f"Error upgrading compman: {res.stderr or res.stdout}", err=True)
            raise SystemExit(1)
    except FileNotFoundError:
        pip_cmd = [sys.executable, "-m", "pip", "install", "--upgrade", f"git+{repo}"]
        res = subprocess.run(pip_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            typer.echo("compman CLI upgraded successfully!")
            return
        typer.echo(f"Error upgrading compman: {res.stderr or res.stdout}", err=True)
        raise SystemExit(1)





# ---- lang ----
@app.command("lang", help=t("cmd.lang"))
def lang_cmd(
    language: Annotated[Optional[str], typer.Argument(help="Language code (en or ko)")] = None,
) -> None:
    if language:
        if language.lower() in ("en", "ko"):
            set_lang(language.lower())
            typer.echo(f"Current session language set to: {language.lower()}")
        else:
            typer.echo(f"Unsupported language code: '{language}'. Use 'en' or 'ko'.", err=True)
            raise SystemExit(1)

    curr = get_lang()
    env_val = os.environ.get("COMPMAN_LANG", "<not set>")

    typer.echo("🌐 compman CLI Language Info:")
    typer.echo(f"  • Active Language : {curr.upper()}")
    typer.echo(f"  • COMPMAN_LANG Env: {env_val}")
    typer.echo("")
    typer.echo("💡 To set language permanently via environment variable:")
    typer.echo("  PowerShell : $env:COMPMAN_LANG=\"ko\"")
    typer.echo("  CMD        : set COMPMAN_LANG=ko")
    typer.echo("  Bash/Zsh   : export COMPMAN_LANG=ko")


# ---- version ----
@app.command("version", help=t("cmd.version"))
def version_cmd() -> None:
    try:
        v = _pkg_version("compman")
    except PackageNotFoundError:
        v = "dev"
    typer.echo(f"compman {v}")


# ---- stack group ----
stack_app = typer.Typer(cls=HelpOnUnknownCommandGroup, help=t("cmd.stack"), no_args_is_help=True)


@stack_app.command("up", help=t("cmd.stack.up"))
def stack_up(
    profile: Annotated[Optional[str], typer.Argument()] = None,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    stack.up(ctx["runtime"], ctx["config"], profile)


@stack_app.command("down", help=t("cmd.stack.down"))
def stack_down(
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
    yes: Annotated[bool, typer.Option("--yes", help="Confirm stack removal")] = False,
) -> None:
    if not yes:
        typer.confirm("Remove the entire stack?", abort=True)
    ctx = _load(config)
    stack.down(ctx["runtime"], ctx["config"])


@stack_app.command("update", help=t("cmd.stack.update"))
def stack_update(
    profile: Annotated[Optional[str], typer.Argument()] = None,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    stack.update(ctx["runtime"], ctx["config"], profile)


app.add_typer(stack_app, name="stack")


# ---- service group ----
service_app = typer.Typer(cls=HelpOnUnknownCommandGroup, help=t("cmd.service"), no_args_is_help=True)


@service_app.command("start", help=t("cmd.service.start"))
def service_start(
    services: Annotated[list[str], typer.Argument()] = [],
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    service.start(ctx["runtime"], ctx["config"], tuple(services))


@service_app.command("stop", help=t("cmd.service.stop"))
def service_stop(
    services: Annotated[list[str], typer.Argument()] = [],
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    service.stop(ctx["runtime"], ctx["config"], tuple(services))


@service_app.command("restart", help=t("cmd.service.restart"))
def service_restart(
    services: Annotated[list[str], typer.Argument()] = [],
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    service.restart(ctx["runtime"], ctx["config"], tuple(services))


@service_app.command("status", help=t("cmd.service.status"))
def service_status(
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    service.status(ctx["runtime"], ctx["config"])


@service_app.command("log", help=t("cmd.service.log"))
def service_log(
    name: Annotated[Optional[str], typer.Argument()] = None,
    follow: Annotated[bool, typer.Option("-f", "--follow", help=t("opt.follow"))] = False,
    tail: Annotated[int, typer.Option("-n", "--tail", help=t("opt.tail"))] = 50,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    service.log(ctx["runtime"], ctx["config"], name, follow=follow, tail=tail)


@service_app.command("connect", help=t("cmd.service.connect"))
def service_connect(
    name: Annotated[Optional[str], typer.Argument()] = None,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    service.connect(ctx["runtime"], ctx["config"], name)


app.add_typer(service_app, name="service")


# ---- volume group ----
volume_app = typer.Typer(cls=HelpOnUnknownCommandGroup, help=t("cmd.volume"), no_args_is_help=True)


@volume_app.command("backup", help=t("cmd.volume.backup"))
def volume_backup(
    no_stop: Annotated[bool, typer.Option("--no-stop", help=t("opt.no_stop"))] = False,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    volume.backup(ctx["runtime"], ctx["config"], no_stop=no_stop)


@volume_app.command("restore", help=t("cmd.volume.restore"))
def volume_restore(
    timestamp: Annotated[Optional[str], typer.Argument(help="Timestamp of backup to restore (YYYYMMDD_HHMM)")] = None,
    no_stop: Annotated[bool, typer.Option("--no-stop", help=t("opt.no_stop"))] = False,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    volume.restore(ctx["runtime"], ctx["config"], timestamp, no_stop=no_stop)


@volume_app.command("pull", help=t("cmd.volume.pull"))
def volume_pull(
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    volume.pull(ctx["runtime"], ctx["config"])


@volume_app.command("push", help=t("cmd.volume.push"))
def volume_push(
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    volume.push(ctx["runtime"], ctx["config"])


app.add_typer(volume_app, name="volume")


# ---- image group ----
image_app = typer.Typer(cls=HelpOnUnknownCommandGroup, help=t("cmd.image"), no_args_is_help=True)


@image_app.command("backup", help=t("cmd.image.backup"))
def image_backup(
    source_image: Annotated[bool, typer.Option("--source-image", help=t("opt.source_image"))] = False,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    image.backup(ctx["runtime"], ctx["config"], source_mode=source_image)


@image_app.command("restore", help=t("cmd.image.restore"))
def image_restore(
    timestamp: Annotated[Optional[str], typer.Argument(help="Timestamp of backup to restore (YYYYMMDD_HHMM)")] = None,
    config: Annotated[Optional[str], typer.Option("--config", "-c", help=t("opt.config"))] = None,
) -> None:
    ctx = _load(config)
    image.restore(ctx["runtime"], ctx["config"], timestamp)


app.add_typer(image_app, name="image")


# ---- utils ----
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


if __name__ == "__main__":
    app()
