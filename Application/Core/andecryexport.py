# -*- coding: utf-8 -*-
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


class MaterialConverter(andesicore.SIMaterial):
    def __init__(self, simat, index, libname, matman):
        self.matman = matman
        self.simat = simat
        self.crymat = crydaemon.CryMaterial()
        self.crymat.index = index + 1
        self.libname = libname
        self.index = index + 1

    def convert(self):
        self.crymat.phys = self.get_phys()
        # self.crymat.emission
        self.crymat.ports['ambient'] = self.get_port('ambient')
        self.crymat.ports['diffuse'] = self.get_port('diffuse')
        self.crymat.ports['specular'] = self.get_port('specular')
        self.crymat.ports['shininess'] = self.get_value('shiny')
        self.crymat.ports['reflective'] = self.get_port('reflectivity')
        self.crymat.ports['reflectivity'] = self.get_value('scalerefl')
        self.crymat.ports['transparent'] = self.get_port('transparency')
        self.crymat.ports['transparency'] = self.get_value('scaletrans')
        self.crymat.ports['index_of_refraction'] = self.get_value('index_of_refraction')
        self.crymat.ports['normal'] = self.get_normal()
        self.crymat.old_name = self.simat.Name
        self.crymat.name = '{0}__{1}__{2}__{3}'.format(self.libname, self.index, self.simat.Name, self.crymat.phys)
        self.crymat.effect_name = '{0}-{1}-{2}-effect'.format(self.libname, self.index, self.simat.Name)
        return self.crymat

    def get_port(self, port_name):
        shader = self.simat.Shaders(0)
        port_param = shader.Parameters(port_name)
        if not port_param:
            return crydaemon.CryColor(0, 0, 0, 0)
        img_out = port_param.Source
        if not img_out:
            col = shader.Parameters(port_name).Value
            return crydaemon.CryColor(col.Red, col.Green, col.Blue, col.Alpha)
        img = img_out.Parent
        if not img:
            return crydaemon.CryColor(0, 0, 0, 0)
        # tex_source = img.tex.Source  # <- doesn't work in ModTool (XSI 7.5)
        tex_source = img.ImageClips(0)
        if not tex_source:
            return crydaemon.CryColor(0, 0, 0, 0)
        relative_filepath = tex_source.Source.Parameters('FileName').Value
        img = crydaemon.CryImageClip(relative_filepath)
        return self.matman.add_clip(img)

    def get_value(self, name):
        shader = self.simat.Shaders(0)
        param = shader.Parameters(name)
        if param:
            return param.Value

    def get_normal(self):
        shader = self.simat.Shaders(0)
        bump_param = shader.Parameters('bump')
        if not bump_param:
            return None
        col2vec_out = bump_param.Source
        if not col2vec_out:
            return None
        col2vec = col2vec_out.Parent
        img_out = col2vec.input.Source
        if not img_out:
            return None
        img = img_out.Parent
        rel_path = img.ImageClips(0).Source.Parameters('FileName').Value
        img = crydaemon.CryImageClip(rel_path)
        return self.matman.add_clip(img)

    def get_phys(self):
        phys = 'physDefault'
        for prop in self.simat.Properties:
            if 'SoftCryProp' in prop.Name:
                phys = prop.Parameters('phys').Value
                return phys
        return phys


