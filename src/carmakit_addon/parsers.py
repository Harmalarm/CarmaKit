"""
File format parsers for Carmageddon files.

This module contains parsers for reading DAT, ACT, and MAT files
in their native big-endian binary format.

:author: CarmaKit Team
"""

import os
from typing import BinaryIO, List, Optional, Tuple

from .binary_io import (
    read_float32,
    read_float32_array,
    read_null_terminated_string,
    read_record_header,
    read_uint16,
    read_uint32,
    read_uint8,
)
from .constants import (
    ACT_RECORD_ACTOR_NAME,
    ACT_RECORD_BOUNDING_BOX,
    ACT_RECORD_HIERARCHY_END,
    ACT_RECORD_HIERARCHY_START,
    ACT_RECORD_MATERIAL_NAMES,
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
    MAT_RECORD_IMAGE_NAME,
    MAT_RECORD_MATERIAL,
)
from .data_structures import (
    ActFile,
    ActorNode,
    BoundingBox,
    DatFile,
    DatModel,
    Face,
    Material,
    MatFile,
    TransformMatrix,
    Vector2,
    Vector3,
)


class ParseError(Exception):
    """Exception raised when parsing fails."""

    pass


def _read_file_header(f: BinaryIO) -> Tuple[int, int]:
    """
    Read and validate a file header.

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: Tuple of (file_type, version).
    :rtype: Tuple[int, int]
    :raises ParseError: If header is invalid.
    """
    record_type, length = read_record_header(f)
    if record_type != FILE_HEADER_TYPE:
        raise ParseError(
            f"Invalid file header type: {hex(record_type)}"
        )
    if length != 8:
        raise ParseError(f"Invalid header length: {length}")

    file_type = read_uint32(f)
    version = read_uint32(f)

    return (file_type, version)


# =============================================================================
# DAT File Parser
# =============================================================================


def parse_dat_file(filepath: str) -> DatFile:
    """
    Parse a DAT model file.

    :param filepath: Path to the DAT file.
    :type filepath: str
    :return: Parsed DAT file structure.
    :rtype: DatFile
    :raises ParseError: If parsing fails.
    :raises FileNotFoundError: If file does not exist.
    """
    result = DatFile()

    with open(filepath, 'rb') as f:
        # Read and validate header.
        file_type, version = _read_file_header(f)
        if file_type != FILE_TYPE_DAT:
            raise ParseError(
                f"Not a DAT file. Type: {hex(file_type)}"
            )

        # Parse models until end of file.
        while True:
            model = _parse_dat_model(f)
            if model is None:
                break
            result.models.append(model)

    return result


def _parse_dat_model(f: BinaryIO) -> Optional[DatModel]:
    """
    Parse a single model from a DAT file.

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: Parsed model or None if at end of file.
    :rtype: Optional[DatModel]
    """
    model = DatModel()
    face_material_indices: List[int] = []

    while True:
        try:
            record_type, length = read_record_header(f)
        except Exception:
            # End of file.
            return model if model.name else None

        # Null marker indicates end of model.
        if record_type == 0 and length == 0:
            # Apply material indices to faces.
            for i, face in enumerate(model.faces):
                if i < len(face_material_indices):
                    face.material_index = face_material_indices[i]
            return model if model.name else None

        if record_type == DAT_RECORD_MODEL_NAME:
            # Read model name and attributes.
            model.attributes = read_uint16(f)
            model.name = read_null_terminated_string(f)

        elif record_type == DAT_RECORD_VERTICES:
            # Read vertex positions.
            count = read_uint32(f)
            for _ in range(count):
                x = read_float32(f)
                y = read_float32(f)
                z = read_float32(f)
                model.vertices.append(Vector3(x, y, z))

        elif record_type == DAT_RECORD_TEX_COORDS:
            # Read texture coordinates.
            count = read_uint32(f)
            for _ in range(count):
                u = read_float32(f)
                v = read_float32(f)
                model.tex_coords.append(Vector2(u, v))

        elif record_type == DAT_RECORD_FACES:
            # Read face vertex indices.
            count = read_uint32(f)
            for _ in range(count):
                v1 = read_uint16(f)
                v2 = read_uint16(f)
                v3 = read_uint16(f)
                flags = f.read(3)
                model.faces.append(Face(v1, v2, v3, flags))

        elif record_type == DAT_RECORD_MATERIAL_NAMES:
            # Read material name list.
            count = read_uint32(f)
            for _ in range(count):
                name = read_null_terminated_string(f)
                model.materials.append(name)

        elif record_type == DAT_RECORD_FACE_MATERIALS:
            # Read face material indices.
            count = read_uint32(f)
            _unknown = read_uint32(f)  # Always 0x00000002.
            for _ in range(count):
                index = read_uint16(f)
                face_material_indices.append(index)

        else:
            # Skip unknown record.
            f.read(length)


# =============================================================================
# ACT File Parser
# =============================================================================


