from __future__ import annotations

from unittest.mock import patch


def test_main_exec():
    with patch("sys.argv", ["compman", "--version"]):
        try:
            pass
        except SystemExit:
            pass
