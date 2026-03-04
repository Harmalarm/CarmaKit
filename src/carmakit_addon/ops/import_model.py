"""
Model import operator for CarmaKit.

This module keeps the Blender operator UI and delegates import logic
to the dedicated import domain package.
"""

from typing import Set

from bpy.props import BoolProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from ..importing import ImportOptions, import_carmageddon_model


class CARMAKIT_OT_import_model(Operator, ImportHelper):
    """
    Import a Carmageddon model from ACT/DAT files.

    This operator provides a file browser for selecting Carmageddon
    model files and imports them into the current Blender scene.
    """

    bl_idname = "carmakit.import_model"
    bl_label = "Import Carmageddon Model"
    bl_description = "Import a Carmageddon model (ACT/DAT format)"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = ".act"

    filter_glob: StringProperty(
        default="*.act;*.dat",
        options={'HIDDEN'},
        maxlen=255,
    )  # type: ignore

    apply_transform: BoolProperty(
        name="Apply Transform",
        description="Apply transformation matrices from ACT file",
        default=True,
    )  # type: ignore

    import_materials: BoolProperty(
        name="Import Materials",
        description="Import materials from MAT file",
        default=True,
    )  # type: ignore

    import_textures: BoolProperty(
        name="Import Textures",
        description="Attempt to load referenced textures",
        default=True,
    )  # type: ignore

    cleanup_scene: BoolProperty(
        name="Cleanup Scene",
        description="Remove existing objects and unused data before import",
        default=False,
    )  # type: ignore

    def execute(self, context: Context) -> Set[str]:
        """
        Execute the import operation.

        """
        options = ImportOptions(
            filepath=self.filepath,
            scale=1.0,
            apply_transform=self.apply_transform,
            import_materials=self.import_materials,
            import_textures=self.import_textures,
            cleanup_scene=self.cleanup_scene,
        )

        try:
            result = import_carmageddon_model(context, options)
            if result.success:
                self.report(
                    {'INFO'},
                    f"Imported {result.objects_created} objects"
                )
                return {'FINISHED'}
            self.report({'ERROR'}, result.error_message)
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            return {'CANCELLED'}

    def draw(self, context: Context) -> None:
        """
        Draw the import options panel.

        """
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        box = layout.box()
        box.label(text="Transform", icon='ORIENTATION_GLOBAL')
        box.prop(self, "apply_transform")

        box = layout.box()
        box.label(text="Materials", icon='MATERIAL')
        box.prop(self, "import_materials")
        sub = box.row()
        sub.enabled = self.import_materials
        sub.prop(self, "import_textures")

        box = layout.box()
        box.label(text="Cleanup", icon='TRASH')
        box.prop(self, "cleanup_scene")
