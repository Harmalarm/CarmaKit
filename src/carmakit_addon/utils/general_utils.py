"""
General utility helpers for CarmaKit.

This module contains utility functions that do not belong to a specific
import/export format, such as scene cleanup.

:author: CarmaKit Team
"""

from typing import Iterable

import bpy


def cleanup_scene(
    context: bpy.types.Context,
    remove_objects: bool = True,
    purge_data: bool = True
) -> None:
    """
    Clean up the current scene and orphaned data blocks.

    :param context: The Blender context.
    :type context: bpy.types.Context
    :param remove_objects: Whether to remove all scene objects.
    :type remove_objects: bool
    :param purge_data: Whether to purge unused data blocks.
    :type purge_data: bool
    :return: None.
    :rtype: None
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

    :param data_blocks: Iterable of data block collections.
    :type data_blocks: Iterable[bpy.types.ID]
    :return: None.
    :rtype: None
    """
    for collection in data_blocks:
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)