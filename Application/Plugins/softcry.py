# Code Copyright (C) Ande 2012
import win32com.client
from win32com.client import constants as const
import sys
import os
from datetime import datetime as dt

xsi = Application
uitk = XSIUIToolkit
utils = XSIUtils

ADDONPATH = xsi.InstallationPath(const.siUserAddonPath)
MATERIAL_PHYS = ('physDefault',  # default collision
                 'physProxyNoDraw',  # default collision but geometry is invisible
                 'physNone',  # no collision
                 'physObstruct',  # only obstructs AI view
                 'physNoCollide')  # will collide with bullets

OLD_VERSION_MSG = '''You are using an old version of SoftCry ({0}.{1}.{2}), please update to the latest ({3}.{4}.{5}).
Go to SoftCry download page?

Note: You can disable the version check in SoftCry>Misc>Settings'''

UP_TO_DATE_MSG = '''Build up to date (local: {0}.{1}.{2}, remote: {3}.{4}.{5}).

Note: You can disable the startup version check in SoftCry>Misc>Settings.'''

CHECK_VERSION_ERROR_MSG = 'Could not connect to github or timed out, version check not successful. Check SoftCry>Misc>Settings>timeout.'


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


def check_version(quiet=False):
    add_to_path()
    import requests as req
    import webbrowser
    import crycore
    config = crycore.load_settings(xsi)
    try:
        timeout = config['check_version_timeout']
    except KeyError:
        crycore.default_settings(xsi)
        config = crycore.load_settings(xsi)
        timeout = config['check_version_timeout']
    pb = uitk.ProgressBar
    pb.Caption = 'Checking SoftCry Version...'
    pb.Visible = True
    pb.Maximum = 1

    origin = get_origin()
    verdir = os.path.abspath(os.path.join(origin, 'softcry.ver'))
    with open(verdir, 'r') as fh:
        local_major, local_minor, local_build = fh.readline().split('.')
    try:
        latest = req.get('http://raw.github.com/Schlechtwetterfront/softcry/master/softcry.ver', timeout=timeout)
    except (req.ConnectionError, req.Timeout):
        if quiet:
            pb.Visible = False
            return
        uitk.MsgBox(CHECK_VERSION_ERROR_MSG)
        pb.Visible = False
        return
    major, minor, build = latest.text.split('.')
    pb.Value = 1
    if build > local_build:
        if uitk.MsgBox(OLD_VERSION_MSG.format(local_major, local_minor, local_build, major, minor, build), 4) == 6:
            webbrowser.open('http://github.com/Schlechtwetterfront/softcry')
    else:
        if quiet:
            pb.Visible = False
            return
        uitk.MsgBox(UP_TO_DATE_MSG.format(local_major, local_minor,
                                          local_build, major, minor, build))
    pb.Visible = False


def XSILoadPlugin(in_reg):
    in_reg.Author = 'Ande'
    in_reg.Name = 'SoftCry'
    in_reg.Email = 'schlchtwtrfrnt@gmail.com'
    in_reg.URL = 'https://github.com/Schlechtwetterfront/softcry'
    in_reg.Major = 1
    in_reg.Minor = 0

    in_reg.RegisterMenu(const.siMenuMainTopLevelID, 'SoftCry', False)
    in_reg.RegisterCommand('SoftCryExport', 'SoftCryExport')
    in_reg.RegisterCommand('SoftCryEditAnimClips', 'SoftCryEditAnimClips')
    in_reg.RegisterCommand('SoftCryCryifyMaterials', 'SoftCryCryifyMaterials')
    in_reg.RegisterCommand('SoftCryShowLog', 'SoftCryShowLog')
    in_reg.RegisterCommand('SoftCryShowRCLog', 'SoftCryShowRCLog')
    in_reg.RegisterCommand('SoftCryTools', 'SoftCryTools')
    in_reg.RegisterCommand('SoftCryCheckVersion', 'SoftCryCheckVersion')
    in_reg.RegisterCommand('SoftCrySetMatLibOrigin', 'SoftCrySetMatLibOrigin')
    in_reg.RegisterCommand('SoftCrySettings', 'SoftCrySettings')

    in_reg.RegisterEvent('SoftCryStartupEvent', const.siOnStartup)
    in_reg.RegisterTimerEvent('SoftCryDelayedStartupEvent', 0, 1000)
    eventtimer = xsi.EventInfos('SoftCryDelayedStartupEvent')
    eventtimer.Mute = True
    return True


