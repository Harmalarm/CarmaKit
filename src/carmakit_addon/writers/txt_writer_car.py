"""
Car text writer for Carmageddon car setup files.

This module provides minimal support for writing groove sections
based on Blender custom groove properties.
"""

from typing import Dict, Iterable, List, Optional

import bpy

from ..props.groove_props import GrooveProps


def write_car_txt(
    filepath: str,
    objects: Iterable[bpy.types.Object]
) -> None:
    """
    Write a car setup text file with groove sections.

    :param filepath: Output text file path.
    :type filepath: str
    :param objects: Objects to scan for groove data.
    :type objects: Iterable[bpy.types.Object]
    :return: None.
    :rtype: None
    """
    grooves = _collect_grooves(objects)
    lines: List[str] = ["START OF GROOVE", ""]

    for index, groove in enumerate(grooves):
        lines.extend(_format_groove_block(groove))
        if index < len(grooves) - 1:
            lines.extend(["", "NEXT GROOVE", ""])

    lines.extend(["", "END OF GROOVE"])
    content = "\n".join(lines) + "\n"

    with open(filepath, "w", encoding="ascii", errors="ignore") as f:
        f.write(content)


def _collect_grooves(
    objects: Iterable[bpy.types.Object]
) -> List[Dict[str, object]]:
    """
    Collect groove dictionaries from objects.

    :param objects: Objects to scan.
    :type objects: Iterable[bpy.types.Object]
    :return: List of groove data dictionaries.
    :rtype: List[Dict[str, object]]
    """
    grooves: List[Dict[str, object]] = []
    for obj in objects:
        grooves.extend(_collect_grooves_from_collection(obj))
        grooves.extend(_collect_grooves_from_custom_props(obj))

    def _sort_key(item: Dict[str, object]) -> tuple[int, str]:
        return (
            _coerce_int(item.get("index"), 0),
            str(item.get("actor_name", ""))
        )

    grooves.sort(key=_sort_key)
    return grooves


def _collect_grooves_from_custom_props(
    obj: bpy.types.Object
) -> List[Dict[str, object]]:
    """
    Collect grooves from stored custom properties.

    :param obj: Blender object.
    :type obj: bpy.types.Object
    :return: Groove data dictionaries.
    :rtype: List[Dict[str, object]]
    """
    raw = obj.get("carmakit_grooves")
    if not raw or not hasattr(raw, "items"):
        return []

    grooves: List[Dict[str, object]] = []
    for key, value in raw.items():
        plain = _to_plain_dict(value)
        if not plain:
            continue
        index = _coerce_int(plain.get("index"), _coerce_int(key, 0))
        grooves.append({
            "index": index,
            "actor_name": plain.get("actor_name") or obj.name,
            "lollipop": plain.get("lollipop", ""),
            "trigger": plain.get("trigger", ""),
            "path": _to_plain_dict(plain.get("path", {})),
            "animation": _to_plain_dict(plain.get("animation", {})),
        })

    return grooves


def _to_plain_dict(value: object) -> Dict[str, object]:
    """
    Convert mapping-like values to plain dicts.

    :param value: Value to normalize.
    :type value: object
    :return: Plain dictionary.
    :rtype: Dict[str, object]
    """
    if isinstance(value, dict):
        return {
            key: _to_plain_value(val)
            for key, val in value.items()
        }
    if hasattr(value, "items"):
        try:
            return {
                key: _to_plain_value(val)
                for key, val in value.items()
            }
        except Exception:
            return {}
    return {}


def _to_plain_value(value: object) -> object:
    """
    Normalize nested values for groove dictionaries.

    :param value: Value to normalize.
    :type value: object
    :return: Plain Python value.
    :rtype: object
    """
    if isinstance(value, dict) or hasattr(value, "items"):
        return _to_plain_dict(value)
    if isinstance(value, (list, tuple)):
        return [
            _to_plain_value(part)
            for part in value
        ]
    sequence = _sequence_from_value(value)
    if sequence is not None:
        return [
            _to_plain_value(part)
            for part in sequence
        ]
    return value


