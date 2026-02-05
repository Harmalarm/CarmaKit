"""
UI Panels for CarmaKit.

This module contains the Blender UI panels that provide
the main interface for the CarmaKit addon.

:author: CarmaKit Team
"""

from typing import Set

import bpy
from bpy.types import Context, Panel


class CARMAKIT_PT_main_panel(Panel):
    """
    Main CarmaKit panel in the 3D View sidebar.

    Provides quick access to import/export operations
    without navigating through File menus.
    """

    bl_idname = "CARMAKIT_PT_main_panel"
    bl_label = "CarmaKit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CarmaKit"

    def draw(self, context: Context) -> None:
        """
        Draw the main panel contents.

        :param context: The Blender context.
        :type context: Context
        :return: None.
        :rtype: None
        """
        layout = self.layout

        # Import/Export section.
        box = layout.box()
        box.label(text="Import / Export", icon='FILE_3D')

        row = box.row(align=True)
        row.scale_y = 1.5
        row.operator(
            "carmakit.import_model",
            text="Import",
            icon='IMPORT'
        )
        row.operator(
            "carmakit.export_model",
            text="Export",
            icon='EXPORT'
        )

        # Info section.
        box = layout.box()
        box.label(text="Scene Info", icon='INFO')

        # Count mesh objects in scene.
        mesh_count = sum(
            1 for obj in context.scene.objects if obj.type == 'MESH'
        )
        selected_count = sum(
            1 for obj in context.selected_objects if obj.type == 'MESH'
        )

        col = box.column(align=True)
        col.label(text=f"Mesh Objects: {mesh_count}")
        col.label(text=f"Selected Meshes: {selected_count}")

        # Quick settings section.
        box = layout.box()
        box.label(text="Quick Settings", icon='PREFERENCES')

        # Get addon preferences.
        prefs = context.preferences.addons.get(__package__)
        if prefs:
            box.prop(prefs.preferences, "game_version")
            box.prop(prefs.preferences, "debug_logging")

        # Button to open addon preferences.
        row = box.row()
        row.operator(
            "carmakit.open_preferences",
            text="Open Addon Settings",
            icon='SETTINGS'
        )


class CARMAKIT_OT_open_preferences(bpy.types.Operator):
    """
    Operator to open the CarmaKit addon preferences.
    """

    bl_idname = "carmakit.open_preferences"
    bl_label = "Open CarmaKit Preferences"
    bl_description = "Open the CarmaKit addon preferences panel"

    def execute(self, context: Context) -> Set[str]:
        """
        Execute the operator to open preferences.

        :param context: The Blender context.
        :type context: Context
        :return: Operator result.
        :rtype: Set[str]
        """
        # Open preferences window.
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')

        # Switch to Add-ons section and search for CarmaKit.
        context.preferences.active_section = 'ADDONS'

        # Set the search filter to find our addon.
        bpy.context.window_manager.addon_search = "CarmaKit"

        return {'FINISHED'}
