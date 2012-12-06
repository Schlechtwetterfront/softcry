import andesicore
import crydaemon
reload(crydaemon)
reload(andesicore)
from win32com.client import constants as const
import subprocess
import os

import logging


class Export(andesicore.SIGeneral):
    def __init__(self, xsi, config):
        self.xsi = xsi
        self.config = config
        logpath = os.path.join(self.xsi.InstallationPath(const.siUserAddonPath), 'SoftCry', 'export.log')
        logging.basicConfig(format='%(levelname)s (%(lineno)d, %(funcName)s): %(message)s',
                            filename=logpath,
                            filemode='w',
                            level=logging.DEBUG)

    def create_options(self):
        for prop in self.xsi.ActiveSceneRoot.Properties:
            if prop.Name == 'SCCrosswalkOptions':
                self.xsi.DeleteObj('SCCrosswalkOptions')
        options = self.xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SCCrosswalkOptions')
        options.AddParameter3('FileName', const.siString, self.config['path'])
        options.AddParameter3('Format', const.siInt4, 1)  # 1 = Collada file.
        options.AddParameter3('Format1', const.siInt4, 0)
        options.AddParameter3('Verbose', const.siBool, True)  # log to console.
        options.AddParameter3('ExportXSIExtra', const.siBool, False)  # XSI extra we don't need.
        options.AddParameter3('ExportSelectionOnly', const.siBool, True)  # yes!
        options.AddParameter3('ExportMaterials', const.siBool, True)
        options.AddParameter3('ExportGeometries', const.siBool, True)
        options.AddParameter3('ExportImageClips', const.siBool, True)  # not sure about that.
        options.AddParameter3('ExportUsedMaterialsAndImagesOnly', const.siBool, True)  # not sure either.
        options.AddParameter3('ExportAnimation', const.siBool, True)  # for now disabled.
        options.AddParameter3('ApplySubdivisionToGeometry', const.siBool, False)  # nope.
        options.AddParameter3('Triangulate', const.siBool, True)  # sure.
        options.AddParameter3('ExportTangentsAsVtxColor', const.siBool, False)  # nope.
        options.AddParameter3('ShapeAnim', const.siInt4, 1)  # maybe in the future.
        options.AddParameter3('PlotAnimation', const.siBool, False)  # maybe.
        options.AddParameter3('PlotNonFCurveActionSources', const.siBool, False)  # maybe?
        options.AddParameter3('PlotStartFrame', const.siInt4, 1)  # need to set that from playcontrol.
        options.AddParameter3('PlotEndFrame', const.siInt4, 1)  # that one, too.
        options.AddParameter3('PlotStepFrame', const.siDouble, 1.0)  # should be Ok like this.
        options.AddParameter3('PlotInterpolation', const.siInt4, 0)  # ?
        options.AddParameter3('PlotFit', const.siBool, True)  # ?
        options.AddParameter3('PlotFitTolerance', const.siDouble, 1.0)  # ?
        options.AddParameter3('PlotProcessRotation', const.siBool, True)  # ?
        options.AddParameter3('ExportXSINormals', const.siBool, True)  # yes for normals.
        options.AddParameter3('PreserveIK', const.siBool, False)  # maybe in the future?
        options.AddParameter3('Target', const.siInt4, 0)  # not important.
        options.AddParameter3('Target1', const.siInt4, 0)  # not important.
        options.AddParameter3('PathRelative', const.siBool, True)  # ?
        options.AddParameter3('ExportAllActionSources', const.siBool, True)  # not sure about that one.
        options.AddParameter3('Models', const.siString, 0)  # should be ok like this.
        options.AddParameter3('MatLib_ExportUsedImageClipsOnly', const.siBool, False)  # maybe change it later.
        # grid data: options.AddParameter3('ActionSourceExportTable', const.siBool, False)
        logging.info('Created Crosswalk export options,')
        return options

    def export(self):
        logging.info('Starting export,')
        self.selection = self.xsi.Selection(0)
        if not self.selection:
            logging.error('No selection')
            raise SystemExit
        # self.hierarchy = self.get_all_children(self.selection)
        lib = self.xsi.ActiveProject.ActiveScene.ActiveMaterialLibrary
        self.materials = []
        logging.info('Getting materials with physicalization.')
        for ind, mat in enumerate(lib.Items):
            phys = 'physDefault'
            for prop in mat.Properties:
                if 'SoftCryProp' in prop.Name:
                    phys = prop.Parameters('phys').Value
            cm = crydaemon.CryMaterial(mat.Name, ind, phys)
            self.materials.append(cm)
        self.do_export()
        logging.info('Finished export.')
        logging.shutdown()

    def do_export(self):
        self.create_options()
        logging.info('Starting Crosswalk COLLADA export.')
        self.xsi.ExportCrosswalk('SCCrosswalkOptions')
        logging.info('Finished Crosswalk COLLADA export.')
        logging.info('Starting .DAE preparation.')
        ed = crydaemon.ColladaEditor(self.config, self.materials)
        ed.prepare_for_rc()
        logging.info('Finished .DAE preparation.')
        exepath = os.path.join(self.config['rcpath'], 'rc.exe')
        logging.info('Calling Resource Compiler with "{0}{1}"'.format(exepath, self.config['path']))
        p = subprocess.Popen((exepath, '{0}'.format(self.config['path'])), stdout=subprocess.PIPE)
        logging.info(p.communicate()[0])
