"""
Binary read utilities for CarmaKit.

This module provides low-level functions for reading binary data in the
big-endian format used by Carmageddon files.

"""

import struct
from typing import BinaryIO, List, Tuple

from ..constants import STRUCT_ENDIAN


class BinaryReader:
    """
    Class wrapper for binary read utilities.
    """

    @staticmethod
    def read_uint32(f: BinaryIO) -> int:
        """
        Read an unsigned 32-bit integer in big-endian format.

        """
        data = f.read(4)
        if len(data) < 4:
            raise struct.error("Not enough bytes to read uint32")
        return struct.unpack(f"{STRUCT_ENDIAN}I", data)[0]

    @staticmethod
    def read_int32(f: BinaryIO) -> int:
        """
        Read a signed 32-bit integer in big-endian format.

        """
        data = f.read(4)
        if len(data) < 4:
            raise struct.error("Not enough bytes to read int32")
        return struct.unpack(f"{STRUCT_ENDIAN}i", data)[0]

    @staticmethod
    def read_uint16(f: BinaryIO) -> int:
        """
        Read an unsigned 16-bit integer in big-endian format.

        """
        data = f.read(2)
        if len(data) < 2:
            raise struct.error("Not enough bytes to read uint16")
        return struct.unpack(f"{STRUCT_ENDIAN}H", data)[0]

    @staticmethod
    def read_int16(f: BinaryIO) -> int:
        """
        Read a signed 16-bit integer in big-endian format.

        """
        data = f.read(2)
        if len(data) < 2:
            raise struct.error("Not enough bytes to read int16")
        return struct.unpack(f"{STRUCT_ENDIAN}h", data)[0]

    @staticmethod
    def read_uint8(f: BinaryIO) -> int:
        """
        Read an unsigned 8-bit integer.

        """
        data = f.read(1)
        if len(data) < 1:
            raise struct.error("Not enough bytes to read uint8")
        return struct.unpack("B", data)[0]

    @staticmethod
    def read_float32(f: BinaryIO) -> float:
        """
        Read a 32-bit floating point number in big-endian format.

        """
        data = f.read(4)
        if len(data) < 4:
            raise struct.error("Not enough bytes to read float32")
        return struct.unpack(f"{STRUCT_ENDIAN}f", data)[0]

    @staticmethod
    def read_float32_array(f: BinaryIO, count: int) -> List[float]:
        """
        Read an array of 32-bit floating point numbers.

        """
        size = count * 4
        data = f.read(size)
        if len(data) < size:
            raise struct.error(
                f"Not enough bytes to read {count} floats"
            )
        return list(struct.unpack(f"{STRUCT_ENDIAN}{count}f", data))

    @staticmethod
    def read_null_terminated_string(f: BinaryIO) -> str:
        """
        Read a null-terminated ASCII string.

        """
        chars = []
        while True:
            byte = f.read(1)
            if not byte or byte == b'\x00':
                break
            chars.append(byte)
        return b''.join(chars).decode('ascii', errors='replace')

    @staticmethod
    def read_fixed_string(f: BinaryIO, length: int) -> str:
        """
        Read a fixed-length string, stripping null bytes.

        """
        data = f.read(length)
        return data.rstrip(b'\x00').decode('ascii', errors='replace')

    @staticmethod
    def read_record_header(f: BinaryIO) -> Tuple[int, int]:
        """
        Read a record header (type and length).

        """
        record_type = BinaryReader.read_uint32(f)
        record_length = BinaryReader.read_uint32(f)
        return (record_type, record_length)