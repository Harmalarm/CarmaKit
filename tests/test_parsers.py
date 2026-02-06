"""
Tests for the file parsers.

These tests use the Eagle3 sample model files to validate parsing.


"""

import os
from pathlib import Path

import pytest

from carmakit_addon.parsers.act_parser import parse_act_file
from carmakit_addon.parsers.dat_parser import parse_dat_file
from carmakit_addon.parsers.mat_parser import parse_mat_file
from carmakit_addon.parsers.utils import ParseError, find_related_files


class TestDatParser:
    """Tests for DAT file parsing."""

    def test_parse_eagle3_dat(self, eagle3_dat_path: Path) -> None:
        """
        Test parsing the Eagle3 DAT file.

        :param eagle3_dat_path: Path to Eagle3.dat fixture.
        :type eagle3_dat_path: Path
        """
        if not eagle3_dat_path.exists():
            pytest.skip(f"Test file not found: {eagle3_dat_path}")

        dat_file = parse_dat_file(str(eagle3_dat_path))

        # Should have at least one model.
        assert len(dat_file.models) > 0

        # Check first model has data.
        model = dat_file.models[0]
        assert model.name != ""
        assert len(model.vertices) > 0
        assert len(model.faces) > 0

    def test_parse_simple_eagle3_dat(
        self, simple_eagle3_dat_path: Path
    ) -> None:
        """
        Test parsing the simple Eagle3 DAT file.

        :param simple_eagle3_dat_path: Path to simple_eagle3.dat fixture.
        :type simple_eagle3_dat_path: Path
        """
        if not simple_eagle3_dat_path.exists():
            pytest.skip(f"Test file not found: {simple_eagle3_dat_path}")

        dat_file = parse_dat_file(str(simple_eagle3_dat_path))
        assert len(dat_file.models) > 0

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """
        Test parsing a file that doesn't exist raises an error.

        :param tmp_path: Temporary directory fixture.
        :type tmp_path: Path
        """
        fake_path = tmp_path / "nonexistent.dat"
        with pytest.raises(FileNotFoundError):
            parse_dat_file(str(fake_path))


class TestActParser:
    """Tests for ACT file parsing."""

    def test_parse_eagle3_act(self, eagle3_act_path: Path) -> None:
        """
        Test parsing the Eagle3 ACT file.

        :param eagle3_act_path: Path to EAGLE3.ACT fixture.
        :type eagle3_act_path: Path
        """
        if not eagle3_act_path.exists():
            pytest.skip(f"Test file not found: {eagle3_act_path}")

        act_file = parse_act_file(str(eagle3_act_path))

        # Should have a root node.
        assert act_file.root is not None
        assert act_file.root.name != ""

    def test_parse_simple_eagle3_act(
        self, simple_eagle3_act_path: Path
    ) -> None:
        """
        Test parsing the simple Eagle3 ACT file.

        :param simple_eagle3_act_path: Path to simple_eagle3.act fixture.
        :type simple_eagle3_act_path: Path
        """
        if not simple_eagle3_act_path.exists():
            pytest.skip(f"Test file not found: {simple_eagle3_act_path}")

        act_file = parse_act_file(str(simple_eagle3_act_path))
        assert act_file.root is not None


class TestMatParser:
    """Tests for MAT file parsing."""

    def test_parse_eagle3_mat(self, eagle3_mat_path: Path) -> None:
        """
        Test parsing the Eagle3 MAT file.

        :param eagle3_mat_path: Path to Eagle3.mat fixture.
        :type eagle3_mat_path: Path
        """
        if not eagle3_mat_path.exists():
            pytest.skip(f"Test file not found: {eagle3_mat_path}")

        mat_file = parse_mat_file(str(eagle3_mat_path))

        # Should have at least one material.
        assert len(mat_file.materials) > 0

        # Check first material has data.
        material = mat_file.materials[0]
        assert material.name != ""

    def test_parse_simple_eagle3_mat(
        self, simple_eagle3_mat_path: Path
    ) -> None:
        """
        Test parsing the simple Eagle3 MAT file.

        :param simple_eagle3_mat_path: Path to simple_eagle3.mat fixture.
        :type simple_eagle3_mat_path: Path
        """
        if not simple_eagle3_mat_path.exists():
            pytest.skip(f"Test file not found: {simple_eagle3_mat_path}")

        mat_file = parse_mat_file(str(simple_eagle3_mat_path))
        assert len(mat_file.materials) > 0


class TestFindRelatedFiles:
    """Tests for the find_related_files utility."""

    def test_find_from_dat(self, eagle3_dir: Path) -> None:
        """
        Test finding related files when given a DAT file.

        :param eagle3_dir: Path to Eagle3 directory fixture.
        :type eagle3_dir: Path
        """
        dat_path = eagle3_dir / "Eagle3.dat"
        if not dat_path.exists():
            pytest.skip(f"Test file not found: {dat_path}")

        act_path, found_dat, mat_path = find_related_files(str(dat_path))

        # Should find the DAT file itself.
        assert found_dat is not None
        assert "eagle3" in found_dat.lower()

    def test_find_from_act(self, eagle3_dir: Path) -> None:
        """
        Test finding related files when given an ACT file.

        :param eagle3_dir: Path to Eagle3 directory fixture.
        :type eagle3_dir: Path
        """
        act_path = eagle3_dir / "EAGLE3.ACT"
        if not act_path.exists():
            pytest.skip(f"Test file not found: {act_path}")

        found_act, dat_path, mat_path = find_related_files(str(act_path))

        # Should find the ACT file itself.
        assert found_act is not None
