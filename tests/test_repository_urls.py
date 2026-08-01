import re
from pathlib import Path


def test_official_repository_urls_use_current_owner():
    root = Path(__file__).parents[1]
    files = ("README.md", "install.cmd", "install.ps1", "install.sh")

    for name in files:
        content = (root / name).read_text(encoding="utf-8")
        assert "aimnext-dev1/compman" not in content
        assert "allbegray/compman" in content


def test_package_version_is_1_1_5():
    root = Path(__file__).parents[1]
    project = (root / "pyproject.toml").read_text(encoding="utf-8")
    lock = (root / "uv.lock").read_text(encoding="utf-8")

    assert re.search(r'(?m)^version = "1\.1\.5"$', project)
    assert re.search(r'(?m)^name = "compman"\r?\nversion = "1\.1\.5"$', lock)
    assert "## [1.1.5]" in (root / "CHANGELOG.md").read_text(encoding="utf-8")


def test_english_is_used_outside_korean_localization_resources():
    root = Path(__file__).parents[1]
    allowed = {
        root / "compman" / "i18n.py",
        root / "tests" / "test_i18n.py",
        root / "tests" / "test_cli.py",
    }
    suffixes = {".cmd", ".html", ".md", ".ps1", ".py", ".sh", ".toml", ".yaml", ".yml"}
    candidates = [root / "AGENTS.md", root / "README.md", root / "REVIEW.md", root / "pyproject.toml"]
    for directory in ("compman", "docs", "scratch", "test", "tests"):
        candidates.extend(path for path in (root / directory).rglob("*") if path.suffix in suffixes)

    hangul = re.compile(r"[\uac00-\ud7a3]")
    offenders = [
        str(path.relative_to(root))
        for path in candidates
        if path not in allowed and hangul.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
    assert [
        str(path.relative_to(root))
        for path in candidates
        if path.suffix == ".html" and 'lang="ko"' in path.read_text(encoding="utf-8")
    ] == []
