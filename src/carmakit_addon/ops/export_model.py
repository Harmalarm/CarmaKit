"""
Model export operator for CarmaKit.

This module keeps the Blender operator UI and delegates export logic
to the dedicated export domain package.
"""

from typing import Set

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ExportHelper

from ..export import ExportOptions, export_carmageddon_model


ADDON_PACKAGE = __package__.split('.')[0]


class CARMAKIT_OT_export_model(Operator, ExportHelper):
    """
    Export selected objects as a Carmageddon model.

    This operator provides a file browser for selecting the output
    location and exports Blender objects to Carmageddon format.
    """

    bl_idname = "carmakit.export_model"
    bl_label = "Export Carmageddon Model"
    bl_description = "Export selected objects as a Carmageddon model"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = ".act"

    filter_glob: StringProperty(
        default="*.act",
        options={'HIDDEN'},
        maxlen=255,
    )  # type: ignore

    selected_only: BoolProperty(
        name="Selected Only",
        description="Export only selected objects",
        default=False,
    )  # type: ignore

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers before exporting",
        default=True,
    )  # type: ignore

    triangulate: BoolProperty(
        name="Triangulate",
        description="Convert all faces to triangles",
        default=True,
    )  # type: ignore

    ignore_act_object_scale: BoolProperty(
        name="Ignore Object Scale",
        description=(
            "Export ACT transforms with 100% scale for regular objects; "
            "objects prefixed with $, £, !, &, or # keep their scale"
        ),
        default=True,
    )  # type: ignore

    generate_sdf: BoolProperty(
        name="Generate SDF",
        description="Create empty SDF file for Plaything compatibility",
        default=True,
    )  # type: ignore

    export_format: EnumProperty(
        name="Export Files",
        description="Which files to generate",
        items=[
            ('ALL', "All Files", "Export ACT, DAT, MAT, and SDF files"),
            ('ACT_DAT', "ACT + DAT", "Export only ACT and DAT files"),
            ('DAT_ONLY', "DAT Only", "Export only DAT mesh file"),
        ],
        default='ALL',
    )  # type: ignore

    game_version: EnumProperty(
        name="Game Version",
        description="Target Carmageddon game version for export",
        items=[
            ('C1', "Carmageddon 1", "Original Carmageddon"),
            (
                'C2',
                "Carmageddon 2",
                "Carmageddon 2: Carpocalypse Now"
            ),
        ],
        default='C2',
    )  # type: ignore

    def invoke(
        self,
        context: Context,
        event: bpy.types.Event
    ) -> Set[str]:
        """
        Initialize export options before showing the file dialog.

        """
        try:
            prefs = bpy.context.preferences.addons[ADDON_PACKAGE].preferences
            self.game_version = prefs.game_version
        except (KeyError, AttributeError):
            pass

        return super().invoke(context, event)

    def execute(self, context: Context) -> Set[str]:
        """
        Execute the export operation.

        """
        options = ExportOptions(
            filepath=self.filepath,
            scale=1.0,
            selected_only=self.selected_only,
            apply_modifiers=self.apply_modifiers,
            triangulate=self.triangulate,
            ignore_act_object_scale=self.ignore_act_object_scale,
            generate_sdf=self.generate_sdf,
            export_format=self.export_format,
            export_kind='AUTO',
            game_version=self.game_version,
        )

        try:
            result = export_carmageddon_model(context, options)
            if result.success:
                self.report(
                    {'INFO'},
                    f"Exported {result.files_written} files"
                )
                return {'FINISHED'}
            self.report({'ERROR'}, result.error_message)
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}

    def draw(self, context: Context) -> None:
        """
        Draw the export options panel.

        """
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        box = layout.box()
        box.label(text="Output", icon='FILE')
        box.prop(self, "export_format")
        box.prop(self, "generate_sdf")
        box.prop(self, "game_version")

        box = layout.box()
        box.label(text="Transform", icon='ORIENTATION_GLOBAL')
        box.prop(self, "ignore_act_object_scale")

        box = layout.box()
        box.label(text="Objects", icon='OBJECT_DATA')
        box.prop(self, "selected_only")
        box.prop(self, "apply_modifiers")
        box.prop(self, "triangulate")
