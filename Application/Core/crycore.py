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


def default_settings(xsi):
    sett = {
        'donotmerge': True,
        'path': 'E:\\AndeSoft\\Projects\\CE\\File\\softtest.dae',
        'customnormals': True,
        'filetype': 'cgf',  # cgf | cgaanm | chrcaf
        'rcpath': 'E:\\AndeSoft\\CE_343\\Bin32\\rc',
        'unit': 'meter',  # meter | centimeter
        'batch': False,
        'onlymaterials': False,
    }
    path = os.path.join(xsi.InstallationPath(const.siUserAddonPath), 'SoftCry', 'Resources', 'settings')
    with open(path, 'w') as fh:
        json.dump(sett, fh)


def get_default_settings():
    sett = {
        'donotmerge': True,
        'path': 'E:\\AndeSoft\\Projects\\CE\\File\\softtest.dae',
        'customnormals': True,
        'filetype': 'cgf',  # cgf | cgaanm | chrcaf
        'rcpath': 'E:\\AndeSoft\\CE_343\\Bin32\\rc',
        'unit': 'meter',  # meter | centimeter
        'batch': False,
        'onlymaterials': False,
    }
    return sett
