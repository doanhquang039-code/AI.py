"""
i18n/__init__.py — Internationalization (i18n) System

Hỗ trợ ngôn ngữ: Vietnamese (vi), English (en), Chinese (zh), Japanese (ja)

Dùng:
    from i18n import t, set_language, get_language
    t("metric_episode")  # -> "Episode" hoặc "回合" tùy ngôn ngữ
    set_language("zh")
"""
import json
import os
from pathlib import Path
from typing import Optional

_LANG_DIR = Path(__file__).parent
_SUPPORTED = ["vi", "en", "zh", "ja"]
_LANG_NAMES = {
    "vi": "Tiếng Việt",
    "en": "English",
    "zh": "中文",
    "ja": "日本語",
}

_strings: dict = {}
_current_lang: str = "vi"


def _load(lang: str) -> dict:
    """Tải file JSON ngôn ngữ."""
    path = _LANG_DIR / f"{lang}.json"
    if not path.exists():
        print(f"[i18n] Language file not found: {path}. Falling back to 'en'.")
        path = _LANG_DIR / "en.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def set_language(lang: str) -> bool:
    """
    Đặt ngôn ngữ hiện tại.
    Trả về True nếu thành công, False nếu ngôn ngữ không được hỗ trợ.
    """
    global _strings, _current_lang
    if lang not in _SUPPORTED:
        print(f"[i18n] Unsupported language: '{lang}'. Supported: {_SUPPORTED}")
        return False
    _strings = _load(lang)
    _current_lang = lang
    print(f"[i18n] Language set to: {lang} ({_LANG_NAMES.get(lang, lang)})")
    return True


def get_language() -> str:
    """Lấy mã ngôn ngữ hiện tại."""
    return _current_lang


def get_language_name(lang: Optional[str] = None) -> str:
    """Lấy tên đầy đủ của ngôn ngữ."""
    return _LANG_NAMES.get(lang or _current_lang, lang or _current_lang)


def t(key: str, **kwargs) -> str:
    """
    Lấy chuỗi dịch theo key. Hỗ trợ f-string placeholders.

    Ví dụ:
        t("metric_episode")          -> "Episode"
        t("log_saved", path="x.pt") -> "Model saved: x.pt"
    """
    text = _strings.get(key, key)   # Fallback về key nếu không tìm thấy
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def next_language() -> str:
    """Chuyển sang ngôn ngữ tiếp theo trong vòng quay."""
    idx = _SUPPORTED.index(_current_lang)
    nxt = _SUPPORTED[(idx + 1) % len(_SUPPORTED)]
    set_language(nxt)
    return nxt


def supported_languages() -> list:
    return list(_SUPPORTED)


def language_menu() -> list:
    """Trả về list [(code, name)] cho menu chọn ngôn ngữ."""
    return [(code, _LANG_NAMES[code]) for code in _SUPPORTED]


# ── Auto-load từ settings ────────────────────────────────────────────────────

def _init_from_settings():
    """Load ngôn ngữ từ config/settings.yaml nếu có."""
    try:
        import yaml
        settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        if settings_path.exists():
            with open(settings_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            lang = data.get("language", "vi")
            set_language(lang)
            return
    except Exception:
        pass
    set_language("vi")   # Default


_init_from_settings()
