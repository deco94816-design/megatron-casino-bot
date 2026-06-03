"""Translation module — loads strings from JSON files."""
import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
_TRANSLATIONS = {}

def _load():
    global _TRANSLATIONS
    for lang in ('en', 'ru'):
        path = os.path.join(_DIR, f'{lang}.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                _TRANSLATIONS[lang] = json.load(f)

_load()

def t(key, lang='en', **kwargs):
    """Look up a translation key. Falls back to English, then to the key itself."""
    user_id = kwargs.get('user_id')
    # Could look up user language preference here
    result = _TRANSLATIONS.get(lang, {}).get(key)
    if not result:
        result = _TRANSLATIONS.get('en', {}).get(key)
    if not result:
        result = key
    return result
