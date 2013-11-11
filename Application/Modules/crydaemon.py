from xml.etree.ElementTree import ElementTree, SubElement, Element
import os

import logging


logpath = os.path.join(os.path.dirname(__file__), 'crydaemon.log')
logging.basicConfig(format='%(levelname)s (%(lineno)d, %(funcName)s): %(message)s',
                    filename=logpath,
                    filemode='w',
                    level=logging.DEBUG)


MATERIAL_PHYS = ('physDefault',  # default collision
                 'physProxyNoDraw',  # default collision but geometry is invisible
                 'physNone',  # no collision
                 'physObstruct',  # only obstructs AI view
                 'physNoCollide')  # will collide with bullets


def indent(elem, level=0):
    i = '\n' + level * '\t'
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + '\t'
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class CryMaterialManager(object):
    def __init__(self):
        self.material_list = None
        self.material_dict = None
        self.material_dict_old = None
        self.clip_list = None
        self.clip_dict = None

    def write(self, path):
        collada = Element('collada')
        asset = SubElement(collada, 'asset')
        contributor = SubElement(asset, 'contributor')
        tool = SubElement(contributor, 'authoring_tool')
        tool.text = 'SoftCry exporter by Ande'
        url = SubElement(contributor, 'url')
        url.text = 'https://github.com/Schlechtwetterfront/softcry'
        collada.append(self.get_lib_images())
        collada.append(self.get_lib_fx())
        collada.append(self.get_lib_materials())
        indent(collada)
        tree = ElementTree(element=collada)
        tree.write(path)

    def create_old_name_dict(self):
        oldnames = {}
        for mat in self.material_list:
            oldnames[mat.old_name] = mat
        self.material_dict_old = oldnames

    def get_clip(self, key):
        if isinstance(key, str):
            return self.clip_dict[key]
        elif isinstance(key, int):
            return self.clip_list[key]

    def get_material(self, key):
        if isinstance(key, str):
            return self.material_dict[key]
        elif isinstance(key, int):
            return self.material_list[key]

    def add_clip(self, clip):
        if clip.name in self.clip_dict.keys():
            return self.clip_dict[clip.name]
        else:
            self.clip_list.append(clip)
            self.clip_dict[clip.name] = clip
            return clip

    def add_material(self, material):
        if material.name in self.material_dict.keys():
            return self.material_dict[material.name]
        else:
            self.material_list.append(material)
            self.material_dict[material.name] = material
            return material

    def get_lib_fx(self):
        lib_fx = Element('library_effects')
        for mat in self.material_list:
            lib_fx.append(mat.to_xml_fx())
        return lib_fx

    def get_lib_images(self):
        lib_images = Element('library_images')
        for clip in self.clip_list:
            lib_images.append(clip.to_xml_image())
        return lib_images

    def get_lib_materials(self):
        lib_mats = Element('library_materials')
        for mat in self.material_list:
            lib_mats.append(mat.to_xml())
        return lib_mats


class CrySource(object):
    '''Source for Materials. Should always implement .get() which returns the value of the source.'''
    type = 'CrySource'

    def get(self):
        return


