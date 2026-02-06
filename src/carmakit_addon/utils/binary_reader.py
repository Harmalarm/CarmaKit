"""
Binary read utilities for CarmaKit.

This module provides low-level functions for reading binary data in the
big-endian format used by Carmageddon files.


"""

import struct
from typing import BinaryIO, List, Tuple

from ..constants import STRUCT_ENDIAN


def read_uint32(f: BinaryIO) -> int:
    """
    Read an unsigned 32-bit integer in big-endian format.

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: The unsigned 32-bit integer value.
    :rtype: int
    :raises struct.error: If not enough bytes are available.
    """
    data = f.read(4)
    if len(data) < 4:
        raise struct.error("Not enough bytes to read uint32")
    return struct.unpack(f"{STRUCT_ENDIAN}I", data)[0]


def read_int32(f: BinaryIO) -> int:
    """
    Read a signed 32-bit integer in big-endian format.

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: The signed 32-bit integer value.
    :rtype: int
    :raises struct.error: If not enough bytes are available.
    """
    data = f.read(4)
    if len(data) < 4:
        raise struct.error("Not enough bytes to read int32")
    return struct.unpack(f"{STRUCT_ENDIAN}i", data)[0]


def read_uint16(f: BinaryIO) -> int:
    """
    Read an unsigned 16-bit integer in big-endian format.

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: The unsigned 16-bit integer value.
    :rtype: int
    :raises struct.error: If not enough bytes are available.
    """
    data = f.read(2)
    if len(data) < 2:
        raise struct.error("Not enough bytes to read uint16")
    return struct.unpack(f"{STRUCT_ENDIAN}H", data)[0]


def read_int16(f: BinaryIO) -> int:
    """
    Read a signed 16-bit integer in big-endian format.

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: The signed 16-bit integer value.
    :rtype: int
    :raises struct.error: If not enough bytes are available.
    """
    data = f.read(2)
    if len(data) < 2:
        raise struct.error("Not enough bytes to read int16")
    return struct.unpack(f"{STRUCT_ENDIAN}h", data)[0]


def read_uint8(f: BinaryIO) -> int:
    """
    Read an unsigned 8-bit integer.

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: The unsigned 8-bit integer value.
    :rtype: int
    :raises struct.error: If not enough bytes are available.
    """
    data = f.read(1)
    if len(data) < 1:
        raise struct.error("Not enough bytes to read uint8")
    return struct.unpack("B", data)[0]


def read_float32(f: BinaryIO) -> float:
    """
    Read a 32-bit floating point number in big-endian format.

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: The floating point value.
    :rtype: float
    :raises struct.error: If not enough bytes are available.
    """
    data = f.read(4)
    if len(data) < 4:
        raise struct.error("Not enough bytes to read float32")
    return struct.unpack(f"{STRUCT_ENDIAN}f", data)[0]


def read_float32_array(f: BinaryIO, count: int) -> List[float]:
    """
    Read an array of 32-bit floating point numbers.

    :param f: Binary file handle.
    :type f: BinaryIO
    :param count: Number of floats to read.
    :type count: int
    :return: List of floating point values.
    :rtype: List[float]
    :raises struct.error: If not enough bytes are available.
    """
    size = count * 4
    data = f.read(size)
    if len(data) < size:
        raise struct.error(f"Not enough bytes to read {count} floats")
    return list(struct.unpack(f"{STRUCT_ENDIAN}{count}f", data))


def read_null_terminated_string(f: BinaryIO) -> str:
    """
    Read a null-terminated ASCII string.

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: The decoded string (without null terminator).
    :rtype: str
    """
    chars = []
    while True:
        byte = f.read(1)
        if not byte or byte == b'\x00':
            break
        chars.append(byte)
    return b''.join(chars).decode('ascii', errors='replace')


def read_fixed_string(f: BinaryIO, length: int) -> str:
    """
    Read a fixed-length string, stripping null bytes.

    :param f: Binary file handle.
    :type f: BinaryIO
    :param length: Number of bytes to read.
    :type length: int
    :return: The decoded string with trailing nulls removed.
    :rtype: str
    """
    data = f.read(length)
    return data.rstrip(b'\x00').decode('ascii', errors='replace')


def read_record_header(f: BinaryIO) -> Tuple[int, int]:
    """
    Read a record header (type and length).

    :param f: Binary file handle.
    :type f: BinaryIO
    :return: Tuple of (record_type, record_length).
    :rtype: Tuple[int, int]
    :raises struct.error: If not enough bytes are available.
    """
    record_type = read_uint32(f)
    record_length = read_uint32(f)
    return (record_type, record_length)