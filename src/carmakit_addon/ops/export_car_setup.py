"""
Car setup export operator for CarmaKit.
"""

from typing import Set

from bpy.props import BoolProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ExportHelper

from ..export import export_car_setup


class CARMAKIT_OT_export_car_setup(Operator, ExportHelper):
    """
    Export a dedicated car setup TXT file.
    """

    bl_idname = "carmakit.export_car_setup"
    bl_label = "Export Car Setup"
    bl_description = "Export a dedicated car setup TXT file"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = ".txt"

    filter_glob: StringProperty(
        default="*.txt",
        options={'HIDDEN'},
        maxlen=255,
    )  # type: ignore

    selected_only: BoolProperty(
        name="Selected Only",
        description="Export setup from selected objects only",
        default=False,
    )  # type: ignore

    def execute(self, context: Context) -> Set[str]:
        """
        Execute the car setup export.

        """
        objects = (
            list(context.selected_objects)
            if self.selected_only
            else list(context.scene.objects)
        )

        try:
            export_car_setup(self.filepath, objects)
            self.report({'INFO'}, "Car setup exported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Car setup export failed: {str(e)}")
            return {'CANCELLED'}

    def draw(self, context: Context) -> None:
        """
        Draw operator options.

        """
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(self, "selected_only")
