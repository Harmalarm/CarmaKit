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

    :param values: The 12 float values of the matrix.
    :type values: Tuple[float, ...]
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

        :return: 3x3 rotation matrix as nested tuples.
        :rtype: Tuple[Tuple[float, float, float], ...]
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

        :return: Position as Vector3.
        :rtype: Vector3
        """
        return Vector3(self.values[9], self.values[10], self.values[11])

@dataclass
class BoundingBox:
    """
    An axis-aligned bounding box.

    :param min_point: Minimum corner of the bounding box.
    :type min_point: Vector3
    :param max_point: Maximum corner of the bounding box.
    :type max_point: Vector3
    """

    min_point: Vector3 = field(default_factory=Vector3)
    max_point: Vector3 = field(default_factory=Vector3)
 
@dataclass
class ActorNode:
    """
    A node in the ACT hierarchy.

    :param name: Actor name.
    :type name: str
    :param attributes: Actor attributes (2 bytes).
    :type attributes: int
    :param transform: Transformation matrix.
    :type transform: TransformMatrix
    :param bounding_box: Bounding box (optional).
    :type bounding_box: Optional[BoundingBox]
    :param model_name: Referenced model name (optional).
    :type model_name: Optional[str]
    :param materials: List of material names (optional).
    :type materials: List[str]
    :param children: Child actor nodes.
    :type children: List[ActorNode]
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

    :param root: Root actor node.
    :type root: Optional[ActorNode]
    """

    root: Optional[ActorNode] = None
