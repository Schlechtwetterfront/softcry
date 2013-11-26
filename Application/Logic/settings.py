try:
    xsi = Application
    ui = XSIUIToolkit
    utils = XSIUtils
except NameError:
    print 'Not loaded from inside XSI.'
try:
    import andesicore
    sigen = andesicore.SIGeneral()
except ImportError:
    print 'Cannot import andesicore, PATH seemingly not including this directory.'
import sys


def add_to_path():
    orig_path = get_origin()
    corepath = utils.BuildPath(orig_path, 'Application', 'Core')
    if corepath not in sys.path:
        sys.path.append(corepath)
    modpath = utils.BuildPath(orig_path, 'Application', 'Modules')
    if modpath not in sys.path:
        sys.path.append(modpath)


def get_origin():
    orig_path = ''
    plugins = xsi.Plugins
    for p in plugins:
        #print p.Name
        if p.Name == 'SoftCry':
            orig_path = p.OriginPath[:-20]
    return orig_path


add_to_path()
import crycore


def reload_settings():
    cfg = crycore.load_settings(xsi)
    params = PPG.Inspected(0).Parameters
    params('rcpath').Value = cfg['rcpath']
    params('check_version_timeout').Value = cfg['check_version_timeout']
    params('check_version_on_startup').Value = cfg['check_version_on_startup']
    params('gamefolder_name').Value = cfg['gamefolder_name']


def save_OnClicked():
    cfg = crycore.load_settings(xsi)
    params = PPG.Inspected(0).Parameters
    cfg['rcpath'] = params('rcpath').Value
    cfg['check_version_on_startup'] = params('check_version_on_startup').Value
    cfg['check_version_timeout'] = params('check_version_timeout').Value
    cfg['gamefolder_name'] = params('gamefolder_name').Value
    crycore.save_settings(xsi, cfg)


def default_OnClicked():
    cfg = crycore.get_default_settings()
    params = PPG.Inspected(0).Parameters
    params('rcpath').Value = cfg['rcpath']
    params('check_version_timeout').Value = cfg['check_version_timeout']
    params('check_version_on_startup').Value = cfg['check_version_on_startup']
    params('gamefolder_name').Value = cfg['gamefolder_name']


def reload_OnClicked():
    reload_settings()


def helpgamefolder_OnClicked():
    sigen.msg('This string will be used to make relative paths (i.e. when syncing a material). The default for 3.5.3+ is "GameSDK".', plugin='SoftCry')
