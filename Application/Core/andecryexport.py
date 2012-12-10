import andesicore
import crydaemon
reload(crydaemon)
reload(andesicore)
from win32com.client import constants as const
import subprocess
import os
from datetime import datetime
now = datetime.now

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

    def get_clip_prop(self):
        for prop in self.xsi.ActiveSceneRoot.Properties:
            if 'SoftCryAnimationClips' in prop.Name:
                return prop

    def get_anim_clips(self):
        clip_prop = self.get_clip_prop()
        if not clip_prop:
            return
        names = clip_prop.Parameters('names').Value
        starts = clip_prop.Parameters('starts').Value
        ends = clip_prop.Parameters('ends').Value

        if not names:
            return ()

        names = names.split('::')
        starts = starts.split('::')
        ends = ends.split('::')

        clips = []
        for index, name in enumerate(names):
            clips.append(crydaemon.CryClip(name, int(starts[index]), int(ends[index])))
        return clips

    def get_normal_map(self, mat):
        shader = mat.Shaders(0)
        col2vec_out = shader.Parameters('bump').Source
        if not col2vec_out:
            return None
        col2vec = col2vec_out.Parent
        img_out = col2vec.input.Source
        if not img_out:
            return None
        img = img_out.Parent
        return img.ImageClips(0).Source.Parameters('FileName').Value

    def retrieve_materials(self):
        lib = self.xsi.ActiveProject.ActiveScene.ActiveMaterialLibrary
        self.materials = []
        logging.info('Retrieving materials.')
        for ind, mat in enumerate(lib.Items):
            phys = 'physDefault'
            normal = ''  # self.get_normal_map(mat)
            for prop in mat.Properties:
                if 'SoftCryProp' in prop.Name:
                    phys = prop.Parameters('phys').Value
            cm = crydaemon.CryMaterial(mat.Name, ind, normal, phys)
            self.materials.append(cm)
        logging.info('Retrieved {0} materials.'.format(len(self.materials)))

    def retrieve_clips(self):
        logging.info('Retrieving animation clips.')
        self.clips = self.get_anim_clips()
        if self.clips:
            logging.info('Retrieved {0} clips.'.format(len(self.clips)))
        else:
            logging.info('Retrieved no clips.')

    def export(self):
        logging.info('Starting export at {0}.'.format(str(now())))
        if self.config['batch']:
            self.selection = self.xsi.Selection(0)
            roots = self.selection.Children
            for root in roots:
                to_select = self.get_all_children(root)
                self.xsi.Selection.Clear()
                for obj in to_select:
                    self.xsi.Selection.Add(obj)
                self.retrieve_materials()
                self.retrieve_clips()
                newpath = self.config['path'].split('\\')
                newpath[-1] = '{0}.dae'.format(root.Name)
                self.do_export('\\'.join(newpath))
            self.xsi.Selection.Clear()
            self.xsi.Selection.Add(self.selection)
            logging.info('Finished export.')
            return
        self.selection = self.xsi.Selection(0)
        if not self.selection:
            logging.error('No selection')
            self.msg('No selection.', plugin='SoftCry')
            raise SystemExit
        self.hierarchy = self.get_all_children(self.selection)
        if not self.hierarchy:
            logging.error('No valid selection')
            self.msg('No selection.', plugin='SoftCry')
            raise SystemExit
        self.retrieve_materials()
        self.retrieve_clips()
        self.do_export()
        logging.info('Finished export.')
        #logging.shutdown()

    def do_export(self, path=None):
        self.create_options()
        logging.info('Starting Crosswalk COLLADA export.')
        self.xsi.ExportCrosswalk('SCCrosswalkOptions')
        logging.info('Finished Crosswalk COLLADA export.')
        logging.info('Starting .DAE preparation.')
        self.config['scenename'] = os.path.basename(path or self.config['path'])[:-4]
        ed = crydaemon.ColladaEditor(self.config, self.materials, self.clips)
        ed.prepare_for_rc()
        logging.info('Finished .DAE preparation.')
        exepath = os.path.join(self.config['rcpath'], 'rc.exe')
        if self.config['onlymaterials']:
            logging.info('Calling Resource Compiler with "{0} {1} {2}"'.format(exepath, self.config['path'], '/createmtl=1'))
            p = subprocess.Popen((exepath, '{0}'.format(self.config['path']), '/createmtl=1'), stdout=subprocess.PIPE)
        else:
            logging.info('Calling Resource Compiler with "{0} {1}"'.format(exepath, self.config['path']))
            p = subprocess.Popen((exepath, '{0}'.format(self.config['path'])), stdout=subprocess.PIPE)
        logging.info(p.communicate()[0])
        if self.config['onlymaterials']:
            orig_path = path or self.config['path']
            orig_path = orig_path.split('\\')
            lib_path = orig_path[:-1]
            lib_path.append('library.mtl')
            lib_path = '\\'.join(lib_path)
            new_path = orig_path[:-1]
            new_path.append(orig_path[-1].replace('dae', 'mtl'))
            new_path = '\\'.join(new_path)
            if os.path.isfile(lib_path):
                if os.path.isfile(new_path):
                    os.remove(new_path)
                os.rename(lib_path, new_path)