def XSIUnloadPlugin(in_reg):
    return True


def SoftCryStartupEvent_OnEvent(in_ctxt):
    evtimer = xsi.EventInfos('SoftCryDelayedStartupEvent')
    evtimer.Mute = False
    return False


def install_preferences():
    pset = xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SoftCry')
    pset.AddParameter3('check_version_on_startup', const.siBool, True, '', '', 0, 0)
    pset.AddParameter3('timeout', const.siDouble, 2, 0, 10, 0, 0)
    xsi.InstallCustomPreferences(pset, 'SoftCry')


def SoftCryDelayedStartupEvent_OnEvent(in_ctxt):
    add_to_path()
    import crycore
    config = crycore.load_settings(xsi)
    try:
        check = config['check_version_on_startup']
    except KeyError:
        crycore.default_settings(xsi)
        check = crycore.load_settings(xsi)['check_version_on_startup']
    if check:
        check_version(True)
    return False


# Menu
def SoftCry_Init(in_ctxt):
    oMenu = in_ctxt.Source
    oMenu.AddCommandItem('Export...', 'SoftCryExport')
    oMenu.AddCommandItem('Edit Animation Clips...', 'SoftCryEditAnimClips')
    oMenu.AddCommandItem('Cryify Materials', 'SoftCryCryifyMaterials')
    oMenu.AddCommandItem('Toolbox...', 'SoftCryTools')
    sub_menu = win32com.client.Dispatch(oMenu.AddItem('Misc', const.siMenuItemSubmenu))
    sub_menu.AddCommandItem('Show Export Log', 'SoftCryShowLog')
    sub_menu.AddCommandItem('Show RC Log', 'SoftCryShowRCLog')
    sub_menu.AddCommandItem('Check Version', 'SoftCryCheckVersion')
    sub_menu.AddCommandItem('Settings...', 'SoftCrySettings')
    return True


def SoftCryExport_Init(in_ctxt):
    oCmd = in_ctxt.Source
    oCmd.Description = ''
    oCmd.ReturnValue = True
    return True


