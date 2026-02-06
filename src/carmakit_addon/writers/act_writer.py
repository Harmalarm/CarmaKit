"""
ACT file writer for Carmageddon actor files.

This module contains the writer for creating ACT actor hierarchy files
in their native big-endian binary format.
"""

from typing import BinaryIO

from ..utils.binary_writer import (
    write_float32_array,
    write_null_marker,
    write_record_header,
    write_uint16,
)
from ..constants import (
    ACT_RECORD_ACTOR_NAME,
    ACT_RECORD_BOUNDING_BOX,
    ACT_RECORD_HIERARCHY_END,
    ACT_RECORD_HIERARCHY_START,
    ACT_RECORD_MODEL_NAME,
    ACT_RECORD_TRANSFORM,
    ACT_RECORD_UNKNOWN,
    FILE_TYPE_ACT,
)
from ..classes.act_classes import ActFile, ActorNode
from .utils import write_file_header


def write_act_file(
    filepath: str,
    act_file: ActFile,
    legacy_hierarchy: bool = False
) -> None:
    """
    Write an ACT actor file.

    :param filepath: Path to the output ACT file.
    :type filepath: str
    :param act_file: The ACT file structure to write.
    :type act_file: ActFile
    :param legacy_hierarchy: Use legacy hierarchy markers without 0x29.
    :type legacy_hierarchy: bool
    :return: None.
    :rtype: None
    """
    with open(filepath, 'wb') as f:
        write_file_header(f, FILE_TYPE_ACT)

        if act_file.root:
            _write_act_node(
                f,
                act_file.root,
                legacy_hierarchy=legacy_hierarchy,
                is_root=True
            )

        # Write final null marker.
        write_null_marker(f)


def _write_act_node(
    f: BinaryIO,
    node: ActorNode,
    legacy_hierarchy: bool,
    is_root: bool = False
) -> None:
    """
    Write an actor node and its children to an ACT file.

    :param f: Binary file handle.
    :type f: BinaryIO
    :param node: The actor node to write.
    :type node: ActorNode
    :param legacy_hierarchy: Use legacy hierarchy markers without 0x29.
    :type legacy_hierarchy: bool
    :param is_root: Whether this node is the root of the ACT file.
    :type is_root: bool
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

    # Write model name if present.
    if node.model_name:
        name_bytes = node.model_name.encode('ascii') + b'\x00'
        write_record_header(f, ACT_RECORD_MODEL_NAME, len(name_bytes))
        f.write(name_bytes)

    # Write children if present.
    if legacy_hierarchy:
        # Legacy ACT files omit hierarchy start markers. Each non-root
        # node is followed by a hierarchy end marker to pop to parent.
        for child in node.children:
            _write_act_node(
                f,
                child,
                legacy_hierarchy=legacy_hierarchy,
                is_root=False
            )

        if not is_root:
            write_record_header(f, ACT_RECORD_HIERARCHY_END, 0)
    elif node.children:
        write_record_header(f, ACT_RECORD_HIERARCHY_START, 0)

        # Write child nodes recursively.
        for child in node.children:
            _write_act_node(
                f,
                child,
                legacy_hierarchy=legacy_hierarchy,
                is_root=False
            )

        write_record_header(f, ACT_RECORD_HIERARCHY_END, 0)
