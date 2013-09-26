import andecryexport
reload(andecryexport)
import crycore
reload(crycore)
xsi = Application


def Export_OnClicked():
    params = PPG.Inspected(0).Parameters
    config = crycore.get_default_settings()
    config['path'] = params('path').Value
    config['rcpath'] = params('rcpath').Value
    config['customnormals'] = params('customnormals').Value
    config['donotmerge'] = params('donotmerge').Value
    config['filetype'] = params('filetype').Value
    config['batch'] = params('batch').Value
    config['unit'] = params('unit').Value
    config['deluncompiled'] = params('deluncompiled').Value
    config['debugdump'] = params('debugdump').Value
    config['verbose'] = params('verbose').Value
    config['addmaterial'] = params('addmaterial').Value
    crycore.save_settings(xsi, config)
    export = andecryexport.Export(xsi, config)
    try:
        export.export()
    except SystemExit:
        return
    return


def help_OnClicked():
    ps = xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'ExportHelp')
    lay = ps.PPGLayout
    lay.Language = "pythonscript"
    agr = lay.AddGroup
    egr = lay.EndGroup
    text = lay.AddStaticText
    text('Note that only the current selection will be exported.')
    agr('Paths', 1)
    text('''The first path control points to the directory where the
.dae, .cgf/.cga/.anm/.chr/.caf and .mtl files will be located after export.
The second control points to the Bin32\\rc\\ subpath of your CE installation.''')
    egr()
    agr('Batch Export', 1)
    text('''Will export every child of the currently selected object with all its children.''')
    egr()
    agr('Only Materials', 1)
    text('''Will export the materials of the currently selected objects.''')
    egr()
    agr('Unit', 1)
    text('''Will export with 1 SI Unit = 1 Meter or 1 SI Unit = 1 Centimeter.''')
    egr()
    agr('Do Not Merge', 1)
    text('Prevents merging of nodes by the RC.')
    egr()
    agr('Custom Normals', 1)
    text('RC will use custom normals.')
    egr()
    agr('File Type')
    text('''CGF: "Brushes"/static geomtry.
CGA: Hard body animated objects and animations (no skinning/weighting).
CHRCAF: Soft body animated objects and animations.''')
    egr()
    xsi.InspectObj(ps, '', 'ExportHelp', 4, False)
    for prop in xsi.ActiveSceneRoot.Properties:
        if prop.Name == 'ExportHelp':
            xsi.DeleteObj('ExportHelp')
