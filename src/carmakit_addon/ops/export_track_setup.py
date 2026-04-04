"""
Track setup export operator for CarmaKit.
"""

from typing import Set

from bpy.props import StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ExportHelper

from ..export import export_track_setup


class CARMAKIT_OT_export_track_setup(Operator, ExportHelper):
    """
    Export a dedicated track setup TXT file.
    """

    bl_idname = "carmakit.export_track_setup"
    bl_label = "Export Track Setup"
    bl_description = "Export a dedicated track setup TXT file"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = ".txt"

    filter_glob: StringProperty(
        default="*.txt",
        options={'HIDDEN'},
        maxlen=255,
    )  # type: ignore

    def execute(self, context: Context) -> Set[str]:
        """
        Execute the track setup export.

        """
        del context
        try:
            export_track_setup(self.filepath)
            self.report({'INFO'}, "Track setup exported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Track setup export failed: {str(e)}")
            return {'CANCELLED'}
