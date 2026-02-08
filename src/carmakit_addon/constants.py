"""
Constants for CarmaKit Blender Addon.

This module contains all magic numbers, record types, and other constants
used throughout the addon for parsing and writing Carmageddon file formats.

All multi-byte values in Carmageddon files are stored in big-endian format.


"""

from typing import Final

# =============================================================================
# Byte Order
# =============================================================================

# Carmageddon files use big-endian byte order (network byte order).
BYTE_ORDER: Final[str] = "big"
STRUCT_ENDIAN: Final[str] = ">"  # Struct format prefix for big-endian.

# =============================================================================
# File Type Identifiers
# =============================================================================

# The first record type in all Carmageddon files (0x12 = 18 decimal).
FILE_HEADER_TYPE: Final[int] = 0x12

# File type identifiers (third word in file header).
FILE_TYPE_ACT: Final[int] = 0x01  # Actor file.
FILE_TYPE_DAT: Final[int] = 0xFACE  # Model/mesh file.
FILE_TYPE_MAT: Final[int] = 0x05  # Material file.
FILE_TYPE_PIX: Final[int] = 0x02  # Image/pixel file.

# Version number (fourth word in file header, always 2 for C1/C2).
FILE_VERSION: Final[int] = 0x02

# =============================================================================
# ACT Record Types (Actor Files)
# =============================================================================

ACT_RECORD_ACTOR_NAME: Final[int] = 0x23  # 35d - Actor name and attributes.
ACT_RECORD_TRANSFORM: Final[int] = 0x2B  # 43d - Transformation matrix.
ACT_RECORD_UNKNOWN: Final[int] = 0x25  # 37d - Unknown (no data).
ACT_RECORD_BOUNDING_BOX: Final[int] = 0x32  # 50d - Bounding box.
ACT_RECORD_HIERARCHY_START: Final[int] = 0x29  # 41d - Start hierarchy level.
ACT_RECORD_MATERIAL_NAMES: Final[int] = 0x26  # 38d - Material names.
ACT_RECORD_MODEL_NAME: Final[int] = 0x24  # 36d - Model name reference.
ACT_RECORD_HIERARCHY_END: Final[int] = 0x2A  # 42d - End hierarchy level.

# =============================================================================
# DAT Record Types (Model/Mesh Files)
# =============================================================================

DAT_RECORD_MODEL_NAME: Final[int] = 0x36  # 54d - Model name and attributes.
DAT_RECORD_VERTICES: Final[int] = 0x17  # 23d - Vertex data.
DAT_RECORD_TEX_COORDS: Final[int] = 0x18  # 24d - Texture coordinates.
DAT_RECORD_FACES: Final[int] = 0x35  # 53d - Face data.
DAT_RECORD_MATERIAL_NAMES: Final[int] = 0x16  # 22d - Material names list.
DAT_RECORD_FACE_MATERIALS: Final[int] = 0x1A  # 26d - Face material indices.

# =============================================================================
# MAT Record Types (Material Files)
# =============================================================================

MAT_RECORD_MATERIAL: Final[int] = 0x3C  # 60d - Material name and attributes.
MAT_RECORD_IMAGE_NAME: Final[int] = 0x1C  # 28d - Image/texture name.

# =============================================================================
# PIX Record Types (Image Files)
# =============================================================================

PIX_RECORD_IMAGE: Final[int] = 0x3D  # 61d - Image name and attributes.
PIX_RECORD_PIXELS: Final[int] = 0x21  # 33d - Pixel data.

# PIX image types.
PIX_TYPE_8BIT: Final[int] = 0x03  # 8-bit indexed image.
PIX_TYPE_16BIT: Final[int] = 0x05  # 16-bit normal image.
PIX_TYPE_16BIT_TRANSLUCENT: Final[int] = 0x12  # 16-bit translucent image.

# =============================================================================
# Material Flags
# =============================================================================