def SoftCryExport_Execute():
    add_to_path()
    import crycore
    reload(crycore)
    config = crycore.load_settings(xsi)

    for prop in xsi.ActiveSceneRoot.Properties:
        if prop.Name == 'SoftCryExport':
            xsi.DeleteObj('SoftCryExport')
    try:
        pS = xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SoftCryExport')
        pS.AddParameter3('path', const.siString, config['path'])
        pS.AddParameter3('customnormals', const.siBool, config['customnormals'], '', 0, 0)
        pS.AddParameter3('donotmerge', const.siBool, config['donotmerge'], '', 0, 0)
        pS.AddParameter3('filetype', const.siString, config['filetype'], '', 0, 0)
        file_types = ('CGF', 'cgf', 'CGA ANM', 'cgaanm', 'CHR CAF', 'chrcaf', 'SKIN', 'skin', 'Material', 'matlib')

        pS.AddParameter3('unit', const.siString, config['unit'], '', 0, 0)
        units = 'Meter', 'meter', 'Centimeter', 'centimeter'

        pS.AddParameter3('deluncompiled', const.siBool, config['deluncompiled'], '', '', 0)
        pS.AddParameter3('debugdump', const.siBool, config['debugdump'], '', '', 0)
        pS.AddParameter3('batch', const.siBool, config['batch'], '', '', 0)
        pS.AddParameter3('verbose', const.siInt4, config['verbose'], 0, 2, 0)
        pS.AddParameter3('usespaces', const.siBool, config['usespaces'], '', '', 0)
        pS.AddParameter3('keyforspace', const.siString, config['keyforspace'], '', '', 0, 1)
        pS.AddParameter3('f32', const.siBool, False, '', '', 0, 0)
    except KeyError:
        crycore.default_settings(xsi)
        xsi.SoftCryExport()
        return

    mLay = pS.PPGLayout
    mLay.SetAttribute(const.siUILogicFile, get_origin() + '\\Application\\Logic\\exporter.py')
    mLay.Language = 'pythonscript'

    btn = mLay.AddButton
    item = mLay.AddItem
    row = mLay.AddRow
    erow = mLay.EndRow
    enum = mLay.AddEnumControl
    text = mLay.AddStaticText
    grp = mLay.AddGroup
    egrp = mLay.EndGroup
    tab = mLay.AddTab
    spacer = mLay.AddSpacer

    tab('Export')
    path_ctrl = item('path', 'File', const.siControlFilePath)
    path_ctrl.SetAttribute(const.siUINoLabel, 1)
    path_ctrl.SetAttribute(const.siUIFileFilter, 'CRYENGINE Files (*.cgf, *.cga, *.chr)|*.cgf:*.cga:*.chr')
    path_ctrl.SetAttribute(const.siUIOpenFile, False)
    path_ctrl.SetAttribute(const.siUIFileMustExist, False)

    '''texPathI = mLay.AddItem('rcpath', 'Resource Compiler', const.siControlFolder)
    texPathI.SetAttribute(const.siUINoLabel, 1)
    texPathI.SetAttribute(const.siUIWidthPercentage, 55)'''


    exgrp = grp('Export', 1)
    row()
    item('deluncompiled', 'Delete Uncompiled')
    item('donotmerge', 'Do Not Merge')
    bf32 = item('f32', 'F32')
    bf32.SetAttribute(const.siUIWidthPercentage, 15.5)
    erow()

    row()
    item('batch', 'Batch Export')
    item('customnormals', 'Custom Normals')
    b = btn('help', 'Help')
    b.SetAttribute(const.siUICX, 80)
    erow()

    row()
    unit = enum('unit', units, 'Unit', const.siControlCombo)
    unit.SetAttribute('NoLabel', True)
    filetype = enum('filetype', file_types, 'File Type', const.siControlCombo)
    filetype.SetAttribute('NoLabel', True)
    b = btn('Export', 'Export')
    b.SetAttribute(const.siUICX, 80)
    erow()
    egrp()

    tab('Special Settings')
    grp('Debug', 1)
    row()
    bdebugdump = item('debugdump', 'Debug Dump CGF')
    bdebugdump.SetAttribute(const.siUIWidthPercentage, 20)
    iverbose = item('verbose', 'Verbose Level')
    iverbose.SetAttribute(const.siUILabelPercentage, 90)
    erow()
    egrp()

    grp('Spaces', 1)
    row()
    bspaces = item('usespaces', 'Enable Spaces')
    bspaces.SetAttribute(const.siUIWidthPercentage, 20)
    skeyforspace = item('keyforspace', 'Replace With Space')
    skeyforspace.SetAttribute(const.siUILabelPercentage, 90)
    erow()
    egrp()

    desk = xsi.Desktop.ActiveLayout
    view = desk.CreateView('Property Panel', 'SoftCryExport')
    view.BeginEdit()
    view.Resize(400, 165)
    view.SetAttributeValue('targetcontent', pS.FullName)
    view.EndEdit()
    return True


def SoftCryEditAnimClips_Init(in_ctxt):
    oCmd = in_ctxt.Source
    oCmd.Description = ''
    oCmd.ReturnValue = True
    return True


def get_ui_clips(prop):
    names = prop.Parameters('names').Value.split('::')
    starts = prop.Parameters('starts').Value.split('::')
    ends = prop.Parameters('ends').Value.split('::')
    clips = []
    if (not names[0]) and (not starts[0]) and (not ends[0]):
        return ()
    print names[0], starts[0], ends[0]
    for n in xrange(len(names)):
        clips.append('{0}: {1} - {2}'.format(names[n], starts[n], ends[n]))
        clips.append('{0}::{1}::{2}'.format(names[n], starts[n], ends[n]))
    return clips


def get_clips(prop):
    names = prop.Parameters('names').Value.split('::')
    starts = prop.Parameters('starts').Value.split('::')
    ends = prop.Parameters('ends').Value.split('::')
    clips = []
    for n in xrange(len(names)):
        clips.append((names[n], int(starts[n]), int(ends[n])))
    return clips


