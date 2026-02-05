"""
Common writer utilities for Carmageddon file writers.

This module contains shared helpers used by all file writers.
"""

from typing import BinaryIO

from ..utils.binary_writer import write_record_header, write_uint32
from ..constants import FILE_HEADER_TYPE, FILE_VERSION


def write_file_header(f: BinaryIO, file_type: int) -> None:
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
