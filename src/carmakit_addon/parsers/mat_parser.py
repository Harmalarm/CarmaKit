"""
MAT file parser for Carmageddon material files.

This module contains the parser for reading MAT material files
in their native big-endian binary format.
"""

from typing import BinaryIO, Optional

from ..utils.binary_reader import BinaryReader
from ..constants import (
    FILE_TYPE_MAT,
    MAT_RECORD_IMAGE_NAME,
    MAT_RECORD_MATERIAL,
)
from ..classes.mat_classes import (
    Material,
    MatFile,
)
from .utils import ParseError, read_file_header


def parse_mat_file(filepath: str) -> MatFile:
    """
    Parse a MAT material file.

    """
    result = MatFile()

    with open(filepath, 'rb') as f:
        # Read and validate header.
        file_type, version = read_file_header(f)
        if file_type != FILE_TYPE_MAT:
            raise ParseError(
                f"Not a MAT file. Type: {hex(file_type)}"
            )

        # Parse materials until end of file.
        while True:
            material = _parse_mat_material(f)
            if material is None:
                break
            result.materials.append(material)

    return result


def _parse_mat_material(f: BinaryIO) -> Optional[Material]:
    """
    Parse a single material from a MAT file.

    """
    material = Material()

    while True:
        try:
            record_type, length = BinaryReader.read_record_header(f)
        except Exception:
            # End of file.
            return material if material.name else None

        # Null marker indicates end of material.
        if record_type == 0 and length == 0:
            return material if material.name else None

        if record_type == MAT_RECORD_MATERIAL:
            # Read material attributes.
            # Color (4 bytes RGBA).
            color_bytes = f.read(4)
            material.color = tuple(color_bytes)

            # Lighting values (4 floats).
            material.ambient = BinaryReader.read_float32(f)
            material.directional = BinaryReader.read_float32(f)
            material.specular = BinaryReader.read_float32(f)
            material.specular_power = BinaryReader.read_float32(f)

            # Flags (4 bytes).
            material.flags = BinaryReader.read_uint32(f)

            # UV transformation matrix (6 floats).
            uv_values = BinaryReader.read_float32_array(f, 6)
            material.uv_transform = tuple(uv_values)

            # Unknown bytes (4 bytes).
            _unknown = f.read(4)

            # Null padding (13 bytes).
            _padding = f.read(13)

            # Material name.
            material.name = BinaryReader.read_null_terminated_string(f)

        elif record_type == MAT_RECORD_IMAGE_NAME:
            # Read texture/image name.
            material.texture_name = BinaryReader.read_null_terminated_string(f)

        else:
            # Skip unknown record.
            f.read(length)
