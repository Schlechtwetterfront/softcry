import andesicore
reload(andesicore)
import crydaemon
reload(crydaemon)
from win32com.client import constants as const
import subprocess
import os
from datetime import datetime as dt
import logging
reload(logging)

from win32com.client import Dispatch
xsi = Dispatch('XSI.Application')


def get_plugin_origin():
    orig_path = ''
    plugins = xsi.Plugins
    for p in plugins:
        if p.Name == 'SoftCry':
            # Remove \\Application\\Plugins\\.
            orig_path = p.OriginPath[:-20]
    return orig_path


logpath = os.path.join(get_plugin_origin(), 'export.log')
logging.basicConfig(format='%(levelname)s (%(lineno)d, %(funcName)s): %(message)s',
                    filename=logpath,
                    filemode='w',
                    level=logging.DEBUG)


class MaterialConverter(andesicore.SIMaterial):
    def __init__(self, simat, index, libname, matman, export):
        self.export = export
        self.matman = matman
        self.simat = simat
        self.crymat = crydaemon.CryMaterial()
        self.crymat.index = index + 1
        self.libname = libname
        self.index = index + 1

    def convert(self):
        self.crymat.phys = self.get_phys()
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
        self.crymat.name = '{0}__{1:0>2}__{2}__{3}'.format(self.libname, self.index, self.simat.Name, self.crymat.phys)
        self.crymat.effect_name = '{0}-{1:0>2}-{2}-effect'.format(self.libname, self.index, self.simat.Name)
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
        filepath = tex_source.Source.Parameters('FileName').Value
        relative_filepath = self.get_relative_path(filepath)
        img = crydaemon.CryImageClip(relative_filepath)
        return self.matman.add_clip(img)

    def get_relative_path(self, path):
        folder_name = self.export.config['gamefolder_name']
        relative = path
        if folder_name in path:
            path_parts = path.split(folder_name)
            relative = path_parts[-1]
            if relative.startswith('\\') or relative.startswith('/'):
                relative = relative[1:]
        return relative

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
        self.temporary_path = os.path.join(self.get_plugin_origin(), 'Resources', 'Temp')
        if not os.path.isdir(self.temporary_path):
            os.mkdir(self.temporary_path)
        self.destination_path = '\\'.join(self.config['path'].split('\\')[:-1])
        self.filename = '.'.join(os.path.basename(self.config['path']).split('.')[:-1])
        self.collada_path = os.path.join(self.temporary_path, self.filename + '.dae')
        self.config['path'] = self.collada_path
        print self.collada_path
        print self.destination_path
        self.rc_path = os.path.join(self.config['rcpath'], 'rc.exe')
        #log_path = os.path.join(self.get_plugin_origin(), 'export.log')
        #logging.baseConfig(format='%(levelname)s (%(lineno)d, %(funcName)s): %(message)s',
        #                   filename=log_path,
        #                   filemode='w',
        #                   level=logging.DEBUG)

    def get_plugin_origin(self):
        orig_path = ''
        plugins = self.xsi.Plugins
        for p in plugins:
            if p.Name == 'SoftCry':
                # Remove \\Application\\Plugins\\.
                orig_path = p.OriginPath[:-20]
        return orig_path

    def copy_temp_files(self):
        import shutil
        for item in os.listdir(self.temporary_path):
            print item
            if item.endswith('.dae') or item.endswith('.rcdone'):
                continue
            possible_file = os.path.join(self.destination_path, os.path.basename(item))
            if os.path.isfile(possible_file):
                os.remove(possible_file)
            shutil.move(os.path.join(self.temporary_path, item), self.destination_path)

    def create_crosswalk_options(self):
        for prop in self.xsi.ActiveSceneRoot.Properties:
            if prop.Name == 'SCCrosswalkOptions':
                self.xsi.DeleteObj('SCCrosswalkOptions')
        options = self.xsi.ActiveSceneRoot.AddProperty('CustomProperty', False, 'SCCrosswalkOptions')
        options.AddParameter3('FileName', const.siString, self.collada_path)
        options.AddParameter3('Format', const.siInt4, 1)  # 1 = Collada file.
        options.AddParameter3('Format1', const.siInt4, 0)
        options.AddParameter3('Verbose', const.siBool, True)  # log to console.
        options.AddParameter3('ExportXSIExtra', const.siBool, False)  # XSI extra we don't need.
        options.AddParameter3('ExportSelectionOnly', const.siBool, True)  # yes!
        options.AddParameter3('ExportMaterials', const.siBool, True)
        options.AddParameter3('ExportGeometries', const.siBool, True)
        options.AddParameter3('ExportImageClips', const.siBool, True)  # not sure about that.
        options.AddParameter3('ExportUsedMaterialsAndImagesOnly', const.siBool, True)  # not sure either.
        options.AddParameter3('ExportAnimation', const.siBool, True)
        options.AddParameter3('ApplySubdivisionToGeometry', const.siBool, False)  # nope.
        options.AddParameter3('Triangulate', const.siBool, True)  # sure.
        options.AddParameter3('ExportTangentsAsVtxColor', const.siBool, False)  # nope.
        options.AddParameter3('ShapeAnim', const.siInt4, 1)  #
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

    def retrieve_materials(self):
        #lib = self.xsi.ActiveProject.ActiveScene.ActiveMaterialLibrary
        lib = self.xsi.Selection(0).Material.Library
        logging.info('Used MaterialLibrary: {0}'.format(lib.FullName))
        self.material_man.material_list = []
        self.material_man.material_dict = {}
        self.material_man.clip_list = []
        self.material_man.clip_dict = {}
        lib_is_external = False
        external_lib_path = ''
        for p in lib.Properties:
            if 'SoftCry' in p.Name:
                lib_is_external = p.Parameters('is_external').Value
                external_lib_path = p.Parameters('external_matlib').Value
        logging.info('Retrieving materials.')
        for ind, mat in enumerate(lib.Items):
            logging.debug('Converting Material: {0}'.format(mat.FullName))
            if lib_is_external is False:
                conv = MaterialConverter(mat, ind, lib.Name, self.material_man, self)
            else:
                conv = MaterialConverter(mat, ind, external_lib_path, self.material_man, self)
            self.material_man.add_material(conv.convert())
        logging.info('Retrieved materials.')

    def retrieve_clips(self):
        logging.info('Retrieving animation clips.')
        self.clips = self.get_anim_clips()
        if self.clips:
            logging.info('Retrieved {0} clips.'.format(len(self.clips)))
        else:
            logging.info('Retrieved no clips.')

    def do_material_export(self):
        logging.info('Starting material-only export.')
        self.material_man.write(self.collada_path)
        logging.info('Finished material-only export to {0}.'.format(self.collada_path))
        logging.info('calling RC with "{0} {1} /createmtl=1"'.format(self.rc_path, self.collada_path))
        p = subprocess.Popen((self.rc_path, self.collada_path, '/createmtl=1'), stdout=subprocess.PIPE)
        logging.info(p.communicate()[0])
        if self.config['deluncompiled']:
            os.remove(self.collada_path)
        self.copy_temp_files()

    def do_export(self):
        self.create_crosswalk_options()
        logging.info('Starting Crosswalk COLLADA export.')
        self.xsi.ExportCrosswalk('SCCrosswalkOptions')
        logging.info('Finished Crosswalk COLLADA export.')
        logging.info('Starting .DAE preparation.')
        self.config['scenename'] = os.path.basename(self.collada_path)[:-4]
        collada = crydaemon.Collada(self.config, material_man=self.material_man, clips=self.clips)
        logging.info('Starting adjust.')
        collada.adjust()
        logging.info('Finished adjusting .DAE.')
        collada.write()
        logging.info('Finished .DAE preparation.')
        command_line = [self.rc_path, self.collada_path]
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
            os.remove(self.collada_path)
        self.copy_temp_files()

    def export(self):
        self.export_start_time = dt.now()
        logging.info('Starting export at {0}.'.format(str(self.export_start_time)))
        # Material-only export.
        if self.config['filetype'] == 'matlib':
            self.material_man = crydaemon.CryMaterialManager()
            self.retrieve_materials()
            self.do_material_export()
            logging.info('Finished material export at {0}.'.format(str(dt.now())))
            return
        # Batch export.
        elif self.config['batch']:
            self.selection = self.xsi.Selection(0)
            roots = self.selection.Children
            for root in roots:
                to_select = self.get_all_children(root)
                self.xsi.Selection.Clear()
                logging.debug('Selection: {0}'.format(', '.join([obj.Name for obj in to_select])))
                for obj in to_select:
                    self.xsi.Selection.Add(obj)
                self.material_man = crydaemon.CryMaterialManager()
                self.retrieve_materials()
                self.retrieve_clips()
                self.collada_path = os.path.join(self.temporary_path, root.Name + '.dae')
                self.do_export()
            self.xsi.Selection.Clear()
            self.xsi.Selection.Add(self.selection)
            timing_result = dt.now() - self.export_start_time
            logging.info('Finished batch export ({0}s, {1}ms).'.format(timing_result.seconds, timing_result.microseconds))
            return
        # Standard export.
        else:
            self.selection = self.xsi.Selection(0)
            if not self.selection:
                logging.error('No selection')
                self.msg('No selection.', plugin='SoftCry')
                raise SystemExit
            try:
                self.hierarchy = self.get_all_children(self.selection)
                logging.debug('Selection: {0}'.format(', '.join([obj.Name for obj in self.hierarchy])))
            except AttributeError:
                logging.exception('')
                self.msg('Selection({0}: {1}) not valid.'.format(self.selection.Name, self.selection.Type), plugin='SoftCry')
                raise SystemExit
            if not self.hierarchy:
                logging.error('No valid selection')
                self.msg('No selection.', plugin='SoftCry')
                raise SystemExit
            self.material_man = crydaemon.CryMaterialManager()
            self.retrieve_materials()
            self.retrieve_clips()
            self.do_export()
            timing_result = dt.now() - self.export_start_time
            logging.info('Finished export ({0}s, {1}ms).'.format(timing_result.seconds, timing_result.microseconds))
            logging.shutdown()
