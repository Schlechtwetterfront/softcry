from xml.etree.ElementTree import ElementTree, Element, SubElement, dump
import os

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
            return '{0}__{1}__sub{2}__{3}'.format(scenename, self.index + 1,
                                                self.index + 1, self.phys)
        else:
            return '{0}__sub{1}__{2}'.format(self.index + 1, self.index + 1, self.phys)


class ColladaEditor(object):
    def __init__(self, path, materials):
        self.path = path
        self.tree = None
        self.vertex_count = 0
        self.scene_name = os.path.basename(self.path)[:-4]
        self.materials = self.adjust_materials(materials)

    def adjust_materials(self, materials):
        dc = {}
        for mat in materials:
            dc[mat.name] = mat.get_adjusted_name(self.scene_name)
        return dc

    def get_adjusted(self):
        with open(self.path, 'r') as fh:
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

    def prepare_library_geometries(self):
        lib_geoms = self.root.find('library_geometries')
        for geom in lib_geoms:
            mesh = geom[0]
            sources = mesh.findall('source')
            # Adjust naming conventions for 'sources'.
            #   <Source>            <XSI>       ->      <CE>
            #   Vertex positions    Pos                 positions
            #   Normals             XSINormal           normals
            #   UV coords           Texture_Projection  coords
            for source in sources:
                if 'Pos' in source.attrib['id']:
                    source.attrib['id'] = source.attrib['id'].replace('Pos', 'positions')
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

    def prepare_visual_scenes(self):
        scenes = self.root.find('library_visual_scenes')
        vis_scene = scenes[0]
        root_nodes = list(vis_scene)
        cryexportnode = SubElement(vis_scene, 'node')
        cryexportnode.attrib['id'] = 'CryExportNode_{0}'.format(self.scene_name)
        extra = SubElement(cryexportnode, 'extra')
        tech = SubElement(extra, 'technique', profile='CryEngine')
        props = SubElement(tech, 'properties')
        # TODO: replace flags from UI.
        props.text = 'fileType=cgf DoNotMerge UseCustomNormals'
        # Remove nodes.
        for node in root_nodes:
            vis_scene.remove(node)
            cryexportnode.append(node)
        self.recursive_adjust_nodes(cryexportnode)

    def recursive_adjust_nodes(self, rootnode):
        nodes = rootnode.findall('node')
        for node in nodes:
            self.recursive_adjust_nodes(node)
        self.adjust_instance_materials(rootnode)

    def adjust_instance_materials(self, node):
        inst_geo = node.find('instance_geometry')
        if inst_geo is not None:
            bind_mat = inst_geo.find('bind_material')
            if bind_mat is not None:
                tech = bind_mat.find('technique_common')
                if tech is not None:
                    for inst_mat in tech:
                        newname = self.materials[inst_mat.attrib['symbol']]
                        inst_mat.attrib['symbol'] = newname
                        inst_mat.attrib['target'] = '#{0}'.format(newname)

    def remove_library_effects(self):
        effects = self.root.find('library_effects')
        self.root.remove(effects)

    def prepare_library_materials(self):
        lib_materials = self.root.find('library_materials')
        for lib_mat in lib_materials:
            newname = self.materials[lib_mat.attrib['id']]
            lib_mat.attrib['id'] = newname
            lib_mat.attrib['name'] = newname

    def prepare_for_rc(self):
        self.temp_path = os.path.join(os.path.dirname(self.path), 'tempfile')
        with open(self.temp_path, 'w') as fh:
            fh.writelines(self.get_adjusted())
        self.tree = ElementTree(file=self.temp_path)
        self.root = self.tree.getroot()

        # self.remove_library_effects()

        self.prepare_library_materials()

        self.prepare_library_geometries()

        self.prepare_visual_scenes()

        self.tree = ElementTree(element=self.root)

        self.tree.write(self.path)

        os.remove(self.temp_path)
