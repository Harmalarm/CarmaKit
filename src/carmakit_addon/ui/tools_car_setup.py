"""
Car setup tool panel for CarmaKit.
"""

from bpy.types import Context, Panel


class CARMAKIT_PT_tool_car_setup(Panel):
    """
    Tool panel for car setup export.
    """

    bl_idname = "CARMAKIT_PT_tool_car_setup"
    bl_label = "Car setup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CarmaKit"
    bl_parent_id = "CARMAKIT_PT_tools_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context) -> None:
        """
        Draw the car setup tool UI.

        """
        del context
        layout = self.layout
        box = layout.box()
        box.operator("carmakit.export_car_setup", icon='EXPORT')
