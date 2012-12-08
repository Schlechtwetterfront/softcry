from xml.etree.ElementTree import ElementTree, SubElement, dump  # , Element
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


class CryMaterial(object):
    def __init__(self, name, index, phys):
        self.name = name
        self.index = index
        self.phys = phys

    def get_adjusted_name(self, scenename=None):
        if scenename:
            return '{0}__{1}__{2}__{3}'.format(scenename, self.index + 1,
                                                self.name, self.phys)
        else:
            return '{0}__sub{1}__{2}'.format(self.index + 1, self.index + 1, self.phys)


class ColladaEditor(object):
    def __init__(self, config, materials):
        self.config = config
        self.tree = None
        self.vertex_count = 0
        self.scene_name = os.path.basename(self.config['path'])[:-4]
        self.materials = self.adjust_materials(materials)
        self.controllers = {}

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

    def adjust_materials(self, materials):
        dc = {}
        for mat in materials:
            dc[mat.name] = mat.get_adjusted_name(self.scene_name)
        return dc

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

    def prepare_library_geometries(self):
        l.info('Preparing Library Geometries.')
        lib_geoms = self.root.find('library_geometries')
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
                elif 'XSINormal' in source.attrib['id']:
                    source.attrib['id'] = source.attrib['id'].replace('XSINormal', 'normals')
                    f_array = source.find('float_array')
                    f_array.attrib['id'] = f_array.attrib['id'].replace('XSINormal', 'normals')
                    acc = source.find('technique_common').find('accessor')
                    acc.attrib['source'] = acc.attrib['source'].replace('XSINormal', 'normals')
                elif 'Texture_Projection' in source.attrib['id']:
                    source.attrib['id'] = source.attrib['id'].replace('Texture_Projection', 'coords')
                    f_array = source.find('float_array')
                    f_array.attrib['id'] = f_array.attrib['id'].replace('Texture_Projection', 'coords')
                    acc = source.find('technique_common').find('accessor')
                    acc.attrib['source'] = acc.attrib['source'].replace('Texture_Projection', 'coords')
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
                tris.attrib['material'] = self.materials[tris.attrib['material']]
                inputs = tris.findall('input')
                for input_ in inputs:
                    if input_.attrib['semantic'] == 'VERTEX':
                        input_.attrib['source'] = input_.attrib['source'].replace('Vtx', 'vertices')
                    elif input_.attrib['semantic'] == 'NORMAL':
                        input_.attrib['source'] = input_.attrib['source'].replace('XSINormal', 'normals')
                    elif input_.attrib['semantic'] == 'TEXCOORD':
                        input_.attrib['source'] = input_.attrib['source'].replace('Texture_Projection', 'coords')
                if tris.find('vcount') is None:
                    vcount = SubElement(tris, 'vcount')
                    vcount.text = ' '.join(['3'] * self.vertex_count)
            l.info('Finished preparing {0}.'.format(geom.get('id')))

    def prepare_visual_scenes(self):
        l.info('Preparing Visual Scenes.')
        scenes = self.root.find('library_visual_scenes')
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
                    newname = self.materials[inst_mat.attrib['symbol']]
                    inst_mat.attrib['symbol'] = newname
                    inst_mat.attrib['target'] = '#{0}'.format(newname)

    def remove_library_effects(self):
        l.info('Removing Library Effects.')
        effects = self.root.find('library_effects')
        self.root.remove(effects)

    def prepare_library_materials(self):
        l.info('Preparing Library Materials.')
        lib_materials = self.root.find('library_materials')
        for lib_mat in lib_materials:
            newname = self.materials[lib_mat.attrib['id']]
            l.info('Setting ID and name from "{0}" to "{1}"'.format(lib_mat.get('id'), newname))
            lib_mat.attrib['id'] = newname
            lib_mat.attrib['name'] = newname
        l.info('Finished preparing Library Materials.')

    def prepare_library_controllers(self):
        l.info('Preparing Library Controllers.')
        lib_controllers = self.root.find('library_controllers')
        if lib_controllers is None:
            return
        for controller in lib_controllers:
            l.info('Preparing Controller "{0}".'.format(controller.get('id')))
            for skin in controller:
                geo_name = skin.get('source')[1:]
                cname = controller.get('id')
                controller.set('id', '{0}_{1}'.format(cname, geo_name))
                self.controllers[cname] = controller.get('id')
                sources = skin.findall('source')
                for source in sources:
                    if 'Joints' in source.get('id'):
                        self.replace_id(source, 'Joints', 'joints')
                        idref = source.find('IDREF_array')
                        if idref is not None:
                            idref.set('id', idref.get('id').replace('Joints', 'joints'))
                        tech = source.find('technique_common')
                        self.replace_technique_source(tech, 'Joints', 'joints')
                    elif 'Matrices' in source.get('id'):
                        self.replace_id(source, 'Matrices', 'matrices')
                        self.replace_id(source.find('float_array'), 'Matrices', 'matrices')
                        self.replace_technique_source(source.find('technique_common'), 'Matrices', 'matrices')
                    elif 'Weights' in source.get('id'):
                        self.replace_id(source, 'Weights', 'weights')
                        self.replace_id(source.find('float_array'), 'Weights', 'weights')
                        self.replace_technique_source(source.find('technique_common'), 'Weights', 'weights')
                joints = skin.find('joints')
                if joints is not None:
                    for input_ in joints:
                        if 'Joints' in input_.get('source'):
                            self.replace(input_, 'source', 'Joints', 'joints')
                        elif 'Matrices' in input_.get('source'):
                            self.replace(input_, 'source', 'Matrices', 'matrices')
                v_weights = skin.find('vertex_weights')
                if v_weights is not None:
                    inputs = v_weights.findall('input')
                    for input_ in inputs:
                        if 'Joints' in input_.get('source'):
                            self.replace(input_, 'source', 'Joints', 'joints')
                        elif 'Weights' in input_.get('source'):
                            self.replace(input_, 'source', 'Weights', 'weights')
        l.info('Finished preparing controllers.')

    def prepare_library_animations(self):
        l.info('Preparing Library Animations.')
        lib_anims = self.root.find('library_animations')
        if lib_anims is None:
            return
        for anim in lib_anims:
            to_replace = None
            with_this = None
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
        if lib_anims is not None:
            lib_clips = SubElement(self.root, 'library_animation_clips')
            clip = SubElement(lib_clips, 'animation_clip')
            clip.set('id', 'mainanim-{0}'.format(self.scene_name))
            #clip.set('name', 'main_anim')
            clip.set('start', '0.033367')
            clip.set('end', '0.3367')
            for anim in lib_anims:
                inst_anim = SubElement(clip, 'instance_animation')
                inst_anim.set('url', '#{0}'.format(anim.get('id')))
            clip2 = SubElement(lib_clips, 'animation_clip')
            clip2.set('id', 'mainanim2-{0}'.format(self.scene_name))
            #clip.set('name', 'main_anim')
            clip2.set('start', '0.33367')
            clip2.set('end', '0.666')
            for anim in lib_anims:
                inst_anim = SubElement(clip2, 'instance_animation')
                inst_anim.set('url', '#{0}'.format(anim.get('id')))
        l.info('Finished adding Clips.')

    def prepare_library_images(self):
        lib_images = self.root.find('library_images')
        if lib_images is None:
            return
        for image in lib_images:
            attribs = ('depth', 'format', 'height', 'width')
            for el in attribs:
                del image.attrib[el]
            path = image[0].text
            image[0].text = os.path.abspath(path)

    def prepare_library_effects(self):
        lib_effects = self.root.find('library_effects')
        if lib_effects is None:
            return
        for effect in lib_effects:
            name = effect.get('id')[:-3]
            self.replace_id(effect, name, self.materials[name])
            self.replace(effect, 'name', name, self.materials[name])
            profile = effect.find('profile_COMMON')
            params = profile.findall('newparam')
            for param in params:
                if '_surface' in param.get('sid'):
                    print dump(param)
                    self.replace(param, 'sid', '_surface', '-surface')
                    #surface = param.get('surface')
                    #init = surface.get('init_from')
                    # what now?
                elif '_sampler' in param.get('sid'):
                    self.replace(param, 'sid', '_sampler', '-sampler')
                    sampler = param[0]  # param.get('sampler2D')
                    print dump(sampler)
                    source = sampler[0]  # sampler.get('source')
                    source.text = source.text.replace('_surface', '-surface')
            tech = profile.find('technique')
            #tech.set('sid', 'common')
            phong = tech.find('phong')
            diff = phong.find('diffuse')
            if diff is not None:
                tex = diff.find('texture')
                if tex is not None:
                    del tex.attrib['texcoord']
                    self.replace(tex, 'texture', '_sampler', '-sampler')
            spec = phong.find('specular')
            if spec is not None:
                tex = spec.find('texture')
                if tex is not None:
                    del tex.attrib['texcoord']
                    self.replace(tex, 'texture', '_sampler', '-sampler')

    def adjust_asset(self):
        asset = self.root.find('asset')
        tool = asset.find('contributor').find('authoring_tool')
        tool.text = 'Softimage Crosswalk exporter featuring SoftCry exporter by Ande'
        unit = asset.find('unit')
        unit.set('meter', '1')
        unit.set('name', 'meter')
        up_axis = asset.find('up_axis')
        up_axis.text = 'Y_UP'

    def prepare_for_rc(self):
        self.temp_path = os.path.join(os.path.dirname(self.config['path']), 'tempfile')
        with open(self.temp_path, 'w') as fh:
            fh.writelines(self.get_adjusted())
        self.tree = ElementTree(file=self.temp_path)
        self.root = self.tree.getroot()

        # self.remove_library_effects()

        self.adjust_asset()

        self.prepare_library_images()

        # self.prepare_library_effects()

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
