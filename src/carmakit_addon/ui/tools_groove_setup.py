"""
Groove setup tool panel for CarmaKit.
"""

import bpy
from bpy.props import (
    CollectionProperty,
    IntProperty,
)
from typing import Tuple

from bpy.types import Context, Operator, Panel, UIList

from ..props.groove_props import GrooveItem, GrooveProps

def _parse_point3(value: object) -> Tuple[float, float, float]:
    """
    Parse a stored point3 into a float tuple.

    :param value: Stored point3 value.
    :type value: object
    :return: Parsed point3 tuple.
    :rtype: Tuple[float, float, float]
    """
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return (
                float(value[0]),
                float(value[1]),
                float(value[2]),
            )
        except (TypeError, ValueError):
            return (0.0, 0.0, 0.0)

    if isinstance(value, str):
        cleaned = value.replace("(", "").replace(")", "")
        parts = [part for part in cleaned.replace(",", " ").split() if part]
        if len(parts) >= 3:
            try:
                return (
                    float(parts[0]),
                    float(parts[1]),
                    float(parts[2]),
                )
            except ValueError:
                return (0.0, 0.0, 0.0)

    return (0.0, 0.0, 0.0)


def _draw_vector_row(
    layout: bpy.types.UILayout,
    label: str,
    item: GrooveItem,
    prop_name: str
) -> None:
    """
    Draw a point3 as horizontal X/Y/Z fields.

    :param layout: UI layout.
    :type layout: bpy.types.UILayout
    :param label: Field label.
    :type label: str
    :param item: Groove item instance.
    :type item: GrooveItem
    :param prop_name: Property name on the item.
    :type prop_name: str
    :return: None.
    :rtype: None
    """
    row = layout.row(align=True)
    row.label(text=label)
    row.prop(item, prop_name, index=0, text="X")
    row.prop(item, prop_name, index=1, text="Y")
    row.prop(item, prop_name, index=2, text="Z")


def _enum_label(value: str, items: list[tuple[str, str, str]]) -> str:
    """
    Resolve an enum identifier to its display label.

    :param value: Enum identifier.
    :type value: str
    :param items: Enum items list.
    :type items: list[tuple[str, str, str]]
    :return: Display label.
    :rtype: str
    """
    for item_id, item_label, _ in items:
        if item_id == value:
            return item_label
    return value



class CARMAKIT_UL_groove_list(UIList):
    """
    UI list for groove items.
    """

    def draw_item(
        self,
        context: Context,
        layout: bpy.types.UILayout,
        data: bpy.types.ID,
        item: GrooveItem,
        icon: int,
        active_data: bpy.types.ID,
        active_propname: str,
        index: int = 0,
        flt_flag: int = 0
    ) -> None:
        """
        Draw a groove list row.

        :param context: Blender context.
        :type context: Context
        :param layout: UI layout.
        :type layout: bpy.types.UILayout
        :param data: Data source.
        :type data: bpy.types.ID
        :param item: Groove item.
        :type item: GrooveItem
        :param icon: Icon identifier.
        :type icon: int
        :param active_data: Active data block.
        :type active_data: bpy.types.ID
        :param active_propname: Active property name.
        :type active_propname: str
        :param index: Item index.
        :type index: int
        :param flt_flag: Filter flag.
        :type flt_flag: int
        :return: None.
        :rtype: None
        """
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text=str(item.index))
            #row.label(text=_enum_label(item.lollipop, GrooveProps.LOLLIPOP_ITEMS))
            #row.label(text=_enum_label(item.trigger, GrooveProps.TRIGGER_ITEMS))
            #row.label(text=_enum_label(item.path_type, GrooveProps.PATH_TYPE_ITEMS))
            #row.label(text=_enum_label(item.animation_type, GrooveProps.ANIMATION_TYPE_ITEMS))
        else:
            layout.label(text=str(item.index))