class CryColor(CrySource):
    type = 'ColorSource'

    def __init__(self, r, g, b, a=0.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def get(self):
        return '{0} {1} {2} {3}'.format(self.r, self.g, self.b, self.a)

    def to_xml(self, color_name):
        col = Element('color')
        col.set('sid', color_name)
        col.text = self.get()
        return col


class CryImageClip(CrySource):
    type = 'ImageSource'

    def __init__(self, imagename):
        self.name = imagename.split('\\')[-1]
        print 'CryImageClip name: ', self.name
        self.image = imagename
        print 'CryImageClip image: ', self.image

    def get(self):
        return self.image

    def to_xml_image(self):
        img = Element('image')
        img.set('id', self.name)
        img.set('name', self.name)
        init = SubElement(img, 'init_from')
        init.text = self.image
        return img

    def to_xml_texture(self):
        tex = Element('texture')
        tex.set('texture', '{0}_sampler'.format(self.name))
        return tex

    def to_xml_sampler(self):
        param = Element('newparam')
        param.set('sid', '{0}_sampler'.format(self.name))
        sampler = SubElement(param, 'sampler2D')
        source = SubElement(sampler, 'source')
        source.text = '{0}_surface'.format(self.name)
        return param

    def to_xml_surface(self):
        param = Element('newparam')
        param.set('sid', '{0}_surface'.format(self.name))
        surf = SubElement(param, 'surface')
        surf.set('type', '2D')
        init = SubElement(surf, 'init_from')
        init.text = self.name
        return param


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
    def __init__(self):
        self.name = 'MATERIAL'
        self.old_name = ''  # name in Softimage.
        self.index = 0
        self.phys = 'physDefault'  # String
        self.ports = {
            'emission': CryColor(0, 0, 0, 0),
            'ambient': CryColor(0.3, 0.3, 0.3, 1),
            'diffuse': CryColor(0.7, 0.7, 0.7, 1),
            'specular': CryColor(1, 1, 1, 1),
            'shininess': 50,
            'reflective': CryColor(0, 0, 0, 0),
            'reflectivity': 1,
            'transparent': CryColor(0, 0, 0, 0),
            'transparency': 1,
            'index_of_refraction': 1,
            'normal': None,
        }

    def to_xml(self):
        mat = Element('material')
        mat.set('id', self.name)
        mat.set('name', self.name)
        inst = SubElement(mat, 'instance_effect')
        inst.set('url', '#{0}_fx'.format(self.name))
        return mat

    def to_xml_fx(self):
        effect = Element('effect')
        effect.set('id', '{0}_fx'.format(self.name))
        effect.set('name', '{0}_fx'.format(self.name))
        profile = SubElement(effect, 'profile_COMMON')
        tech = SubElement(profile, 'technique')
        tech.set('sid', 'default')
        phong = SubElement(tech, 'phong')
        for port in self.ports.keys():
            port_node = SubElement(phong, port)
            source = self.ports[port]
            if not source:
                phong.remove(port_node)
                continue
            if isinstance(source, float) or isinstance(source, int):
                float_node = SubElement(port_node, 'float')
                float_node.set('sid', port)
                float_node.text = str(source)
            elif source.type == 'ColorSource':
                port_node.append(source.to_xml(port))
            elif source.type == 'ImageSource':
                port_node.append(source.to_xml_texture())
                profile.append(source.to_xml_surface())
                profile.append(source.to_xml_sampler())
        return effect


class Collada(object):
    def __init__(self, config, material_man=None, clips=None):
        # config keys:
        #   donotmerge      bool
        #   path            string
        #   customnormals   bool
        #   filetype        string  : cgf | cgaanm | chrcaf
        #   rcpath          string
        #   unit            string  : meter | centimeter
        #   onlymaterials   bool
        #   scenename       string
        self.config = config
        self.tree = None
        self.material_man = material_man
        self.controllers = {}
        self.clips = self.adjust_clips(clips)
        #self.temporary_path = '\\'.join(self.config['path'].split('\\')[:-1])
        #self.temporary_file = ps.path.join(temporary_path, 'tempfile.dae')

    def adjust_clips(self, clips):
        if not clips:
            return ()
        for clip in clips:
            clip.adjust_name(self.config['scenename'])
            clip.adjust_time()
        return clips

    def recursive_strip(self, elem):
        if elem.tail:
            elem.tail = elem.tail.strip()
        if elem.text:
            elem.text = elem.text.strip()
        for child in elem:
            self.recursive_strip(child)

    def roundx(self, text):
        # Doesn't actually round right now.
        lines = text.split('\n')
        new_text = []
        logging.info('Rounding {0} lines.'.format(len(lines)))
        for line in lines:
            if not line:
                continue
            line = line.strip()
            if not line:
                logging.error('Line "{0}" not valid.'.format(repr(line)))
            items = line.split(' ')
            # theoretically do rounding.
            new_text.extend(items)
        return ' '.join(new_text)

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
        bind_mat = inst.find('bind_material')
        if bind_mat is not None:
            tech = bind_mat.find('technique_common')
            if tech is not None:
                for inst_mat in tech:
                    if '.' in inst_mat.get('symbol'):
                        # If multiple material libraries are in a scene the materials will be named
                        # <matlib>.<matname>. '.' can't be used for names by the user, so it's safe
                        # to just split the material name if it occurs.
                        newname = self.material_man.material_dict_old[inst_mat.get('symbol').split('.')[-1]].name
                    else:
                        newname = self.material_man.material_dict_old[inst_mat.attrib['symbol']].name
                    inst_mat.attrib['symbol'] = newname
                    inst_mat.attrib['target'] = '#{0}'.format(newname)

    def adjust_asset(self):
        logging.info('Adjusting asset.')
        asset = self.root.find('asset')
        tool = asset.find('contributor').find('authoring_tool')
        tool.text = 'Softimage Crosswalk exporter featuring SoftCry exporter by Ande'
        url = asset.find('contributor').find('url')
        if not url:
            url = SubElement(asset.find('contributor'), 'url')
        url.text = 'https://github.com/Schlechtwetterfront/softcry'
        unit = asset.find('unit')
        if self.config['unit'] != 'meter':
            del unit.attrib['meter']
            unit.set(self.config['unit'], '1')
        else:
            unit.set('meter', '1')
        unit.set('name', self.config['unit'])
        up_axis = asset.find('up_axis')
        up_axis.text = 'Y_UP'
        logging.info('Adjusted asset.')

    def replace_library_images(self):
        logging.info('Replacing Library Images.')
        lib_images = self.root.find('library_images')
        if lib_images is None:
            logging.info('No images.')
            return
        self.root.remove(lib_images)
        self.root.append(self.material_man.get_lib_images())
        logging.info('Finished replacing Library Images.')

    def replace_library_effects(self):
        logging.info('Replacing library effects.')
        lib_effects = self.root.find('library_effects')
        if lib_effects is None:
            return
        self.root.remove(lib_effects)
        self.root.append(self.material_man.get_lib_fx())
        logging.info('Finished replacing library effects.')

    def replace_library_materials(self):
        logging.info('Replacing Library Materials.')
        lib_materials = self.root.find('library_materials')
        if lib_materials is None:
            logging.error('No materials.')
            return
        self.root.remove(lib_materials)
        self.root.append(self.material_man.get_lib_materials())
        logging.info('Finished replacing library materials.')

    def adjust_library_geometries(self):
        logging.info('Preparing Library Geometries.')
        lib_geoms = self.root.find('library_geometries')
        if lib_geoms is None:
            logging.error('No geometries.')
            return
        for geom in lib_geoms:
            logging.info('Preparing Geometry {0}'.format(geom.get('id')))
            mesh = geom[0]
            # Adjust material name.
            triangles = mesh.findall('triangles')
            for tris in triangles:
                print tris.get('material')
                print self.material_man.material_dict_old.keys()
                if '.' in tris.get('material'):
                    # If multiple material libraries are in a scene the materials will be named
                    # <matlib>.<matname>. '.' can't be used for names by the user, so it's safe
                    # to just split the material name if it occurs.
                    tris.set('material', self.material_man.material_dict_old[tris.get('material').split('.')[-1]].name)
                else:
                    tris.attrib['material'] = self.material_man.material_dict_old[tris.attrib['material']].name
                p = tris.find('p')
                if p is not None:
                    p.text = self.roundx(p.text)
            logging.info('Finished preparing {0}.'.format(geom.get('id')))

    def adjust_library_controllers(self):
        logging.info('Adjusting Library Controllers.')
        lib_controllers = self.root.find('library_controllers')
        if lib_controllers is None:
            logging.info('No controllers.')
            return
        for controller in lib_controllers:
            logging.info('Preparing Controller "{0}".'.format(controller.get('id')))
            for skin in controller:
                v_weights = skin.find('vertex_weights')
                if v_weights is not None:
                    v = v_weights.find('v')
                    if v is not None:
                        lines = v.text.split('\n')
                        new_lines = []
                        for line in lines:
                            new_line = line.strip().split(' ')
                            new_lines.extend(new_line)
                        v.text = ' '.join(new_lines)
        logging.info('Finished adjusting controllers.')

    def adjust_visual_scenes(self):
        logging.info('Adjusting Visual Scenes.')
        scenes = self.root.find('library_visual_scenes')
        if scenes is None:
            logging.error('No scenes.')
            return
        vis_scene = scenes[0]
        root_nodes = list(vis_scene)
        logging.info('Creating CryExport Node.')
        cryexportnode = SubElement(vis_scene, 'node')
        cryexportnode.attrib['id'] = 'CryExportNode_{0}'.format(self.config['scenename'])
        extra = SubElement(cryexportnode, 'extra')
        tech = SubElement(extra, 'technique', profile='CryEngine')
        props = SubElement(tech, 'properties')
        ft = 'fileType={0}'.format(self.config['filetype'])
        flags = [ft]
        if self.config['donotmerge']:
            flags.append('DoNotMerge')
        if self.config['customnormals']:
            flags.append('CustomNormals')
        if self.config['f32']:
            flags.append('UseF32VertexFormat')
        props.text = '\n\t\t'.join(flags)
        logging.info('Applied flags "{0}" to CryExport Node.'.format(' '.join(flags)))
        # Remove nodes.
        for node in root_nodes:
            vis_scene.remove(node)
            cryexportnode.append(node)
        logging.info('Reparented nodes.')
        self.recursive_adjust_nodes(cryexportnode)
        logging.info('Finished adjusting Visual Scenes.')

    def add_library_animation_clips(self):
        logging.info('Adding Library Animation Clips.')
        lib_anims = self.root.find('library_animations')
        if (lib_anims is not None) and self.clips:
            lib_clips = SubElement(self.root, 'library_animation_clips')
            for clip in self.clips:
                clip_node = SubElement(lib_clips, 'animation_clip')
                clip_node.set('start', str(clip.start))
                clip_node.set('end', str(clip.end))
                clip_node.set('id', clip.name)
                clip_node.set('name', clip.name)
                for anim in lib_anims:
                    inst_anim = SubElement(clip_node, 'instance_animation')
                    inst_anim.set('url', '#{0}'.format(anim.get('id')))
        logging.info('Added {0} clips.'.format(len(self.clips)))

    def remove_xmlns(self):
        lines = []
        with open(self.config['path'], 'r') as fh:
            for line in fh:
                if line.startswith('<?'):
                    continue
                elif ('COLLADA' in line) and ('xmlns' in line):
                    lines.append('<COLLADA>\n')
                else:
                    lines.append(line)
        with open(self.config['path'], 'w') as fh:
            fh.writelines(lines)
        logging.info('Removed xmlns.')

    def adjust(self):
        logging.info('Starting adjust.')
        self.remove_xmlns()

        logging.info('Reading .dae.')
        self.tree = ElementTree(file=self.config['path'])
        self.root = self.tree.getroot()
        logging.info('Finished reading .dae.')

        self.material_man.create_old_name_dict()

        self.recursive_strip(self.root)

        self.adjust_asset()

        self.replace_library_images()
        self.replace_library_effects()
        self.replace_library_materials()
        self.adjust_library_geometries()
        # Animations?
        self.adjust_library_controllers()
        self.adjust_visual_scenes()

        self.add_library_animation_clips()

        indent(self.root)

        self.tree = ElementTree(element=self.root)

        logging.info('Finished adjust.')

    def write(self, path=None):
        filepath = path or self.config['path']
        self.tree.write(filepath)
