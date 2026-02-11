"""
Main UI panel for CarmaKit.
"""

import bpy
from bpy.types import Context, Panel

from .utils import get_addon_version


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

        """
        layout = self.layout

        header = layout.box()
        row = header.row(align=True)
        row.label(text=f"Version {get_addon_version()}", icon='INFO')
        sub = row.row(align=True)
        sub.scale_x = 1.0
        sub.operator(
            "carmakit.open_preferences",
            text="",
            icon='PREFERENCES'
        )

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
