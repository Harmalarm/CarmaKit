"""
DAT file parser for Carmageddon model files.

This module contains the parser for reading DAT model files
in their native big-endian binary format.
"""

from typing import BinaryIO, List, Optional

from ..utils.binary_reader import BinaryReader
from ..constants import (
    DAT_RECORD_FACES,
    DAT_RECORD_FACE_MATERIALS,
    DAT_RECORD_MATERIAL_NAMES,
    DAT_RECORD_MODEL_NAME,
    DAT_RECORD_TEX_COORDS,
    DAT_RECORD_VERTICES,
    FILE_TYPE_DAT,
)
from ..classes.shared_classes import (
    Vector2,
    Vector3,
)
from ..classes.dat_classes import (
    DatFile,
    DatModel,
    Face,
)

from .utils import ParseError, read_file_header


def parse_dat_file(filepath: str) -> DatFile:
    """
    Parse a DAT model file.

    """
    result = DatFile()

    with open(filepath, 'rb') as f:
        # Read and validate header.
        file_type, version = read_file_header(f)
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

    """
    model = DatModel()
    face_material_indices: List[int] = []

    while True:
        try:
            record_type, length = BinaryReader.read_record_header(f)
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
            model.attributes = BinaryReader.read_uint16(f)
            model.name = BinaryReader.read_null_terminated_string(f)

        elif record_type == DAT_RECORD_VERTICES:
            # Read vertex positions.
            count = BinaryReader.read_uint32(f)
            for _ in range(count):
                x = BinaryReader.read_float32(f)
                y = BinaryReader.read_float32(f)
                z = BinaryReader.read_float32(f)
                model.vertices.append(Vector3(x, y, z))

        elif record_type == DAT_RECORD_TEX_COORDS:
            # Read texture coordinates.
            count = BinaryReader.read_uint32(f)
            for _ in range(count):
                u = BinaryReader.read_float32(f)
                v = BinaryReader.read_float32(f)
                model.tex_coords.append(Vector2(u, v))

        elif record_type == DAT_RECORD_FACES:
            # Read face vertex indices.
            count = BinaryReader.read_uint32(f)
            for _ in range(count):
                v1 = BinaryReader.read_uint16(f)
                v2 = BinaryReader.read_uint16(f)
                v3 = BinaryReader.read_uint16(f)
                flags = f.read(3)
                model.faces.append(Face(v1, v2, v3, flags))

        elif record_type == DAT_RECORD_MATERIAL_NAMES:
            # Read material name list.
            count = BinaryReader.read_uint32(f)
            for _ in range(count):
                name = BinaryReader.read_null_terminated_string(f)
                model.materials.append(name)

        elif record_type == DAT_RECORD_FACE_MATERIALS:
            # Read face material indices.
            count = BinaryReader.read_uint32(f)
            _unknown = BinaryReader.read_uint32(f)  # Always 0x00000002.
            for _ in range(count):
                index = BinaryReader.read_uint16(f)
                face_material_indices.append(index)

        else:
            # Skip unknown record.
            f.read(length)
