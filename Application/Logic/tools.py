try:
    xsi = Application
    ui = XSIUIToolkit
except NameError:
    print 'Not loaded from inside XSI.'
try:
    import andesicore
    sigen = andesicore.SIGeneral()
except ImportError:
    print 'Cannot import andesicore, PATH seemingly not including this directory.'
from win32com.client import constants as const


class SyncMaterial(object):
    name = ''
    diffuse = 1, 1, 1
    specular = 1, 1, 1
    emissive = 0, 0, 0
    shininess = 255
    opacity = 1
    textures = dict()

    def color(self, string):
        r, g, b = string.split(',')
        return float(r), float(g), float(b)


# Determinant of matrix a.
def det(a):
    return a[0][0]*a[1][1]*a[2][2] + a[0][1]*a[1][2]*a[2][0] + a[0][2]*a[1][0]*a[2][1] - a[0][2]*a[1][1]*a[2][0] - a[0][1]*a[1][0]*a[2][2] - a[0][0]*a[1][2]*a[2][1]


# Unit normal vector of plane defined by points a, b, and c.
def unit_normal(a, b, c):
    x = det([[1, a[1], a[2]],
            [1, b[1], b[2]],
            [1, c[1], c[2]]])
    y = det([[a[0], 1, a[2]],
            [b[0], 1, b[2]],
            [c[0], 1, c[2]]])
    z = det([[a[0], a[1], 1],
            [b[0], b[1], 1],
            [c[0], c[1], 1]])
    magnitude = (x**2 + y**2 + z**2)**.5
    return (x/magnitude, y/magnitude, z/magnitude)


# Dot product of vectors a and b.
def dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


# Cross product of vectors a and b.
def cross(a, b):
    x = a[1] * b[2] - a[2] * b[1]
    y = a[2] * b[0] - a[0] * b[2]
    z = a[0] * b[1] - a[1] * b[0]
    return (x, y, z)


# Area of polygon poly.
def area(poly):
    if len(poly) < 3:  # not a plane - no area
        return 0

    total = [0, 0, 0]
    for i in range(len(poly)):
        vi1 = poly[i]
        if i is len(poly)-1:
            vi2 = poly[0]
        else:
            vi2 = poly[i+1]
        prod = cross(vi1, vi2)
        total[0] += prod[0]
        total[1] += prod[1]
        total[2] += prod[2]
    result = dot(total, unit_normal(poly[0], poly[1], poly[2]))
    return abs(result/2)


def area2d(p):
    return 0.5 * abs(sum(x0*y1 - x1*y0
                         for ((x0, y0), (x1, y1)) in segments(p)))


def segments(p):
    return zip(p, p[1:] + [p[0]])


def set_vc_display(mode):
    mode = (1 if mode == 'rgb' else 2)
    viewman = xsi.Desktop.ActiveLayout.Views('vm')
    focused = viewman.GetAttributeValue('focusedviewport')
    cam_type = viewman.GetAttributeValue('activecamera:{0}'.format(focused))
    if cam_type == 'User':
        xsi.SetValue('Views.View{0}.UserCamera.camdisp.vcdisplay'.format(focused), mode, '')
    elif cam_type == 'Camera':
        xsi.SetValue('{0}.camdisp.vcdisplay'.format(cam_type), mode, '')


def get_matlib_property(matlib):
    for prop in matlib.Properties:
        if 'SoftCryMatLib' in prop.Name:
            return prop


def add_matlib_property(matlib, extpath, isext=True):
    prop = get_matlib_property(matlib)
    if prop:
        xsi.DeleteObj(prop)
    ps = matlib.AddProperty('CustomProperty', False, 'SoftCryMatLib')
    ps.AddParameter3('external_matlib', const.siString, extpath)
    ps.AddParameter3('is_external', const.siBool, isext, 0, 0, 0)

    lay = ps.PPGLayout

    lay.AddGroup('External')
    lay.AddItem('is_external', 'Is External')
    lay.AddItem('external_matlib', 'Path')
    lay.EndGroup()
    return ps


def get_relative_sdk_path(path):
    rel_path = path.split('\\')
    for index, item in enumerate(rel_path):
        if item.lower() == 'gamesdk':
            rel_path = rel_path[index + 1:]
            break
    rel_path = '\\'.join(rel_path).split('.')[0]
    return rel_path


### Callbacks ###


def finddegenerates_OnClicked():
    progress_bar = andesicore.SIProgressBar()
    progress_bar.show()
    progress_bar.setc('Getting Selection...')
    sel = xsi.Selection
    degenerates = []
    for item in sel:
        geo = item.ActivePrimitive.GetGeometry2(0)
        faces = geo.Facets
        progress_bar.set(faces.Count, 'Iterating faces...')
        for index, face in enumerate(faces):
            if face.Points.Count > 4:
                sigen.msg('Polygon {0} has more than 4 sides.'.format(face.Index), plugin='SoftCry')
                progress_bar.hide()
                return
            points = []
            for point in face.Points:
                points.append((point.Position.X, point.Position.Y, point.Position.Z))
            A = area(points)
            #print round(A)
            if A < 0.001:
                degenerates.append(face)
            progress_bar.inc()
    ppg = PPG.Inspected(0)
    ppg.Parameters('degeneratetxt').Value = 'Found {0} degenerate(s).'.format(str(len(degenerates)))
    progress_bar.set(1, 'Setting Selection...')
    sel.Clear()
    for face in degenerates:
        sel.Add(face)
    progress_bar.hide()


def degenerateuvs_OnClicked():
    # Not currently in use.
    sel = xsi.Selection
    degenerates = []
    for item in sel:
        geo = item.ActivePrimitive.GetGeometry2(0)
        for face in geo.Facets:
            if face.Samples.Count > 4:
                sigen.msg('Polygon {0} has more than 4 sides.'.format(face.Index), plugin='SoftCry')
                return
            samples = []
            for sample in face.Points:
                subc = sample.SubComponent
                print [c for c in subc.ComponentCollection]
            return
            A = area(samples)
            print round(A)
            if A < 0.001:
                degenerates.extend(sample for sample in face.Samples)
    ppg = PPG.Inspected(0)
    ppg.Parameters('degeneratetxtuv').Value = 'Found {0} degenerate(s).'.format(str(len(degenerates)))
    sel.Clear()
    for sample in degenerates:
        sel.Add(sample)


def setphys_OnClicked():
    sel = xsi.Selection
    ppg = PPG.Inspected(0)
    for item in sel:
        for p in item.Properties:
            if 'SoftCryProp' in p.Name:
                p.Parameters('phys').Value = ppg.Parameters('phystypes').Value
                return


def helpsetphys_OnClicked():
    sigen.msg('Will set phys type of selected materials (select them in the explorer).', plugin='SoftCry')


def showrgb_OnClicked():
    set_vc_display('rgb')


def showalpha_OnClicked():
    set_vc_display('alpha')


def helpvc_OnClicked():
    sigen.msg('Will set the Vertex Color display mode for the focused viewport to either RGB or Alpha.', plugin='SoftCry')


def synchelp_OnClicked():
    sigen.msg('''Sync the selected .mtl multi material file.
If the Material Library exists (checked via name), any missing materials will be created.
If it doesn't exist, the Library and all its sub-materials will be created.
If "Make External" is checked the .mtl file will be used as multi-material on export.''', plugin='SoftCry')


def matlibhelp_OnClicked():
    sigen.msg('''Set Selected As Active: Sets the selected Library to be the "current"/"active".
Edit Settings: Edit SoftCry specific MatLib settings (like external MatLibs).
''', plugin='SoftCry')


def sync_library(lib, materials, external):
    non_existent = []
    for material in materials:
        corresponding_material = None
        for simat in lib.Items:
            if material.name.lower() == simat.Name.lower():
                corresponding_material = material
                break
        if not corresponding_material:
            non_existent.append(material)
    for material in non_existent:
        lib.CreateMaterial('Phong', material.name)
    xsi.SetCurrentMaterialLibrary(lib)
    xsi.SoftCryCryifyMaterials()
    if external:
        add_matlib_property(lib, external, True)
    else:
        add_matlib_property(lib, '', False)
    return lib


def create_library(lib_name, materials, external):
    lib = xsi.CreateLibrary(lib_name)[0]  # CreateLibrary returns a tuple/array, the first value is the lib.
    for material in materials:
        lib.CreateMaterial('Phong', material.name)
    xsi.SetCurrentMaterialLibrary(lib)
    xsi.SoftCryCryifyMaterials()
    if external:
        add_matlib_property(lib, external, True)
    else:
        add_matlib_property(lib, '', False)
    return lib


def get_materials(path):
    from xml.etree.ElementTree import ElementTree
    tree = ElementTree(file=path)
    materials = []
    for material_node in tree.getroot().find('SubMaterials'):
        material = SyncMaterial()
        material.name = material_node.get('Name')
        material.diffuse = material.color(material_node.get('Diffuse'))
        material.specular = material.color(material_node.get('Specular'))
        material.emissive = material.color(material_node.get('Emissive'))
        if material_node.get('Shininess'):
            material.shininess = float(material_node.get('Shininess'))
        material.opacity = float(material_node.get('Opacity'))
        for tex in material_node.find('Textures'):
            material.textures[tex.get('Map')] = tex.get('File')
        materials.append(material)
    return materials


def sync_OnClicked():
    import os
    ppg = PPG.Inspected(0)
    path = ppg.Parameters('mtlpath').Value
    lib_name = os.path.basename(path).split('.')[0]
    make_external = ppg.Parameters('isexternal').Value
    external = None
    if make_external:
        external = get_relative_sdk_path(path)
    if not path:
        return
    libraries = xsi.ActiveProject.ActiveScene.MaterialLibraries
    for lib in libraries:
        if lib.Name == lib_name:
            sync_library(lib, get_materials(path), external)
            return
    create_library(lib_name, get_materials(path), external)


def edit_OnClicked():
    ppg = PPG.Inspected(0)
    lib = ppg.Parameters('matlib').Value
    if not lib:
        return
    lib = xsi.Dictionary.GetObject(lib)
    prop = get_matlib_property(lib)
    if prop:
        xsi.InspectObj(prop)
    else:
        xsi.InspectObj(add_matlib_property(lib, '', False))


def setmatlib_OnClicked():
    ppg = PPG.Inspected(0)
    lib = ppg.Parameters('matlib').Value
    if not lib:
        return
    xsi.SetCurrentMaterialLibrary(lib)
