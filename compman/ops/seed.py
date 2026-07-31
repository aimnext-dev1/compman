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
    target_dir = Path(output).resolve()

    if target_dir.exists() and not force and any(target_dir.iterdir()):
        click.echo(
            t("msg.seed_exists", path=target_dir.name),
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

    compose_content = (
        "services:\n"
        "  app:\n"
        "    build: .\n"
        "    ports:\n"
        f'      - "{port}:{port}"\n'
        "    restart: unless-stopped\n"
    )
    (target_dir / "docker-compose.yml").write_text(compose_content, encoding="utf-8")

    compman_content = (
        "compman:\n"
        f"  name: {target_dir.name}\n"
        f"  deploy: s3://deploy-test/archives/{target_dir.name}.tar.gz\n"
        "  compose:\n"
        "    - docker-compose.yml\n"
    )
    (target_dir / "compman.yml").write_text(compman_content, encoding="utf-8")

    click.echo(t("msg.seed_created", path=target_dir.name))
    click.echo("----------------------------------------")
    click.echo(f"[{target_dir.name}/compman.yml]")
    click.echo(compman_content.strip())
    click.echo("----------------------------------------")
    click.echo(f"[{target_dir.name}/docker-compose.yml]")
    click.echo(compose_content.strip())
    click.echo("----------------------------------------")

    if archive:
        archive_file = target_dir.parent / f"{target_dir.name}.tar.gz"
        with tarfile.open(archive_file, "w:gz") as tar:
            tar.add(target_dir, arcname=target_dir.name)
        click.echo(t("msg.seed_archive_created", path=archive_file.name))
