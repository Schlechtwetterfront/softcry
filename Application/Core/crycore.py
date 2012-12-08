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
