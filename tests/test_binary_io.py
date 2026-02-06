"""
Tests for the binary I/O utility functions.

:author: CarmaKit Team
"""

import io
import struct
import pytest

from carmakit_addon.utils.binary_reader import (
    read_float32,
    read_float32_array,
    read_int16,
    read_int32,
    read_null_terminated_string,
    read_record_header,
    read_uint16,
    read_uint32,
    read_uint8,
)
from carmakit_addon.utils.binary_writer import (
    write_float32,
    write_float32_array,
    write_int16,
    write_int32,
    write_null_marker,
    write_null_terminated_string,
    write_record_header,
    write_uint16,
    write_uint32,
    write_uint8,
)
from carmakit_addon.constants import STRUCT_ENDIAN


class TestReadFunctions:
    """Tests for binary read functions."""

    def test_read_uint32(self) -> None:
        """Test reading unsigned 32-bit integers in big-endian format."""
        # 0x12345678 in big-endian.
        data = b'\x12\x34\x56\x78'
        f = io.BytesIO(data)
        result = read_uint32(f)
        assert result == 0x12345678

    def test_read_int32_positive(self) -> None:
        """Test reading positive signed 32-bit integers."""
        data = b'\x00\x00\x00\x7F'  # 127
        f = io.BytesIO(data)
        result = read_int32(f)
        assert result == 127

    def test_read_int32_negative(self) -> None:
        """Test reading negative signed 32-bit integers."""
        data = b'\xFF\xFF\xFF\xFF'  # -1
        f = io.BytesIO(data)
        result = read_int32(f)
        assert result == -1

    def test_read_uint16(self) -> None:
        """Test reading unsigned 16-bit integers in big-endian format."""
        data = b'\x12\x34'
        f = io.BytesIO(data)
        result = read_uint16(f)
        assert result == 0x1234

    def test_read_int16_positive(self) -> None:
        """Test reading positive signed 16-bit integers."""
        data = b'\x00\x7F'  # 127
        f = io.BytesIO(data)
        result = read_int16(f)
        assert result == 127

    def test_read_int16_negative(self) -> None:
        """Test reading negative signed 16-bit integers."""
        data = b'\xFF\xFF'  # -1
        f = io.BytesIO(data)
        result = read_int16(f)
        assert result == -1

    def test_read_uint8(self) -> None:
        """Test reading unsigned 8-bit integers."""
        data = b'\xAB'
        f = io.BytesIO(data)
        result = read_uint8(f)
        assert result == 0xAB

    def test_read_float32(self) -> None:
        """Test reading 32-bit floats in big-endian format."""
        # 1.0 in IEEE 754 big-endian.
        data = b'\x3F\x80\x00\x00'
        f = io.BytesIO(data)
        result = read_float32(f)
        assert result == pytest.approx(1.0)

    def test_read_float32_negative(self) -> None:
        """Test reading negative 32-bit floats."""
        # -1.0 in IEEE 754 big-endian.
        data = b'\xBF\x80\x00\x00'
        f = io.BytesIO(data)
        result = read_float32(f)
        assert result == pytest.approx(-1.0)

    def test_read_float32_array(self) -> None:
        """Test reading an array of floats."""
        # 1.0, 2.0, 3.0 in big-endian.
        data = b'\x3F\x80\x00\x00\x40\x00\x00\x00\x40\x40\x00\x00'
        f = io.BytesIO(data)
        result = read_float32_array(f, 3)
        assert len(result) == 3
        assert result[0] == pytest.approx(1.0)
        assert result[1] == pytest.approx(2.0)
        assert result[2] == pytest.approx(3.0)

    def test_read_null_terminated_string(self) -> None:
        """Test reading null-terminated ASCII strings."""
        data = b'Hello\x00World'
        f = io.BytesIO(data)
        result = read_null_terminated_string(f)
        assert result == "Hello"

    def test_read_null_terminated_string_at_eof(self) -> None:
        """Test reading string that ends at EOF without null."""
        data = b'Hello'
        f = io.BytesIO(data)
        result = read_null_terminated_string(f)
        assert result == "Hello"

    def test_read_record_header(self) -> None:
        """Test reading a record header (type + length)."""
        # Type 0x12, Length 8.
        data = b'\x00\x00\x00\x12\x00\x00\x00\x08'
        f = io.BytesIO(data)
        record_type, length = read_record_header(f)
        assert record_type == 0x12
        assert length == 8


