import json
import os


def get_origin(xsi):
    orig_path = ''
    plugins = xsi.Plugins
    for p in plugins:
        #print p.Name
        if p.Name == 'SoftCry':
            orig_path = p.OriginPath[:-20]
    print orig_path
    return orig_path


def load_settings(xsi):
    path = os.path.join(get_origin(xsi), 'Resources', 'settings')
    try:
        with open(path, 'r') as fh:
            return json.load(fh)
    except IOError:
        default_settings(xsi)
        return get_default_settings()


def save_settings(xsi, settings):
    path = os.path.join(get_origin(xsi), 'Resources', 'settings')
    with open(path, 'w') as fh:
        json.dump(settings, fh)


def get_default_settings():
    sett = {
        'donotmerge': True,
        'path': 'C:\\Users\\administrator\\Documents\\CE_353\\GameSDK\\Objects\\xxx.dae',
        'customnormals': True,
        'filetype': 'cgf',  # cgf | cgaanm | chrcaf | skin
        'rcpath': 'C:\\Users\\administrator\\Documents\\CE_353\\bin32\\rc\\',
        'unit': 'meter',  # meter | centimeter
        'batch': False,
        'deluncompiled': True,
        'debugdump': False,
        'verbose': 0,
        'usespaces': False,
        'keyforspace': '-',
        'f32': False,
        'gamefolder_name': 'GameSDK',
        'check_version_on_startup': True,
        'check_version_timeout': 2,
    }
    return sett


def default_settings(xsi):
    print 'Defaulted SoftCry settings.'
    sett = get_default_settings()
    path = os.path.join(get_origin(xsi), 'Resources', 'settings')
    with open(path, 'w') as fh:
        json.dump(sett, fh)
