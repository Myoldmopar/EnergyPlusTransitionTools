import json
import os
from sys import platform

from ep_transition.international import Language


class Keys:
    last_idf_folder = 'last_idf_folder'
    last_idf = 'last_idf'
    language = 'language'


def load_settings(settings_file_name):
    try:
        settings = json.load(open(settings_file_name))
    except Exception:
        settings = {}
    if Keys.last_idf_folder not in settings:
        settings[Keys.last_idf_folder] = os.path.expanduser("~")
    if Keys.last_idf not in settings:
        if platform.startswith("win"):
            settings[Keys.last_idf] = 'C:\\Path\\to.idf'
        else:
            settings[Keys.last_idf] = '/path/to.idf'
    if Keys.language not in settings:
        settings[Keys.language] = Language.English
    return settings


def save_settings(settings, settings_file_name):
    try:
        json.dump(settings, open(settings_file_name, 'w'), indent=2)
    except Exception:
        pass
