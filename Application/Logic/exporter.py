import andecryexport
reload(andecryexport)
xsi = Application


def Export_OnClicked():
    params = PPG.Inspected(0).Parameters
    config = {}
    config['path'] = params('path').Value
    config['rcpath'] = params('rcpath').Value
    config['customnormals'] = params('customnormals').Value
    config['donotmerge'] = params('donotmerge').Value
    config['filetype'] = params('filetype').Value
    print config['filetype']
    export = andecryexport.Export(xsi, config)
    try:
        export.export()
    except SystemExit:
        return
    return