class TestWriteFunctions:
    """Tests for binary write functions."""

    def test_write_uint32(self) -> None:
        """Test writing unsigned 32-bit integers in big-endian format."""
        f = io.BytesIO()
        write_uint32(f, 0x12345678)
        assert f.getvalue() == b'\x12\x34\x56\x78'

    def test_write_int32_positive(self) -> None:
        """Test writing positive signed 32-bit integers."""
        f = io.BytesIO()
        write_int32(f, 127)
        assert f.getvalue() == b'\x00\x00\x00\x7F'

    def test_write_int32_negative(self) -> None:
        """Test writing negative signed 32-bit integers."""
        f = io.BytesIO()
        write_int32(f, -1)
        assert f.getvalue() == b'\xFF\xFF\xFF\xFF'

    def test_write_uint16(self) -> None:
        """Test writing unsigned 16-bit integers in big-endian format."""
        f = io.BytesIO()
        write_uint16(f, 0x1234)
        assert f.getvalue() == b'\x12\x34'

    def test_write_int16_positive(self) -> None:
        """Test writing positive signed 16-bit integers."""
        f = io.BytesIO()
        write_int16(f, 127)
        assert f.getvalue() == b'\x00\x7F'

    def test_write_int16_negative(self) -> None:
        """Test writing negative signed 16-bit integers."""
        f = io.BytesIO()
        write_int16(f, -1)
        assert f.getvalue() == b'\xFF\xFF'

    def test_write_uint8(self) -> None:
        """Test writing unsigned 8-bit integers."""
        f = io.BytesIO()
        write_uint8(f, 0xAB)
        assert f.getvalue() == b'\xAB'

    def test_write_float32(self) -> None:
        """Test writing 32-bit floats in big-endian format."""
        f = io.BytesIO()
        write_float32(f, 1.0)
        assert f.getvalue() == b'\x3F\x80\x00\x00'

    def test_write_float32_array(self) -> None:
        """Test writing an array of floats."""
        f = io.BytesIO()
        write_float32_array(f, [1.0, 2.0, 3.0])
        expected = b'\x3F\x80\x00\x00\x40\x00\x00\x00\x40\x40\x00\x00'
        assert f.getvalue() == expected

    def test_write_null_terminated_string(self) -> None:
        """Test writing null-terminated ASCII strings."""
        f = io.BytesIO()
        write_null_terminated_string(f, "Hello")
        assert f.getvalue() == b'Hello\x00'

    def test_write_record_header(self) -> None:
        """Test writing a record header."""
        f = io.BytesIO()
        write_record_header(f, 0x12, 8)
        assert f.getvalue() == b'\x00\x00\x00\x12\x00\x00\x00\x08'

    def test_write_null_marker(self) -> None:
        """Test writing the null marker (8 zero bytes)."""
        f = io.BytesIO()
        write_null_marker(f)
        assert f.getvalue() == b'\x00' * 8


class TestRoundTrip:
    """Tests for read/write round-trip consistency."""

    def test_uint32_round_trip(self) -> None:
        """Test that uint32 survives a write/read cycle."""
        value = 0xDEADBEEF
        f = io.BytesIO()
        write_uint32(f, value)
        f.seek(0)
        result = read_uint32(f)
        assert result == value

    def test_float32_round_trip(self) -> None:
        """Test that float32 survives a write/read cycle."""
        value = 3.14159
        f = io.BytesIO()
        write_float32(f, value)
        f.seek(0)
        result = read_float32(f)
        assert result == pytest.approx(value, rel=1e-6)

    def test_string_round_trip(self) -> None:
        """Test that strings survive a write/read cycle."""
        value = "TestModel"
        f = io.BytesIO()
        write_null_terminated_string(f, value)
        f.seek(0)
        result = read_null_terminated_string(f)
        assert result == value
