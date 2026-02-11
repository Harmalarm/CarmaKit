"""
Groove section parser for Carmageddon text files.

This module parses GROOVE sections from Carmageddon car setup files
(e.g., Eagle3.txt) and returns structured groove definitions.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class GrooveDefinition:
    """
    Parsed groove definition from a car setup file.

    """

    index: int
    actor_name: str
    lollipop: str
    trigger: str
    path: Dict[str, object] = field(default_factory=dict)
    animation: Dict[str, object] = field(default_factory=dict)

    def to_custom_property(self) -> Dict[str, object]:
        """
        Convert the groove definition into a custom property dict.

        """
        return {
            "index": self.index,
            "actor_name": self.actor_name,
            "lollipop": self.lollipop,
            "trigger": self.trigger,
            "path": self.path,
            "animation": self.animation,
        }


@dataclass
class GrooveParseResult:
    """
    Parsed groove data from a file.

    """

    grooves: List[GrooveDefinition] = field(default_factory=list)

    def by_actor_name(self) -> Dict[str, List[GrooveDefinition]]:
        """
        Group grooves by normalized actor name.

        """
        result: Dict[str, List[GrooveDefinition]] = {}
        for groove in self.grooves:
            key = normalize_actor_name(groove.actor_name)
            result.setdefault(key, []).append(groove)
        return result


def parse_groove_sections(filepath: str) -> GrooveParseResult:
    """
    Parse groove sections from a Carmageddon car setup file.

    """
    with open(filepath, "r", encoding="ascii", errors="ignore") as f:
        raw_lines = f.readlines()

    lines = _sanitize_lines(raw_lines)
    groove_lines = _extract_groove_lines(lines)
    grooves = _parse_groove_blocks(groove_lines)
    return GrooveParseResult(grooves=grooves)


def normalize_actor_name(name: str) -> str:
    """
    Normalize actor names for matching.

    """
    base = name.strip()
    if base.lower().endswith(".act"):
        base = base[:-4]
    return base.lower()


def _sanitize_lines(lines: Iterable[str]) -> List[str]:
    """
    Clean lines by removing comments and empty lines.

    """
    result: List[str] = []
    for line in lines:
        clean = line.split("//", 1)[0].strip()
        if clean:
            result.append(clean)
    return result


def _extract_groove_lines(lines: List[str]) -> List[str]:
    """
    Extract the lines within the groove section.

    """
    start_token = "START OF GROOVE"
    end_token = "END OF GROOVE"

    try:
        start_index = lines.index(start_token)
    except ValueError:
        return []

    try:
        end_index = lines.index(end_token, start_index + 1)
    except ValueError:
        end_index = len(lines)

    return lines[start_index + 1: end_index]


def _parse_groove_blocks(lines: List[str]) -> List[GrooveDefinition]:
    """
    Parse groove blocks from a groove section.

    """
    blocks: List[List[str]] = []
    current: List[str] = []
    for line in lines:
        if line == "NEXT GROOVE":
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)

    if current:
        blocks.append(current)

    grooves: List[GrooveDefinition] = []
    for index, block in enumerate(blocks):
        groove = _parse_groove_block(index, block)
        if groove:
            grooves.append(groove)

    return grooves


def _parse_groove_block(
    index: int,
    lines: List[str]
) -> Optional[GrooveDefinition]:
    """
    Parse a single groove block.

    """
    if len(lines) < 4:
        return None

    cursor = 0

    actor_name = lines[cursor]
    cursor += 1
    lollipop = lines[cursor] if cursor < len(lines) else ""
    cursor += 1
    trigger = lines[cursor] if cursor < len(lines) else ""
    cursor += 1
    path_type = lines[cursor] if cursor < len(lines) else ""
    cursor += 1

    path_data, cursor = _parse_path(path_type, lines, cursor)

    animation_type = lines[cursor] if cursor < len(lines) else ""
    cursor += 1
    animation_data, _ = _parse_animation(animation_type, lines, cursor)

    return GrooveDefinition(
        index=index,
        actor_name=actor_name,
        lollipop=lollipop,
        trigger=trigger,
        path=path_data,
        animation=animation_data,
    )


def _parse_path(
    path_type: str,
    lines: List[str],
    cursor: int
) -> tuple[Dict[str, object], int]:
    """
    Parse path details for a groove.

    """
    data: Dict[str, object] = {"type": path_type}

    if path_type == "straight":
        movement, cursor = _next_line(lines, cursor)
        data["movement"] = movement
        if movement == "absolute":
            centre, cursor = _next_line(lines, cursor)
            groovy_ref, cursor = _next_line(lines, cursor)
            distance, cursor = _next_line(lines, cursor)
            data["groovy_funk_ref"] = _parse_value(groovy_ref)
            data["centre"] = _parse_value(centre)
            data["distance"] = _parse_value(distance)
        else:
            cycles, cursor = _next_line(lines, cursor)
            distance, cursor = _next_line(lines, cursor)
            data["cycles_per_second"] = _parse_value(cycles)
            data["distance"] = _parse_value(distance)

    elif path_type == "circular":
        movement, cursor = _next_line(lines, cursor)
        data["movement"] = movement
        if movement == "absolute":
            centre, cursor = _next_line(lines, cursor)
            groovy_ref, cursor = _next_line(lines, cursor)
            data["groovy_funk_ref"] = _parse_value(groovy_ref)
            data["centre"] = _parse_value(centre)
        else:
            speed, cursor = _next_line(lines, cursor)
            radius, cursor = _next_line(lines, cursor)
            data["speed"] = _parse_value(speed)
            data["radius"] = _parse_value(radius)
        axis, cursor = _next_line(lines, cursor)
        data["axis"] = axis

    return data, cursor


def _parse_animation(
    animation_type: str,
    lines: List[str],
    cursor: int
) -> tuple[Dict[str, object], int]:
    """
    Parse animation details for a groove.

    """
    data: Dict[str, object] = {"type": animation_type}

    if animation_type == "spin":
        spin_type, cursor = _next_line(lines, cursor)
        data["spin_type"] = spin_type
        if spin_type == "controlled":
            groovy_ref, cursor = _next_line(lines, cursor)
            data["groovy_funk_ref"] = _parse_value(groovy_ref)
        else:
            cycles, cursor = _next_line(lines, cursor)
            data["cycles_per_second"] = _parse_value(cycles)
        centre, cursor = _next_line(lines, cursor)
        axis, cursor = _next_line(lines, cursor)
        data["centre"] = _parse_value(centre)
        data["axis"] = axis

    elif animation_type == "rock":
        rock_type, cursor = _next_line(lines, cursor)
        data["rock_type"] = rock_type
        if rock_type == "absolute":
            groovy_ref, cursor = _next_line(lines, cursor)
            data["groovy_funk_ref"] = _parse_value(groovy_ref)
        else:
            cycles, cursor = _next_line(lines, cursor)
            data["cycles_per_second"] = _parse_value(cycles)
        centre, cursor = _next_line(lines, cursor)
        axis, cursor = _next_line(lines, cursor)
        degrees, cursor = _next_line(lines, cursor)
        data["centre"] = _parse_value(centre)
        data["axis"] = axis
        data["degrees"] = _parse_value(degrees)

    elif animation_type == "shear":
        shear_type, cursor = _next_line(lines, cursor)
        data["shear_type"] = shear_type
        if shear_type in {"absolute", "controlled"}:
            groovy_ref, cursor = _next_line(lines, cursor)
            data["groovy_funk_ref"] = _parse_value(groovy_ref)
        centre, cursor = _next_line(lines, cursor)
        extents, cursor = _next_line(lines, cursor)
        data["centre"] = _parse_value(centre)
        data["extents"] = _parse_value(extents)

    return data, cursor


def _next_line(lines: List[str], cursor: int) -> tuple[str, int]:
    """
    Safely fetch the next line from the block.

    """
    if cursor >= len(lines):
        return "", cursor
    return lines[cursor], cursor + 1


def _parse_value(value: str) -> object:
    """
    Parse a numeric or vector value from a groove line.

    """
    if "," in value:
        parts = [part.strip() for part in value.split(",")]
        parsed: List[object] = []
        for part in parts:
            parsed.append(_parse_scalar(part))
        return parsed

    return _parse_scalar(value)


def _parse_scalar(value: str) -> object:
    """
    Parse a scalar numeric value.

    """
    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        return value