def SoftCryEditAnimClips_Execute():
    for prop in xsi.ActiveSceneRoot.Properties:
        if prop.Name == 'SoftCryEditAnimClips':
            xsi.DeleteObj('SoftCryEditAnimClips')
    pS = xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SoftCryEditAnimClips')
    pS.AddParameter3('clips', const.siString)
    pS.AddParameter3('clipname', const.siString, '', '', '', 0, 1)
    pS.AddParameter3('clipstart', const.siInt4, 0, -9999, 9999, 0, 1)
    pS.AddParameter3('clipend', const.siInt4, 0, -9999, 9999, 0, 1)
    pS.AddParameter3('current', const.siString, '')

    clip_prop = None
    for prop in xsi.ActiveSceneRoot.Properties:
        if prop.Name == 'SoftCryAnimationClips':
            clip_prop = prop
    if not clip_prop:
        clip_prop = xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SoftCryAnimationClips')
        clip_prop.AddParameter3('names', const.siString, '')
        clip_prop.AddParameter3('starts', const.siString, '')
        clip_prop.AddParameter3('ends', const.siString, '')
    clips = get_ui_clips(clip_prop)

    mLay = pS.PPGLayout
    mLay.SetAttribute(const.siUILogicFile, get_origin() + '\\Application\\Logic\\clipeditor.py')
    mLay.Language = 'pythonscript'

    g = mLay.AddGroup
    eg = mLay.Endgroup
    btn = mLay.AddButton
    item = mLay.AddItem
    row = mLay.AddRow
    erow = mLay.EndRow
    enum = mLay.AddEnumControl
    text = mLay.AddStaticText

    g('Animation Clips')

    box = enum('clips', '', 'Clips', const.siControlListBox)
    box.SetAttribute('NoLabel', True)
    box.UIItems = clips

    row()

    add = btn('add', 'Add')
    add.SetAttribute(const.siUICX, 66)

    edit = btn('edit', 'Edit')
    edit.SetAttribute(const.siUICX, 66)

    remove = btn('remove', 'Remove')
    remove.SetAttribute(const.siUICX, 66)

    clear = btn('clear', 'Clear')
    clear.SetAttribute(const.siUICX, 66)

    erow()

    eg()

    g('Clip')

    item('clipname', 'Name')

    row()

    item('clipstart', 'Start Frame')

    item('clipend', 'End Frame')

    erow()

    row()

    text('')

    fpc = btn('fromplaycontrol', 'From Frame Range')
    fpc.SetAttribute('buttondisable', True)

    sv = btn('save', 'Save')
    sv.SetAttribute('buttondisable', True)

    erow()

    eg()

    desk = xsi.Desktop.ActiveLayout
    view = desk.CreateView('Property Panel', 'SoftCryAnimClipEditor')
    view.BeginEdit()
    view.Resize(300, 290)
    view.SetAttributeValue('targetcontent', pS.FullName)
    view.EndEdit()
    return True


def SoftCryCryifyMaterials_Init(in_ctxt):
    oCmd = in_ctxt.Source
    oCmd.Description = ''
    oCmd.ReturnValue = True
    return True


def SoftCryCryifyMaterials_Execute():
    lib = xsi.ActiveProject.ActiveScene.ActiveMaterialLibrary
    mat_phys_special = []
    for item in MATERIAL_PHYS:
        mat_phys_special.extend((item, item))
    for mat in lib.Items:
        exists = False
        for prop in mat.Properties:
            if 'SoftCryProperty' in prop.Name:
                exists = True
        if exists:
            continue
        mat_prop = mat.AddProperty('CustomProperty', False, 'SoftCryProperty')
        mat_prop.AddParameter3('phys', const.siString, 'physDefault')

        layout = mat_prop.PPGLayout

        layout.AddEnumControl('phys', mat_phys_special, 'Physicalization', const.siControlCombo)
    return True


def SoftCryShowLog_Init(in_ctxt):
    oCmd = in_ctxt.Source
    oCmd.Description = ''
    oCmd.ReturnValue = True
    return True


