from pathlib import Path


def test_official_repository_urls_use_current_owner():
    root = Path(__file__).parents[1]
    files = ("README.md", "install.cmd", "install.ps1", "install.sh")

    for name in files:
        content = (root / name).read_text(encoding="utf-8")
        assert "aimnext-dev1/compman" not in content
        assert "allbegray/compman" in content