def parse_act_file(filepath: str) -> ActFile:
    """
    Parse an ACT actor file.

    :param filepath: Path to the ACT file.
    :type filepath: str
    :return: Parsed ACT file structure.
    :rtype: ActFile
    :raises ParseError: If parsing fails.
    :raises FileNotFoundError: If file does not exist.
    """
    result = ActFile()

    with open(filepath, 'rb') as f:
        # Read and validate header.
        file_type, version = _read_file_header(f)
        if file_type != FILE_TYPE_ACT:
            raise ParseError(
                f"Not an ACT file. Type: {hex(file_type)}"
            )

        # Parse all actors from the file into a flat list first.
        all_nodes: List[ActorNode] = []
        current_node: Optional[ActorNode] = None

        while True:
            try:
                record_type, length = read_record_header(f)
            except Exception:
                # End of file.
                if current_node and current_node.name:
                    all_nodes.append(current_node)
                break

            # Null marker - current node is complete.
            if record_type == 0 and length == 0:
                if current_node and current_node.name:
                    all_nodes.append(current_node)
                    current_node = None
                continue

            if record_type == ACT_RECORD_ACTOR_NAME:
                # New actor - save previous if exists.
                if current_node and current_node.name:
                    all_nodes.append(current_node)
                current_node = ActorNode()
                current_node.attributes = read_uint16(f)
                current_node.name = read_null_terminated_string(f)

            elif record_type == ACT_RECORD_TRANSFORM:
                if current_node:
                    values = read_float32_array(f, 12)
                    current_node.transform = TransformMatrix(tuple(values))

            elif record_type == ACT_RECORD_UNKNOWN:
                # Empty record, skip any data if present.
                if length > 0:
                    f.read(length)

            elif record_type == ACT_RECORD_BOUNDING_BOX:
                if current_node:
                    values = read_float32_array(f, 6)
                    current_node.bounding_box = BoundingBox(
                        Vector3(values[0], values[1], values[2]),
                        Vector3(values[3], values[4], values[5])
                    )

            elif record_type == ACT_RECORD_HIERARCHY_START:
                # Hierarchy markers are used for structure but we
                # parse flat and build hierarchy from names later.
                if length > 0:
                    f.read(length)

            elif record_type == ACT_RECORD_HIERARCHY_END:
                # End of a hierarchy section.
                if current_node and current_node.name:
                    all_nodes.append(current_node)
                    current_node = None
                if length > 0:
                    f.read(length)

            elif record_type == ACT_RECORD_MATERIAL_NAMES:
                # ACT material names record contains null-terminated strings
                # without a count prefix (unlike DAT format).
                if current_node and length > 0:
                    data = f.read(length)
                    # Split on null bytes and filter empty strings.
                    names = data.split(b'\x00')
                    for name_bytes in names:
                        if name_bytes:
                            name = name_bytes.decode('ascii', errors='replace')
                            current_node.materials.append(name)

            elif record_type == ACT_RECORD_MODEL_NAME:
                if current_node:
                    current_node.model_name = read_null_terminated_string(f)

            else:
                # Skip unknown record types.
                if length > 0:
                    f.read(length)

        # Build hierarchy: first node is root, others are children.
        if all_nodes:
            result.root = all_nodes[0]
            for node in all_nodes[1:]:
                result.root.children.append(node)

    return result


def parse_mat_file(filepath: str) -> MatFile:
    """
    Parse a MAT material file.

    :param filepath: Path to the MAT file.
    :type filepath: str
    :return: Parsed MAT file structure.
    :rtype: MatFile
    :raises ParseError: If parsing fails.
    :raises FileNotFoundError: If file does not exist.
    """
    result = MatFile()

    with open(filepath, 'rb') as f:
        # Read and validate header.
        file_type, version = _read_file_header(f)
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

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: Parsed material or None if at end of file.
    :rtype: Optional[Material]
    """
    material = Material()

    while True:
        try:
            record_type, length = read_record_header(f)
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
            material.ambient = read_float32(f)
            material.directional = read_float32(f)
            material.specular = read_float32(f)
            material.specular_power = read_float32(f)

            # Flags (4 bytes).
            material.flags = read_uint32(f)

            # UV transformation matrix (6 floats).
            uv_values = read_float32_array(f, 6)
            material.uv_transform = tuple(uv_values)

            # Unknown bytes (4 bytes).
            _unknown = f.read(4)

            # Null padding (13 bytes).
            _padding = f.read(13)

            # Material name.
            material.name = read_null_terminated_string(f)

        elif record_type == MAT_RECORD_IMAGE_NAME:
            # Read texture/image name.
            material.texture_name = read_null_terminated_string(f)

        else:
            # Skip unknown record.
            f.read(length)


def find_related_files(
    filepath: str
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Find related ACT, DAT, and MAT files for a given file.

    Given any of these file types, attempts to locate the other
    related files in the same directory.

    :param filepath: Path to any ACT, DAT, or MAT file.
    :type filepath: str
    :return: Tuple of (act_path, dat_path, mat_path).
    :rtype: Tuple[Optional[str], Optional[str], Optional[str]]
    """
    directory = os.path.dirname(filepath)
    base_name = os.path.splitext(os.path.basename(filepath))[0]

    act_path = None
    dat_path = None
    mat_path = None

    # Check for each file type.
    for ext in ['.act', '.ACT']:
        candidate = os.path.join(directory, base_name + ext)
        if os.path.exists(candidate):
            act_path = candidate
            break

    for ext in ['.dat', '.DAT']:
        candidate = os.path.join(directory, base_name + ext)
        if os.path.exists(candidate):
            dat_path = candidate
            break

    for ext in ['.mat', '.MAT']:
        candidate = os.path.join(directory, base_name + ext)
        if os.path.exists(candidate):
            mat_path = candidate
            break

    return (act_path, dat_path, mat_path)
