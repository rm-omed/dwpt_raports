import os
import json

_language_data = {}
_current_lang = "fr"

def load_language(lang_code: str):
    global _language_data, _current_lang
    _current_lang = lang_code
    path = os.path.join("translations", f"{lang_code}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _language_data = json.load(f)
        print(f"[DEBUG] Loaded language: {lang_code}")
    except Exception as e:
        print(f"[ERROR] Failed to load language {lang_code}: {e}")
        _language_data = {}

def translate(key: str) -> str:
    return _language_data.get(key, key)

def current_lang() -> str:
    return _current_lang
