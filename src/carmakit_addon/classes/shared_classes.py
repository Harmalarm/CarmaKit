"""
Data structures for CarmaKit file formats.

This module defines dataclasses that represent the various structures
found in Carmageddon ACT, DAT, and MAT files.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class Vector3:
    """
    A 3D vector with x, y, z components.

    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def as_tuple(self) -> Tuple[float, float, float]:
        """
        Convert to tuple representation.

        """
        return (self.x, self.y, self.z)


@dataclass
class Vector2:
    """
    A 2D vector with u, v components (for texture coordinates).

    """

    u: float = 0.0
    v: float = 0.0

    def as_tuple(self) -> Tuple[float, float]:
        """
        Convert to tuple representation.

        """
        return (self.u, self.v)
