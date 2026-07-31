from __future__ import annotations

import sys
from unittest.mock import patch


def test_main_exec():
    with patch("sys.argv", ["compman", "--version"]):
        try:
            import compman.__main__
        except SystemExit:
            pass