MAT_FLAG_LIT: Final[int] = 0x00000001
MAT_FLAG_PRELIT: Final[int] = 0x00000002
MAT_FLAG_SMOOTH: Final[int] = 0x00000004
MAT_FLAG_ENV_MAPPED: Final[int] = 0x00000018
MAT_FLAG_CORRECT_PERSPECTIVE: Final[int] = 0x00000020
MAT_FLAG_DECAL: Final[int] = 0x00000040
MAT_FLAG_IUV: Final[int] = 0x00000780
MAT_FLAG_ALWAYS_VISIBLE: Final[int] = 0x00000800
MAT_FLAG_TWO_SIDED: Final[int] = 0x00001000
MAT_FLAG_FORCE_FRONT: Final[int] = 0x00002000
MAT_FLAG_DITHER: Final[int] = 0x00004000
MAT_FLAG_MAP_MIP: Final[int] = 0x00070000
MAT_FLAG_FOG_LOCAL: Final[int] = 0x00080000
MAT_FLAG_SUBDIVIDE: Final[int] = 0x00100000
MAT_FLAG_Z_TRANSPARENCY: Final[int] = 0x00200000

# Default material flags used by Plaything.
MAT_FLAG_DEFAULT: Final[int] = 0x00000021

# =============================================================================
# Transformation Matrix Defaults
# =============================================================================

# Identity transformation matrix (3x3 rotation + 1x3 position).
IDENTITY_MATRIX: Final[tuple] = (
    1.0, 0.0, 0.0,  # Xx, Yx, Zx
    0.0, 1.0, 0.0,  # Xy, Yy, Zy
    0.0, 0.0, 1.0,  # Xz, Yz, Zz
    0.0, 0.0, 0.0,  # Px, Py, Pz (position)
)

# 2D identity matrix for material UV transform (2x2 rotation + 1x2 position).
IDENTITY_MATRIX_2D: Final[tuple] = (
    1.0, 0.0,  # Uu, Vu
    0.0, 1.0,  # Uv, Vv
    0.0, 0.0,  # Pu, Pv (position)
)

# =============================================================================
# Size Constants
# =============================================================================

# Record header size (type word + length word).
RECORD_HEADER_SIZE: Final[int] = 8

# File header data size (file type + version).
FILE_HEADER_DATA_SIZE: Final[int] = 8

# Transformation matrix size in bytes (12 floats * 4 bytes each).
TRANSFORM_MATRIX_SIZE: Final[int] = 48

# Bounding box size in bytes (6 floats * 4 bytes each).
BOUNDING_BOX_SIZE: Final[int] = 24

# Face data size (3 vertex indices of 2 bytes + 3 unknown bytes).
FACE_SIZE: Final[int] = 9

# Material attribute block size before name.
MATERIAL_ATTR_SIZE: Final[int] = 76

# Null marker size (8 null bytes to end records).
NULL_MARKER_SIZE: Final[int] = 8

# =============================================================================
# File Extensions
# =============================================================================

EXT_ACT: Final[str] = ".act"
EXT_DAT: Final[str] = ".dat"
EXT_MAT: Final[str] = ".mat"
EXT_PIX: Final[str] = ".pix"
EXT_SDF: Final[str] = ".sdf"
EXT_TWT: Final[str] = ".twt"

# =============================================================================
# Default Values
# =============================================================================

# Default material color (RGBA as bytes: white with full alpha).
DEFAULT_MATERIAL_COLOR: Final[bytes] = b'\xFF\xFF\xFF\xFF'

# Default lighting values (as hex from documentation).
DEFAULT_AMBIENT: Final[float] = 0.1  # 0x3DCCCCCD
DEFAULT_DIRECTIONAL: Final[float] = 0.7  # 0x3F333333
DEFAULT_SPECULAR: Final[float] = 0.0  # 0x00000000
DEFAULT_SPECULAR_POWER: Final[float] = 20.0  # 0x41A00000

# Default face unknown bytes (Plaything uses 0x00, 0x01, 0x00).
DEFAULT_FACE_FLAGS: Final[bytes] = b'\x00\x01\x00'

# =============================================================================
# Unit Conversion
# =============================================================================

# Carmageddon BRU (Brender Units) to meters scale factor.
BRU_SCALE_FACTOR: Final[float] = 6.9
