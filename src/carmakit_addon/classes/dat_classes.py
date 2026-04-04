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

        """
        if len(self.flags) >= 3:
            return self.flags[2]
        return 0

@dataclass
class DatModel:
    """
    A mesh model from a DAT file.

    """

    name: str = ""
    attributes: int = 1
    vertices: List[Vector3] = field(default_factory=list)
    tex_coords: List[Vector2] = field(default_factory=list)
    faces: List[Face] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)

@dataclass
class DatFile:
    """
    A complete DAT file with multiple models.

    """

    models: List[DatModel] = field(default_factory=list)