def _collect_grooves_from_collection(
    obj: bpy.types.Object
) -> List[Dict[str, object]]:
    """
    Collect grooves from the UI collection on the object.

    :param obj: Blender object.
    :type obj: bpy.types.Object
    :return: Groove data dictionaries.
    :rtype: List[Dict[str, object]]
    """
    if not hasattr(obj, "carmakit_groove_items"):
        return []

    items = obj.carmakit_groove_items
    if not items:
        return []

    grooves: List[Dict[str, object]] = []
    for item in items:
        grooves.append(_groove_item_to_dict(obj, item))

    return grooves


def _groove_item_to_dict(
    obj: bpy.types.Object,
    item: bpy.types.PropertyGroup
) -> Dict[str, object]:
    """
    Convert a groove item to a data dictionary.

    :param obj: Blender object.
    :type obj: bpy.types.Object
    :param item: Groove item instance.
    :type item: bpy.types.PropertyGroup
    :return: Groove data dictionary.
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

    path_data: Dict[str, object] = {"type": path_type}
    if path_type == "straight":
        movement = GrooveProps.enum_value(
            item.path_movement_straight,
            GrooveProps.PATH_STRAIGHT_MOVEMENT_MAP
        )
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

    anim_data: Dict[str, object] = {"type": anim_type}
    if anim_type == "spin":
        spin_type = GrooveProps.enum_value(
            item.spin_type,
            GrooveProps.SPIN_TYPE_MAP
        )
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
        anim_data["shear_type"] = shear_type
        if shear_type in {"absolute", "controlled"}:
            anim_data["groovy_funk_ref"] = item.anim_groovy_ref
        anim_data["centre"] = list(item.anim_centre)
        anim_data["extents"] = list(item.anim_extents)

    return {
        "index": _coerce_int(item.index, 0),
        "actor_name": obj.name,
        "lollipop": lollipop,
        "trigger": trigger,
        "path": path_data,
        "animation": anim_data,
    }


def _format_groove_block(groove: Dict[str, object]) -> List[str]:
    """
    Format a groove dictionary as text lines.

    :param groove: Groove data dictionary.
    :type groove: Dict[str, object]
    :return: Formatted text lines.
    :rtype: List[str]
    """
    actor_name = _format_actor_name(str(groove.get("actor_name", "")))
    lollipop = str(groove.get("lollipop") or "not a lollipop")
    trigger = str(groove.get("trigger") or "constant")
    path = groove.get("path", {})
    animation = groove.get("animation", {})

    lines = [actor_name, lollipop, trigger]
    lines.extend(_format_path(path if isinstance(path, dict) else {}))
    lines.extend(
        _format_animation(animation if isinstance(animation, dict) else {})
    )
    return lines


def _format_path(path: Dict[str, object]) -> List[str]:
    """
    Format path data lines for a groove.

    :param path: Path data dictionary.
    :type path: Dict[str, object]
    :return: Path lines.
    :rtype: List[str]
    """
    path_type = str(path.get("type") or "no path")
    lines = [path_type]

    if path_type == "straight":
        movement = str(path.get("movement") or "absolute")
        lines.append(movement)
        if movement == "absolute":
            lines.append(
                _format_value(path.get("centre", (0, 0, 0)))
            )
            lines.append(
                _format_value(path.get("groovy_funk_ref", 0))
            )
            lines.append(
                _format_value(path.get("distance", (0, 0, 0)))
            )
        else:
            lines.append(
                _format_value(path.get("cycles_per_second", 0))
            )
            lines.append(
                _format_value(path.get("distance", (0, 0, 0)))
            )

    elif path_type == "circular":
        movement = str(path.get("movement") or "absolute")
        lines.append(movement)
        if movement == "absolute":
            lines.append(
                _format_value(path.get("centre", (0, 0, 0)))
            )
            lines.append(
                _format_value(path.get("groovy_funk_ref", 0))
            )
        else:
            lines.append(_format_value(path.get("speed", 0)))
            lines.append(_format_value(path.get("radius", 0)))
        lines.append(str(path.get("axis") or "x"))

    return lines


def _format_animation(animation: Dict[str, object]) -> List[str]:
    """
    Format animation data lines for a groove.

    :param animation: Animation data dictionary.
    :type animation: Dict[str, object]
    :return: Animation lines.
    :rtype: List[str]
    """
    anim_type = str(animation.get("type") or "no animation")
    lines = [anim_type]

    if anim_type == "spin":
        spin_type = str(animation.get("spin_type") or "controlled")
        lines.append(spin_type)
        if spin_type == "controlled":
            lines.append(
                _format_value(animation.get("groovy_funk_ref", 0))
            )
        else:
            lines.append(
                _format_value(animation.get("cycles_per_second", 0))
            )
        lines.append(
            _format_value(animation.get("centre", (0, 0, 0)))
        )
        lines.append(str(animation.get("axis") or "x"))

    elif anim_type == "rock":
        rock_type = str(animation.get("rock_type") or "absolute")
        lines.append(rock_type)
        if rock_type == "absolute":
            lines.append(
                _format_value(animation.get("groovy_funk_ref", 0))
            )
        else:
            lines.append(
                _format_value(animation.get("cycles_per_second", 0))
            )
        lines.append(
            _format_value(animation.get("centre", (0, 0, 0)))
        )
        lines.append(str(animation.get("axis") or "x"))
        lines.append(_format_value(animation.get("degrees", 0)))

    elif anim_type == "shear":
        shear_type = str(animation.get("shear_type") or "absolute")
        lines.append(shear_type)
        if shear_type in {"absolute", "controlled"}:
            lines.append(
                _format_value(animation.get("groovy_funk_ref", 0))
            )
        lines.append(
            _format_value(animation.get("centre", (0, 0, 0)))
        )
        lines.append(
            _format_value(animation.get("extents", (0, 0, 0)))
        )

    return lines


def _format_actor_name(name: str) -> str:
    """
    Format actor name for groove output.

    :param name: Actor name.
    :type name: str
    :return: Actor name with .ACT suffix.
    :rtype: str
    """
    base = name.strip()
    if base.lower().endswith(".act"):
        return base
    return f"{base}.ACT"


def _format_value(value: object) -> str:
    """
    Format scalar or vector values for output.

    :param value: Value to format.
    :type value: object
    :return: Formatted value string.
    :rtype: str
    """
    sequence = _sequence_from_value(value)
    if sequence is not None:
        parts = [_format_scalar(part) for part in sequence]
        return ",".join(parts)
    if isinstance(value, str):
        return value
    return _format_scalar(value)


def _is_sequence_value(value: object) -> bool:
    """
    Check if a value should be treated as a sequence.

    :param value: Value to test.
    :type value: object
    :return: True when value is a non-string iterable.
    :rtype: bool
    """
    if isinstance(value, (str, bytes, dict)):
        return False
    if hasattr(value, "__iter__"):
        return True
    return hasattr(value, "__len__") and hasattr(value, "__getitem__")


def _sequence_from_value(value: object) -> Optional[List[object]]:
    """
    Extract a list of values from a sequence-like value.

    :param value: Value to normalize.
    :type value: object
    :return: List of items or None when not sequence-like.
    :rtype: Optional[List[object]]
    """
    if isinstance(value, (str, bytes, dict)):
        return None
    if hasattr(value, "to_list"):
        try:
            return list(value.to_list())
        except Exception:
            return None
    if hasattr(value, "to_tuple"):
        try:
            return list(value.to_tuple())
        except Exception:
            return None
    if _is_sequence_value(value):
        try:
            return list(value)
        except Exception:
            return None
    return None


def _format_scalar(value: object) -> str:
    """
    Format a scalar numeric value.

    :param value: Value to format.
    :type value: object
    :return: Formatted scalar string.
    :rtype: str
    """
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:g}"
    return str(value)


def _coerce_int(value: object, fallback: int) -> int:
    """
    Coerce values to int with a fallback.

    :param value: Value to convert.
    :type value: object
    :param fallback: Fallback value.
    :type fallback: int
    :return: Integer value.
    :rtype: int
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback
