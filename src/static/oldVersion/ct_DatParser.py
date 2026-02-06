import bpy
import bmesh
import math
from struct import unpack
from bpy_extras import object_utils
from pathlib import Path

from .ct_BinaryReader import *


class DatModel:
    name = ""
    vertices = []
    map_vertices = []
    faces = []
    smoothing_groups = []
    edge_visibillity = []
    mat_names = []
    face_ids = []
    mesh = None
    
def import_dat(datfile):

    dat_models = []

    with open(datfile, 'rb') as f:
        file_size = get_size(f)

        # read header
        first = read_float(f)
        second = read_float(f)
        face = read_float(f)
        two = read_float(f)

        f.seek(0,0)
        while (f.tell() < file_size):
            identifier = read_int(f)
            block_length = read_int(f)

            if identifier == 54:  # read modelname
                dat_model = DatModel()
                attributes = f.read(2)  # always 21?
                dat_model.name = read_string(f)

            if identifier == 23:  # read vertices
                vertex_count = read_int(f)
                dat_model.vertices = []
                for i in range(vertex_count):
                    x = read_float(f)
                    y = read_float(f)
                    z = read_float(f)
                    dat_model.vertices.append([x, -z, y])

            if identifier == 24:  # read map vertices
                map_vertex_count = read_int(f)
                dat_model.map_vertices = []
                for i in range(map_vertex_count):
                    u = read_float(f)
                    v = read_float(f)
                    dat_model.map_vertices.append((u, -v))

            if identifier == 53:  # read face data
                face_count = read_int(f)
                dat_model.faces = []
                dat_model.smoothing_groups = []
                dat_model.edge_visibillity = []
                for i in range(face_count):
                    v1 = read_short(f)  # vertex indices
                    v2 = read_short(f)
                    v3 = read_short(f)
                    sm = read_short(f)  # smoothing group as 2
                    ev = read_char(f)
                    dat_model.faces.append([v1, v2, v3])
                    dat_model.smoothing_groups.append(sm)
                    dat_model.edge_visibillity.append(ev)

            if identifier == 22:  # read material names
                mat_name_count = read_int(f)
                dat_model.mat_names = []
                for i in range(mat_name_count):
                    dat_model.mat_names.append(read_string(f))

            if identifier == 26:  # read face ids
                face_count = read_int(f)
                face_flags = read_int(f)
                dat_model.face_ids = []
                for i in range(face_count):
                    dat_model.face_ids.append(read_short(f))

            if identifier == 0:  # end of a model entry
                mesh = build_model(dat_model)
                dat_model.mesh = mesh
                dat_models.append(dat_model)  # add model to model list
                dat_model = None

    return dat_models


def build_model(dat_model):

    mesh = bpy.data.meshes.new(dat_model.name)
    # [] is in place of edges, is an empty list
    mesh.from_pydata(dat_model.vertices, [], dat_model.faces)

    # enable autosmooth for showing the hard edge effects
    mesh.use_auto_smooth = 1
    mesh.auto_smooth_angle = math.radians(90)

    # create a bmesh to do fancy operations on
    bm = bmesh.new()
    bm.from_mesh(mesh)

    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    
    bm.edges.ensure_lookup_table()
    bm.edges.index_update()

    uvs = dat_model.map_vertices
    # set extra face information
    for i in range(len(bm.faces)):
        face = bm.faces[i]
        face.smooth = True

        # add material ids
        if len(dat_model.face_ids) > 0:
            if dat_model.face_ids[i] == 0:
                face.material_index = 0    
            else:
                face.material_index = dat_model.face_ids[i] - 1
        else:
           face.material_index = 1  
        
        # add uv'
        if bm.loops.layers.uv.items():
            uv_layer = bm.loops.layers.uv[0]
        else:
            uv_layer = bm.loops.layers.uv.new()

        for j in range(len(face.verts)):
            vert = face.verts[j]
            index = vert.index
            face.loops[j][uv_layer].uv = uvs[index]

        # add hard and soft edges
        smoothing_group = dat_model.smoothing_groups[i]
        for edge in face.edges:
           linked_faces = edge.link_faces
           for j in range(len(linked_faces)):
                linked_face = linked_faces[j]
                if linked_face.index != face.index:
                    linked_smoothing_group = dat_model.smoothing_groups[linked_face.index]
                    if (smoothing_group != linked_smoothing_group):
                        edge.smooth = False
                    else:
                        edge.smooth = True
        
        # add edge visibility
        edgevis = dat_model.edge_visibillity[face.index]
        match edgevis:
            case 1:
                face.edges[0].hide = True
            case 2:
                face.edges[1].hide = True
            case 3:
                face.edges[0].hide = True
                face.edges[1].hide = True
            case 4:
                face.edges[2].hide = True
            case 5:
                face.edges[0].hide = True
                face.edges[2].hide = True
            case 6:
                face.edges[1].hide = True
                face.edges[2].hide = True
            case 7:
                face.edges[0].hide = True
                face.edges[1].hide = True
                face.edges[2].hide = True
            case _:
                pass

    # move bmesh back to mesh to update
    bm.to_mesh(mesh)
    mesh.update()
    return mesh

def export_dat(datfile):
    dat_models = []
    
    
