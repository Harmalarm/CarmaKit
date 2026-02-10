"""
Groove property group for CarmaKit.
"""

from typing import Dict, List, Optional, Tuple

import bpy  # Blender API for custom properties and UI definitions.
from bpy.props import (
    EnumProperty,
    FloatVectorProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import Context, PropertyGroup

class GrooveProps:
    """
    Container for groove constants and helper functions.
    """

    LOLLIPOP_ITEMS = [
        ("NOT_A_LOLLIPOP", "not a lollipop", ""),
        ("X_LOLLIPOP", "xLollipop", ""),
        ("Y_LOLLIPOP", "yLollipop", ""),
        ("Z_LOLLIPOP", "zLollipop", ""),
    ]
    TRIGGER_ITEMS = [
        ("CONSTANT", "constant", ""),
        ("DISTANCE", "distance", ""),
    ]
    PATH_TYPE_ITEMS = [
        ("NO_PATH", "no path", ""),
        ("STRAIGHT", "straight", ""),
        ("CIRCULAR", "circular", ""),
    ]
    PATH_STRAIGHT_MOVEMENT_ITEMS = [
        ("ABSOLUTE", "absolute", ""),
        ("HARMONIC", "harmonic", ""),
        ("LINEAR", "linear", ""),
        ("FLASH", "flash", ""),
    ]
    PATH_CIRCULAR_MOVEMENT_ITEMS = [
        ("ABSOLUTE", "absolute", ""),
        ("LINEAR", "linear", ""),
    ]
    AXIS_ITEMS = [
        ("X", "x", ""),
        ("Y", "y", ""),
        ("Z", "z", ""),
    ]
    ANIMATION_TYPE_ITEMS = [
        ("NO_ANIMATION", "no animation", ""),
        ("ROCK", "rock", ""),
        ("SHEAR", "shear", ""),
        ("SPIN", "spin", ""),
        ("THROB", "throb", ""),
    ]
    SPIN_TYPE_ITEMS = [
        ("CONTROLLED", "controlled", ""),
        ("CONTINUOUS", "continuous", ""),
    ]
    ROCK_TYPE_ITEMS = [
        ("ABSOLUTE", "absolute", ""),
        ("HARMONIC", "harmonic", ""),
        ("LINEAR", "linear", ""),
    ]
    SHEAR_TYPE_ITEMS = [
        ("ABSOLUTE", "absolute", ""),
        ("CONTROLLED", "controlled", ""),
    ]

    LOLLIPOP_MAP = {
        item[0]: item[1]
        for item in LOLLIPOP_ITEMS
        if item[0] != "NONE"
    }
    TRIGGER_MAP = {
        item[0]: item[1]
        for item in TRIGGER_ITEMS
        if item[0] != "NONE"
    }
    PATH_TYPE_MAP = {
        item[0]: item[1]
        for item in PATH_TYPE_ITEMS
        if item[0] != "NONE"
    }
    PATH_STRAIGHT_MOVEMENT_MAP = {
        item[0]: item[1]
        for item in PATH_STRAIGHT_MOVEMENT_ITEMS
        if item[0] != "NONE"
    }
    PATH_CIRCULAR_MOVEMENT_MAP = {
        item[0]: item[1]
        for item in PATH_CIRCULAR_MOVEMENT_ITEMS
        if item[0] != "NONE"
    }
    AXIS_MAP = {
        item[0]: item[1]
        for item in AXIS_ITEMS
        if item[0] != "NONE"
    }
    ANIMATION_TYPE_MAP = {
        item[0]: item[1]
        for item in ANIMATION_TYPE_ITEMS
        if item[0] != "NONE"
    }
    SPIN_TYPE_MAP = {
        item[0]: item[1]
        for item in SPIN_TYPE_ITEMS
        if item[0] != "NONE"
    }
    ROCK_TYPE_MAP = {
        item[0]: item[1]
        for item in ROCK_TYPE_ITEMS
        if item[0] != "NONE"
    }
    SHEAR_TYPE_MAP = {
        item[0]: item[1]
        for item in SHEAR_TYPE_ITEMS
        if item[0] != "NONE"
    }

    @staticmethod
    def first_enum_item(items: List[Tuple[str, str, str]]) -> str:
        """
        Get the first enum identifier.

        :param items: Enum items list.
        :type items: List[Tuple[str, str, str]]
        :return: First enum identifier.
        :rtype: str
        """
        return items[0][0]

    @staticmethod
    def enum_value(value: str, mapping: Dict[str, str]) -> str:
        """
        Convert an enum identifier into its text value.

        :param value: Enum identifier.
        :type value: str
        :param mapping: Mapping of enum identifiers to text values.
        :type mapping: Dict[str, str]
        :return: Mapped string or empty string.
        :rtype: str
        """
        return mapping.get(value, "")

    @staticmethod
    def normalize_enum(
        value: Optional[str],
        items: List[Tuple[str, str, str]]
    ) -> str:
        """
        Normalize a stored value to an enum identifier.

        :param value: Stored value.
        :type value: Optional[str]
        :param items: Enum items list.
        :type items: List[Tuple[str, str, str]]
        :return: Enum identifier.
        :rtype: str
        """
        if not value:
            return GrooveProps.first_enum_item(items)
        for item_id, item_value, _ in items:
            if item_id == value or item_value == value:
                return item_id
        return GrooveProps.first_enum_item(items)

    @staticmethod
    def ensure_groove_dict(obj: bpy.types.Object) -> Dict[str, object]:
        """
        Ensure the groove dictionary is present on the object.

        :param obj: Blender object.
        :type obj: bpy.types.Object
        :return: Groove dictionary.
        :rtype: Dict[str, object]
        """
        grooves = obj.get("carmakit_grooves")
        if isinstance(grooves, dict):
            return grooves
        if grooves is None:
            obj["carmakit_grooves"] = {}
            return obj["carmakit_grooves"]
        if hasattr(grooves, "keys"):
            return grooves
        obj["carmakit_grooves"] = dict(grooves)
        return obj["carmakit_grooves"]


def _item_to_dict(item: "GrooveItem") -> Dict[str, object]:
    """
    Convert a groove item to a custom property dictionary.

    :param item: Groove item.
    :type item: GrooveItem
    :return: Groove dictionary.
    :rtype: Dict[str, object]
    """
    lollipop = GrooveProps.enum_value(
        item.lollipop,
        GrooveProps.LOLLIPOP_MAP
    )
    trigger = GrooveProps.enum_value(
        item.trigger,
        GrooveProps.TRIGGER_MAP
    )
    path_type = GrooveProps.enum_value(
        item.path_type,
        GrooveProps.PATH_TYPE_MAP
    )
    anim_type = GrooveProps.enum_value(
        item.animation_type,
        GrooveProps.ANIMATION_TYPE_MAP
    )

    path_data: Dict[str, object] = {}
    if path_type:
        path_data["type"] = path_type
        if path_type == "straight":
            movement = GrooveProps.enum_value(
                item.path_movement_straight,
                GrooveProps.PATH_STRAIGHT_MOVEMENT_MAP
            )
            if movement:
                path_data["movement"] = movement
                if movement == "absolute":
                    path_data["centre"] = list(item.path_centre)
                    path_data["groovy_funk_ref"] = item.path_groovy_ref
                    path_data["distance"] = list(item.path_distance)
                else:
                    path_data["cycles_per_second"] = item.path_cycles
                    path_data["distance"] = list(item.path_distance)
        elif path_type == "circular":
            movement = GrooveProps.enum_value(
                item.path_movement_circular,
                GrooveProps.PATH_CIRCULAR_MOVEMENT_MAP
            )
            if movement:
                path_data["movement"] = movement
                if movement == "absolute":
                    path_data["centre"] = list(item.path_centre)
                    path_data["groovy_funk_ref"] = item.path_groovy_ref
                else:
                    path_data["speed"] = item.path_speed
                    path_data["radius"] = item.path_radius
            axis = GrooveProps.enum_value(
                item.path_axis,
                GrooveProps.AXIS_MAP
            )
            if axis:
                path_data["axis"] = axis

    anim_data: Dict[str, object] = {}
    if anim_type:
        anim_data["type"] = anim_type
        if anim_type == "spin":
            spin_type = GrooveProps.enum_value(
                item.spin_type,
                GrooveProps.SPIN_TYPE_MAP
            )
            if spin_type:
                anim_data["spin_type"] = spin_type
                if spin_type == "controlled":
                    anim_data["groovy_funk_ref"] = item.anim_groovy_ref
                else:
                    anim_data["cycles_per_second"] = item.anim_cycles
            anim_data["centre"] = list(item.anim_centre)
            axis = GrooveProps.enum_value(
                item.anim_axis,
                GrooveProps.AXIS_MAP
            )
            if axis:
                anim_data["axis"] = axis
        elif anim_type == "rock":
            rock_type = GrooveProps.enum_value(
                item.rock_type,
                GrooveProps.ROCK_TYPE_MAP
            )
            if rock_type:
                anim_data["rock_type"] = rock_type
                if rock_type == "absolute":
                    anim_data["groovy_funk_ref"] = item.anim_groovy_ref
                else:
                    anim_data["cycles_per_second"] = item.anim_cycles
            anim_data["centre"] = list(item.anim_centre)
            axis = GrooveProps.enum_value(
                item.anim_axis,
                GrooveProps.AXIS_MAP
            )
            if axis:
                anim_data["axis"] = axis
            anim_data["degrees"] = item.anim_degrees
        elif anim_type == "shear":
            shear_type = GrooveProps.enum_value(
                item.shear_type,
                GrooveProps.SHEAR_TYPE_MAP
            )
            if shear_type:
                anim_data["shear_type"] = shear_type
                if shear_type in {"absolute", "controlled"}:
                    anim_data["groovy_funk_ref"] = item.anim_groovy_ref
            anim_data["centre"] = list(item.anim_centre)
            anim_data["extents"] = list(item.anim_extents)

    return {
        "index": item.index,
        "lollipop": lollipop,
        "trigger": trigger,
        "path": path_data,
        "animation": anim_data,
    }


def _update_groove_item(item: "GrooveItem", context: Context) -> None:
    """
    Update custom properties when groove items change.

    :param item: Groove item.
    :type item: GrooveItem
    :param context: Blender context.
    :type context: Context
    :return: None.
    :rtype: None
    """
    wm = context.window_manager
    if wm.get("carmakit_syncing_grooves"):
        return

    obj = context.object
    if not obj:
        return
    grooves = GrooveProps.ensure_groove_dict(obj)
    key = item.groove_key or str(item.index)
    grooves[key] = _item_to_dict(item)
    if isinstance(grooves, dict):
        obj["carmakit_grooves"] = grooves


class GrooveItem(PropertyGroup):
    """
    Editable groove settings item.
    """

    groove_key: StringProperty(
        name="Groove Key",
        default="",
    )  # type: ignore

    index: IntProperty(
        name="Index",
        default=0,
        update=_update_groove_item,
    )  # type: ignore

    lollipop: EnumProperty(
        name="Lollipop",
        items=GrooveProps.LOLLIPOP_ITEMS,
        default=GrooveProps.first_enum_item(GrooveProps.LOLLIPOP_ITEMS),
        update=_update_groove_item,
    )  # type: ignore

    trigger: EnumProperty(
        name="Trigger",
        items=GrooveProps.TRIGGER_ITEMS,
        default=GrooveProps.first_enum_item(GrooveProps.TRIGGER_ITEMS),
        update=_update_groove_item,
    )  # type: ignore

    path_type: EnumProperty(
        name="Path Type",
        items=GrooveProps.PATH_TYPE_ITEMS,
        default=GrooveProps.first_enum_item(GrooveProps.PATH_TYPE_ITEMS),
        update=_update_groove_item,
    )  # type: ignore

    path_movement_straight: EnumProperty(
        name="Path Movement",
        items=GrooveProps.PATH_STRAIGHT_MOVEMENT_ITEMS,
        default=GrooveProps.first_enum_item(
            GrooveProps.PATH_STRAIGHT_MOVEMENT_ITEMS
        ),
        update=_update_groove_item,
    )  # type: ignore

    path_movement_circular: EnumProperty(
        name="Path Movement",
        items=GrooveProps.PATH_CIRCULAR_MOVEMENT_ITEMS,
        default=GrooveProps.first_enum_item(
            GrooveProps.PATH_CIRCULAR_MOVEMENT_ITEMS
        ),
        update=_update_groove_item,
    )  # type: ignore

    path_centre: FloatVectorProperty(
        name="Centre",
        size=3,
        subtype='XYZ',
        default=(0.0, 0.0, 0.0),
        update=_update_groove_item,
    )  # type: ignore

    path_groovy_ref: StringProperty(
        name="GroovyFunkRef",
        default="",
        update=_update_groove_item,
    )  # type: ignore

    path_distance: FloatVectorProperty(
        name="Distance",
        size=3,
        subtype='XYZ',
        default=(0.0, 0.0, 0.0),
        update=_update_groove_item,
    )  # type: ignore

    path_cycles: StringProperty(
        name="Cycles / Second",
        default="",
        update=_update_groove_item,
    )  # type: ignore

    path_speed: StringProperty(
        name="Speed",
        default="",
        update=_update_groove_item,
    )  # type: ignore

    path_radius: StringProperty(
        name="Radius",
        default="",
        update=_update_groove_item,
    )  # type: ignore

    path_axis: EnumProperty(
        name="Axis",
        items=GrooveProps.AXIS_ITEMS,
        default=GrooveProps.first_enum_item(GrooveProps.AXIS_ITEMS),
        update=_update_groove_item,
    )  # type: ignore

    animation_type: EnumProperty(
        name="Animation",
        items=GrooveProps.ANIMATION_TYPE_ITEMS,
        default=GrooveProps.first_enum_item(
            GrooveProps.ANIMATION_TYPE_ITEMS
        ),
        update=_update_groove_item,
    )  # type: ignore

    spin_type: EnumProperty(
        name="Spin Type",
        items=GrooveProps.SPIN_TYPE_ITEMS,
        default=GrooveProps.first_enum_item(GrooveProps.SPIN_TYPE_ITEMS),
        update=_update_groove_item,
    )  # type: ignore

    rock_type: EnumProperty(
        name="Rock Type",
        items=GrooveProps.ROCK_TYPE_ITEMS,
        default=GrooveProps.first_enum_item(GrooveProps.ROCK_TYPE_ITEMS),
        update=_update_groove_item,
    )  # type: ignore

    shear_type: EnumProperty(
        name="Shear Type",
        items=GrooveProps.SHEAR_TYPE_ITEMS,
        default=GrooveProps.first_enum_item(GrooveProps.SHEAR_TYPE_ITEMS),
        update=_update_groove_item,
    )  # type: ignore

    anim_groovy_ref: StringProperty(
        name="GroovyFunkRef",
        default="",
        update=_update_groove_item,
    )  # type: ignore

    anim_cycles: StringProperty(
        name="Cycles / Second",
        default="",
        update=_update_groove_item,
    )  # type: ignore

    anim_centre: FloatVectorProperty(
        name="Centre",
        size=3,
        subtype='XYZ',
        default=(0.0, 0.0, 0.0),
        update=_update_groove_item,
    )  # type: ignore

    anim_axis: EnumProperty(
        name="Axis",
        items=GrooveProps.AXIS_ITEMS,
        default=GrooveProps.first_enum_item(GrooveProps.AXIS_ITEMS),
        update=_update_groove_item,
    )  # type: ignore

    anim_degrees: StringProperty(
        name="Degrees",
        default="",
        update=_update_groove_item,
    )  # type: ignore

    anim_extents: FloatVectorProperty(
        name="Extents",
        size=3,
        subtype='XYZ',
        default=(0.0, 0.0, 0.0),
        update=_update_groove_item,
    )  # type: ignore
