"""
Shared UI helpers for CarmaKit panels.
"""

import sys
from typing import Optional

import bpy


def get_addon_version() -> tuple:
    """
    Get the addon version tuple.

    :return: Version tuple.
    :rtype: tuple
    """
    addon = sys.modules.get(__package__.split(".")[0])
    if addon and hasattr(addon, "bl_info"):
        return addon.bl_info.get("version", (0, 0, 0))
    return (0, 0, 0)


def _get_addon_key() -> str:
    """
    Get the addon key used by Blender preferences.

    :return: Addon key name.
    :rtype: str
    """
    package = __package__ or __name__
    return package.split(".")[0]


def find_addon() -> Optional[bpy.types.Addon]:
    """
    Find the addon entry in Blender preferences.

    :return: Addon entry or None when not found.
    :rtype: Optional[bpy.types.Addon]
    """
    addons = bpy.context.preferences.addons
    addon = addons.get(_get_addon_key())
    if addon:
        return addon

    for candidate in addons:
        module = getattr(candidate, "module", None)
        bl_info = getattr(module, "bl_info", {})
        if bl_info.get("name") == "CarmaKit - Carmageddon Model Tools":
            return candidate

    return None
