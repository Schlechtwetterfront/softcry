from xml.etree.ElementTree import ElementTree, SubElement  # , dump  # , Element
import os

import logging as l

'''logpath = os.path.join(os.path.dirname(__file__), 'crydaemon.log')
l.basicConfig(format='%(levelname)s (%(lineno)d, %(funcName)s): %(message)s',
                    filename=logpath,
                    filemode='w',
                    level=l.DEBUG)'''


MATERIAL_PHYS = ('physDefault',  # default collision
                'physProxyNoDraw',  # default collision but geometry is invisible
                'physNone',  # no collision
                'physObstruct',  # only obstructs AI view
                'physNoCollide')  # will collide with bullets


class CryClip(object):
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end

    def adjust_name(self, scenename):
        self.name = '{0}-{1}'.format(self.name, scenename)

    def adjust_time(self):
        self.start = self.start / 30.0
        self.end = self.end / 30.0


class CryMaterial(object):
    def __init__(self, name, index, normalmap, phys):
        self.name = name
        self.index = index
        self.phys = phys
        self.normal_map = normalmap

    def get_normal_map_name(self):
        return os.path.basename(self.normal_map).replace('.', '_')

    def get_adjusted_name(self, scenename=None):
        if scenename:
            return '{0}__{1}__{2}__{3}'.format(scenename, self.index + 1,
                                                self.name, self.phys)
        else:
            return '{0}__sub{1}__{2}'.format(self.index + 1, self.index + 1, self.phys)