def SoftCryShowLog_Execute():
    import webbrowser
    webbrowser.open(get_origin() + 'export.log')
    return True


def SoftCryShowRCLog_Init(in_ctxt):
    oCmd = in_ctxt.Source
    oCmd.Description = ''
    oCmd.ReturnValue = True
    return True


def SoftCryShowRCLog_Execute():
    add_to_path()
    import webbrowser
    import os
    import crycore
    reload(crycore)
    config = crycore.load_settings(xsi)
    logpath = os.path.join(config['rcpath'], 'rc_log.log')
    if os.path.isfile(logpath):
        webbrowser.open(logpath)
    return True


def SoftCryTools_Init(in_ctxt):
    oCmd = in_ctxt.Source
    oCmd.Description = ''
    oCmd.ReturnValue = True
    return True


def SoftCryTools_Execute():
    add_to_path()
    for prop in xsi.ActiveSceneRoot.Properties:
        if prop.Name == 'SoftCryToolsProp':
            xsi.DeleteObj('SoftCryToolsProp')
    pS = xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SoftCryToolsProp')
    txt = pS.AddParameter3('degeneratetxt', const.siString, '', '', 0, 0)
    txt.ReadOnly = True
    txt = pS.AddParameter3('degeneratetxtuv', const.siString, '', '', 0, 0)
    txt.ReadOnly = True
    pS.AddParameter3('mtlpath', const.siString, '', '', 0, 0)
    pS.AddParameter3('addmtl', const.siBool, True, '', 0, 0)

    pS.AddParameter3('phystypes', const.siString, 'physDefault')

    pS.AddParameter3('matlib', const.siString, '')

    pS.AddParameter3('originpath', const.siString, '', '', 0, 0)
    pS.AddParameter3('isexternal', const.siBool, False, '', 0, 0)


    mLay = pS.PPGLayout
    mLay.SetAttribute(const.siUILogicFile, get_origin() + '\\Application\\Logic\\tools.py')
    mLay.Language = 'pythonscript'

    g = mLay.AddGroup
    eg = mLay.Endgroup
    btn = mLay.AddButton
    item = mLay.AddItem
    row = mLay.AddRow
    erow = mLay.EndRow
    enum = mLay.AddEnumControl
    text = mLay.AddStaticText
    spacer = mLay.AddSpacer

    mLay.AddTab('Material Library')

    matg = g('Material Library', 1)
    matg.SetAttribute(const.siUIWidthPercentage, 60)

    row()
    path_ctrl = item('mtlpath', 'Material File', const.siControlFilePath)
    path_ctrl.SetAttribute(const.siUIFileFilter, 'File (*.mtl)|*.mtl')
    path_ctrl.SetAttribute(const.siUIOpenFile, True)
    path_ctrl.SetAttribute(const.siUIFileMustExist, True)
    path_ctrl.SetAttribute(const.siUILabelPercentage, 50)
    erow()

    row()
    btn('synchelp', '?')
    spacer(188, 5)
    item('isexternal', 'Make External')
    btn('sync', 'Sync')
    erow()

    matlibs = []
    for library in xsi.ActiveProject.ActiveScene.MaterialLibraries:
        matlibs.extend((library.Name, library.FullName))
    filetype = enum('matlib', matlibs, 'Material Library', const.siControlCombo)
    filetype.SetAttribute(const.siUILabelPercentage, 50)
    #text('Used MatLib')
    row()
    btn('matlibhelp', '?')
    spacer(185, 5)
    btn('edit', 'Edit Settings')
    btn('setmatlib', 'Set Selected As Active')
    erow()
    eg()

    mLay.AddTab('Misc')

    g('Geometry', 1)

    row()

    degtext = item('degeneratetxt')
    degtext.SetAttribute('NoLabel', True)
    btn('finddegenerates', 'Find Degenerates')

    erow()

    eg()

    row()
    vcg = g('Vertex Colors', 1)
    vcg.SetAttribute(const.siUIWidthPercentage, 35)

    row()
    b = btn('showrgb', 'Show RGB')
    b.SetAttribute(const.siUICX, 70)
    b = btn('showalpha', 'Show Alpha')
    b.SetAttribute(const.siUICX, 70)
    btn('helpvc', '?')
    erow()

    eg()

    g('Materials', 1)
    row()
    mat_phys_special = []
    for phys_type in MATERIAL_PHYS:
        mat_phys_special.extend((phys_type, phys_type))
    enum_ctrl = enum('phystypes', mat_phys_special, 'Physicalization', const.siControlCombo)
    enum_ctrl.SetAttribute('NoLabel', True)

    btn('setphys', 'Set For Selected')
    erow()
    eg()
    erow()

    desk = xsi.Desktop.ActiveLayout
    view = desk.CreateView('Property Panel', 'SoftCryTools')
    view.BeginEdit()
    view.Resize(450, 170)
    view.SetAttributeValue('targetcontent', pS.FullName)
    view.EndEdit()
    return True