class CARMAKIT_OT_add_groove_item(Operator):
    """
    Add a new groove item to the active object.
    """

    bl_idname = "carmakit.add_groove_item"
    bl_label = "Add Groove"
    bl_description = "Add a new groove entry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: Context) -> set:
        """
        Execute the add operation.

        :param context: Blender context.
        :type context: Context
        :return: Operator result.
        :rtype: set
        """
        obj = context.object
        if not obj:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        wm = context.window_manager
        wm["carmakit_syncing_grooves"] = True
        try:
            grooves = GrooveProps.ensure_groove_dict(obj)
            existing = [int(k) for k in grooves.keys() if str(k).isdigit()]
            next_index = max(existing, default=-1) + 1
            key = str(next_index)
            grooves[key] = {
                "index": next_index,
                "lollipop": "",
                "trigger": "",
                "path": {},
                "animation": {},
            }
            if isinstance(grooves, dict):
                obj["carmakit_grooves"] = grooves

            item = obj.carmakit_groove_items.add()
            item.groove_key = key
            item.index = next_index
            obj.carmakit_groove_index = len(obj.carmakit_groove_items) - 1
        finally:
            wm["carmakit_syncing_grooves"] = False
        return {'FINISHED'}


class CARMAKIT_OT_remove_groove_item(Operator):
    """
    Remove the selected groove item from the active object.
    """

    bl_idname = "carmakit.remove_groove_item"
    bl_label = "Remove Groove"
    bl_description = "Remove the selected groove entry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: Context) -> set:
        """
        Execute the remove operation.

        :param context: Blender context.
        :type context: Context
        :return: Operator result.
        :rtype: set
        """
        obj = context.object
        if not obj:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        index = obj.carmakit_groove_index
        if index < 0 or index >= len(obj.carmakit_groove_items):
            self.report({'ERROR'}, "No groove selected")
            return {'CANCELLED'}

        item = obj.carmakit_groove_items[index]
        grooves = GrooveProps.ensure_groove_dict(obj)
        if item.groove_key in grooves:
            grooves.pop(item.groove_key, None)
            if isinstance(grooves, dict):
                obj["carmakit_grooves"] = grooves

        obj.carmakit_groove_items.remove(index)
        obj.carmakit_groove_index = max(0, index - 1)
        return {'FINISHED'}


def _sync_items_from_props(obj: bpy.types.Object) -> None:
    """
    Sync groove items collection from custom properties.

    :param obj: Blender object.
    :type obj: bpy.types.Object
    :return: None.
    :rtype: None
    """
    grooves = obj.get("carmakit_grooves")
    if not grooves or not hasattr(grooves, "keys"):
        obj.carmakit_groove_items.clear()
        obj.carmakit_groove_index = 0
        return

    keys = [str(key) for key in grooves.keys()]
    existing_keys = [item.groove_key for item in obj.carmakit_groove_items]
    if set(keys) == set(existing_keys):
        return

    wm = bpy.context.window_manager
    wm["carmakit_syncing_grooves"] = True
    try:
        obj.carmakit_groove_items.clear()

        def _sort_key(value):
            try:
                return (0, int(value))
            except (TypeError, ValueError):
                return (1, str(value))

        for key in sorted(keys, key=_sort_key):
            groove = grooves.get(key, {})
            item = obj.carmakit_groove_items.add()
            item.groove_key = key
            item.index = groove.get("index", 0)
            item.lollipop = GrooveProps.normalize_enum(
                groove.get("lollipop"),
                GrooveProps.LOLLIPOP_ITEMS
            )
            item.trigger = GrooveProps.normalize_enum(
                groove.get("trigger"),
                GrooveProps.TRIGGER_ITEMS
            )
            path = groove.get("path", {})
            item.path_type = GrooveProps.normalize_enum(
                path.get("type"),
                GrooveProps.PATH_TYPE_ITEMS
            )
            movement = path.get("movement", "")
            item.path_movement_straight = GrooveProps.normalize_enum(
                movement,
                GrooveProps.PATH_STRAIGHT_MOVEMENT_ITEMS
            )
            item.path_movement_circular = GrooveProps.normalize_enum(
                movement,
                GrooveProps.PATH_CIRCULAR_MOVEMENT_ITEMS
            )
            item.path_centre = _parse_point3(path.get("centre"))
            item.path_groovy_ref = str(path.get("groovy_funk_ref", ""))
            item.path_distance = _parse_point3(path.get("distance"))
            item.path_cycles = str(path.get("cycles_per_second", ""))
            item.path_speed = str(path.get("speed", ""))
            item.path_radius = str(path.get("radius", ""))
            item.path_axis = GrooveProps.normalize_enum(
                path.get("axis"),
                GrooveProps.AXIS_ITEMS
            )

            anim = groove.get("animation", {})
            item.animation_type = GrooveProps.normalize_enum(
                anim.get("type"),
                GrooveProps.ANIMATION_TYPE_ITEMS
            )
            item.spin_type = GrooveProps.normalize_enum(
                anim.get("spin_type"),
                GrooveProps.SPIN_TYPE_ITEMS
            )
            item.rock_type = GrooveProps.normalize_enum(
                anim.get("rock_type"),
                GrooveProps.ROCK_TYPE_ITEMS
            )
            item.shear_type = GrooveProps.normalize_enum(
                anim.get("shear_type"),
                GrooveProps.SHEAR_TYPE_ITEMS
            )
            item.anim_groovy_ref = str(anim.get("groovy_funk_ref", ""))
            item.anim_cycles = str(anim.get("cycles_per_second", ""))
            item.anim_centre = _parse_point3(anim.get("centre"))
            item.anim_axis = GrooveProps.normalize_enum(
                anim.get("axis"),
                GrooveProps.AXIS_ITEMS
            )
            item.anim_degrees = str(anim.get("degrees", ""))
            item.anim_extents = _parse_point3(anim.get("extents"))
    finally:
        wm["carmakit_syncing_grooves"] = False

