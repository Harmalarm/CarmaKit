"""
ACT file writer for Carmageddon actor files.

This module contains the writer for creating ACT actor hierarchy files
in their native big-endian binary format.
"""

from typing import BinaryIO

from ..utils.binary_writer import BinaryWriter
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
        BinaryWriter.write_null_marker(f)


def _write_act_node(
    f: BinaryIO,
    node: ActorNode,
    legacy_hierarchy: bool,
    is_root: bool = False
) -> None:
    """
    Write an actor node and its children to an ACT file.

    """
    # Write actor name and attributes.
    name_bytes = node.name.encode('ascii') + b'\x00'
    record_length = 2 + len(name_bytes)
    BinaryWriter.write_record_header(
        f,
        ACT_RECORD_ACTOR_NAME,
        record_length
    )
    BinaryWriter.write_uint16(f, node.attributes)
    f.write(name_bytes)

    # Write transformation matrix.
    BinaryWriter.write_record_header(f, ACT_RECORD_TRANSFORM, 48)
    BinaryWriter.write_float32_array(
        f,
        list(node.transform.values)
    )

    # Write unknown empty record (required by Plaything).
    BinaryWriter.write_record_header(f, ACT_RECORD_UNKNOWN, 0)

    # Write bounding box if present.
    if node.bounding_box:
        BinaryWriter.write_record_header(
            f,
            ACT_RECORD_BOUNDING_BOX,
            24
        )
        bb = node.bounding_box
        BinaryWriter.write_float32_array(f, [
            bb.min_point.x, bb.min_point.y, bb.min_point.z,
            bb.max_point.x, bb.max_point.y, bb.max_point.z,
        ])

    # Write model name if present.
    if node.model_name:
        name_bytes = node.model_name.encode('ascii') + b'\x00'
        BinaryWriter.write_record_header(
            f,
            ACT_RECORD_MODEL_NAME,
            len(name_bytes)
        )
        f.write(name_bytes)

    # Write children if present.
    is_helper_with_children = (node.model_name is None and bool(node.children))
    is_pp01_helper = node.name.startswith('PP01 ')
    is_no_identifier_helper = (
        node.name == ''
        or node.name.upper().startswith('NO_IDENTIFIER')
    )
    should_write_hierarchy_start = (
        is_helper_with_children
        and (is_pp01_helper or is_no_identifier_helper)
    )

    if legacy_hierarchy:
        # Legacy ACT files omit hierarchy start markers. Each non-root
        # node is followed by a hierarchy end marker to pop to parent.
        wrote_start = False
        if should_write_hierarchy_start:
            BinaryWriter.write_record_header(
                f,
                ACT_RECORD_HIERARCHY_START,
                0
            )
            wrote_start = True

        for child in node.children:
            _write_act_node(
                f,
                child,
                legacy_hierarchy=legacy_hierarchy,
                is_root=False
            )

        if wrote_start or not is_root:
            BinaryWriter.write_record_header(
                f,
                ACT_RECORD_HIERARCHY_END,
                0
            )
    elif node.children:
        BinaryWriter.write_record_header(
            f,
            ACT_RECORD_HIERARCHY_START,
            0
        )

        # Write child nodes recursively.
        for child in node.children:
            _write_act_node(
                f,
                child,
                legacy_hierarchy=legacy_hierarchy,
                is_root=False
            )

        BinaryWriter.write_record_header(
            f,
            ACT_RECORD_HIERARCHY_END,
            0
        )
