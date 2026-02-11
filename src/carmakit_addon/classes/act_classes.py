"""
Data structures for CarmaKit file formats.

This module defines dataclasses that represent the various structures
found in Carmageddon ACT files.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .shared_classes import (
    Vector3,
)

@dataclass
class TransformMatrix:
    """
    A 3x4 transformation matrix (3x3 rotation + position).

    The matrix is stored in the format used by Carmageddon:
    Xx, Yx, Zx, Xy, Yy, Zy, Xz, Yz, Zz, Px, Py, Pz

    """

    values: Tuple[float, ...] = field(
        default_factory=lambda: (
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
            0.0, 0.0, 0.0,
        )
    )

    @property
    def rotation_3x3(self) -> Tuple[Tuple[float, float, float], ...]:
        """
        Get the 3x3 rotation portion of the matrix.

        """
        return (
            (self.values[0], self.values[1], self.values[2]),
            (self.values[3], self.values[4], self.values[5]),
            (self.values[6], self.values[7], self.values[8]),
        )

    @property
    def position(self) -> 'Vector3':
        """
        Get the position (translation) portion of the matrix.

        """
        return Vector3(self.values[9], self.values[10], self.values[11])

@dataclass
class BoundingBox:
    """
    An axis-aligned bounding box.

    """

    min_point: Vector3 = field(default_factory=Vector3)
    max_point: Vector3 = field(default_factory=Vector3)
 
@dataclass
class ActorNode:
    """
    A node in the ACT hierarchy.

    """

    name: str = ""
    attributes: int = 0
    transform: TransformMatrix = field(default_factory=TransformMatrix)
    bounding_box: Optional[BoundingBox] = None
    model_name: Optional[str] = None
    materials: List[str] = field(default_factory=list)
    children: List['ActorNode'] = field(default_factory=list)
    
@dataclass
class ActFile:
    """
    A complete ACT file with the actor hierarchy.

    """

    root: Optional[ActorNode] = None
