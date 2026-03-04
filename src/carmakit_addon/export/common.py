"""
Shared export helpers.
"""

from typing import List, Optional

import bpy

from ..constants import BRU_SCALE_FACTOR
from .types import ExportOptions


ADDON_PACKAGE = __package__.split('.')[0]
SPECIAL_SCALE_PREFIXES = ('$', '£', '!', '&', '#')


def log_debug(message: str) -> None:
    """
    Log a debug message when debug logging is enabled.

    """
    try:
        prefs = bpy.context.preferences.addons[ADDON_PACKAGE].preferences
        if prefs.debug_logging:
            print(f"[CarmaKit Export] {message}")
    except (KeyError, AttributeError):
        pass


def is_preprocessed_track(objects: List[bpy.types.Object]) -> bool:
    """
    Check if the scene uses a preprocessed track hierarchy.

    """
    for obj in objects:
        if obj.type == 'EMPTY' and obj.name.startswith("PP01 "):
            return True

    for obj in objects:
        if obj.type == 'MESH' and obj.parent:
            parent = obj.parent
            if parent.type == 'EMPTY' and parent.name.startswith("node_"):
                return True

    return False


def find_preprocessed_collection(
    scene: bpy.types.Scene
) -> Optional[bpy.types.Collection]:
    """
    Find a CarmaKit preprocess collection in the active scene.

    """
    collections = [
        col for col in bpy.data.collections
        if col.name.startswith("CarmaKit Preprocess")
    ]

    if not collections:
        return None

    scene_children = set(scene.collection.children_recursive)
    candidates = [col for col in collections if col in scene_children]
    if not candidates:
        candidates = collections

    for col in sorted(candidates, key=lambda item: item.name, reverse=True):
        if any(obj.type == 'EMPTY' and obj.name.startswith("PP01 ") for obj in col.all_objects):
            return col

    return sorted(candidates, key=lambda item: item.name, reverse=True)[0]


def apply_bru_export_scale(options: ExportOptions) -> None:
    """
    Apply BRU unit conversion to the export scale when enabled.

    """
    try:
        prefs = bpy.context.preferences.addons[ADDON_PACKAGE].preferences
        if prefs.use_bru_scale:
            options.scale /= BRU_SCALE_FACTOR
    except (KeyError, AttributeError):
        pass


def should_preserve_act_scale_for_object(obj: bpy.types.Object) -> bool:
    """
    Return whether an object should keep ACT scale in export.

    """
    return obj.name.startswith(SPECIAL_SCALE_PREFIXES)
