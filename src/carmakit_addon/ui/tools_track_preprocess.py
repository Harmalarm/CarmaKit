"""
Track preprocessing tool panel for CarmaKit.
"""

import bpy
from bpy.props import IntProperty
from bpy.types import Context, Panel


class CARMAKIT_PT_tool_track_preprocess(Panel):
    """
    Tool panel for track preprocessing.
    """

    bl_idname = "CARMAKIT_PT_tool_track_preprocess"
    bl_label = "Track Preprocess"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CarmaKit"
    bl_parent_id = "CARMAKIT_PT_tools_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context) -> None:
        """
        Draw the track preprocessing UI.
        """
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        box = layout.box()
        box.label(text="Grid Settings", icon='GRID')
        box.prop(context.scene, "carmakit_pp_cols_x")
        box.prop(context.scene, "carmakit_pp_cols_y")

        box = layout.box()
        box.label(text="Action", icon='MOD_BOOLEAN')
        box.operator("carmakit.preprocess_track", icon='MOD_TRIANGULATE')


def register_properties() -> None:
    """
    Register track preprocessing properties.
    """
    bpy.types.Scene.carmakit_pp_cols_x = IntProperty(
        name="Columns X",
        description="Number of grid columns along X",
        default=4,
        min=1,
    )  # type: ignore
    bpy.types.Scene.carmakit_pp_cols_y = IntProperty(
        name="Columns Y",
        description="Number of grid columns along Y",
        default=4,
        min=1,
    )  # type: ignore


def unregister_properties() -> None:
    """
    Unregister track preprocessing properties.
    """
    if hasattr(bpy.types.Scene, "carmakit_pp_cols_x"):
        del bpy.types.Scene.carmakit_pp_cols_x
    if hasattr(bpy.types.Scene, "carmakit_pp_cols_y"):
        del bpy.types.Scene.carmakit_pp_cols_y
