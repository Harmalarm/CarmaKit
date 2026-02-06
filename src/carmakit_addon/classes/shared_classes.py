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

    :param x: X coordinate.
    :type x: float
    :param y: Y coordinate.
    :type y: float
    :param z: Z coordinate.
    :type z: float
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def as_tuple(self) -> Tuple[float, float, float]:
        """
        Convert to tuple representation.

        :return: Tuple of (x, y, z).
        :rtype: Tuple[float, float, float]
        """
        return (self.x, self.y, self.z)


@dataclass
class Vector2:
    """
    A 2D vector with u, v components (for texture coordinates).

    :param u: U texture coordinate.
    :type u: float
    :param v: V texture coordinate.
    :type v: float
    """

    u: float = 0.0
    v: float = 0.0

    def as_tuple(self) -> Tuple[float, float]:
        """
        Convert to tuple representation.

        :return: Tuple of (u, v).
        :rtype: Tuple[float, float]
        """
        return (self.u, self.v)
