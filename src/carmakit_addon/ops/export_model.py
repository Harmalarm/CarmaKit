"""
Model export operator for CarmaKit.

This module provides the operator that exports Blender objects
into Carmageddon ACT/DAT/MAT formats.
"""

from typing import Set

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ExportHelper

from .. import exporter


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

    # File browser settings.
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

    export_kind: EnumProperty(
        name="Export Type",
        description="Choose whether to export a car or a track",
        items=[
            ('CAR', "Car", "Export using car-style ACT layout"),
            ('TRACK', "Track", "Export using track-style ACT layout"),
        ],
        default='CAR',
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

        :param context: The Blender context.
        :type context: Context
        :param event: The Blender event.
        :type event: bpy.types.Event
        :return: Operator result.
        :rtype: Set[str]
        """
        try:
            prefs = bpy.context.preferences.addons[__package__].preferences
            self.game_version = prefs.game_version
        except (KeyError, AttributeError):
            pass

        return super().invoke(context, event)

    def execute(self, context: Context) -> Set[str]:
        """
        Execute the export operation.

        :param context: The Blender context.
        :type context: Context
        :return: Status set indicating success or failure.
        :rtype: Set[str]
        """
        # Build export options from operator properties.
        options = exporter.ExportOptions(
            filepath=self.filepath,
            scale=1.0,
            selected_only=self.selected_only,
            apply_modifiers=self.apply_modifiers,
            triangulate=self.triangulate,
            generate_sdf=self.generate_sdf,
            export_format=self.export_format,
            export_kind=self.export_kind,
            game_version=self.game_version,
        )

        try:
            result = exporter.export_carmageddon_model(context, options)
            if result.success:
                self.report(
                    {'INFO'},
                    f"Exported {result.files_written} files"
                )
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, result.error_message)
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}

    def draw(self, context: Context) -> None:
        """
        Draw the export options panel.

        :param context: The Blender context.
        :type context: Context
        :return: None.
        :rtype: None
        """
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        box = layout.box()
        box.label(text="Output", icon='FILE')
        box.prop(self, "export_format")
        box.prop(self, "generate_sdf")
        box.prop(self, "export_kind")
        box.prop(self, "game_version")

        box = layout.box()
        box.label(text="Transform", icon='ORIENTATION_GLOBAL')

        box = layout.box()
        box.label(text="Objects", icon='OBJECT_DATA')
        box.prop(self, "selected_only")
        box.prop(self, "apply_modifiers")
        box.prop(self, "triangulate")
