"""
Tests for the data structures module.

:author: CarmaKit Team
"""

import pytest

from carmakit_addon.classes.shared_classes import (
    Vector2,
    Vector3,
)
from carmakit_addon.classes.act_classes  import (
    ActFile,
    ActorNode,
    BoundingBox,
    TransformMatrix,
)
from carmakit_addon.classes.mat_classes  import (
    Material,
    MatFile,
)
from carmakit_addon.classes.dat_classes  import ( 
    DatFile,
    DatModel,
    Face,
)

class TestVector3:
    """Tests for Vector3 class."""

    def test_default_values(self) -> None:
        """Test default vector values are zero."""
        v = Vector3()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 0.0

    def test_custom_values(self) -> None:
        """Test creating vector with custom values."""
        v = Vector3(1.0, 2.0, 3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_as_tuple(self) -> None:
        """Test converting vector to tuple."""
        v = Vector3(1.0, 2.0, 3.0)
        assert v.as_tuple() == (1.0, 2.0, 3.0)


class TestVector2:
    """Tests for Vector2 class."""

    def test_default_values(self) -> None:
        """Test default vector values are zero."""
        v = Vector2()
        assert v.u == 0.0
        assert v.v == 0.0

    def test_custom_values(self) -> None:
        """Test creating vector with custom values."""
        v = Vector2(0.5, 0.75)
        assert v.u == 0.5
        assert v.v == 0.75

    def test_as_tuple(self) -> None:
        """Test converting vector to tuple."""
        v = Vector2(0.5, 0.75)
        assert v.as_tuple() == (0.5, 0.75)


class TestTransformMatrix:
    """Tests for TransformMatrix class."""

    def test_default_is_identity(self) -> None:
        """Test that default matrix is identity."""
        m = TransformMatrix()
        expected = (
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
            0.0, 0.0, 0.0,
        )
        assert m.values == expected

    def test_rotation_3x3(self) -> None:
        """Test extracting 3x3 rotation portion."""
        m = TransformMatrix()
        rot = m.rotation_3x3
        assert rot == (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        )

    def test_position(self) -> None:
        """Test extracting position from matrix."""
        m = TransformMatrix((
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
            10.0, 20.0, 30.0,
        ))
        pos = m.position
        assert pos.x == 10.0
        assert pos.y == 20.0
        assert pos.z == 30.0


class TestBoundingBox:
    """Tests for BoundingBox class."""

    def test_default_values(self) -> None:
        """Test default bounding box is at origin."""
        bb = BoundingBox()
        assert bb.min_point.x == 0.0
        assert bb.max_point.x == 0.0

    def test_custom_values(self) -> None:
        """Test creating bounding box with custom values."""
        bb = BoundingBox(
            Vector3(-1.0, -2.0, -3.0),
            Vector3(1.0, 2.0, 3.0)
        )
        assert bb.min_point.x == -1.0
        assert bb.max_point.x == 1.0


class TestFace:
    """Tests for Face class."""

    def test_default_values(self) -> None:
        """Test default face values."""
        f = Face()
        assert f.v1 == 0
        assert f.v2 == 0
        assert f.v3 == 0
        assert f.flags == b'\x00\x01\x00'
        assert f.material_index == 1

    def test_custom_values(self) -> None:
        """Test creating face with custom values."""
        f = Face(1, 2, 3, b'\x00\x00\x00', 5)
        assert f.v1 == 1
        assert f.v2 == 2
        assert f.v3 == 3
        assert f.material_index == 5


class TestDatModel:
    """Tests for DatModel class."""

    def test_empty_model(self) -> None:
        """Test creating an empty model."""
        m = DatModel()
        assert m.name == ""
        assert len(m.vertices) == 0
        assert len(m.faces) == 0
        assert len(m.materials) == 0

    def test_model_with_data(self) -> None:
        """Test model with vertices and faces."""
        m = DatModel()
        m.name = "TestModel"
        m.vertices.append(Vector3(0.0, 0.0, 0.0))
        m.vertices.append(Vector3(1.0, 0.0, 0.0))
        m.vertices.append(Vector3(0.0, 1.0, 0.0))
        m.faces.append(Face(0, 1, 2))
        m.materials.append("TestMat")

        assert m.name == "TestModel"
        assert len(m.vertices) == 3
        assert len(m.faces) == 1
        assert len(m.materials) == 1


class TestMaterial:
    """Tests for Material class."""

    def test_default_values(self) -> None:
        """Test default material values."""
        m = Material()
        assert m.color == (255, 255, 255, 255)
        assert m.flags == 0x21

    def test_is_two_sided(self) -> None:
        """Test two-sided flag detection."""
        m = Material()
        assert not m.is_two_sided

        m.flags = 0x00001000
        assert m.is_two_sided

    def test_is_lit(self) -> None:
        """Test lit flag detection."""
        m = Material()
        m.flags = 0x00000001
        assert m.is_lit

        m.flags = 0x00000000
        assert not m.is_lit


class TestActorNode:
    """Tests for ActorNode class."""

    def test_empty_node(self) -> None:
        """Test creating an empty actor node."""
        n = ActorNode()
        assert n.name == ""
        assert n.model_name is None
        assert len(n.children) == 0

    def test_node_with_children(self) -> None:
        """Test node with child hierarchy."""
        parent = ActorNode()
        parent.name = "Parent"

        child1 = ActorNode()
        child1.name = "Child1"
        child2 = ActorNode()
        child2.name = "Child2"

        parent.children.append(child1)
        parent.children.append(child2)

        assert len(parent.children) == 2
        assert parent.children[0].name == "Child1"
        assert parent.children[1].name == "Child2"


class TestFileStructures:
    """Tests for file-level structures."""

    def test_dat_file_empty(self) -> None:
        """Test empty DAT file structure."""
        dat = DatFile()
        assert len(dat.models) == 0

    def test_mat_file_empty(self) -> None:
        """Test empty MAT file structure."""
        mat = MatFile()
        assert len(mat.materials) == 0

    def test_act_file_empty(self) -> None:
        """Test empty ACT file structure."""
        act = ActFile()
        assert act.root is None
