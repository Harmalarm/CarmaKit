"""
Common parser utilities for Carmageddon file parsers.

This module contains shared utilities used by all file parsers.
"""
import os
from typing import BinaryIO, Tuple, Optional

from ..utils.binary_reader import BinaryReader
from ..constants import FILE_HEADER_TYPE


class ParseError(Exception):
    """Exception raised when parsing fails."""
    pass


def read_file_header(f: BinaryIO) -> Tuple[int, int]:
    """
    Read and validate a file header.

    """
    record_type, length = BinaryReader.read_record_header(f)
    if record_type != FILE_HEADER_TYPE:
        raise ParseError(
            f"Invalid file header type: {hex(record_type)}"
        )
    if length != 8:
        raise ParseError(f"Invalid header length: {length}")

    file_type = BinaryReader.read_uint32(f)
    version = BinaryReader.read_uint32(f)

    return (file_type, version)

def find_related_files(
    filepath: str
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Find related ACT, DAT, and MAT files for a given file.

    Given any of these file types, attempts to locate the other
    related files in the same directory.

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