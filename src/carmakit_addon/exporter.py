"""
Carmageddon model exporter for Blender.

This module handles exporting Blender meshes to Carmageddon
DAT, ACT, and MAT file formats.


"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import bpy
import bmesh
from mathutils import Matrix, Vector

from .classes.act_classes import (
    ActFile,
    ActorNode,
    BoundingBox,
    TransformMatrix,
)
from .classes.dat_classes import (
    DatFile,
    DatModel,
    Face, 
)
from .classes.mat_classes import (
    Material as CarMaterial,
    MatFile,
)
from .classes.shared_classes import (
    Vector2,
    Vector3,
)

from .writers.act_writer import write_act_file
from .writers.dat_writer import write_dat_file
from .writers.mat_writer import write_mat_file
from .writers.sdf_writer import write_sdf_file
from .constants import DEFAULT_FACE_FLAGS, MAT_FLAG_DEFAULT


@dataclass
class ExportOptions:
    """
    Options for the export operation.

    :param filepath: Path to the output file.
    :type filepath: str
    :param scale: Scale factor to apply to geometry.
    :type scale: float
    :param selected_only: Export only selected objects.
    :type selected_only: bool
    :param apply_modifiers: Apply modifiers before export.
    :type apply_modifiers: bool
    :param triangulate: Triangulate faces before export.
    :type triangulate: bool
    :param generate_sdf: Generate SDF file for Plaything.
    :type generate_sdf: bool
    :param export_format: Which files to export.
    :type export_format: str
    """

    filepath: str
    scale: float = 1.0
    selected_only: bool = False
    apply_modifiers: bool = True
    triangulate: bool = True
    generate_sdf: bool = True
    export_format: str = 'ALL'
    export_kind: str = 'CAR'


@dataclass
class ExportResult:
    """
    Result of an export operation.

    :param success: Whether the export was successful.
    :type success: bool
    :param files_written: Number of files written.
    :type files_written: int
    :param error_message: Error message if export failed.
    :type error_message: str
    """

    success: bool = True
    files_written: int = 0
    error_message: str = ""


def export_carmageddon_model(
    context: bpy.types.Context,
    options: ExportOptions
) -> ExportResult:
    """
    Export Blender objects to Carmageddon format.

    :param context: The Blender context.
    :type context: bpy.types.Context
    :param options: Export options.
    :type options: ExportOptions
    :return: Result of the export operation.
    :rtype: ExportResult
    """
    result = ExportResult()

    try:
        # Get base path and name.
        base_path = os.path.dirname(options.filepath)
        base_name = os.path.splitext(os.path.basename(options.filepath))[0]

        # Collect objects to export.
        if options.selected_only:
            scene_objects = list(context.selected_objects)
        else:
            scene_objects = list(context.scene.objects)

        act_objects = [
            obj for obj in scene_objects
            if obj.type in {'MESH', 'EMPTY'}
        ]
        mesh_objects = [obj for obj in act_objects if obj.type == 'MESH']

        if not mesh_objects:
            result.error_message = "No mesh objects to export"
            result.success = False
            return result

        # Collect all materials.
        all_materials: Dict[str, bpy.types.Material] = {}
        for obj in mesh_objects:
            for slot in obj.material_slots:
                if slot.material:
                    all_materials[slot.material.name] = slot.material

        # Create DAT file.
        dat_file = _create_dat_file(context, mesh_objects, options)

        # Create MAT file.
        mat_file = _create_mat_file(all_materials, base_path)

        # Create ACT file.
        act_file = _create_act_file(act_objects, base_name, options)

        # Write files based on export format.
        if options.export_format in ['ALL', 'ACT_DAT']:
            # Write ACT file.
            act_path = os.path.join(base_path, base_name + '.act')
            write_act_file(
                act_path,
                act_file,
                legacy_hierarchy=(options.export_kind == 'CAR')
            )
            result.files_written += 1

        if options.export_format in ['ALL', 'ACT_DAT', 'DAT_ONLY']:
            # Write DAT file.
            dat_path = os.path.join(base_path, base_name + '.dat')
            write_dat_file(dat_path, dat_file)
            result.files_written += 1

        if options.export_format == 'ALL':
            # Write MAT file.
            mat_path = os.path.join(base_path, base_name + '.mat')
            write_mat_file(mat_path, mat_file)
            result.files_written += 1

        # Write SDF file if requested.
        if options.generate_sdf:
            sdf_path = os.path.join(base_path, base_name + '.sdf')
            write_sdf_file(sdf_path)
            result.files_written += 1

    except Exception as e:
        result.error_message = str(e)
        result.success = False

    return result


def _create_dat_file(
    context: bpy.types.Context,
    objects: List[bpy.types.Object],
    options: ExportOptions
) -> DatFile:
    """
    Create a DatFile from Blender objects.

    :param context: The Blender context.
    :type context: bpy.types.Context
    :param objects: List of objects to export.
    :type objects: List[bpy.types.Object]
    :param options: Export options.
    :type options: ExportOptions
    :return: The created DatFile.
    :rtype: DatFile
    """
    dat_file = DatFile()

    for obj in objects:
        model = _create_model_from_object(context, obj, options)
        if model:
            dat_file.models.append(model)

    return dat_file


def _create_model_from_object(
    context: bpy.types.Context,
    obj: bpy.types.Object,
    options: ExportOptions
) -> Optional[DatModel]:
    """
    Create a DatModel from a Blender object.

    :param context: The Blender context.
    :type context: bpy.types.Context
    :param obj: The Blender object to convert.
    :type obj: bpy.types.Object
    :param options: Export options.
    :type options: ExportOptions
    :return: The created model or None if conversion failed.
    :rtype: Optional[DatModel]
    """
    # Get evaluated mesh (with modifiers applied if requested).
    if options.apply_modifiers:
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        mesh = obj_eval.to_mesh()
    else:
        mesh = obj.data

    if not mesh:
        return None

    model = DatModel()
    # Use mesh data name for DAT model name to match Blender mesh naming.
    model.name = obj.data.name

    # Create bmesh for processing.
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Triangulate if requested.
    if options.triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces[:])

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    smoothing_groups = _compute_smoothing_groups(bm)

    # Export vertices with axis conversion.
    # Blender uses Z-up, Carmageddon uses Y-up.
    # Convert: X stays, Y becomes -Z, Z becomes Y.
    scale = options.scale
    for vert in bm.verts:
        co = obj.matrix_world @ vert.co
        model.vertices.append(Vector3(
            co.x * scale,
            co.z * scale,
            -co.y * scale
        ))

    # Build material list.
    mat_name_to_index: Dict[str, int] = {}
    for i, slot in enumerate(obj.material_slots):
        if slot.material:
            mat_name = slot.material.name
            if mat_name not in mat_name_to_index:
                model.materials.append(mat_name)
                mat_name_to_index[mat_name] = len(model.materials)

    # If no materials, add a default one.
    if not model.materials:
        model.materials.append("default")
        mat_name_to_index["default"] = 1

    # Get UV layer.
    uv_layer = bm.loops.layers.uv.active

    # Export texture coordinates (per vertex).
    # Carmageddon uses per-vertex UVs, not per-loop.
    vert_uvs: Dict[int, Tuple[float, float]] = {}

    for face in bm.faces:
        for loop in face.loops:
            vert_idx = loop.vert.index
            if vert_idx not in vert_uvs and uv_layer:
                uv = loop[uv_layer].uv
                vert_uvs[vert_idx] = (uv.x, 1.0 - uv.y)

    # Fill in UVs for all vertices.
    for i in range(len(bm.verts)):
        if i in vert_uvs:
            u, v = vert_uvs[i]
            model.tex_coords.append(Vector2(u, v))
        else:
            model.tex_coords.append(Vector2(0.0, 0.0))

    # Export faces.
    for face in bm.faces:
        if len(face.loops) != 3:
            continue  # Skip non-triangles.

        v1 = face.loops[0].vert.index
        v2 = face.loops[1].vert.index
        v3 = face.loops[2].vert.index

        # Get material index.
        mat_index = 1  # Default.
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

    bm.free()

    # Clean up evaluated mesh.
    if options.apply_modifiers:
        obj_eval.to_mesh_clear()

    return model


def _compute_smoothing_groups(bm: bmesh.types.BMesh) -> Dict[int, int]:
    """
    Compute smoothing group bitmasks from smooth edges.

    Faces connected by a soft edge will share at least one smoothing
    group bit. Faces can accumulate multiple bits if they share soft
    edges with different neighboring groups.

    :param bm: The bmesh to analyze.
    :type bm: bmesh.types.BMesh
    :return: Mapping of face index to smoothing group bitmask.
    :rtype: Dict[int, int]
    """
    face_masks: Dict[int, int] = {face.index: 0 for face in bm.faces}
    next_bit = 0

    def _allocate_bit() -> int:
        nonlocal next_bit
        if next_bit < 16:
            bit = 1 << next_bit
            next_bit += 1
            return bit
        # Fall back to bit 0 when exceeding 16 groups.
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

        new_bit = _allocate_bit()
        face_masks[face_a.index] = mask_a | new_bit
        face_masks[face_b.index] = mask_b | new_bit

    return face_masks


def _create_mat_file(
    materials: Dict[str, bpy.types.Material],
    base_path: str
) -> MatFile:
    """
    Create a MatFile from Blender materials.

    :param materials: Dictionary of materials to export.
    :type materials: Dict[str, bpy.types.Material]
    :param base_path: Base path for texture references.
    :type base_path: str
    :return: The created MatFile.
    :rtype: MatFile
    """
    mat_file = MatFile()

    for name, blender_mat in materials.items():
        car_mat = CarMaterial()
        car_mat.name = name

        # Get color from principled BSDF if available.
        if blender_mat.use_nodes:
            for node in blender_mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    color = node.inputs['Base Color'].default_value
                    car_mat.color = (
                        int(color[0] * 255),
                        int(color[1] * 255),
                        int(color[2] * 255),
                        255
                    )
                    # Get roughness and convert to specular.
                    roughness = node.inputs['Roughness'].default_value
                    car_mat.specular = 1.0 - roughness
                    break

        # Check for backface culling setting.
        if not blender_mat.use_backface_culling:
            car_mat.flags |= 0x00001000  # Two-sided flag.

        # Try to find linked texture.
        if blender_mat.use_nodes:
            for node in blender_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    # Use image name as texture reference.
                    tex_name = os.path.splitext(node.image.name)[0]
                    car_mat.texture_name = tex_name
                    break

        mat_file.materials.append(car_mat)

    return mat_file


def _create_act_file(
    objects: List[bpy.types.Object],
    base_name: str,
    options: ExportOptions
) -> ActFile:
    """
    Create an ActFile from Blender objects.

    :param objects: List of objects to export.
    :type objects: List[bpy.types.Object]
    :param base_name: Base name for the model.
    :type base_name: str
    :param options: Export options.
    :type options: ExportOptions
    :return: The created ActFile.
    :rtype: ActFile
    """
    act_file = ActFile()

    include_bounding_boxes = options.export_kind == 'TRACK'

    # Build actor nodes and preserve Blender parenting where possible.
    node_map: Dict[bpy.types.Object, ActorNode] = {}
    for obj in objects:
        node_map[obj] = _create_actor_node_from_object(
            obj,
            options,
            include_bounding_box=include_bounding_boxes
        )

    root_candidates: List[ActorNode] = []
    for obj, node in node_map.items():
        if obj.parent and obj.parent in node_map:
            node_map[obj.parent].children.append(node)
        else:
            root_candidates.append(node)

    if not root_candidates:
        return act_file

    if options.export_kind == 'TRACK':
        # Track exports use a synthetic root container.
        root = ActorNode()
        root.name = base_name
        root.attributes = 0x0104

        if include_bounding_boxes:
            min_co = Vector((float('inf'), float('inf'), float('inf')))
            max_co = Vector((float('-inf'), float('-inf'), float('-inf')))

            for obj in objects:
                for corner in obj.bound_box:
                    world_co = obj.matrix_world @ Vector(corner)
                    min_co.x = min(min_co.x, world_co.x)
                    min_co.y = min(min_co.y, world_co.y)
                    min_co.z = min(min_co.z, world_co.z)
                    max_co.x = max(max_co.x, world_co.x)
                    max_co.y = max(max_co.y, world_co.y)
                    max_co.z = max(max_co.z, world_co.z)

            scale = options.scale
            # Convert bounding box from Blender Z-up to Carmageddon Y-up.
            root.bounding_box = BoundingBox(
                Vector3(min_co.x * scale, min_co.z * scale, -max_co.y * scale),
                Vector3(max_co.x * scale, max_co.z * scale, -min_co.y * scale)
            )

        root.children.extend(sorted(root_candidates, key=lambda n: n.name))
        act_file.root = root
    else:
        # Car exports use a real actor as root.
        root_candidates = sorted(root_candidates, key=lambda n: n.name)
        root = root_candidates[0]
        for extra in root_candidates[1:]:
            root.children.append(extra)
        act_file.root = root

    return act_file


def _create_actor_node_from_object(
    obj: bpy.types.Object,
    options: ExportOptions,
    include_bounding_box: bool = False
) -> ActorNode:
    """
    Create an ActorNode from a Blender object.

    :param obj: The Blender object.
    :type obj: bpy.types.Object
    :param options: Export options.
    :type options: ExportOptions
    :param include_bounding_box: Whether to include bounding box data.
    :type include_bounding_box: bool
    :return: The created ActorNode.
    :rtype: ActorNode
    """
    node = ActorNode()
    node.name = obj.name
    node.attributes = 0x0104
    if obj.type == 'MESH' and obj.data:
        node.model_name = _format_model_name(obj.data.name)

    # Extract transform.
    matrix = obj.matrix_world
    scale = options.scale

    # Convert Blender 4x4 matrix to Carmageddon 3x4 format.
    # Convert from Blender Z-up to Carmageddon Y-up.
    # Swap Y and Z axes in rotation and position.
    node.transform = TransformMatrix((
        matrix[0][0], matrix[0][2], -matrix[0][1],
        matrix[2][0], matrix[2][2], -matrix[2][1],
        -matrix[1][0], -matrix[1][2], matrix[1][1],
        matrix[0][3] * scale, matrix[2][3] * scale, -matrix[1][3] * scale,
    ))

    if include_bounding_box and obj.type == 'MESH':
        # Calculate bounding box.
        min_co = Vector((float('inf'), float('inf'), float('inf')))
        max_co = Vector((float('-inf'), float('-inf'), float('-inf')))

        for corner in obj.bound_box:
            world_co = obj.matrix_world @ Vector(corner)
            min_co.x = min(min_co.x, world_co.x)
            min_co.y = min(min_co.y, world_co.y)
            min_co.z = min(min_co.z, world_co.z)
            max_co.x = max(max_co.x, world_co.x)
            max_co.y = max(max_co.y, world_co.y)
            max_co.z = max(max_co.z, world_co.z)

        # Convert bounding box from Blender Z-up to Carmageddon Y-up.
        node.bounding_box = BoundingBox(
            Vector3(min_co.x * scale, min_co.z * scale, -max_co.y * scale),
            Vector3(max_co.x * scale, max_co.z * scale, -min_co.y * scale)
        )

    return node


def _format_model_name(object_name: str) -> str:
    """
    Format a model name for ACT references.

    :param object_name: The Blender object name.
    :type object_name: str
    :return: Model name as-is (verbatim object name).
    :rtype: str
    """
    return object_name
