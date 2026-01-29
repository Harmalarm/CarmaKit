"""
File format writers for Carmageddon files.

This module contains writers for creating DAT, ACT, and MAT files
in their native big-endian binary format.

:author: CarmaKit Team
"""

import os
from typing import BinaryIO, List

from .binary_io import (
    write_float32,
    write_float32_array,
    write_null_marker,
    write_null_terminated_string,
    write_record_header,
    write_uint16,
    write_uint32,
)
from .constants import (
    ACT_RECORD_ACTOR_NAME,
    ACT_RECORD_BOUNDING_BOX,
    ACT_RECORD_HIERARCHY_END,
    ACT_RECORD_HIERARCHY_START,
    ACT_RECORD_MODEL_NAME,
    ACT_RECORD_TRANSFORM,
    ACT_RECORD_UNKNOWN,
    DAT_RECORD_FACES,
    DAT_RECORD_FACE_MATERIALS,
    DAT_RECORD_MATERIAL_NAMES,
    DAT_RECORD_MODEL_NAME,
    DAT_RECORD_TEX_COORDS,
    DAT_RECORD_VERTICES,
    FILE_HEADER_TYPE,
    FILE_TYPE_ACT,
    FILE_TYPE_DAT,
    FILE_TYPE_MAT,
    FILE_VERSION,
    MAT_RECORD_IMAGE_NAME,
    MAT_RECORD_MATERIAL,
)
from .data_structures import (
    ActFile,
    ActorNode,
    DatFile,
    DatModel,
    Material,
    MatFile,
)


def _write_file_header(f: BinaryIO, file_type: int) -> None:
    """
    Write a file header.

    :param f: Binary file handle.
    :type f: BinaryIO
    :param file_type: The file type identifier.
    :type file_type: int
    :return: None.
    :rtype: None
    """
    write_record_header(f, FILE_HEADER_TYPE, 8)
    write_uint32(f, file_type)
    write_uint32(f, FILE_VERSION)


# =============================================================================
# DAT File Writer
# =============================================================================


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
        _write_file_header(f, FILE_TYPE_DAT)

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


# =============================================================================
# ACT File Writer
# =============================================================================


def write_act_file(filepath: str, act_file: ActFile) -> None:
    """
    Write an ACT actor file.

    :param filepath: Path to the output ACT file.
    :type filepath: str
    :param act_file: The ACT file structure to write.
    :type act_file: ActFile
    :return: None.
    :rtype: None
    """
    with open(filepath, 'wb') as f:
        _write_file_header(f, FILE_TYPE_ACT)

        if act_file.root:
            _write_act_node(f, act_file.root)

        # Write final null marker.
        write_null_marker(f)


def _write_act_node(f: BinaryIO, node: ActorNode) -> None:
    """
    Write an actor node and its children to an ACT file.

    :param f: Binary file handle.
    :type f: BinaryIO
    :param node: The actor node to write.
    :type node: ActorNode
    :return: None.
    :rtype: None
    """
    # Write actor name and attributes.
    name_bytes = node.name.encode('ascii') + b'\x00'
    record_length = 2 + len(name_bytes)
    write_record_header(f, ACT_RECORD_ACTOR_NAME, record_length)
    write_uint16(f, node.attributes)
    f.write(name_bytes)

    # Write transformation matrix.
    write_record_header(f, ACT_RECORD_TRANSFORM, 48)
    write_float32_array(f, list(node.transform.values))

    # Write unknown empty record (required by Plaything).
    write_record_header(f, ACT_RECORD_UNKNOWN, 0)

    # Write bounding box if present.
    if node.bounding_box:
        write_record_header(f, ACT_RECORD_BOUNDING_BOX, 24)
        bb = node.bounding_box
        write_float32_array(f, [
            bb.min_point.x, bb.min_point.y, bb.min_point.z,
            bb.max_point.x, bb.max_point.y, bb.max_point.z,
        ])

    # Write children.
    if node.children or node.model_name:
        write_record_header(f, ACT_RECORD_HIERARCHY_START, 0)

        # Write model name if present.
        if node.model_name:
            name_bytes = node.model_name.encode('ascii') + b'\x00'
            write_record_header(f, ACT_RECORD_MODEL_NAME, len(name_bytes))
            f.write(name_bytes)

        # Write child nodes recursively.
        for child in node.children:
            _write_act_node(f, child)

        write_record_header(f, ACT_RECORD_HIERARCHY_END, 0)


# =============================================================================
# MAT File Writer
# =============================================================================


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
        _write_file_header(f, FILE_TYPE_MAT)

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


def write_sdf_file(filepath: str) -> None:
    """
    Write an empty SDF file for Plaything compatibility.

    SDF files are empty marker files that enable editing in Plaything.

    :param filepath: Path to the output SDF file.
    :type filepath: str
    :return: None.
    :rtype: None
    """
    # Create an empty file.
    with open(filepath, 'wb') as f:
        pass
