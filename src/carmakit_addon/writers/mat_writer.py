"""
MAT file writer for Carmageddon material files.

This module contains the writer for creating MAT material files
in their native big-endian binary format.
"""

from typing import BinaryIO

from ..utils.binary_writer import (
    write_float32,
    write_float32_array,
    write_null_marker,
    write_record_header,
    write_uint32,
)
from ..constants import (
    FILE_TYPE_MAT,
    MAT_RECORD_IMAGE_NAME,
    MAT_RECORD_MATERIAL,
)
from ..classes.mat_classes import Material, MatFile
from .utils import write_file_header


def write_mat_file(filepath: str, mat_file: MatFile) -> None:
    """
    Write a MAT material file.

    :param filepath: Path to the output MAT file.
    :type filepath: str
    :param mat_file: The MAT file structure to write.
    :type mat_file: MatFile
    :return: None.
    :rtype: None
    """
    with open(filepath, 'wb') as f:
        write_file_header(f, FILE_TYPE_MAT)

        for material in mat_file.materials:
            _write_mat_material(f, material)


def _write_mat_material(f: BinaryIO, material: Material) -> None:
    """
    Write a single material to a MAT file.

    :param f: Binary file handle.
    :type f: BinaryIO
    :param material: The material to write.
    :type material: Material
    :return: None.
    :rtype: None
    """
    # Calculate record length.
    name_bytes = material.name.encode('ascii') + b'\x00'
    # 4 (color) + 16 (lighting) + 4 (flags) + 24 (uv) + 4 (unknown) +
    # 13 (padding) + name
    record_length = 4 + 16 + 4 + 24 + 4 + 13 + len(name_bytes)

    write_record_header(f, MAT_RECORD_MATERIAL, record_length)

    # Write color.
    f.write(bytes(material.color))

    # Write lighting values.
    write_float32(f, material.ambient)
    write_float32(f, material.directional)
    write_float32(f, material.specular)
    write_float32(f, material.specular_power)

    # Write flags.
    write_uint32(f, material.flags)

    # Write UV transformation matrix.
    write_float32_array(f, list(material.uv_transform))

    # Write unknown bytes (Plaything uses 0x0A1F0000).
    f.write(b'\x0A\x1F\x00\x00')

    # Write null padding.
    f.write(b'\x00' * 13)

    # Write material name.
    f.write(name_bytes)

    # Write texture name if present.
    if material.texture_name:
        tex_bytes = material.texture_name.encode('ascii') + b'\x00'
        write_record_header(f, MAT_RECORD_IMAGE_NAME, len(tex_bytes))
        f.write(tex_bytes)

    # Write null marker to end material.
    write_null_marker(f)