def SoftCryCheckVersion_Init(in_ctxt):
    oCmd = in_ctxt.Source
    oCmd.Description = ''
    oCmd.ReturnValue = True
    return True


def SoftCryCheckVersion_Execute():
    check_version()
    return True


def SoftCrySettings_Init(context):
    command = context.Source
    command.Description = ''
    command.ReturnValue = True
    return True


def SoftCrySettings_Execute():
    add_to_path()
    import crycore
    reload(crycore)
    config = crycore.load_settings(xsi)

    for prop in xsi.ActiveSceneRoot.Properties:
        if prop.Name == 'SoftCrySettings':
            xsi.DeleteObj('SoftCrySettings')
    try:
        pS = xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SoftCrySettings')
        pS.AddParameter3('rcpath', const.siString, config['rcpath'])
        pS.AddParameter3('gamefolder_name', const.siString, config['gamefolder_name'], '', '', 0, 0)
        pS.AddParameter3('check_version_on_startup', const.siBool, config['check_version_on_startup'], 0, 1, 0, 0)
        pS.AddParameter3('check_version_timeout', const.siDouble, config['check_version_timeout'], 0, 10, 0, 0)
    except KeyError:
        crycore.default_settings(xsi)
        xsi.SoftCryExport()
        return

    mLay = pS.PPGLayout
    mLay.SetAttribute(const.siUILogicFile, get_origin() + '\\Application\\Logic\\settings.py')
    mLay.Language = 'pythonscript'

    btn = mLay.AddButton
    item = mLay.AddItem
    r = mLay.AddRow
    er = mLay.EndRow
    enum = mLay.AddEnumControl
    text = mLay.AddStaticText
    g = mLay.AddGroup
    eg = mLay.EndGroup
    tab = mLay.AddTab
    spacer = mLay.AddSpacer

    g('Settings')

    path_ctrl = item('rcpath', 'RC Path', const.siControlFolder)
    path_ctrl.SetAttribute(const.siUILabelPercentage, 70)
    r()
    folder_ctrl = item('gamefolder_name', 'Game Folder Name')
    folder_ctrl.SetAttribute(const.siUILabelPercentage, 80)
    help_btn = btn('helpgamefolder', '?')
    help_btn.SetAttribute(const.siUICX, 40)
    er()
    spacer(100, 5)
    r()
    item('check_version_on_startup', 'Check Version on Startup')
    item('check_version_timeout', 'Timeout')
    er()

    r()
    spacer(190, 5)
    reload_btn = btn('reload', 'Reload')
    reload_btn.SetAttribute(const.siUICX, 60)
    reload_btn.SetAttribute(const.siUICY, 22)
    def_btn = btn('default', 'Default')
    def_btn.SetAttribute(const.siUICX, 60)
    def_btn.SetAttribute(const.siUICY, 22)
    save_btn = btn('save', 'Save')
    save_btn.SetAttribute(const.siUICX, 60)
    save_btn.SetAttribute(const.siUICY, 22)
    er()

    eg()

    desk = xsi.Desktop.ActiveLayout
    view = desk.CreateView('Property Panel', 'SoftCrySettings')
    view.BeginEdit()
    view.Resize(400, 150)
    view.SetAttributeValue('targetcontent', pS.FullName)
    view.EndEdit()
    return True
