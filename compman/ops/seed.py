from __future__ import annotations

import tarfile
from pathlib import Path
import click
from compman.i18n import t


def generate_seed(
    output: str = "seed",
    archive: bool = False,
    port: int = 18080,
    force: bool = False,
) -> None:
    cwd = Path.cwd()
    target_dir = (cwd / output).resolve()

    compman_yml = cwd / "compman.yml"
    compose_yml = cwd / "docker-compose.yml"

    if (compman_yml.exists() or compose_yml.exists()) and not force:
        click.echo(
            t("msg.seed_exists", path="compman.yml / docker-compose.yml"),
            err=True,
        )
        return

    target_dir.mkdir(parents=True, exist_ok=True)

    app_py_content = (
        'import http.server\n'
        'import socketserver\n'
        'import datetime\n'
        '\n'
        f'PORT = {port}\n'
        '\n'
        'class Handler(http.server.SimpleHTTPRequestHandler):\n'
        '    def do_GET(self):\n'
        '        self.send_response(200)\n'
        '        self.send_header("Content-type", "text/plain; charset=utf-8")\n'
        '        self.end_headers()\n'
        '        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")\n'
        '        message = f"🚀 compman sample seed app running! Current time: {now}\\n"\n'
        '        self.wfile.write(message.encode("utf-8"))\n'
        '\n'
        'if __name__ == "__main__":\n'
        '    print(f"Server starting on port {PORT}...")\n'
        '    with socketserver.TCPServer(("", PORT), Handler) as httpd:\n'
        '        httpd.serve_forever()\n'
    )
    (target_dir / "app.py").write_text(app_py_content, encoding="utf-8")

    dockerfile_content = (
        "FROM python:3.11-slim\n"
        "WORKDIR /app\n"
        "COPY app.py .\n"
        f"EXPOSE {port}\n"
        'CMD ["python", "-u", "app.py"]\n'
    )
    (target_dir / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")

    rel_build_path = f"./{output}" if output != "." else "."
    compose_content = (
        "services:\n"
        "  app:\n"
        f"    build: {rel_build_path}\n"
        "    ports:\n"
        f'      - "{port}:{port}"\n'
        "    restart: unless-stopped\n"
    )
    compose_yml.write_text(compose_content, encoding="utf-8")

    project_name = cwd.name
    compman_content = (
        "compman:\n"
        f"  name: {project_name}\n"
        f"  deploy: s3://deploy-test/archives/{output}.tar.gz\n"
        "  compose:\n"
        "    - docker-compose.yml\n"
    )
    compman_yml.write_text(compman_content, encoding="utf-8")

    click.echo(t("msg.seed_created", path=output))
    click.echo("----------------------------------------")
    click.echo("[compman.yml]")
    click.echo(compman_content.strip())
    click.echo("----------------------------------------")
    click.echo("[docker-compose.yml]")
    click.echo(compose_content.strip())
    click.echo("----------------------------------------")

    if archive:
        archive_file = cwd / f"{output}.tar.gz"
        with tarfile.open(archive_file, "w:gz") as tar:
            tar.add(target_dir, arcname=target_dir.name)
        click.echo(t("msg.seed_archive_created", path=archive_file.name))