class Export(andesicore.SIGeneral):
    def __init__(self, xsi, config):
        self.xsi = xsi
        self.config = config
        logpath = os.path.join(self.xsi.InstallationPath(const.siUserAddonPath), 'SoftCry', 'export.log')
        logging.basicConfig(format='%(levelname)s (%(lineno)d, %(funcName)s): %(message)s',
                            filename=logpath,
                            filemode='w',
                            level=logging.DEBUG)
        self.config['path'] = self.get_fixed_path()

    def create_options(self):
        for prop in self.xsi.ActiveSceneRoot.Properties:
            if prop.Name == 'SCCrosswalkOptions':
                self.xsi.DeleteObj('SCCrosswalkOptions')
        options = self.xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SCCrosswalkOptions')
        options.AddParameter3('FileName', const.siString, self.get_fixed_path())
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

    def retrieve_materials(self, matman):
        lib = self.xsi.ActiveProject.ActiveScene.ActiveMaterialLibrary
        matman.material_list = []
        matman.material_dict = {}
        matman.clip_list = []
        matman.clip_dict = {}
        logging.info('Retrieving materials.')
        for ind, mat in enumerate(lib.Items):
            conv = MaterialConverter(mat, ind, lib.Name, matman)
            matman.add_material(conv.convert())
            #self.materials.append(conv.convert())
        logging.info('Retrieved materials.')

    def retrieve_clips(self):
        logging.info('Retrieving animation clips.')
        self.clips = self.get_anim_clips()
        if self.clips:
            logging.info('Retrieved {0} clips.'.format(len(self.clips)))
        else:
            logging.info('Retrieved no clips.')

    def export(self):
        logging.info('Starting export at {0}.'.format(str(now())))
        if self.config['filetype'] == 'matlib':
            matmanager = crydaemon.CryMaterialManager()
            self.retrieve_materials(matmanager)
            self.do_material_export(matmanager)
            logging.info('Finished material export.')
            return

        if self.config['batch']:
            self.selection = self.xsi.Selection(0)
            roots = self.selection.Children
            for root in roots:
                to_select = self.get_all_children(root)
                self.xsi.Selection.Clear()
                for obj in to_select:
                    self.xsi.Selection.Add(obj)
                matmanager = crydaemon.CryMaterialManager()
                self.retrieve_materials(matmanager)
                self.retrieve_clips()
                newpath = self.config['path'].split('\\')
                newpath[-1] = '{0}.dae'.format(root.Name)
                self.do_export(matmanager, '\\'.join(newpath))
            self.xsi.Selection.Clear()
            self.xsi.Selection.Add(self.selection)
            logging.info('Finished export.')
            return
        self.selection = self.xsi.Selection(0)
        if not self.selection:
            logging.error('No selection')
            self.msg('No selection.', plugin='SoftCry')
            raise SystemExit
        try:
            self.hierarchy = self.get_all_children(self.selection)
        except AttributeError:
            logging.exception('')
            self.msg('Selection({0}: {1}) not valid.'.format(self.selection.Name, self.selection.Type), plugin='SoftCry')
            raise SystemExit
        if not self.hierarchy:
            logging.error('No valid selection')
            self.msg('No selection.', plugin='SoftCry')
            raise SystemExit
        matmanager = crydaemon.CryMaterialManager()
        self.retrieve_materials(matmanager)
        self.retrieve_clips()
        self.do_export(matmanager)
        logging.info('Finished export.')
        #logging.shutdown()

    def do_material_export(self, matman):
        libname = self.xsi.ActiveProject.ActiveScene.ActiveMaterialLibrary.Name
        writer = crydaemon.ColladaWriter()
        writer.material_manager = matman
        writer.material_lib_name = libname
        logging.info('Starting only-material collada writing.')
        writer.write_materials(self.config['path'])
        logging.info('Finished writing Collada file to {0}.'.format(self.get_fixed_path()))
        exepath = os.path.join(self.config['rcpath'], 'rc.exe')
        logging.info('Calling Resource Compiler with "{0} {1} /createmtl=1"'.format(exepath, self.get_fixed_path()))
        p = subprocess.Popen((exepath, '{0}'.format(self.get_fixed_path()), '/createmtl=1'), stdout=subprocess.PIPE)
        logging.info(p.communicate()[0])

    def get_fixed_path(self):
        path = self.config['path']
        print path
        if not path.endswith('.dae'):
            return '{0}.dae'.format(path)
        else:
            return path

    def do_export(self, matman, path=None):
        self.create_options()
        logging.info('Starting Crosswalk COLLADA export.')
        self.xsi.ExportCrosswalk('SCCrosswalkOptions')
        logging.info('Finished Crosswalk COLLADA export.')
        logging.info('Starting .DAE preparation.')
        self.config['scenename'] = os.path.basename(path or self.get_fixed_path())[:-4]
        ed = crydaemon.ColladaEditor(self.config, materialman=matman, clips=self.clips)
        ed.prepare_for_rc()
        logging.info('Finished .DAE preparation.')
        exepath = os.path.join(self.config['rcpath'], 'rc.exe')

        command_line = [exepath, self.get_fixed_path()]
        if self.config['debugdump']:
            command_line.append('/debugdump')
        command_line.append('/verbose={0}'.format(self.config['verbose']))

        logging.info('Calling Resource Compiler with "{0}"'.format(' '.join(command_line)))
        try:
            p = subprocess.Popen(command_line, stdout=subprocess.PIPE)
        except WindowsError:
            logging.exception('')
            self.msg('Make sure your RC path is correct.', plugin='SoftCry')
            raise SystemExit
        logging.info(p.communicate()[0])
        if self.config['deluncompiled']:
            os.remove(self.get_fixed_path())
