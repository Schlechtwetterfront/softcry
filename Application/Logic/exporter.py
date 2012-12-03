import andecryexport
reload(andecryexport)
xsi = Application


def Export_OnClicked():
    path = PPG.Inspected(0).Parameters('path').Value
    export = andecryexport.Export(xsi, path)
    try:
        export.export()
    except SystemExit:
        return
    return
