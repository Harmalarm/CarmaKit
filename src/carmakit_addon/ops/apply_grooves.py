"""
Groove application operator for CarmaKit.

This module provides the operator for applying GROOVE data from
car text files onto matching scene objects.
"""

from typing import Dict, List, Set

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from ..parsers.groove_parser import (
    GrooveDefinition,
    normalize_actor_name,
    parse_groove_sections,
)


def _build_groove_map(
    grooves: List[GrooveDefinition]
) -> Dict[str, List[GrooveDefinition]]:
    """
    Build a groove map keyed by normalized actor names.

    """
    result: Dict[str, List[GrooveDefinition]] = {}
    for groove in grooves:
        key = normalize_actor_name(groove.actor_name)
        result.setdefault(key, []).append(groove)
    return result


def _apply_grooves_to_object(
    obj: bpy.types.Object,
    groove_map: Dict[str, List[GrooveDefinition]]
) -> bool:
    """
    Apply groove custom properties to an object.

    """
    key = normalize_actor_name(obj.name)
    grooves = groove_map.get(key)
    if not grooves:
        return False

    obj["carmakit_grooves"] = {
        str(groove.index): groove.to_custom_property()
        for groove in grooves
    }
    return True


class CARMAKIT_OT_apply_grooves(Operator, ImportHelper):
    """
    Apply groove definitions from a car text file to scene objects.

    This operator parses the GROOVE section from a car setup file
    and attaches groove metadata to matching objects.
    """

    bl_idname = "carmakit.apply_grooves"
    bl_label = "Apply Car Grooves"
    bl_description = "Apply GROOVE settings from a car .txt file"
    bl_options = {'REGISTER', 'UNDO'}

    # File browser settings.
    filename_ext = ".txt"

    filter_glob: StringProperty(
        default="*.txt;*.TXT",
        options={'HIDDEN'},
        maxlen=255,
    )  # type: ignore

    selected_only: BoolProperty(
        name="Selected Only",
        description="Apply grooves only to selected objects",
        default=False,
    )  # type: ignore

    def execute(self, context: Context) -> Set[str]:
        """
        Execute the groove application operation.

        """
        try:
            result = parse_groove_sections(self.filepath)
        except Exception as exc:
            self.report({'ERROR'}, f"Failed to parse grooves: {exc}")
            return {'CANCELLED'}

        groove_map = _build_groove_map(result.grooves)
        if not groove_map:
            self.report({'WARNING'}, "No grooves found in file")
            return {'CANCELLED'}

        if self.selected_only:
            targets = list(context.selected_objects)
        else:
            targets = list(context.scene.objects)

        applied = 0
        for obj in targets:
            if _apply_grooves_to_object(obj, groove_map):
                applied += 1

        self.report(
            {'INFO'},
            f"Applied grooves to {applied} objects"
        )
        return {'FINISHED'}

    def draw(self, context: Context) -> None:
        """
        Draw groove application options.

        """
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(self, "selected_only")
