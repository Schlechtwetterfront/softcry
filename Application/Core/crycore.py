import json
import os
from win32com.client import constants as const


def load_settings(xsi):
    path = os.path.join(xsi.InstallationPath(const.siUserAddonPath), 'SoftCry', 'Resources', 'settings')
    with open(path, 'r') as fh:
        return json.load(fh)


def save_settings(xsi, settings):
    path = os.path.join(xsi.InstallationPath(const.siUserAddonPath), 'SoftCry', 'Resources', 'settings')
    with open(path, 'w') as fh:
        json.dump(settings, fh)


def get_default_settings():
    sett = {
        'donotmerge': True,
        'path': 'C:\\Users\\administrator\\Documents\\CE_353\\GameSDK\\Objects\\xxx.dae',
        'customnormals': True,
        'filetype': 'cgf',  # cgf | cgaanm | chrcaf
        'rcpath': 'C:\\Users\\administrator\\Documents\\CE_353\\bin32\\rc\\',
        'unit': 'meter',  # meter | centimeter
        'batch': False,
        'deluncompiled': True,
        'debugdump': False,
        'verbose': 0,
        'usespaces': False,
        'keyforspace': '-',
        'f32': False,
    }
    return sett


def default_settings(xsi):
    sett = get_default_settings()
    path = os.path.join(xsi.InstallationPath(const.siUserAddonPath), 'SoftCry', 'Resources', 'settings')
    with open(path, 'w') as fh:
        json.dump(sett, fh)
