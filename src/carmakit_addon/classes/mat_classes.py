"""
Data structures for CarmaKit file formats.

This module defines dataclasses that represent the various structures
found in Carmageddon MAT files.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .shared_classes import (
    Vector3,
    Vector2
)

@dataclass
class Material:
    """
    A material from a MAT file.

    """

    name: str = ""
    color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    ambient: float = 0.1
    directional: float = 0.7
    specular: float = 0.0
    specular_power: float = 20.0
    flags: int = 0x21
    uv_transform: Tuple[float, ...] = field(
        default_factory=lambda: (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    )
    texture_name: Optional[str] = None

    @property
    def is_two_sided(self) -> bool:
        """
        Check if material is two-sided.

        """
        return bool(self.flags & 0x00001000)

    @property
    def is_lit(self) -> bool:
        """
        Check if material is lit.

        """
        return bool(self.flags & 0x00000001)


@dataclass
class MatFile:
    """
    A complete MAT file with multiple materials.

    """

    materials: List[Material] = field(default_factory=list)