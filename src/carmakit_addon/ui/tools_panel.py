"""
Tools panel container for CarmaKit.
"""

from bpy.types import Context, Panel


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
        layout.label(text="Expand a tool below.")
