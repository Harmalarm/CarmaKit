"""
General utility helpers for CarmaKit.

This module contains utility functions that do not belong to a specific
import/export format, such as scene cleanup.

"""

from dataclasses import dataclass
from typing import Iterable, Optional

import bmesh
import bpy


@dataclass
class ExportVertexIndexResult:
    """
    Result for exporting a single vertex index lookup.

    """

    status: str
    message: str
    index: Optional[int] = None
    modifier_warning: bool = False


def get_export_vertex_index(
    context: bpy.types.Context
) -> ExportVertexIndexResult:
    """
    Get the Carmageddon export vertex index for a single selection.

    """
    obj = context.active_object
    if not obj or obj.type != 'MESH':
        return ExportVertexIndexResult(
            status="info",
            message="Select a mesh object."
        )

    if context.mode != 'EDIT_MESH':
        return ExportVertexIndexResult(
            status="info",
            message="Enter Edit Mode and select one vertex."
        )

    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    selected_verts = [vert for vert in bm.verts if vert.select]

    if not selected_verts:
        return ExportVertexIndexResult(
            status="info",
            message="No vertex selected."
        )

    if len(selected_verts) > 1:
        return ExportVertexIndexResult(
            status="error",
            message=(
                f"Multiple vertices selected ({len(selected_verts)})."
            )
        )

    modifier_warning = False
    try:
        addon_key = (__package__ or "").split(".")[0]
        prefs = bpy.context.preferences.addons[addon_key].preferences
        modifier_warning = bool(
            prefs.export_apply_modifiers and obj.modifiers
        )
    except (KeyError, AttributeError, IndexError):
        pass

    return ExportVertexIndexResult(
        status="ok",
        message="Carmageddon index",
        index=selected_verts[0].index,
        modifier_warning=modifier_warning
    )


def cleanup_scene(
    context: bpy.types.Context,
    remove_objects: bool = True,
    purge_data: bool = True
) -> None:
    """
    Clean up the current scene and orphaned data blocks.

    """
    if remove_objects:
        # Remove all objects in the current scene.
        for obj in list(context.scene.objects):
            bpy.data.objects.remove(obj, do_unlink=True)

    if purge_data:
        _purge_orphaned_data_blocks(
            (
                bpy.data.meshes,
                bpy.data.materials,
                bpy.data.images,
            )
        )


def _purge_orphaned_data_blocks(
    data_blocks: Iterable[bpy.types.ID]
) -> None:
    """
    Remove any data blocks with zero users.

    """
    for collection in data_blocks:
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)