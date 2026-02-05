"""
DAT file writer for Carmageddon model files.

This module contains the writer for creating DAT model files
in their native big-endian binary format.
"""

from typing import BinaryIO, List

from ..utils.binary_writer import (
    write_float32,
    write_null_marker,
    write_null_terminated_string,
    write_record_header,
    write_uint16,
    write_uint32,
)
from ..constants import (
    DAT_RECORD_FACES,
    DAT_RECORD_FACE_MATERIALS,
    DAT_RECORD_MATERIAL_NAMES,
    DAT_RECORD_MODEL_NAME,
    DAT_RECORD_TEX_COORDS,
    DAT_RECORD_VERTICES,
    FILE_TYPE_DAT,
)
from ..classes.dat_classes import DatFile, DatModel
from .utils import write_file_header


def write_dat_file(filepath: str, dat_file: DatFile) -> None:
    """
    Write a DAT model file.

    :param filepath: Path to the output DAT file.
    :type filepath: str
    :param dat_file: The DAT file structure to write.
    :type dat_file: DatFile
    :return: None.
    :rtype: None
    """
    with open(filepath, 'wb') as f:
        write_file_header(f, FILE_TYPE_DAT)

        for model in dat_file.models:
            _write_dat_model(f, model)


def _write_dat_model(f: BinaryIO, model: DatModel) -> None:
    """
    Write a single model to a DAT file.

    :param f: Binary file handle.
    :type f: BinaryIO
    :param model: The model to write.
    :type model: DatModel
    :return: None.
    :rtype: None
    """
    # Write model name and attributes.
    name_bytes = model.name.encode('ascii') + b'\x00'
    record_length = 2 + len(name_bytes)
    write_record_header(f, DAT_RECORD_MODEL_NAME, record_length)
    write_uint16(f, model.attributes)
    f.write(name_bytes)

    # Write vertices.
    if model.vertices:
        vertex_count = len(model.vertices)
        record_length = 4 + (vertex_count * 12)  # 3 floats per vertex.
        write_record_header(f, DAT_RECORD_VERTICES, record_length)
        write_uint32(f, vertex_count)
        for vertex in model.vertices:
            write_float32(f, vertex.x)
            write_float32(f, vertex.y)
            write_float32(f, vertex.z)

    # Write texture coordinates.
    if model.tex_coords:
        tex_count = len(model.tex_coords)
        record_length = 4 + (tex_count * 8)  # 2 floats per coord.
        write_record_header(f, DAT_RECORD_TEX_COORDS, record_length)
        write_uint32(f, tex_count)
        for tc in model.tex_coords:
            write_float32(f, tc.u)
            write_float32(f, tc.v)

    # Write faces.
    if model.faces:
        face_count = len(model.faces)
        record_length = 4 + (face_count * 9)  # 3 uint16 + 3 bytes per face.
        write_record_header(f, DAT_RECORD_FACES, record_length)
        write_uint32(f, face_count)
        for face in model.faces:
            write_uint16(f, face.v1)
            write_uint16(f, face.v2)
            write_uint16(f, face.v3)
            f.write(face.flags)

    # Write material names.
    if model.materials:
        mat_count = len(model.materials)
        # Calculate total length of material names.
        names_length = sum(
            len(name.encode('ascii')) + 1 for name in model.materials
        )
        record_length = 4 + names_length
        write_record_header(f, DAT_RECORD_MATERIAL_NAMES, record_length)
        write_uint32(f, mat_count)
        for name in model.materials:
            write_null_terminated_string(f, name)

    # Write face materials.
    if model.faces:
        face_count = len(model.faces)
        record_length = 4 + 4 + (face_count * 2)
        write_record_header(f, DAT_RECORD_FACE_MATERIALS, record_length)
        write_uint32(f, face_count)
        write_uint32(f, 0x00000002)  # Unknown constant.
        for face in model.faces:
            write_uint16(f, face.material_index)

    # Write null marker to end model.
    write_null_marker(f)