def _handle_active_object_change() -> None:
    """
    Refresh the groove list when the active object changes.

    :return: None.
    :rtype: None
    """
    wm = bpy.context.window_manager
    if wm.get("carmakit_syncing_grooves"):
        return
    active = bpy.context.view_layer.objects.active
    if not bpy.context.selected_objects:
        wm["carmakit_last_groove_obj"] = ""
        if active:
            active.carmakit_groove_items.clear()
            active.carmakit_groove_index = 0
        return
    active_name = active.name if active else ""
    last_name = wm.get("carmakit_last_groove_obj", "")
    if active_name == last_name:
        return

    wm["carmakit_last_groove_obj"] = active_name
    if not active:
        return

    _sync_items_from_props(active)


def _depsgraph_update_handler(_scene: bpy.types.Scene, _depsgraph) -> None:
    """
    Blender depsgraph update handler.

    :param _scene: Current scene.
    :type _scene: bpy.types.Scene
    :param _depsgraph: Depsgraph instance.
    :type _depsgraph: bpy.types.Depsgraph
    :return: None.
    :rtype: None
    """
    _handle_active_object_change()


def register_handlers() -> None:
    """
    Register handlers for groove UI updates.

    :return: None.
    :rtype: None
    """
    handler = _depsgraph_update_handler
    if handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(handler)


def unregister_handlers() -> None:
    """
    Unregister handlers for groove UI updates.

    :return: None.
    :rtype: None
    """
    handler = _depsgraph_update_handler
    if handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(handler)


