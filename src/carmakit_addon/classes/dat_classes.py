"""
Data structures for CarmaKit file formats.

This module defines dataclasses that represent the various structures
found in Carmageddon DAT files.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .shared_classes import (
    Vector3,
    Vector2
)

@dataclass
class Face:
    """
    A triangular face with vertex indices.

    :param v1: First vertex index.
    :type v1: int
    :param v2: Second vertex index.
    :type v2: int
    :param v3: Third vertex index.
    :type v3: int
    :param flags: Face flags (3 bytes: 2 bytes smoothing group + 1 byte edge visibility).
    :type flags: bytes
    :param material_index: Index into material list (1-based).
    :type material_index: int
    """

    v1: int = 0
    v2: int = 0
    v3: int = 0
    flags: bytes = b'\x00\x01\x00'
    material_index: int = 1

    @property
    def smoothing_group(self) -> int:
        """
        Get the smoothing group from the flags.

        The smoothing group is stored in the first 2 bytes of flags.

        :return: Smoothing group index.
        :rtype: int
        """
        if len(self.flags) >= 2:
            # Big-endian 16-bit value from first 2 bytes.
            return (self.flags[0] << 8) | self.flags[1]
        return 0

    @property
    def edge_visibility(self) -> int:
        """
        Get the edge visibility flags.

        The edge visibility is stored in the 3rd byte of flags.
        Bit 0 (value 1): Edge 0 hidden
        Bit 1 (value 2): Edge 1 hidden
        Bit 2 (value 4): Edge 2 hidden

        :return: Edge visibility bitmask.
        :rtype: int
        """
        if len(self.flags) >= 3:
            return self.flags[2]
        return 0

@dataclass
class DatModel:
    """
    A mesh model from a DAT file.

    :param name: Model name.
    :type name: str
    :param attributes: Model attributes (2 bytes).
    :type attributes: int
    :param vertices: List of vertex positions.
    :type vertices: List[Vector3]
    :param tex_coords: List of texture coordinates.
    :type tex_coords: List[Vector2]
    :param faces: List of faces.
    :type faces: List[Face]
    :param materials: List of material names.
    :type materials: List[str]
    """

    name: str = ""
    attributes: int = 0
    vertices: List[Vector3] = field(default_factory=list)
    tex_coords: List[Vector2] = field(default_factory=list)
    faces: List[Face] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)

@dataclass
class DatFile:
    """
    A complete DAT file with multiple models.

    :param models: List of models.
    :type models: List[DatModel]
    """

    models: List[DatModel] = field(default_factory=list)