class ColladaEditor(object):
    def __init__(self, config, materials=None, clips=None):
        # config keys:
        #   donotmerge      bool
        #   path            string
        #   nustomnormals   bool
        #   filetype        string  : cgf | cgaanm | chrcaf
        #   rcpath          string
        #   unit            string  : meter | centimeter
        #   onlymaterials   bool
        #   scenename       string
        self.config = config
        self.tree = None
        self.vertex_count = 0
        self.scene_name = config['scenename']  # os.path.basename(self.config['path'])[:-4]
        self.material_names, self.materials = self.adjust_materials(materials)
        self.controllers = {}
        self.clips = self.adjust_clips(clips)

    def indent(self, elem, level=0):
        i = '\n' + level * '\t'
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + '\t'
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def adjust_clips(self, clips):
        if not clips:
            return ()
        for clip in clips:
            clip.adjust_name(self.scene_name)
            clip.adjust_time()
        return clips

    def adjust_materials(self, materials):
        dc = {}
        names = {}
        for mat in materials:
            names[mat.name] = mat.get_adjusted_name(self.scene_name)
            dc[mat.name] = mat
        return names, dc

    def get_adjusted(self):
        with open(self.config['path'], 'r') as fh:
            newfile = []
            for line in fh:
                if line[:2] == '<?':
                    continue
                elif 'COLLADA' in line:
                    if 'xmlns' in line:
                        newfile.append('<collada>\n')
                        continue
                    newfile.append(line.replace('COLLADA', 'collada'))
                else:
                    newfile.append(line)
            return newfile

    def replace_technique_source(self, tech_node, to_replace, with_this):
        acc = tech_node.find('accessor')
        if acc is not None:
            acc.set('source', acc.get('source').replace(to_replace, with_this))

    def replace_id(self, source_node, replace_this, with_this):
        source_node.set('id', source_node.get('id').replace(replace_this, with_this))

    def replace(self, node, attribute, to_replace, with_this):
        node.set(attribute, node.get(attribute).replace(to_replace, with_this))

    def round3(self, text):
        # Doesn't actually round right now.
        lines = text.split('\n')
        new_text = []
        l.info('Rounding {0} lines.'.format(len(lines)))
        for line in lines:
            if not line:
                continue
            line = line.strip()
            if not line:
                l.error('Line "{0}" not valid.'.format(repr(line)))
            try:
                x, y, z = line.split(' ')
            except ValueError:
                l.error('Line "{0}" not valid.'.format(line.split(' ')))
            #x = round(float(x), 2)
            #y = round(float(y), 2)
            #z = round(float(z), 2)
            new_text.extend((str(x), str(y), str(z)))
        return ' '.join(new_text)

    def round2(self, text):
        # Doesn't actually round right now.
        lines = text.split('\n')
        new_text = []
        l.info('Rounding {0} lines.'.format(len(lines)))
        for line in lines:
            if not line:
                continue
            line = line.strip()
            if not line:
                l.error('Line "{0}" not valid.'.format(repr(line)))
            try:
                x, y = line.split(' ')
            except ValueError:
                l.error('Line "{0}" not valid.'.format(line.split(' ')))
            #x = round(float(x), 2)
            #y = round(float(y), 2)
            #z = round(float(z), 2)
            new_text.extend((str(x), str(y)))
        return ' '.join(new_text)

    def roundx(self, text):
        # Doesn't actually round right now.
        lines = text.split('\n')
        new_text = []
        l.info('Rounding {0} lines.'.format(len(lines)))
        for line in lines:
            if not line:
                continue
            line = line.strip()
            if not line:
                l.error('Line "{0}" not valid.'.format(repr(line)))
            items = line.split(' ')
            # theoretically do rounding.
            new_text.extend(items)
        return ' '.join(new_text)

    def prepare_library_geometries(self):
        l.info('Preparing Library Geometries.')
        lib_geoms = self.root.find('library_geometries')
        if lib_geoms is None:
            l.error('No geometries.')
            return
        for geom in lib_geoms:
            l.info('Preparing Geometry {0}'.format(geom.get('id')))
            mesh = geom[0]
            sources = mesh.findall('source')
            # Adjust naming conventions for 'sources'.
            #   <Source>            <XSI>       ->      <CE>
            #   Vertex positions    Pos                 positions
            #   Normals             XSINormal           normals
            #   UV coords           Texture_Projection  coords
            for source in sources:
                if 'Pos' in source.get('id'):
                    source.set('id', source.get('id').replace('Pos', 'positions'))
                    f_array = source.find('float_array')
                    f_array.attrib['id'] = f_array.attrib['id'].replace('Pos', 'positions')
                    acc = source.find('technique_common').find('accessor')
                    acc.attrib['source'] = acc.attrib['source'].replace('Pos', 'positions')
                    self.vertex_count = int(f_array.attrib['count'])
                    f_array.text = self.round3(f_array.text)
                elif 'XSINormal' in source.attrib['id']:
                    source.attrib['id'] = source.attrib['id'].replace('XSINormal', 'normals')
                    f_array = source.find('float_array')
                    f_array.attrib['id'] = f_array.attrib['id'].replace('XSINormal', 'normals')
                    acc = source.find('technique_common').find('accessor')
                    acc.attrib['source'] = acc.attrib['source'].replace('XSINormal', 'normals')
                    f_array.text = self.round3(f_array.text)
                elif 'Texture_Projection' in source.attrib['id']:
                    source.attrib['id'] = source.attrib['id'].replace('Texture_Projection', 'coords')
                    f_array = source.find('float_array')
                    f_array.attrib['id'] = f_array.attrib['id'].replace('Texture_Projection', 'coords')
                    acc = source.find('technique_common').find('accessor')
                    acc.attrib['source'] = acc.attrib['source'].replace('Texture_Projection', 'coords')
                    f_array.text = self.round2(f_array.text)
            # Adjust vertices element id from 'Vtx' to 'vertices'.
            vertices = mesh.find('vertices')
            if 'Vtx' in vertices.attrib['id']:
                vertices.attrib['id'] = vertices.attrib['id'].replace('Vtx', 'vertices')
                input_ = vertices.find('input')
                if 'Pos' in input_.attrib['source']:
                    input_.attrib['source'] = input_.attrib['source'].replace('Pos', 'positions')
            # Adjust material name.
            triangles = mesh.findall('triangles')
            for tris in triangles:
                tris.attrib['material'] = self.material_names[tris.attrib['material']]
                inputs = tris.findall('input')
                for input_ in inputs:
                    if input_.attrib['semantic'] == 'VERTEX':
                        input_.attrib['source'] = input_.attrib['source'].replace('Vtx', 'vertices')
                    elif input_.attrib['semantic'] == 'NORMAL':
                        input_.attrib['source'] = input_.attrib['source'].replace('XSINormal', 'normals')
                    elif input_.attrib['semantic'] == 'TEXCOORD':
                        input_.attrib['source'] = input_.attrib['source'].replace('Texture_Projection', 'coords')
                p = tris.find('p')
                if p is not None:
                    p.text = self.roundx(p.text)
                if tris.find('vcount') is None:
                    vcount = SubElement(tris, 'vcount')
                    #vcount.text = ' '.join(['3'] * self.vertex_count)
                    vcount.text = ' '.join(['3'] * int(tris.get('count')))
            l.info('Finished preparing {0}.'.format(geom.get('id')))

    def prepare_visual_scenes(self):
        l.info('Preparing Visual Scenes.')
        scenes = self.root.find('library_visual_scenes')
        if scenes is None:
            l.error('No scenes.')
            return
        vis_scene = scenes[0]
        root_nodes = list(vis_scene)
        l.info('Creating CryExport Node.')
        cryexportnode = SubElement(vis_scene, 'node')
        cryexportnode.attrib['id'] = 'CryExportNode_{0}'.format(self.scene_name)
        extra = SubElement(cryexportnode, 'extra')
        tech = SubElement(extra, 'technique', profile='CryEngine')
        props = SubElement(tech, 'properties')
        ft = 'fileType={0}'.format(self.config['filetype'])
        flags = [ft]
        if self.config['donotmerge']:
            flags.append('DoNotMerge')
        if self.config['customnormals']:
            flags.append('CustomNormals')
        props.text = '\n'.join(flags)
        l.info('Applied flags "{0}" to CryExport Node.'.format(' '.join(flags)))
        # Remove nodes.
        for node in root_nodes:
            vis_scene.remove(node)
            cryexportnode.append(node)
        l.info('Reparented nodes.')
        self.recursive_adjust_nodes(cryexportnode)
        l.info('Finished preparing Visual Scenes.')

    def recursive_adjust_nodes(self, rootnode):
        nodes = rootnode.findall('node')
        for node in nodes:
            self.recursive_adjust_nodes(node)
        self.adjust_instance_materials(rootnode)
        '''extra = SubElement(rootnode, 'extra')
        tech = SubElement(extra, 'technique')
        tech.set('profile', 'CryEngine')
        props = SubElement(tech, 'properties')
        props.text = ''
        if rootnode.get('type') == 'JOINT':
            helper = SubElement(tech, 'helper')
            helper.set('type', 'dummy')
            bb_max = SubElement(helper, 'bound_box_max')
            bb_max.text = '0.5 0.5 0.5'
            bb_min = SubElement(helper, 'bound_box_min')
            bb_min.text = '-0.5 -0.5 -0.5'''

    def adjust_instance_materials(self, node):
        inst = node.find('instance_geometry')
        if inst is None:
            inst = node.find('instance_controller')
            if inst is None:
                return
            else:
                inst.set('url', '#{0}'.format(self.controllers[inst.get('url')[1:]]))
        bind_mat = inst.find('bind_material')
        if bind_mat is not None:
            tech = bind_mat.find('technique_common')
            if tech is not None:
                for inst_mat in tech:
                    newname = self.material_names[inst_mat.attrib['symbol']]
                    inst_mat.attrib['symbol'] = newname
                    inst_mat.attrib['target'] = '#{0}'.format(newname)

    def prepare_library_materials(self):
        l.info('Preparing Library Materials.')
        lib_materials = self.root.find('library_materials')
        if lib_materials is None:
            l.error('No materials.')
            return
        for lib_mat in lib_materials:
            newname = self.material_names[lib_mat.attrib['id']]
            l.info('Setting ID and name from "{0}" to "{1}"'.format(lib_mat.get('id'), newname))
            lib_mat.attrib['id'] = newname
            lib_mat.attrib['name'] = newname
        l.info('Finished preparing Library Materials.')

    def prepare_library_controllers(self):
        l.info('Preparing Library Controllers.')
        lib_controllers = self.root.find('library_controllers')
        if lib_controllers is None:
            l.info('No controllers.')
            return
        for controller in lib_controllers:
            l.info('Preparing Controller "{0}".'.format(controller.get('id')))
            for skin in controller:
                geo_name = skin.get('source')[1:]
                cname = controller.get('id')
                newname = '{0}_{1}'.format(cname, geo_name)
                controller.set('id', newname)
                self.controllers[cname] = controller.get('id')
                sources = skin.findall('source')
                for source in sources:
                    if 'Joints' in source.get('id'):
                        #self.replace_id(source, '-Joints', 'joints')
                        source.set('id', '{0}_joints'.format(newname))
                        idref = source.find('IDREF_array')
                        if idref is not None:
                            idref.set('id', '{0}_joints_array'.format(newname))
                        tech = source.find('technique_common')
                        #self.replace_technique_source(tech, '-Joints-array', '_joints_array')
                        acc = tech.find('accessor')
                        acc.set('source', '#{0}_joints_array'.format(newname))
                    elif 'Matrices' in source.get('id'):
                        #self.replace_id(source, '-Matrices', '_matrices')
                        #self.replace_id(source.find('float_array'), '-Matrices-array', '_matrices_array')
                        #self.replace_technique_source(source.find('technique_common'), '-Matrices-array', '_matrices_array')
                        source.set('id', '{0}_matrices'.format(newname))
                        source.find('float_array').set('id', '{0}_matrices_array'.format(newname))
                        tech = source.find('technique_common')
                        acc = tech.find('accessor')
                        acc.set('source', '#{0}_matrices_array'.format(newname))
                    elif 'Weights' in source.get('id'):
                        #self.replace_id(source, '-Weights', '_weights')
                        #self.replace_id(source.find('float_array'), '-Weights-array', '_weights_array')
                        #self.replace_technique_source(source.find('technique_common'), '-Weights-array', '_weights_array')
                        source.set('id', '{0}_weights'.format(newname))
                        source.find('float_array').set('id', '{0}_weights_array'.format(newname))
                        tech = source.find('technique_common')
                        acc = tech.find('accessor')
                        acc.set('source', '#{0}_weights_array'.format(newname))
                joints = skin.find('joints')
                if joints is not None:
                    for input_ in joints:
                        if 'Joints' in input_.get('source'):
                            #self.replace(input_, 'source', '-Joints', '_joints')
                            input_.set('source', '#{0}_joints'.format(newname))
                        elif 'Matrices' in input_.get('source'):
                            #self.replace(input_, 'source', '-Matrices', '_matrices')
                            input_.set('source', '#{0}_matrices'.format(newname))
                v_weights = skin.find('vertex_weights')
                if v_weights is not None:
                    inputs = v_weights.findall('input')
                    for input_ in inputs:
                        if 'Joints' in input_.get('source'):
                            #self.replace(input_, 'source', '-Joints', '_joints')
                            input_.set('source', '#{0}_joints'.format(newname))
                        elif 'Weights' in input_.get('source'):
                            #self.replace(input_, 'source', '-Weights', '_weights')
                            input_.set('source', '#{0}_weights'.format(newname))
        l.info('Finished preparing controllers.')

    def prepare_library_animations(self):
        l.info('Preparing Library Animations.')
        lib_anims = self.root.find('library_animations')
        if lib_anims is None:
            l.info('No animations.')
            return
        for anim in lib_anims:
            to_replace = ''
            with_this = ''
            if 'translation_X' in anim.get('id'):
                to_replace = 'translation_X-anim'
                with_this = 'location_X'
            elif 'translation_Y' in anim.get('id'):
                to_replace = 'translation_Y-anim'
                with_this = 'location_Y'
            elif 'translation_Z' in anim.get('id'):
                to_replace = 'translation_Z-anim'
                with_this = 'location_Z'
            elif 'rotation_x_ANGLE' in anim.get('id'):
                to_replace = 'rotation_x_ANGLE-anim'
                with_this = 'rotation_euler_X'
            elif 'rotation_y_ANGLE' in anim.get('id'):
                to_replace = 'rotation_y_ANGLE-anim'
                with_this = 'rotation_euler_Y'
            elif 'rotation_z_ANGLE' in anim.get('id'):
                to_replace = 'rotation_z_ANGLE-anim'
                with_this = 'rotation_euler_Z'
            self.replace_id(anim, to_replace, with_this)
            for source in anim.findall('source'):
                self.replace_id(source, to_replace, with_this)
                self.replace_technique_source(source.find('technique_common'), to_replace, with_this)
                farray = source.find('float_array')
                if farray is None:
                    farray = source.find('Name_array')
                self.replace_id(farray, to_replace, with_this)
                if 'InTan' in source.get('id'):
                    self.replace_id(source, 'InTan', 'intangent')
                    self.replace_technique_source(source.find('technique_common'), 'InTan', 'intangent')
                    self.replace_id(source.find('float_array'), 'InTan', 'intangent')
                elif 'OutTan' in source.get('id'):
                    self.replace_id(source, 'OutTan', 'outtangent')
                    self.replace_technique_source(source.find('technique_common'), 'OutTan', 'outtangent')
                    self.replace_id(source.find('float_array'), 'OutTan', 'outtangent')
                elif 'interp' in source.get('id'):
                    self.replace_id(source, 'interp', 'interpolation')
                    self.replace_technique_source(source.find('technique_common'), 'interp', 'interpolation')
                    self.replace_id(source.find('Name_array'), 'interp', 'interpolation')
            sampler = anim.find('sampler')
            if sampler is not None:
                self.replace_id(sampler, to_replace, with_this)
                for input_ in sampler:
                    self.replace(input_, 'source', to_replace, with_this)
                    self.replace(input_, 'source', 'InTan', 'intangent')
                    self.replace(input_, 'source', 'OutTan', 'outtangent')
                    self.replace(input_, 'source', 'interp', 'interpolation')
            channel = anim.find('channel')
            if channel is not None:
                self.replace(channel, 'source', to_replace, with_this)
        l.info('Finished preparing Library Animations.')

    def add_library_animation_clips(self):
        l.info('Adding Library Animation Clips.')
        lib_anims = self.root.find('library_animations')
        if (lib_anims is not None) and self.clips:
            lib_clips = SubElement(self.root, 'library_animation_clips')
            for clip in self.clips:
                clip_node = SubElement(lib_clips, 'animation_clip')
                clip_node.set('start', str(clip.start))
                clip_node.set('end', str(clip.end))
                clip_node.set('id', clip.name)
                for anim in lib_anims:
                    inst_anim = SubElement(clip_node, 'instance_animation')
                    inst_anim.set('url', '#{0}'.format(anim.get('id')))
        l.info('Added {0} clips.'.format(len(self.clips)))

    def prepare_library_images(self):
        l.info('Preparing Library Images.')
        lib_images = self.root.find('library_images')
        if lib_images is None:
            l.info('No images.')
            return
        for image in lib_images:
            attribs = ('depth', 'format', 'height', 'width')
            for el in attribs:
                del image.attrib[el]
            path = image[0].text
            image[0].text = os.path.abspath(path)
        l.info('Finished preparing Library Images.')

    def prepare_library_effects(self):
        l.info('Preparing Library Effects.')
        lib_effects = self.root.find('library_effects')
        if lib_effects is None:
            return
        for effect in lib_effects:
            material_name = effect.get('id')[:-3]
            print material_name
            profile = effect.find('profile_COMMON')
            mat = self.materials[material_name]
            if mat and mat.normal_map:
                normal_param = SubElement(profile, 'newparam')
                normal_param.set('sid', '{0}_surface'.format(mat.get_normal_map_name()))
                surf = SubElement(normal_param, 'surface')
                surf.set('type', '2D')
                init = SubElement(surf, 'init_from')
                init.text = '{0}_img'.format(mat.get_normal_map_name())

                sampler_param = SubElement(profile, 'newparam')
                sampler_param.set('sid', '{0}_sampler'.format(mat.get_normal_map_name()))
                sampler = SubElement(sampler_param, 'sampler2D')
                source = SubElement(sampler, 'source')
                source.text = '{0}_surface'.format(mat.get_normal_map_name())

                tech = profile.find('technique')
                phong = tech.find('phong')
                normal = SubElement(phong, 'normal')
                tex = SubElement(normal, 'texture')
                tex.set('texture', '{0}_sampler'.format(mat.get_normal_map_name()))
        l.info('Finished preparing Library Effects.')

    def adjust_asset(self):
        l.info('Adjusting asset.')
        asset = self.root.find('asset')
        tool = asset.find('contributor').find('authoring_tool')
        tool.text = 'Softimage Crosswalk exporter featuring SoftCry exporter by Ande'
        unit = asset.find('unit')
        if self.config['unit'] != 'meter':
            del unit.attrib['meter']
            unit.set(self.config['unit'], '1')
        else:
            unit.set('meter', '1')
        unit.set('name', self.config['unit'])
        up_axis = asset.find('up_axis')
        up_axis.text = 'Y_UP'
        l.info('Adjusted asset.')

    def remove_geometries(self):
        l.info('Removing geometries.')
        lib_geoms = self.root.find('library_geometries')
        if lib_geoms is not None:
            self.root.remove(lib_geoms)
            l.info('Removed geometries.')
            return
        l.info('No geometries.')

    def remove_controllers(self):
        l.info('Removing controllers.')
        lib_ctrls = self.root.find('library_controllers')
        if lib_ctrls is not None:
            self.root.remove(lib_ctrls)
            l.info('Removed controllers.')
            return
        l.info('No controllers.')

    def remove_animations(self):
        l.info('Removing animations.')
        lib_animations = self.root.find('library_animations')
        if lib_animations is not None:
            self.root.remove(lib_animations)
            l.info('Removed animations.')
            return
        l.info('No animations.')

    def remove_clips(self):
        l.info('Removing clips.')
        lib_clips = self.root.find('library_animation_clips')
        if lib_clips is not None:
            self.root.remove(lib_clips)
            l.info('Removed clips.')
            return
        l.info('No clips.')

    def remove_scenes(self):
        l.info('Removing scenes.')
        lib_scenes = self.root.find('library_visual_scenes')
        if lib_scenes is not None:
            self.root.remove(lib_scenes)
            l.info('Removed scenes.')
            return
        l.info('No scenes.')

    def remove_scene(self):
        l.info('Removing scene.')
        lib_scene = self.root.find('scene')
        if lib_scene is not None:
            self.root.remove(lib_scene)
            l.info('Removed scene.')
            return
        l.info('No scene.')

    def prepare_for_rc(self):
        self.temp_path = os.path.join(os.path.dirname(self.config['path']), 'tempfile')
        with open(self.temp_path, 'w') as fh:
            fh.writelines(self.get_adjusted())
        self.tree = ElementTree(file=self.temp_path)
        self.root = self.tree.getroot()

        if self.config['onlymaterials']:
            self.remove_geometries()

            self.remove_controllers()

            self.remove_animations()

            self.remove_clips()

            self.remove_scenes()

            self.remove_scene()

        else:
            self.adjust_asset()

            self.prepare_library_images()

            self.prepare_library_effects()

            self.prepare_library_materials()

            self.prepare_library_geometries()

            self.prepare_library_animations()

            self.prepare_library_controllers()

            self.prepare_visual_scenes()

            #self.indent(self.root)

            self.add_library_animation_clips()

        self.tree = ElementTree(element=self.root)

        self.tree.write(self.config['path'])

        os.remove(self.temp_path)
