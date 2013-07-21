# Code Copyright (C) Ande 2012
import win32com.client
from win32com.client import constants as const
import sys

xsi = Application
uitk = XSIUIToolkit
utils = XSIUtils

ADDONPATH = xsi.InstallationPath(const.siUserAddonPath)
MATERIAL_PHYS = ('physDefault',  # default collision
                'physProxyNoDraw',  # default collision but geometry is invisible
                'physNone',  # no collision
                'physObstruct',  # only obstructs AI view
                'physNoCollide')  # will collide with bullets


def XSILoadPlugin(in_reg):
    in_reg.Author = 'Ande'
    in_reg.Name = 'SoftCry'
    in_reg.Email = 'schlchtwtrfrnt@gmail.com'
    in_reg.URL = 'https://sites.google.com/site/andescp/'
    in_reg.Major = 1
    in_reg.Minor = 0

    in_reg.RegisterMenu(const.siMenuMainTopLevelID, 'SoftCry', False)
    in_reg.RegisterCommand('SoftCryExport', 'SoftCryExport')
    in_reg.RegisterCommand('SoftCryEditAnimClips', 'SoftCryEditAnimClips')
    in_reg.RegisterCommand('SoftCryCryifyMaterials', 'SoftCryCryifyMaterials')

    orig_path = ''
    plugins = xsi.Plugins
    for p in plugins:
        #print p.Name
        if p.Name == 'SoftCry':
            orig_path = p.OriginPath[:-20]
    print 'orig_path', orig_path
    if not orig_path:
        uitk.MsgBox('No orig path.')
    corepath = utils.BuildPath(orig_path, 'Application', 'Core')
    if corepath not in sys.path:
        sys.path.append(corepath)
    modpath = utils.BuildPath(orig_path, 'Application', 'Modules')
    if modpath not in sys.path:
        sys.path.append(modpath)
    '''corepath = utils.BuildPath(ADDONPATH, 'SoftCry', 'Application', 'Core')
    if corepath not in sys.path:
        sys.path.append(corepath)
    modpath = utils.BuildPath(ADDONPATH, 'SoftCry', 'Application', 'Modules')
    if modpath not in sys.path:
        sys.path.append(modpath)'''
    return True


def XSIUnloadPlugin(in_reg):
    return True


# Menu
def SoftCry_Init(in_ctxt):
    oMenu = in_ctxt.Source
    oMenu.AddCommandItem('Export...', 'SoftCryExport')
    oMenu.AddCommandItem('Edit Clips...', 'SoftCryEditAnimClips')
    oMenu.AddCommandItem('Cryify Materials', 'SoftCryCryifyMaterials')
    return True


def SoftCryExport_Init(in_ctxt):
    oCmd = in_ctxt.Source
    oCmd.Description = ''
    oCmd.ReturnValue = True
    return True


def SoftCryExport_Execute():
    import crycore
    reload(crycore)
    config = crycore.load_settings(xsi)

    for prop in xsi.ActiveSceneRoot.Properties:
        if prop.Name == 'SoftCryExport':
            xsi.DeleteObj('SoftCryExport')
    try:
        pS = xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SoftCryExport')
        pS.AddParameter3('path', const.siString, config['path'])
        pS.AddParameter3('rcpath', const.siString, config['rcpath'])
        pS.AddParameter3('customnormals', const.siBool, config['customnormals'], '', 0, 0)
        pS.AddParameter3('donotmerge', const.siBool, config['donotmerge'], '', 0, 0)
        pS.AddParameter3('filetype', const.siString, config['filetype'], '', 0, 0)
        file_types = ('CGF', 'cgf', 'CGA', 'cgaanm', 'CHRCAF', 'chrcaf', 'Material', 'matlib')

        pS.AddParameter3('unit', const.siString, config['unit'], '', 0, 0)
        units = 'Meter', 'meter', 'Centimeter', 'centimeter'

        pS.AddParameter3('batch', const.siBool, config['batch'], '', 0, 0)
    except KeyError:
        crycore.default_settings(xsi)
        xsi.SoftCryExport()
        return

    mLay = pS.PPGLayout
    mLay.SetAttribute(const.siUILogicFile, ADDONPATH + '\\SoftCry\\Application\\Logic\\exporter.py')
    mLay.Language = 'pythonscript'

    btn = mLay.AddButton
    item = mLay.AddItem
    row = mLay.AddRow
    erow = mLay.EndRow
    enum = mLay.AddEnumControl
    text = mLay.AddStaticText
    grp = mLay.AddGroup
    egrp = mLay.EndGroup

    path_ctrl = item('path', 'File', const.siControlFilePath)
    path_ctrl.SetAttribute(const.siUINoLabel, 1)
    path_ctrl.SetAttribute(const.siUIFileFilter, 'File (*.dae)|*.dae')
    path_ctrl.SetAttribute(const.siUIOpenFile, False)
    path_ctrl.SetAttribute(const.siUIFileMustExist, False)

    texPathI = mLay.AddItem('rcpath', 'Resource Compiler', const.siControlFolder)
    texPathI.SetAttribute(const.siUINoLabel, 1)
    texPathI.SetAttribute(const.siUIWidthPercentage, 55)

    grp('Export', 1)
    row()
    item('batch', 'Batch Export')
    item('onlymaterials', 'Only Materials')
    unit = enum('unit', units, 'Unit', const.siControlCombo)
    unit.SetAttribute('NoLabel', True)
    erow()
    egrp()

    grp('In Game', 1)
    row()
    item('donotmerge', 'Do Not Merge')
    item('customnormals', 'Custom Normals')
    filetype = enum('filetype', file_types, 'File Type', const.siControlCombo)
    filetype.SetAttribute('NoLabel', True)
    erow()
    egrp()

    row()
    text('')
    btn('help', 'Help')
    btn('Export', 'Export')
    erow()

    desk = xsi.Desktop.ActiveLayout
    view = desk.CreateView('Property Panel', 'SoftCryExport')
    view.BeginEdit()
    view.Resize(400, 190)
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
    mLay.SetAttribute(const.siUILogicFile, ADDONPATH + '\\SoftCry\\Application\\Logic\\clipeditor.py')
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
