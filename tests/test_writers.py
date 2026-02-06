"""
Tests for the file writers.

These tests verify that data structures can be written and re-read correctly.


"""

import os
from pathlib import Path

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
from carmakit_addon.parsers.act_parser import parse_act_file
from carmakit_addon.parsers.dat_parser import parse_dat_file
from carmakit_addon.parsers.mat_parser import parse_mat_file
from carmakit_addon.writers.act_writer import write_act_file
from carmakit_addon.writers.dat_writer import write_dat_file
from carmakit_addon.writers.mat_writer import write_mat_file
from carmakit_addon.writers.sdf_writer import write_sdf_file


class TestDatWriter:
    """Tests for DAT file writing."""

    def test_write_simple_model(self, tmp_path: Path) -> None:
        """
        Test writing a simple model to a DAT file.

        :param tmp_path: Temporary directory fixture.
        :type tmp_path: Path
        """
        # Create a simple triangle.
        model = DatModel()
        model.name = "Triangle"
        model.vertices = [
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        ]
        model.tex_coords = [
            Vector2(0.0, 0.0),
            Vector2(1.0, 0.0),
            Vector2(0.0, 1.0),
        ]
        model.faces = [Face(0, 1, 2)]
        model.materials = ["TestMaterial"]

        dat_file = DatFile()
        dat_file.models.append(model)

        # Write to file.
        output_path = tmp_path / "test.dat"
        write_dat_file(str(output_path), dat_file)

        # Verify file exists and has content.
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_dat_round_trip(self, tmp_path: Path) -> None:
        """
        Test that a DAT file can be written and re-read.

        :param tmp_path: Temporary directory fixture.
        :type tmp_path: Path
        """
        # Create test model.
        model = DatModel()
        model.name = "RoundTripTest"
        model.vertices = [
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
            Vector3(1.0, 1.0, 0.0),
        ]
        model.tex_coords = [
            Vector2(0.0, 0.0),
            Vector2(1.0, 0.0),
            Vector2(0.0, 1.0),
            Vector2(1.0, 1.0),
        ]
        model.faces = [
            Face(0, 1, 2, b'\x00\x01\x00', 1),
            Face(1, 3, 2, b'\x00\x01\x00', 1),
        ]
        model.materials = ["Material1"]

        dat_file = DatFile()
        dat_file.models.append(model)

        # Write and re-read.
        output_path = tmp_path / "roundtrip.dat"
        write_dat_file(str(output_path), dat_file)

        read_dat = parse_dat_file(str(output_path))

        # Verify data matches.
        assert len(read_dat.models) == 1
        read_model = read_dat.models[0]
        assert read_model.name == model.name
        assert len(read_model.vertices) == len(model.vertices)
        assert len(read_model.faces) == len(model.faces)


class TestActWriter:
    """Tests for ACT file writing."""

    def test_write_simple_act(self, tmp_path: Path) -> None:
        """
        Test writing a simple ACT file.

        :param tmp_path: Temporary directory fixture.
        :type tmp_path: Path
        """
        # Create actor node.
        root = ActorNode()
        root.name = "TestActor"
        root.model_name = "TestModel.dat"
        root.bounding_box = BoundingBox(
            Vector3(-1.0, -1.0, -1.0),
            Vector3(1.0, 1.0, 1.0)
        )

        act_file = ActFile()
        act_file.root = root

        # Write to file.
        output_path = tmp_path / "test.act"
        write_act_file(str(output_path), act_file)

        # Verify file exists and has content.
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_act_round_trip(self, tmp_path: Path) -> None:
        """
        Test that an ACT file can be written and re-read.

        :param tmp_path: Temporary directory fixture.
        :type tmp_path: Path
        """
        # Create actor hierarchy.
        root = ActorNode()
        root.name = "Root"
        root.transform = TransformMatrix((
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
            5.0, 10.0, 15.0,
        ))

        child = ActorNode()
        child.name = "Child"
        child.model_name = "ChildModel.dat"
        root.children.append(child)

        act_file = ActFile()
        act_file.root = root

        # Write and re-read.
        output_path = tmp_path / "roundtrip.act"
        write_act_file(str(output_path), act_file)

        read_act = parse_act_file(str(output_path))

        # Verify data matches.
        assert read_act.root is not None
        assert read_act.root.name == root.name


class TestMatWriter:
    """Tests for MAT file writing."""

    def test_write_simple_mat(self, tmp_path: Path) -> None:
        """
        Test writing a simple MAT file.

        :param tmp_path: Temporary directory fixture.
        :type tmp_path: Path
        """
        # Create material.
        mat = Material()
        mat.name = "TestMaterial"
        mat.color = (255, 128, 64, 255)
        mat.texture_name = "TestTexture"

        mat_file = MatFile()
        mat_file.materials.append(mat)

        # Write to file.
        output_path = tmp_path / "test.mat"
        write_mat_file(str(output_path), mat_file)

        # Verify file exists and has content.
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_mat_round_trip(self, tmp_path: Path) -> None:
        """
        Test that a MAT file can be written and re-read.

        :param tmp_path: Temporary directory fixture.
        :type tmp_path: Path
        """
        # Create material.
        mat = Material()
        mat.name = "RoundTripMat"
        mat.color = (200, 150, 100, 255)
        mat.flags = 0x00001021  # Lit + two-sided.

        mat_file = MatFile()
        mat_file.materials.append(mat)

        # Write and re-read.
        output_path = tmp_path / "roundtrip.mat"
        write_mat_file(str(output_path), mat_file)

        read_mat = parse_mat_file(str(output_path))

        # Verify data matches.
        assert len(read_mat.materials) == 1
        read_material = read_mat.materials[0]
        assert read_material.name == mat.name


class TestSdfWriter:
    """Tests for SDF file writing."""

    def test_write_sdf(self, tmp_path: Path) -> None:
        """
        Test writing an empty SDF file.

        :param tmp_path: Temporary directory fixture.
        :type tmp_path: Path
        """
        output_path = tmp_path / "test.sdf"
        write_sdf_file(str(output_path))

        # Verify file exists and is empty.
        assert output_path.exists()
        assert output_path.stat().st_size == 0
