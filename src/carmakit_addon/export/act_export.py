"""
ACT export logic for Carmageddon formats.
"""

import re
from typing import Dict, List

import bpy
from mathutils import Matrix, Vector

from ..classes.act_classes import (
    ActFile,
    ActorNode,
    BoundingBox,
    TransformMatrix,
)
from ..classes.shared_classes import Vector3
from .common import log_debug, should_preserve_act_scale_for_object
from .types import ExportOptions


_ROW_COL_HELPER_NAME = re.compile(r"^\d+\s+\d+$")
_SPECIAL_NAME_PREFIXES = ('&', '%', '$', '!', '£', '#')


def _is_row_col_name(name: str) -> bool:
    """
    Return whether a node name matches the row/column pattern.

    """
    return bool(_ROW_COL_HELPER_NAME.match(name.strip()))


def _is_nameless_helper_name(name: str) -> bool:
    """
    Return whether a helper should be exported with an empty name.

    """
    lowered = name.lower()
    return lowered.startswith("no_identifier") or "node" in lowered


def _should_include_bbox_for_node(
    obj: bpy.types.Object,
    strip_legacy_helper_name: bool
) -> bool:
    """
    Return whether a node should carry a bounding box in ACT export.

    """
    if obj.name.startswith("PP01 "):
        return True
    if strip_legacy_helper_name and _is_nameless_helper_name(obj.name):
        return True
    return False


def _is_special_object_name(name: str) -> bool:
    """
    Return whether a name is a special-prefix noncar/instance object.

    """
    return name.startswith(_SPECIAL_NAME_PREFIXES)


def _find_export_parent(
    obj: bpy.types.Object,
    node_map: Dict[bpy.types.Object, ActorNode],
    is_preprocessed: bool
) -> bpy.types.Object | None:
    """
    Resolve the parent object to use for ACT hierarchy export.

    """
    parent = obj.parent
    while parent and parent not in node_map:
        parent = parent.parent

    if not is_preprocessed or not parent:
        return parent

    if parent.type != 'MESH':
        return parent

    ancestor = parent.parent
    while ancestor and ancestor not in node_map:
        ancestor = ancestor.parent

    if obj.type == 'MESH' and (
        _is_row_col_name(obj.name)
        or _is_nameless_helper_name(obj.name)
    ):
        seek = ancestor
        while seek:
            if (
                seek.type == 'EMPTY'
                and (
                    _is_nameless_helper_name(seek.name)
                    or seek.name.startswith("PP01 ")
                )
            ):
                return seek
            seek = seek.parent if seek.parent in node_map else None
        return ancestor

    if _is_special_object_name(obj.name):
        seek = ancestor
        while seek:
            if seek.type == 'EMPTY' and _is_row_col_name(seek.name):
                return seek
            seek = seek.parent if seek.parent in node_map else None
        return ancestor

    return ancestor

def create_act_file(
    objects: List[bpy.types.Object],
    base_name: str,
    options: ExportOptions,
    is_preprocessed: bool
) -> ActFile:
    """
    Create an ActFile from Blender objects.

    """
    act_file = ActFile()
    if not objects:
        return act_file

    root_objects = [obj for obj in objects if obj.parent is None]
    root_objects_count = len(root_objects)
    log_debug(f"Root objects in export set: {root_objects_count}")

    use_bounding_boxes = is_preprocessed

    # build a node map of ActorNodes from provided objects only
    node_map: Dict[bpy.types.Object, ActorNode] = {}
    for obj in objects:
        node_map[obj] = create_actor_node_from_object(
            obj,
            options,
            include_bounding_box=use_bounding_boxes,
            strip_legacy_helper_name=is_preprocessed
        )

    # build the act file hierarchy based on parent-child relationships, adding to root if required
    root_candidates: List[ActorNode] = []
    for obj, node in node_map.items():
        export_parent = _find_export_parent(obj, node_map, is_preprocessed)
        if export_parent and export_parent in node_map:
            node_map[export_parent].children.append(node)
        else:
            root_candidates.append(node)

    # Ensure we always have a valid ACT root.
    if act_file.root is None:
        if not root_candidates:
            act_file.root = ActorNode(name=base_name, attributes=0x0500)
            return act_file

        # Preprocessed tracks should prefer the PP01 root if present.
        if is_preprocessed:
            pp01_roots = [
                node for node in root_candidates
                if node.name.startswith("PP01 ")
            ]
            if pp01_roots:
                act_file.root = pp01_roots[0]
            elif len(root_candidates) == 1:
                act_file.root = root_candidates[0]
            else:
                act_file.root = ActorNode(name=base_name, attributes=0x0500)
        elif len(root_candidates) == 1:
            act_file.root = root_candidates[0]
        else:
            act_file.root = ActorNode(name=base_name, attributes=0x0104)

    # Attach all top-level candidates under the selected root.
    for candidate in root_candidates:
        if candidate is act_file.root:
            continue
        act_file.root.children.append(candidate)

    log_debug(f"Root object used: {act_file.root.name}")

    return act_file


