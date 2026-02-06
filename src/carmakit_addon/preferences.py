"""
Addon preferences for CarmaKit.

This module defines user-configurable preferences that appear in Blender's
addon preferences panel. These settings persist across Blender sessions.

:author: CarmaKit Team
"""

from typing import Set

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import AddonPreferences


class CarmaKitPreferences(AddonPreferences):
    """
    Addon preferences for CarmaKit.

    These preferences are accessible via Edit > Preferences > Add-ons
    and control the default behavior of import/export operations.
    """

    bl_idname = __package__

    # =========================================================================
    # General Preferences
    # =========================================================================

    game_version: EnumProperty(
        name="Game Version",
        description="Target Carmageddon game version for file format",
        items=[
            ('C1', "Carmageddon 1", "Original Carmageddon"),
            ('C2', "Carmageddon 2", "Carmageddon 2: Carpocalypse Now"),
        ],
        default='C2',
    )  # type: ignore

    game_folder: StringProperty(
        name="Game Folder",
        description=(
            "Path to the Carmageddon game installation folder. "
            "Used to find missing textures in Data/Reg/PIXELMAP/tiffrgb"
        ),
        default="E:\\Games\\VanillaC2",
        subtype='DIR_PATH',
    )  # type: ignore

    # =========================================================================
    # Import Preferences
    # =========================================================================

    import_scale: FloatProperty(
        name="Import Scale",
        description="Scale factor applied when importing models",
        default=1.0,
        min=0.001,
        max=1000.0,
        soft_min=0.01,
        soft_max=100.0,
    )  # type: ignore

    import_apply_transform: BoolProperty(
        name="Apply Transform",
        description="Apply transformation matrices from ACT files on import",
        default=True,
    )  # type: ignore

    import_materials: BoolProperty(
        name="Import Materials",
        description="Import materials from MAT files",
        default=True,
    )  # type: ignore

    import_textures: BoolProperty(
        name="Import Textures",
        description="Attempt to load textures referenced by materials",
        default=True,
    )  # type: ignore

    texture_search_paths: StringProperty(
        name="Texture Search Paths",
        description=(
            "Additional paths to search for textures, separated by semicolons"
        ),
        default="",
        subtype='DIR_PATH',
    )  # type: ignore

    # =========================================================================
    # Export Preferences
    # =========================================================================

    export_scale: FloatProperty(
        name="Export Scale",
        description="Scale factor applied when exporting models",
        default=1.0,
        min=0.001,
        max=1000.0,
        soft_min=0.01,
        soft_max=100.0,
    )  # type: ignore

    export_apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers before exporting geometry",
        default=True,
    )  # type: ignore

    export_selected_only: BoolProperty(
        name="Selected Only",
        description="Export only selected objects",
        default=False,
    )  # type: ignore

    export_generate_sdf: BoolProperty(
        name="Generate SDF File",
        description=(
            "Generate an empty SDF file for Plaything compatibility"
        ),
        default=True,
    )  # type: ignore

    export_triangulate: BoolProperty(
        name="Triangulate Faces",
        description="Convert all faces to triangles before export",
        default=True,
    )  # type: ignore

    # =========================================================================
    # Advanced Preferences
    # =========================================================================

    debug_logging: BoolProperty(
        name="Debug Logging",
        description="Enable verbose debug output to console",
        default=False,
    )  # type: ignore

    verbose_import_logging: BoolProperty(
        name="Verbose Import Logging",
        description="Enable detailed step-by-step logging during import operations",
        default=False,
    )  # type: ignore

    max_vertices_per_model: IntProperty(
        name="Max Vertices Per Model",
        description=(
            "Maximum vertices per model (DAT format limit is 65536)"
        ),
        default=32768,
        min=1,
        max=65536,
    )  # type: ignore

    def draw(self, context: bpy.types.Context) -> None:
        """
        Draw the addon preferences panel.

        :param context: The Blender context.
        :type context: bpy.types.Context
        :return: None.
        :rtype: None
        """
        layout = self.layout

        # General settings.
        box = layout.box()
        box.label(text="General Settings", icon='PREFERENCES')
        box.prop(self, "game_version")
        box.prop(self, "game_folder")
        box.prop(self, "debug_logging")
        box.prop(self, "verbose_import_logging")

        # Import settings.
        box = layout.box()
        box.label(text="Import Settings", icon='IMPORT')
        row = box.row()
        row.prop(self, "import_scale")
        row.prop(self, "import_apply_transform")
        row = box.row()
        row.prop(self, "import_materials")
        row.prop(self, "import_textures")
        box.prop(self, "texture_search_paths")

        # Export settings.
        box = layout.box()
        box.label(text="Export Settings", icon='EXPORT')
        row = box.row()
        row.prop(self, "export_scale")
        row.prop(self, "export_apply_modifiers")
        row = box.row()
        row.prop(self, "export_selected_only")
        row.prop(self, "export_triangulate")
        box.prop(self, "export_generate_sdf")

        # Advanced settings.
        box = layout.box()
        box.label(text="Advanced Settings", icon='TOOL_SETTINGS')
        box.prop(self, "max_vertices_per_model")
