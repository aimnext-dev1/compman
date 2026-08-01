from __future__ import annotations

import sys
from contextlib import contextmanager

import typer

from compman.config import Config
from compman.docker import ComposeContext, ContainerRuntime
from compman.errors import CommandError
from compman.i18n import t


def ensure_runtime_ready(runtime: ContainerRuntime) -> None:
    runtime.ensure_ready_for_start(
        lambda: typer.confirm(
            "Docker Desktop is not running. Start it now?", default=True, abort=False
        )
    )


def get_key() -> str:
    if sys.platform == "win32":
        import msvcrt

        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            ch2 = msvcrt.getch()
            if ch2 == b"H":
                return "up"
            elif ch2 == b"P":
                return "down"
            return "other"
        elif ch in (b"\r", b"\n"):
            return "enter"
        elif ch == b"\x1b":
            return "esc"
        elif ch == b"\x03":
            raise KeyboardInterrupt()
        return "other"
    else:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                if rlist:
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A":
                            return "up"
                        elif ch3 == "B":
                            return "down"
                return "esc"
            elif ch in ("\r", "\n"):
                return "enter"
            elif ch == "\x03":
                raise KeyboardInterrupt()
            return "other"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def prompt_select(title: str, options: list[str], default_index: int = 0) -> int:
    if not sys.stdin.isatty():
        typer.echo(title)
        for i, opt in enumerate(options, 1):
            typer.echo(f"  [{i}] {opt}")
        choice = typer.prompt(f"Select option [1-{len(options)}]", default=str(default_index + 1))
        return int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(options) else default_index

    selected = default_index

    def render(redraw: bool = False) -> None:
        if redraw:
            sys.stdout.write(f"\033[{len(options)}A")
        for i, option in enumerate(options):
            if i == selected:
                sys.stdout.write(f"\033[K \033[36m> {option}\033[0m\n")
            else:
                sys.stdout.write(f"\033[K   {option}\n")
        sys.stdout.flush()

    typer.echo(f"{title} (Use Up/Down, Enter to select, Esc to cancel):")
    render(redraw=False)

    while True:
        try:
            key = get_key()
            if key == "up":
                selected = (selected - 1) % len(options)
                render(redraw=True)
            elif key == "down":
                selected = (selected + 1) % len(options)
                render(redraw=True)
            elif key == "enter":
                break
            elif key == "esc":
                typer.echo(t("msg.operation_cancelled"))
                raise SystemExit(0)
        except KeyboardInterrupt:
            typer.echo("")
            raise SystemExit(0)

    return selected


def select_backup_timestamp(config: Config, kind: str) -> str:
    pattern = f"{config.name}.{kind}."
    if not config.backup_dir.is_dir():
        raise CommandError(t("msg.backup_dir_not_found", path=config.backup_dir))

    files = sorted(config.backup_dir.glob(f"{pattern}*.tar.gz"))
    if not files:
        raise CommandError(t("msg.no_backups", kind=kind, path=config.backup_dir))

    timestamps = [f.name.replace(pattern, "").replace(".tar.gz", "") for f in files]

    idx = prompt_select(
        f"Available {kind} backups",
        timestamps,
        default_index=len(timestamps) - 1,
    )
    selected = timestamps[idx]
    typer.echo(t("msg.selected_backup", name=selected))
    return selected


@contextmanager
def stack_paused(runtime: ContainerRuntime, context: ComposeContext, enabled: bool = True):
    stopped = False
    if enabled:
        typer.echo("Stopping stack for consistent operation...")
        runtime.run_compose(
            ["stop"], project=context.project, compose_files=context.files,
            env=context.env, capture=False,
        )
        stopped = True
    failed = False
    try:
        yield
    except BaseException:
        failed = True
        raise
    finally:
        if stopped:
            try:
                typer.echo("Starting stack again...")
                runtime.run_compose(
                    ["start"], project=context.project, compose_files=context.files,
                    env=context.env, capture=False,
                )
            except Exception as error:
                if not failed:
                    raise
                typer.echo(f"Warning: failed to restart stack: {error}", err=True)
