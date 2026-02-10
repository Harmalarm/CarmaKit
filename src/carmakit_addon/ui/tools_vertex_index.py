"""
Export vertex index tool panel for CarmaKit.
"""

from bpy.types import Context, Panel

from ..utils.general_utils import get_export_vertex_index


class CARMAKIT_PT_tool_vertex_index(Panel):
    """
    Tool panel for export vertex index lookup.
    """

    bl_idname = "CARMAKIT_PT_tool_vertex_index"
    bl_label = "Export Vertex Index"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CarmaKit"
    bl_parent_id = "CARMAKIT_PT_tools_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context) -> None:
        """
        Draw the export vertex index tool.

        :param context: The Blender context.
        :type context: Context
        :return: None.
        :rtype: None
        """
        layout = self.layout
        box = layout.box()
        box.label(text="Current Selection", icon='VERTEXSEL')

        result = get_export_vertex_index(context)
        if result.status == "ok":
            box.label(
                text=f"{result.message}: {result.index}",
                icon='DOT'
            )
        elif result.status == "error":
            box.label(text=result.message, icon='ERROR')
        else:
            box.label(text=result.message, icon='INFO')

        if result.modifier_warning:
            box.label(
                text="Apply Modifiers is enabled; indices may differ.",
                icon='ERROR'
            )