def create_actor_node_from_object(
    obj: bpy.types.Object,
    options: ExportOptions,
    include_bounding_box: bool = False,
    strip_legacy_helper_name: bool = False
) -> ActorNode:
    """
    Create an ActorNode from a Blender object.
    """
    node = ActorNode()

    # Apply ACT attribute rules.
    if obj.type == 'MESH':
        node.name = obj.name
        node.attributes = 0x0104
        node.model_name = obj.data.name
    else:
        if strip_legacy_helper_name and _is_nameless_helper_name(obj.name):
            node.name = ""
        else:
            node.name = obj.name

        if _is_nameless_helper_name(obj.name) or obj.name.startswith("PP01 "):
            node.attributes = 0x0500
        else:
            node.attributes = 0x0004

    log_debug(
        f"  Actor node: {node.name}, type={obj.type}, "
        f"model_name={node.model_name or 'none'}"
    )

    matrix = obj.matrix_world
    preserve_scale = should_preserve_act_scale_for_object(obj)
    if options.ignore_act_object_scale and not preserve_scale:
        matrix = Matrix.Identity(4)
        log_debug(
            f"  Exporting ACT transform as identity for '{obj.name}' "
            "(Apply All Transforms behavior)"
        )
    scale = options.scale

    node.transform = TransformMatrix((
        matrix[0][0], matrix[0][2], -matrix[0][1],
        matrix[2][0], matrix[2][2], -matrix[2][1],
        -matrix[1][0], -matrix[1][2], matrix[1][1],
        matrix[0][3] * scale, matrix[2][3] * scale, -matrix[1][3] * scale,
    ))

    if include_bounding_box and _should_include_bbox_for_node(
        obj,
        strip_legacy_helper_name
    ):
        bbox = _compute_actor_bbox_from_object(obj, scale)
        if bbox is not None:
            node.bounding_box = bbox
            log_debug(
                f"  Bounding box for {node.name}: "
                f"min={node.bounding_box.min_point}, "
                f"max={node.bounding_box.max_point}"
            )

    return node


def _compute_actor_bbox_from_object(
    obj: bpy.types.Object,
    scale: float
) -> BoundingBox | None:
    """
    Compute bounding box from object content (self + descendants).

    """
    meshes: List[bpy.types.Object] = []
    if obj.type == 'MESH':
        meshes.append(obj)
    meshes.extend(child for child in obj.children_recursive if child.type == 'MESH')

    if not meshes:
        return None

    min_co = Vector((float('inf'), float('inf'), float('inf')))
    max_co = Vector((float('-inf'), float('-inf'), float('-inf')))

    for mesh_obj in meshes:
        for corner in mesh_obj.bound_box:
            world_co = mesh_obj.matrix_world @ Vector(corner)
            min_co.x = min(min_co.x, world_co.x)
            min_co.y = min(min_co.y, world_co.y)
            min_co.z = min(min_co.z, world_co.z)
            max_co.x = max(max_co.x, world_co.x)
            max_co.y = max(max_co.y, world_co.y)
            max_co.z = max(max_co.z, world_co.z)

    return BoundingBox(
        Vector3(min_co.x * scale, min_co.z * scale, -max_co.y * scale),
        Vector3(max_co.x * scale, max_co.z * scale, -min_co.y * scale)
    )
