"""
ACT import logic for Carmageddon formats.
"""

from typing import Any, Dict, List, Optional

import bpy
from mathutils import Euler, Matrix, Vector

from ..classes.act_classes import ActorNode
from ..classes.dat_classes import DatModel
from .common import apply_grooves_to_object, log_debug
from .dat_import import create_mesh_from_model, find_model_in_dict
from .types import ImportOptions


def create_hierarchy_from_act(
    context: bpy.types.Context,
    node: ActorNode,
    models: Dict[str, DatModel],
    materials: Dict[str, bpy.types.Material],
    options: ImportOptions,
    parent: Optional[bpy.types.Object],
    groove_map: Dict[str, List[Any]]
) -> List[bpy.types.Object]:
    """
    Create Blender objects from an ACT hierarchy.

    """
    created_objects: List[bpy.types.Object] = []
    log_debug(
        f"Processing ACT node: '{node.name}' "
        f"(model_name='{node.model_name}', children={len(node.children)})"
    )
    if node.materials:
        log_debug(f"  ACT node has materials: {node.materials}")

    if node.model_name:
        log_debug(f"  Looking for model: '{node.model_name}'")
        found_model = find_model_in_dict(node.model_name, models)

        if found_model:
            log_debug(f"  Found model '{found_model.name}', creating mesh...")
            act_materials = node.materials if node.materials else None
            obj = create_mesh_from_model(
                context,
                found_model,
                materials,
                options,
                parent,
                act_materials
            )
            if obj:
                obj.name = node.name
                log_debug(f"  Created mesh object: '{obj.name}'")
                if options.apply_transform:
                    log_debug(f"    Applying transform to '{obj.name}'")
                    apply_transform(obj, node, options.scale)
                apply_grooves_to_object(obj, groove_map)
                created_objects.append(obj)
                parent = obj
            else:
                log_debug(
                    "  WARNING: _create_mesh_from_model returned None for "
                    f"'{found_model.name}'"
                )
        else:
            log_debug(
                f"  Model '{node.model_name}' not found in loaded models, "
                f"available: {list(models.keys())}"
            )
            log_debug(
                f"  Creating empty for missing model node: '{node.name}'"
            )
            obj = create_empty(context, node.name, parent)
            if options.apply_transform:
                apply_transform(obj, node, options.scale)
            apply_grooves_to_object(obj, groove_map)
            created_objects.append(obj)
            parent = obj
    else:
        log_debug(f"  Node '{node.name}' has no model, creating empty")
        obj = create_empty(context, node.name, parent)
        if options.apply_transform:
            apply_transform(obj, node, options.scale)
        apply_grooves_to_object(obj, groove_map)
        created_objects.append(obj)
        parent = obj

    if node.children:
        log_debug(f"  Processing {len(node.children)} children of '{node.name}'")
    for child in node.children:
        child_objects = create_hierarchy_from_act(
            context, child, models, materials, options, parent, groove_map
        )
        created_objects.extend(child_objects)

    log_debug(
        f"  Finished node '{node.name}', created {len(created_objects)} objects"
    )
    return created_objects


def create_empty(
    context: bpy.types.Context,
    name: str,
    parent: Optional[bpy.types.Object]
) -> bpy.types.Object:
    """
    Create an empty object for hierarchy.

    """
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.empty_display_size = 0.1

    context.collection.objects.link(empty)

    if parent:
        empty.parent = parent

    return empty


def apply_transform(
    obj: bpy.types.Object,
    node: ActorNode,
    scale: float
) -> None:
    """
    Apply transformation from ACT node to Blender object.

    """
    m = node.transform.values

    act_matrix = Matrix((
        (m[0], m[1], m[2], m[9]),
        (m[3], m[4], m[5], m[10]),
        (m[6], m[7], m[8], m[11]),
        (0.0, 0.0, 0.0, 1.0)
    ))

    euler = act_matrix.to_euler('XYZ')
    rotation_matrix = Euler(
        (-euler.x, euler.z, -euler.y), 'YZX'
    ).to_matrix().to_4x4()

    p1 = m[9] * scale
    p2 = m[10] * scale
    p3 = m[11] * scale
    translation_matrix = Matrix.Translation(Vector((p1, -p3, p2)))

    scale_x = act_matrix.col[0].xyz.length
    scale_y = act_matrix.col[1].xyz.length
    scale_z = act_matrix.col[2].xyz.length
    scale_matrix = Matrix.Diagonal(
        Vector((scale_x, scale_z, scale_y, 1.0))
    )

    transformation_matrix = translation_matrix @ rotation_matrix @ scale_matrix

    if obj.parent is not None:
        obj.matrix_world = transformation_matrix @ obj.parent.matrix_world
    else:
        obj.matrix_world = transformation_matrix
