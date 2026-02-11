"""
Binary write utilities for CarmaKit.

This module provides low-level functions for writing binary data in the
big-endian format used by Carmageddon files.

"""

import struct
from typing import BinaryIO, List

from ..constants import STRUCT_ENDIAN


class BinaryWriter:
    """
    Class wrapper for binary write utilities.
    """

    @staticmethod
    def write_uint32(f: BinaryIO, value: int) -> None:
        """
        Write an unsigned 32-bit integer in big-endian format.

        """
        f.write(struct.pack(f"{STRUCT_ENDIAN}I", value))

    @staticmethod
    def write_int32(f: BinaryIO, value: int) -> None:
        """
        Write a signed 32-bit integer in big-endian format.

        """
        f.write(struct.pack(f"{STRUCT_ENDIAN}i", value))

    @staticmethod
    def write_uint16(f: BinaryIO, value: int) -> None:
        """
        Write an unsigned 16-bit integer in big-endian format.

        """
        f.write(struct.pack(f"{STRUCT_ENDIAN}H", value))

    @staticmethod
    def write_int16(f: BinaryIO, value: int) -> None:
        """
        Write a signed 16-bit integer in big-endian format.

        """
        f.write(struct.pack(f"{STRUCT_ENDIAN}h", value))

    @staticmethod
    def write_uint8(f: BinaryIO, value: int) -> None:
        """
        Write an unsigned 8-bit integer.

        """
        f.write(struct.pack("B", value))

    @staticmethod
    def write_float32(f: BinaryIO, value: float) -> None:
        """
        Write a 32-bit floating point number in big-endian format.

        """
        f.write(struct.pack(f"{STRUCT_ENDIAN}f", value))

    @staticmethod
    def write_float32_array(f: BinaryIO, values: List[float]) -> None:
        """
        Write an array of 32-bit floating point numbers.

        """
        count = len(values)
        f.write(struct.pack(f"{STRUCT_ENDIAN}{count}f", *values))

    @staticmethod
    def write_null_terminated_string(f: BinaryIO, value: str) -> None:
        """
        Write a null-terminated ASCII string.

        """
        f.write(value.encode('ascii'))
        f.write(b'\x00')

    @staticmethod
    def write_record_header(
        f: BinaryIO,
        record_type: int,
        length: int
    ) -> None:
        """
        Write a record header (type and length).

        """
        BinaryWriter.write_uint32(f, record_type)
        BinaryWriter.write_uint32(f, length)

    @staticmethod
    def write_null_marker(f: BinaryIO) -> None:
        """
        Write an 8-byte null marker to end a record.

        """
        f.write(b'\x00' * 8)