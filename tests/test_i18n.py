from __future__ import annotations

import os
from unittest.mock import patch

from compman import i18n
from compman.i18n import get_lang, set_lang, t


def test_i18n_lang_setting():
    set_lang("ko")
    assert get_lang() == "ko"
    set_lang("en")
    assert get_lang() == "en"
    set_lang("invalid")
    assert get_lang() == "en"
    set_lang(None)


def test_i18n_env_variable():
    with patch.dict(os.environ, {"COMPMAN_LANG": "ko"}):
        i18n._CURRENT_LANG = None
        assert get_lang() == "ko"

    with patch.dict(os.environ, {"COMPMAN_LANG": "korean"}):
        i18n._CURRENT_LANG = None
        assert get_lang() == "ko"

    with patch.dict(os.environ, {"COMPMAN_LANG": "en"}):
        i18n._CURRENT_LANG = None
        assert get_lang() == "en"


def test_i18n_translation_fallback():
    set_lang("ko")
    res_ko = t("cmd.init")
    assert "프로젝트" in res_ko

    set_lang("en")
    res_en = t("cmd.init")
    assert "Initialize" in res_en

    # Non-existent key
    assert t("non_existent_key_123") == "non_existent_key_123"


def test_i18n_formatting_error():
    set_lang("en")
    # Formatting mismatch error branch test
    res = t("msg.seed_created", invalid_kwarg="foo")
    assert "{path}" in res
