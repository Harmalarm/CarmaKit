# Blender addon stubs for type checking.
# This file helps IDEs understand Blender types when running outside Blender.
# It is not used at runtime.

"""
Stub file for Blender API type hints.

This module provides empty type stubs that allow the addon code to be
analyzed by type checkers and linters without requiring Blender.
"""

from typing import Any, Dict, List, Optional, Tuple


class Context:
    """Stub for bpy.types.Context."""

    scene: Any
    collection: Any
    selected_objects: List[Any]
    preferences: Any
    evaluated_depsgraph_get: Any


class Operator:
    """Stub for bpy.types.Operator."""

    bl_idname: str
    bl_label: str
    bl_description: str
    bl_options: set

    def report(self, type: set, message: str) -> None:
        """Report a message to the user."""
        pass

    def execute(self, context: Context) -> set:
        """Execute the operator."""
        return {'FINISHED'}


class Panel:
    """Stub for bpy.types.Panel."""

    bl_idname: str
    bl_label: str
    bl_space_type: str
    bl_region_type: str
    bl_category: str

    layout: Any

    def draw(self, context: Context) -> None:
        """Draw the panel."""
        pass


class AddonPreferences:
    """Stub for bpy.types.AddonPreferences."""

    bl_idname: str

    def draw(self, context: Context) -> None:
        """Draw the preferences panel."""
        pass
