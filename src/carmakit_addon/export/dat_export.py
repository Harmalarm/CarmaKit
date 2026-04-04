"""
DAT export logic for Carmageddon formats.
"""

from typing import Dict, List, Optional, Tuple

import bmesh
import bpy
from mathutils import Matrix

from ..classes.dat_classes import DatFile, DatModel, Face
from ..classes.shared_classes import Vector2, Vector3
from ..constants import DEFAULT_FACE_FLAGS
from .common import log_debug, should_preserve_act_scale_for_object
from .types import ExportOptions


def create_dat_file(
    context: bpy.types.Context,
    objects: List[bpy.types.Object],
    options: ExportOptions
) -> DatFile:
    """
    Create a DatFile from Blender objects.

    """
    dat_file = DatFile()

    log_debug(f"Creating DAT from {len(objects)} objects")

    for obj in objects:
        log_debug(f"  Converting object: {obj.name} ({obj.type})")
        model = create_model_from_object(context, obj, options)
        if model:
            dat_file.models.append(model)

    log_debug(f"DAT models created: {len(dat_file.models)}")

    return dat_file


def create_model_from_object(
    context: bpy.types.Context,
    obj: bpy.types.Object,
    options: ExportOptions
) -> Optional[DatModel]:
    """
    Create a DatModel from a Blender object.

    """
    if options.apply_modifiers:
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        mesh = obj_eval.to_mesh()
    else:
        obj_eval = None
        mesh = obj.data

    if not mesh:
        log_debug(f"  Skipping object with no mesh: {obj.name}")
        return None

    model = DatModel()
    model.name = obj.data.name
    model.attributes = 277

    log_debug(
        f"  Building DAT model '{model.name}', apply_modifiers="
        f"{options.apply_modifiers}, triangulate={options.triangulate}"
    )

    bm = bmesh.new()
    bm.from_mesh(mesh)

    if options.triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces[:])

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    log_debug(
        f"  Mesh stats: verts={len(bm.verts)}, faces={len(bm.faces)}"
    )

    smoothing_groups = compute_smoothing_groups(bm)

    preserve_act_scale = should_preserve_act_scale_for_object(obj)
    vertex_matrix = obj.matrix_world
    bake_static_transform = (
        options.ignore_act_object_scale
        and not preserve_act_scale
    )
    if bake_static_transform:
        vertex_matrix = obj.matrix_local
        log_debug(
            f"  Baking local transform into DAT vertices for '{obj.name}' "
            "(Apply All Transforms behavior)"
        )
    elif preserve_act_scale:
        vertex_matrix = Matrix.Identity(4)
        log_debug(
            f"  Exporting DAT vertices in local space for preserved-scale "
            f"object '{obj.name}'"
        )

    mat_name_to_index: Dict[str, int] = {}
    for slot in obj.material_slots:
        if slot.material:
            mat_name = slot.material.name
            if mat_name not in mat_name_to_index:
                model.materials.append(mat_name)
                mat_name_to_index[mat_name] = len(model.materials)

    if not model.materials:
        model.materials.append("default")
        mat_name_to_index["default"] = 1

    scale = options.scale
    uv_layer = bm.loops.layers.uv.active

    if uv_layer:
        vert_uv_map: Dict[Tuple[int, float, float], int] = {}

        for face in bm.faces:
            if len(face.loops) != 3:
                continue

            face_verts: List[int] = []
            for loop in face.loops:
                uv = loop[uv_layer].uv
                key = (loop.vert.index, uv.x, uv.y)
                if key not in vert_uv_map:
                    co = vertex_matrix @ loop.vert.co
                    model.vertices.append(Vector3(
                        co.x * scale,
                        co.z * scale,
                        -co.y * scale
                    ))
                    model.tex_coords.append(Vector2(
                        uv.x,
                        1.0 - uv.y
                    ))
                    vert_uv_map[key] = len(model.vertices) - 1
                face_verts.append(vert_uv_map[key])

            mat_index = 1
            if face.material_index < len(obj.material_slots):
                slot = obj.material_slots[face.material_index]
                if slot.material and slot.material.name in mat_name_to_index:
                    mat_index = mat_name_to_index[slot.material.name]

            smoothing_group = smoothing_groups.get(face.index, 0)
            flags = bytes([
                (smoothing_group >> 8) & 0xFF,
                smoothing_group & 0xFF,
                DEFAULT_FACE_FLAGS[2],
            ])

            model.faces.append(Face(
                v1=face_verts[0],
                v2=face_verts[1],
                v3=face_verts[2],
                flags=flags,
                material_index=mat_index
            ))
    else:
        for vert in bm.verts:
            co = vertex_matrix @ vert.co
            model.vertices.append(Vector3(
                co.x * scale,
                co.z * scale,
                -co.y * scale
            ))
            model.tex_coords.append(Vector2(0.0, 0.0))

        for face in bm.faces:
            if len(face.loops) != 3:
                continue

            v1 = face.loops[0].vert.index
            v2 = face.loops[1].vert.index
            v3 = face.loops[2].vert.index

            mat_index = 1
            if face.material_index < len(obj.material_slots):
                slot = obj.material_slots[face.material_index]
                if slot.material and slot.material.name in mat_name_to_index:
                    mat_index = mat_name_to_index[slot.material.name]

            smoothing_group = smoothing_groups.get(face.index, 0)
            flags = bytes([
                (smoothing_group >> 8) & 0xFF,
                smoothing_group & 0xFF,
                DEFAULT_FACE_FLAGS[2],
            ])

            model.faces.append(Face(
                v1=v1,
                v2=v2,
                v3=v3,
                flags=flags,
                material_index=mat_index
            ))

    log_debug(
        f"  Exported faces: {len(model.faces)}, materials: "
        f"{len(model.materials)}"
    )

    bm.free()

    if options.apply_modifiers and obj_eval is not None:
        obj_eval.to_mesh_clear()

    return model


def compute_smoothing_groups(bm: bmesh.types.BMesh) -> Dict[int, int]:
    """
    Compute smoothing group bitmasks from smooth edges.

    """
    face_masks: Dict[int, int] = {face.index: 0 for face in bm.faces}
    next_bit = 0

    def allocate_bit() -> int:
        nonlocal next_bit
        if next_bit < 16:
            bit = 1 << next_bit
            next_bit += 1
            return bit
        return 1

    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            continue
        face_a, face_b = edge.link_faces
        if not edge.smooth or not face_a.smooth or not face_b.smooth:
            continue

        mask_a = face_masks[face_a.index]
        mask_b = face_masks[face_b.index]

        if mask_a & mask_b:
            continue

        new_bit = allocate_bit()
        face_masks[face_a.index] = mask_a | new_bit
        face_masks[face_b.index] = mask_b | new_bit

    return face_masks
