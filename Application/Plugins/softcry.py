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
    in_reg.RegisterCommand('SoftCryCryifyMaterials', 'SoftCryCryifyMaterials')

    corepath = utils.BuildPath(ADDONPATH, 'SoftCry', 'Application', 'Core')
    if corepath not in sys.path:
        sys.path.append(corepath)
    modpath = utils.BuildPath(ADDONPATH, 'SoftCry', 'Application', 'Modules')
    if modpath not in sys.path:
        sys.path.append(modpath)
    return True


def XSIUnloadPlugin(in_reg):
    return True


# Menu
def SoftCry_Init(in_ctxt):
    oMenu = in_ctxt.Source
    oMenu.AddCommandItem('Export...', 'SoftCryExport')
    oMenu.AddCommandItem('Cryify Materials', 'SoftCryCryifyMaterials')
    return True


def SoftCryExport_Init(in_ctxt):
    oCmd = in_ctxt.Source
    oCmd.Description = ''
    oCmd.ReturnValue = True
    return True


def SoftCryExport_Execute():
    for prop in xsi.ActiveSceneRoot.Properties:
        if prop.Name == 'SoftCryExport':
            xsi.DeleteObj('SoftCryExport')
    pS = xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SoftCryExport')
    pS.AddParameter3('path', const.siString, 'E:\\AndeSoft\\Projects\\CE\\File\\softtest.dae')
    pS.AddParameter3('rcpath', const.siString, 'E:\\AndeSoft\\CE_343\\bin32\\rc\\')
    pS.AddParameter3('customnormals', const.siBool, True, '', 0, 0)
    pS.AddParameter3('donotmerge', const.siBool, True, '', 0, 0)
    pS.AddParameter3('filetype', const.siString, 'cgf', '', 0, 0)
    file_types = ('CGF', 'cgf', 'CGA', 'cgaanm', 'CHRCAF', 'chrcaf')

    mLay = pS.PPGLayout
    mLay.SetAttribute(const.siUILogicFile, ADDONPATH + '\\SoftCry\\Application\\Logic\\exporter.py')
    mLay.Language = 'pythonscript'

    btn = mLay.AddButton
    item = mLay.AddItem
    row = mLay.AddRow
    erow = mLay.EndRow
    enum = mLay.AddEnumControl

    path_ctrl = item('path', 'File', const.siControlFilePath)
    path_ctrl.SetAttribute(const.siUINoLabel, 1)
    path_ctrl.SetAttribute(const.siUIFileFilter, 'File (*.dae)|*.dae')
    path_ctrl.SetAttribute(const.siUIOpenFile, False)
    path_ctrl.SetAttribute(const.siUIFileMustExist, False)

    texPathI = mLay.AddItem('rcpath', 'Resource Compiler', const.siControlFolder)
    texPathI.SetAttribute(const.siUINoLabel, 1)
    texPathI.SetAttribute(const.siUIWidthPercentage, 55)

    row()
    item('donotmerge', 'Do Not Merge')
    item('customnormals', 'Custom Normals')
    erow()

    row()
    enum('filetype', file_types, 'File Type', const.siControlCombo)
    btn('Export', 'Export')
    erow()

    desk = xsi.Desktop.ActiveLayout
    view = desk.CreateView('Property Panel', 'SoftCryExport')
    view.BeginEdit()
    view.Resize(400, 150)
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
