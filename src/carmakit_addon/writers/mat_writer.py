"""
MAT file writer for Carmageddon material files.

This module contains the writer for creating MAT material files
in their native big-endian binary format.
"""

from typing import BinaryIO

from ..utils.binary_writer import BinaryWriter
from ..constants import (
    FILE_TYPE_MAT,
    MAT_RECORD_IMAGE_NAME,
    MAT_RECORD_MATERIAL,
)
from ..classes.mat_classes import Material, MatFile
from .utils import write_file_header


def write_mat_file(
    filepath: str,
    mat_file: MatFile,
    game_version: str = 'C2'
) -> None:
    """
    Write a MAT material file.

    """
    with open(filepath, 'wb') as f:
        write_file_header(f, FILE_TYPE_MAT)

        for material in mat_file.materials:
            _write_mat_material(f, material, game_version)


def _write_mat_material(
    f: BinaryIO,
    material: Material,
    game_version: str
) -> None:
    """
    Write a single material to a MAT file.

    """
    # Calculate record length.
    material_name = _format_mat_name(material.name, game_version)
    name_bytes = material_name.encode('ascii') + b'\x00'
    # 4 (color) + 16 (lighting) + 4 (flags) + 24 (uv) + 4 (unknown) +
    # 13 (padding) + name
    record_length = 4 + 16 + 4 + 24 + 4 + 13 + len(name_bytes)

    BinaryWriter.write_record_header(
        f,
        MAT_RECORD_MATERIAL,
        record_length
    )

    # Write color.
    f.write(bytes(material.color))

    # Write lighting values.
    BinaryWriter.write_float32(f, material.ambient)
    BinaryWriter.write_float32(f, material.directional)
    BinaryWriter.write_float32(f, material.specular)
    BinaryWriter.write_float32(f, material.specular_power)

    # Write flags.
    BinaryWriter.write_uint32(f, material.flags)

    # Write UV transformation matrix.
    BinaryWriter.write_float32_array(
        f,
        list(material.uv_transform)
    )

    # Write unknown bytes (Plaything uses 0x0A1F0000).
    f.write(b'\x0A\x1F\x00\x00')

    # Write null padding.
    f.write(b'\x00' * 13)

    # Write material name.
    f.write(name_bytes)

    # Write texture name if present.
    if material.texture_name:
        texture_name = _format_pix_name(
            material.texture_name,
            game_version
        )
        tex_bytes = texture_name.encode('ascii') + b'\x00'
        BinaryWriter.write_record_header(
            f,
            MAT_RECORD_IMAGE_NAME,
            len(tex_bytes)
        )
        f.write(tex_bytes)

    # Write null marker to end material.
    BinaryWriter.write_null_marker(f)


def _format_mat_name(name: str, game_version: str) -> str:
    """
    Format the material name based on game version requirements.

    """
    if game_version != 'C1':
        return name

    if name.lower().endswith('.mat'):
        return name

    return f"{name}.MAT"


def _format_pix_name(name: str, game_version: str) -> str:
    """
    Format the texture name based on game version requirements.

    """
    if game_version != 'C1':
        return name

    if name.lower().endswith('.pix'):
        return name

    return f"{name}.PIX"
