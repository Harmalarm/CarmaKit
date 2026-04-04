"""
Shared import helpers.
"""

import os
from typing import Any, Dict, List, Optional

import bpy

from ..constants import BRU_SCALE_FACTOR
from ..parsers.groove_parser import normalize_actor_name, parse_groove_sections
from .types import ImportOptions


ADDON_PACKAGE = __package__.split('.')[0]


def log_debug(message: str) -> None:
    """
    Log a debug message when debug logging is enabled.

    """
    try:
        prefs = bpy.context.preferences.addons[ADDON_PACKAGE].preferences
        if prefs.debug_logging:
            print(f"[CarmaKit Import] {message}")
    except (KeyError, AttributeError):
        pass


def apply_bru_import_scale(options: ImportOptions) -> None:
    """
    Apply BRU unit conversion to the import scale when enabled.

    """
    try:
        prefs = bpy.context.preferences.addons[ADDON_PACKAGE].preferences
        if prefs.use_bru_scale:
            options.scale *= BRU_SCALE_FACTOR
            log_debug(
                "BRU conversion enabled; import scale multiplied by "
                f"{BRU_SCALE_FACTOR}"
            )
    except (KeyError, AttributeError):
        pass


def find_groove_txt_path(base_path: str, base_name: str) -> Optional[str]:
    """
    Locate a groove text file matching the base name.

    """
    for ext in [".txt", ".TXT"]:
        candidate = os.path.join(base_path, base_name + ext)
        if os.path.exists(candidate):
            return candidate

    return None


def load_groove_map(
    filepath: str,
    act_path: Optional[str],
    dat_path: Optional[str]
) -> Dict[str, List[Any]]:
    """
    Load groove definitions and map them by actor name.

    """
    reference_path = act_path or dat_path or filepath
    base_path = os.path.dirname(reference_path)
    base_name = os.path.splitext(os.path.basename(reference_path))[0]
    txt_path = find_groove_txt_path(base_path, base_name)
    if not txt_path:
        return {}

    try:
        result = parse_groove_sections(txt_path)
    except Exception as exc:
        log_debug(f"Failed to parse groove file: {exc}")
        return {}

    log_debug(f"Parsed {len(result.grooves)} grooves from {txt_path}")
    return result.by_actor_name()


def apply_grooves_to_object(
    obj: bpy.types.Object,
    groove_map: Dict[str, List[Any]]
) -> None:
    """
    Apply groove definitions to a Blender object as custom properties.

    """
    key = normalize_actor_name(obj.name)
    grooves = groove_map.get(key)
    if not grooves:
        return

    obj["carmakit_grooves"] = {
        str(groove.index): groove.to_custom_property()
        for groove in grooves
    }
    log_debug(
        f"Attached {len(grooves)} grooves to object '{obj.name}'"
    )
