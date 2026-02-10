"""
CarmaKit Blender Addon - Import/Export Carmageddon model files.

This addon enables importing and exporting of Carmageddon 1/2 model files
directly in Blender, supporting DAT (mesh), ACT (actor hierarchy),
MAT (material), and related formats.


:version: 0.1.0
:blender_version: (5, 0, 0)
"""

bl_info = {
    "name": "CarmaKit - Carmageddon Model Tools",
    "author": "Harmalarm",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "location": "File > Import/Export > Carmageddon",
    "description": "Import and export Carmageddon model files (DAT, ACT, MAT)",
    "warning": "",
    "doc_url": "https://github.com/Harmalarm/CarmaKit",
    "category": "Import-Export",
}

from typing import List, Tuple, Set

import bpy

from . import operators
from . import ui
from . import preferences


# List of classes to register with Blender.
_classes: List[type] = [
    preferences.CarmaKitPreferences,
    operators.CARMAKIT_OT_import_model,
    operators.CARMAKIT_OT_apply_grooves,
    operators.CARMAKIT_OT_export_model,
    ui.GrooveItem,
    ui.CARMAKIT_UL_groove_list,
    ui.CARMAKIT_OT_add_groove_item,
    ui.CARMAKIT_OT_remove_groove_item,
    ui.CARMAKIT_OT_open_preferences,
    ui.CARMAKIT_PT_main_panel,
    ui.CARMAKIT_PT_tools_panel,
    ui.CARMAKIT_PT_tool_vertex_index,
    ui.CARMAKIT_PT_tool_groove_setup,
]


def menu_func_import(self, context: bpy.types.Context) -> None:
    """
    Add import option to File > Import menu.

    :param self: The menu instance.
    :param context: The Blender context.
    :return: None.
    :rtype: None
    """
    self.layout.operator(
        operators.CARMAKIT_OT_import_model.bl_idname,
        text="Carmageddon Model (.act/.dat)"
    )


def menu_func_export(self, context: bpy.types.Context) -> None:
    """
    Add export option to File > Export menu.

    :param self: The menu instance.
    :param context: The Blender context.
    :return: None.
    :rtype: None
    """
    self.layout.operator(
        operators.CARMAKIT_OT_export_model.bl_idname,
        text="Carmageddon Model (.act/.dat)"
    )


def register() -> None:
    """
    Register all addon classes and menu entries with Blender.

    This function is called by Blender when enabling the addon.

    :return: None.
    :rtype: None
    """
    for cls in _classes:
        bpy.utils.register_class(cls)

    ui.register_properties()
    ui.register_handlers()

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister() -> None:
    """
    Unregister all addon classes and menu entries from Blender.

    This function is called by Blender when disabling the addon.

    :return: None.
    :rtype: None
    """
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    ui.unregister_handlers()
    ui.unregister_properties()

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
