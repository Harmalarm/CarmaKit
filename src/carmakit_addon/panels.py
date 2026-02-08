"""
UI Panels for CarmaKit.

This module contains the Blender UI panels that provide
the main interface for the CarmaKit addon.


"""
import sys
from typing import Optional, Set
import bpy
from bpy.types import Context, Panel

from .utils.general_utils import get_export_vertex_index


def _get_addon_key() -> str:
    """
    Get the addon key used by Blender preferences.

    :return: Addon key name.
    :rtype: str
    """
    # Use the last package segment for src-layout compatibility.
    package = __package__ or __name__
    return package.split(".")[-1]


def _find_addon() -> Optional[bpy.types.Addon]:
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

def get_addon_version():
    addon = sys.modules.get(__package__)
    if addon and hasattr(addon, "bl_info"):
        return addon.bl_info.get("version", (0, 0, 0))
    return (0, 0, 0)

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


class CARMAKIT_PT_tools_panel(Panel):
    """
    Tools panel for quick CarmaKit utilities.
    """

    bl_idname = "CARMAKIT_PT_tools_panel"
    bl_label = "Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CarmaKit"
    bl_parent_id = "CARMAKIT_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context) -> None:
        """
        Draw the tools panel contents.

        :param context: The Blender context.
        :type context: Context
        :return: None.
        :rtype: None
        """
        layout = self.layout
        box = layout.box()
        box.label(text="Export Vertex Index", icon='VERTEXSEL')

        result = get_export_vertex_index(context)
        if result.status == "ok":
            box.label(
                text=f"{result.message}: {result.index}",
                icon='DOT'
            )
        elif result.status == "error":
            box.label(text=result.message, icon='ERROR')
        else:
            box.label(text=result.message, icon='INFO')

        if result.modifier_warning:
            box.label(
                text="Apply Modifiers is enabled; indices may differ.",
                icon='ERROR'
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
