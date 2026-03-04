"""
DAT import logic for Carmageddon formats.
"""

from typing import Dict, List, Optional

import bmesh
import bpy

from ..classes.dat_classes import DatModel
from .common import log_debug
from .types import ImportOptions


def find_model_in_dict(
    model_name: str,
    models: Dict[str, DatModel]
) -> Optional[DatModel]:
    """
    Find a model in the models dictionary.

    """
    if not model_name:
        return None

    key = model_name.upper()
    if not key.endswith('.DAT'):
        key = key + '.DAT'

    if key in models:
        log_debug(f"    Found model with key '{key}'")
        return models[key]

    log_debug(f"    Model key '{key}' not found")
    return None


def create_mesh_from_model(
    context: bpy.types.Context,
    model: DatModel,
    materials: Dict[str, bpy.types.Material],
    options: ImportOptions,
    parent: Optional[bpy.types.Object],
    act_materials: Optional[List[str]] = None
) -> Optional[bpy.types.Object]:
    """
    Create a Blender mesh object from a DAT model.

    """
    log_debug(
        f"  _create_mesh_from_model: '{model.name}' - "
        f"{len(model.vertices)} verts, {len(model.faces)} faces"
    )
    if not model.vertices or not model.faces:
        log_debug(
            f"    WARNING: Model '{model.name}' has no vertices or faces, "
            "skipping"
        )
        return None

    mesh = bpy.data.meshes.new(name=model.name)
    obj = bpy.data.objects.new(model.name, mesh)

    context.collection.objects.link(obj)

    if parent:
        obj.parent = parent

    log_debug("    Creating bmesh and adding vertices...")
    bm = bmesh.new()

    scale = options.scale
    for v in model.vertices:
        bm.verts.new((v.x * scale, -v.z * scale, v.y * scale))

    bm.verts.ensure_lookup_table()
    log_debug(
        f"    Added {len(bm.verts)} vertices to bmesh "
        "(with Y-up to Z-up conversion)"
    )

    material_names = act_materials if act_materials else model.materials
    if act_materials:
        log_debug(f"    Using ACT materials: {act_materials}")
    else:
        log_debug(f"    Using DAT materials: {model.materials}")

    mat_name_to_index: Dict[str, int] = {}
    for mat_name in material_names:
        mat_key = mat_name.lower()
        if mat_key in materials:
            blender_mat = materials[mat_key]
        else:
            existing_mat = None
            for existing in bpy.data.materials:
                if existing.name.lower() == mat_key:
                    existing_mat = existing
                    break

            if existing_mat:
                blender_mat = existing_mat
                log_debug(f"    Reusing existing material: '{existing_mat.name}'")
            else:
                blender_mat = bpy.data.materials.new(name=mat_name)
                blender_mat.use_nodes = True
                log_debug(f"    Created placeholder material: '{mat_name}'")

        mesh.materials.append(blender_mat)
        mat_name_to_index[mat_key] = len(mesh.materials) - 1

    log_debug(f"    Adding {len(model.faces)} faces...")
    uv_layer = bm.loops.layers.uv.new("UVMap")
    faces_created = 0
    faces_failed = 0
    face_smoothing_groups: Dict[int, int] = {}

    for face in model.faces:
        try:
            verts = [
                bm.verts[face.v1],
                bm.verts[face.v2],
                bm.verts[face.v3]
            ]
            bm_face = bm.faces.new(verts)

            face_smoothing_groups[bm_face.index] = face.smoothing_group

            if face.material_index > 0 and face.material_index <= len(
                material_names
            ):
                mat_name = material_names[face.material_index - 1].lower()
                if mat_name in mat_name_to_index:
                    bm_face.material_index = mat_name_to_index[mat_name]

            if model.tex_coords:
                for i, loop in enumerate(bm_face.loops):
                    vert_index = [face.v1, face.v2, face.v3][i]
                    if vert_index < len(model.tex_coords):
                        tc = model.tex_coords[vert_index]
                        loop[uv_layer].uv = (tc.u, 1.0 - tc.v)
            faces_created += 1

        except ValueError:
            faces_failed += 1
            continue

    log_debug(f"    Faces created: {faces_created}, failed: {faces_failed}")

    log_debug("    Processing smoothing groups...")
    bm.edges.ensure_lookup_table()
    sharp_edges = 0
    smooth_edges = 0

    for edge in bm.edges:
        linked_faces = edge.link_faces
        if len(linked_faces) == 2:
            sg1 = face_smoothing_groups.get(linked_faces[0].index, 0)
            sg2 = face_smoothing_groups.get(linked_faces[1].index, 0)

            if sg1 != sg2:
                edge.smooth = False
                sharp_edges += 1
            else:
                edge.smooth = True
                smooth_edges += 1
        elif len(linked_faces) == 1:
            edge.smooth = False
            sharp_edges += 1
        else:
            edge.smooth = True
            smooth_edges += 1

    log_debug(
        f"    Smoothing: {sharp_edges} sharp edges, {smooth_edges} smooth edges"
    )

    log_debug("    Converting bmesh to mesh...")
    bm.to_mesh(mesh)
    bm.free()

    log_debug("    Processing edge visibility...")
    hidden_edges = 0
    for face_idx, face in enumerate(model.faces):
        if face_idx >= len(mesh.polygons):
            break

        edgevis = face.edge_visibility
        if edgevis == 0:
            continue

        poly = mesh.polygons[face_idx]
        loop_start = poly.loop_start

        for i in range(3):
            edge_hidden = False
            if i == 0 and (edgevis & 1):
                edge_hidden = True
            elif i == 1 and (edgevis & 2):
                edge_hidden = True
            elif i == 2 and (edgevis & 4):
                edge_hidden = True

            if edge_hidden:
                loop_idx = loop_start + i
                if loop_idx < len(mesh.loops):
                    edge_idx = mesh.loops[loop_idx].edge_index
                    mesh.edges[edge_idx].hide = True
                    hidden_edges += 1

    log_debug(f"    Hidden edges: {hidden_edges}")

    try:
        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = 3.14159
    except AttributeError:
        pass

    for poly in mesh.polygons:
        poly.use_smooth = True
    log_debug(f"    Enabled smooth shading on {len(mesh.polygons)} polygons")

    mesh.update()
    log_debug(f"    Mesh '{model.name}' created successfully")

    return obj
