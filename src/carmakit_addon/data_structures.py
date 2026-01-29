"""
Data structures for CarmaKit file formats.

This module defines dataclasses that represent the various structures
found in Carmageddon ACT, DAT, and MAT files.

:author: CarmaKit Team
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
    def position(self) -> Vector3:
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
class Face:
    """
    A triangular face with vertex indices.

    :param v1: First vertex index.
    :type v1: int
    :param v2: Second vertex index.
    :type v2: int
    :param v3: Third vertex index.
    :type v3: int
    :param flags: Unknown flags (3 bytes, Plaything uses 0x00, 0x01, 0x00).
    :type flags: bytes
    :param material_index: Index into material list (1-based).
    :type material_index: int
    """

    v1: int = 0
    v2: int = 0
    v3: int = 0
    flags: bytes = b'\x00\x01\x00'
    material_index: int = 1


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
class Material:
    """
    A material from a MAT file.

    :param name: Material name.
    :type name: str
    :param color: RGBA color (4 bytes).
    :type color: Tuple[int, int, int, int]
    :param ambient: Ambient lighting factor.
    :type ambient: float
    :param directional: Directional lighting factor.
    :type directional: float
    :param specular: Specular lighting factor.
    :type specular: float
    :param specular_power: Specular power/shininess.
    :type specular_power: float
    :param flags: Material flags.
    :type flags: int
    :param uv_transform: UV transformation matrix (6 floats).
    :type uv_transform: Tuple[float, ...]
    :param texture_name: Referenced texture/image name.
    :type texture_name: Optional[str]
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

        :return: True if two-sided flag is set.
        :rtype: bool
        """
        return bool(self.flags & 0x00001000)

    @property
    def is_lit(self) -> bool:
        """
        Check if material is lit.

        :return: True if lit flag is set.
        :rtype: bool
        """
        return bool(self.flags & 0x00000001)


@dataclass
class MatFile:
    """
    A complete MAT file with multiple materials.

    :param materials: List of materials.
    :type materials: List[Material]
    """

    materials: List[Material] = field(default_factory=list)


@dataclass
class DatFile:
    """
    A complete DAT file with multiple models.

    :param models: List of models.
    :type models: List[DatModel]
    """

    models: List[DatModel] = field(default_factory=list)


@dataclass
class ActFile:
    """
    A complete ACT file with the actor hierarchy.

    :param root: Root actor node.
    :type root: Optional[ActorNode]
    """

    root: Optional[ActorNode] = None
