import sys
import os
import json
sys.path.append('.')
sys.path.append('..')
import src.Settings  # noqa: E402


def test_Settings_1():
    os.makedirs('tests', exist_ok=True)
    settingsPath = './tests/test_Settings_1.json'
    settings = src.Settings.Settings(settingsPath)
    with open(settingsPath, 'r', encoding='utf-8') as file:
        localSettings = json.load(file)
        assert localSettings == settings.DEFAULT_SETTINGS
        assert localSettings['download_path'] == settings['download_path']
        settings['debug'] = not settings['debug']
        assert localSettings['debug'] != settings['debug']
    os.remove(settingsPath)


def test_Settings_2():
    os.makedirs('tests', exist_ok=True)
    settingsPath = './tests/test_Settings_2.json'
    localSettings = {
        "debug": True,
    }
    with open(settingsPath, 'w', encoding='utf-8') as file:
        json.dump(localSettings, file, ensure_ascii=False, indent=4)
    settings = src.Settings.Settings(settingsPath)
    assert settings['debug'] is True
    os.remove(settingsPath)
