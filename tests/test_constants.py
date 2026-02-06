"""
Tests for the constants module.


"""

import pytest

from carmakit_addon.constants import (
    ACT_RECORD_ACTOR_NAME,
    ACT_RECORD_BOUNDING_BOX,
    ACT_RECORD_HIERARCHY_END,
    ACT_RECORD_HIERARCHY_START,
    ACT_RECORD_MODEL_NAME,
    ACT_RECORD_TRANSFORM,
    DAT_RECORD_FACES,
    DAT_RECORD_MATERIAL_NAMES,
    DAT_RECORD_MODEL_NAME,
    DAT_RECORD_TEX_COORDS,
    DAT_RECORD_VERTICES,
    FILE_HEADER_TYPE,
    FILE_TYPE_ACT,
    FILE_TYPE_DAT,
    FILE_TYPE_MAT,
    FILE_VERSION,
    IDENTITY_MATRIX,
    MAT_FLAG_DEFAULT,
    MAT_FLAG_LIT,
    MAT_FLAG_TWO_SIDED,
    STRUCT_ENDIAN,
)


class TestByteOrder:
    """Tests for byte order constants."""

    def test_struct_endian_is_big(self) -> None:
        """Test that struct endian prefix is for big-endian."""
        assert STRUCT_ENDIAN == ">"


class TestFileTypes:
    """Tests for file type constants."""

    def test_file_header_type(self) -> None:
        """Test file header type value."""
        assert FILE_HEADER_TYPE == 0x12

    def test_file_type_act(self) -> None:
        """Test ACT file type identifier."""
        assert FILE_TYPE_ACT == 0x01

    def test_file_type_dat(self) -> None:
        """Test DAT file type identifier (FACE magic)."""
        assert FILE_TYPE_DAT == 0xFACE

    def test_file_type_mat(self) -> None:
        """Test MAT file type identifier."""
        assert FILE_TYPE_MAT == 0x05

    def test_file_version(self) -> None:
        """Test file version is always 2."""
        assert FILE_VERSION == 0x02


class TestRecordTypes:
    """Tests for record type constants."""

    def test_act_record_types(self) -> None:
        """Test ACT record type values match documentation."""
        assert ACT_RECORD_ACTOR_NAME == 0x23  # 35 decimal
        assert ACT_RECORD_TRANSFORM == 0x2B  # 43 decimal
        assert ACT_RECORD_BOUNDING_BOX == 0x32  # 50 decimal
        assert ACT_RECORD_HIERARCHY_START == 0x29  # 41 decimal
        assert ACT_RECORD_MODEL_NAME == 0x24  # 36 decimal
        assert ACT_RECORD_HIERARCHY_END == 0x2A  # 42 decimal

    def test_dat_record_types(self) -> None:
        """Test DAT record type values match documentation."""
        assert DAT_RECORD_MODEL_NAME == 0x36  # 54 decimal
        assert DAT_RECORD_VERTICES == 0x17  # 23 decimal
        assert DAT_RECORD_TEX_COORDS == 0x18  # 24 decimal
        assert DAT_RECORD_FACES == 0x35  # 53 decimal
        assert DAT_RECORD_MATERIAL_NAMES == 0x16  # 22 decimal


class TestMaterialFlags:
    """Tests for material flag constants."""

    def test_mat_flag_lit(self) -> None:
        """Test lit flag value."""
        assert MAT_FLAG_LIT == 0x00000001

    def test_mat_flag_two_sided(self) -> None:
        """Test two-sided flag value."""
        assert MAT_FLAG_TWO_SIDED == 0x00001000

    def test_mat_flag_default(self) -> None:
        """Test default flag value (lit + correct perspective)."""
        assert MAT_FLAG_DEFAULT == 0x00000021


class TestMatrixConstants:
    """Tests for matrix constants."""

    def test_identity_matrix_length(self) -> None:
        """Test identity matrix has 12 elements."""
        assert len(IDENTITY_MATRIX) == 12

    def test_identity_matrix_diagonal(self) -> None:
        """Test identity matrix has 1s on diagonal."""
        # Diagonal elements are at indices 0, 4, 8.
        assert IDENTITY_MATRIX[0] == 1.0  # Xx
        assert IDENTITY_MATRIX[4] == 1.0  # Yy
        assert IDENTITY_MATRIX[8] == 1.0  # Zz

    def test_identity_matrix_position(self) -> None:
        """Test identity matrix has zero position."""
        assert IDENTITY_MATRIX[9] == 0.0   # Px
        assert IDENTITY_MATRIX[10] == 0.0  # Py
        assert IDENTITY_MATRIX[11] == 0.0  # Pz