class CARMAKIT_PT_tool_groove_setup(Panel):
    """
    Tool panel for applying and reviewing groove settings.
    """

    bl_idname = "CARMAKIT_PT_tool_groove_setup"
    bl_label = "Groove Setup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CarmaKit"
    bl_parent_id = "CARMAKIT_PT_tools_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context) -> None:
        """
        Draw the groove setup tool.

        :param context: The Blender context.
        :type context: Context
        :return: None.
        :rtype: None
        """
        layout = self.layout
        box = layout.box()
        box.label(text="Apply Grooves", icon='FILE_FOLDER')
        box.operator(
            "carmakit.apply_grooves",
            text="Apply From .txt",
            icon='IMPORT'
        )

        obj = context.active_object
        if not obj:
            layout.label(text="No active object.", icon='INFO')
            return

        row = layout.row()
        row.template_list(
            "CARMAKIT_UL_groove_list",
            "",
            obj,
            "carmakit_groove_items",
            obj,
            "carmakit_groove_index",
            rows=4
        )

        col = row.column(align=True)
        col.operator("carmakit.add_groove_item", icon='ADD', text="")
        col.operator("carmakit.remove_groove_item", icon='REMOVE', text="")

        if not obj.carmakit_groove_items:
            layout.label(
                text="No grooves assigned. Use Refresh to load.",
                icon='INFO'
            )
            return

        if obj.carmakit_groove_index < 0:
            return

        item = obj.carmakit_groove_items[obj.carmakit_groove_index]
        box = layout.box()
        box.label(text="Groove Properties", icon='SETTINGS')
        box.prop(item, "lollipop")
        box.prop(item, "trigger")
        box.prop(item, "path_type")

        if item.path_type != "NONE" and item.path_type != "NO_PATH":
            path_box = box.box()
            path_box.label(text="Path Details")
            if item.path_type == "STRAIGHT":
                path_box.prop(item, "path_movement_straight")
                if item.path_movement_straight == "ABSOLUTE":
                    _draw_vector_row(path_box, "Centre", item, "path_centre")
                    path_box.prop(item, "path_groovy_ref")
                    _draw_vector_row(
                        path_box,
                        "Distance",
                        item,
                        "path_distance"
                    )
                elif item.path_movement_straight != "NONE":
                    path_box.prop(item, "path_cycles")
                    _draw_vector_row(
                        path_box,
                        "Distance",
                        item,
                        "path_distance"
                    )
            elif item.path_type == "CIRCULAR":
                path_box.prop(item, "path_movement_circular")
                if item.path_movement_circular == "ABSOLUTE":
                    _draw_vector_row(path_box, "Centre", item, "path_centre")
                    path_box.prop(item, "path_groovy_ref")
                elif item.path_movement_circular != "NONE":
                    path_box.prop(item, "path_speed")
                    path_box.prop(item, "path_radius")
                path_box.prop(item, "path_axis")

        box.prop(item, "animation_type")

        if item.animation_type != "NONE" and item.animation_type != "NO_ANIMATION":
            anim_box = box.box()
            anim_box.label(text="Animation Details")
            if item.animation_type == "SPIN":
                anim_box.prop(item, "spin_type")
                if item.spin_type == "CONTROLLED":
                    anim_box.prop(item, "anim_groovy_ref")
                elif item.spin_type != "NONE":
                    anim_box.prop(item, "anim_cycles")
                _draw_vector_row(anim_box, "Centre", item, "anim_centre")
                anim_box.prop(item, "anim_axis")
            elif item.animation_type == "ROCK":
                anim_box.prop(item, "rock_type")
                if item.rock_type == "ABSOLUTE":
                    anim_box.prop(item, "anim_groovy_ref")
                elif item.rock_type != "NONE":
                    anim_box.prop(item, "anim_cycles")
                _draw_vector_row(anim_box, "Centre", item, "anim_centre")
                anim_box.prop(item, "anim_axis")
                anim_box.prop(item, "anim_degrees")
            elif item.animation_type == "SHEAR":
                anim_box.prop(item, "shear_type")
                if item.shear_type != "NONE":
                    anim_box.prop(item, "anim_groovy_ref")
                _draw_vector_row(anim_box, "Centre", item, "anim_centre")
                _draw_vector_row(anim_box, "Extents", item, "anim_extents")


def register_properties() -> None:
    """
    Register groove UI properties on Blender objects.

    :return: None.
    :rtype: None
    """
    bpy.types.Object.carmakit_groove_items = CollectionProperty(
        type=GrooveItem,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Object.carmakit_groove_index = IntProperty(
        default=0,
        options={'HIDDEN', 'SKIP_SAVE'},
    )


def unregister_properties() -> None:
    """
    Unregister groove UI properties from Blender objects.

    :return: None.
    :rtype: None
    """
    if hasattr(bpy.types.Object, "carmakit_groove_items"):
        del bpy.types.Object.carmakit_groove_items
    if hasattr(bpy.types.Object, "carmakit_groove_index"):
        del bpy.types.Object.carmakit_groove_index
