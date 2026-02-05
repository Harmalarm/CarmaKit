"""
ACT file parser for Carmageddon actor files.

This module contains the parser for reading ACT actor hierarchy files
in their native big-endian binary format.
"""

from typing import List, Optional

from ..utils.binary_reader import (
    read_float32_array,
    read_null_terminated_string,
    read_record_header,
    read_uint16,
)
from ..constants import (
    ACT_RECORD_ACTOR_NAME,
    ACT_RECORD_BOUNDING_BOX,
    ACT_RECORD_HIERARCHY_END,
    ACT_RECORD_HIERARCHY_START,
    ACT_RECORD_MATERIAL_NAMES,
    ACT_RECORD_MODEL_NAME,
    ACT_RECORD_TRANSFORM,
    ACT_RECORD_UNKNOWN,
    FILE_TYPE_ACT,
)
from ..classes.shared_classes import (
    Vector3,
)
from ..classes.act_classes import (
    ActFile,
    ActorNode,
    TransformMatrix,
    BoundingBox,
)
from .utils import ParseError, read_file_header


def parse_act_file(filepath: str) -> ActFile:
    """
    Parse an ACT actor file.

    Parses actors in order and tracks parent-child relationships using
    parent indices. Each actor's parent is the actor that was current
    when it was created, and the hierarchy end record pops back up.

    :param filepath: Path to the ACT file.
    :type filepath: str
    :return: Parsed ACT file structure.
    :rtype: ActFile
    :raises ParseError: If parsing fails.
    :raises FileNotFoundError: If file does not exist.
    """
    result = ActFile()

    with open(filepath, 'rb') as f:
        # Read and validate header.
        file_type, version = read_file_header(f)
        if file_type != FILE_TYPE_ACT:
            raise ParseError(
                f"Not an ACT file. Type: {hex(file_type)}"
            )

        # Parse actors maintaining parent index tracking like original code.
        all_nodes: List[ActorNode] = []
        parent_indices: List[int] = []  # Track parent index for each node.
        current_node: Optional[ActorNode] = None
        parent_index: int = -1  # Current parent index (-1 = no parent).

        while True:
            try:
                record_type, length = read_record_header(f)
            except Exception:
                # End of file.
                break

            # Null marker or EOF.
            if record_type == 0 and length == 0:
                continue

            if record_type == ACT_RECORD_ACTOR_NAME:
                # New actor starting.
                current_node = ActorNode()
                current_node.attributes = read_uint16(f)
                current_node.name = read_null_terminated_string(f)
                # Store parent index for this node.
                parent_indices.append(parent_index)
                all_nodes.append(current_node)
                # This node becomes the new parent for any subsequent nodes.
                parent_index = len(all_nodes) - 1

            elif record_type == ACT_RECORD_TRANSFORM:
                if current_node:
                    values = read_float32_array(f, 12)
                    current_node.transform = TransformMatrix(tuple(values))

            elif record_type == ACT_RECORD_UNKNOWN:
                # Empty record, skip any data if present.
                if length > 0:
                    f.read(length)

            elif record_type == ACT_RECORD_BOUNDING_BOX:
                if current_node:
                    values = read_float32_array(f, 6)
                    current_node.bounding_box = BoundingBox(
                        Vector3(values[0], values[1], values[2]),
                        Vector3(values[3], values[4], values[5])
                    )

            elif record_type == ACT_RECORD_HIERARCHY_START:
                # Hierarchy start marker - skip any data.
                if length > 0:
                    f.read(length)

            elif record_type == ACT_RECORD_HIERARCHY_END:
                # End of a hierarchy section - pop back to grandparent.
                # This makes the parent of current actor the new parent.
                if parent_index >= 0 and parent_index < len(parent_indices):
                    parent_index = parent_indices[parent_index]
                if length > 0:
                    f.read(length)

            elif record_type == ACT_RECORD_MATERIAL_NAMES:
                # ACT material names record contains null-terminated strings
                # without a count prefix (unlike DAT format).
                if current_node and length > 0:
                    data = f.read(length)
                    # Split on null bytes and filter empty strings.
                    names = data.split(b'\x00')
                    for name_bytes in names:
                        if name_bytes:
                            name = name_bytes.decode('ascii', errors='replace')
                            current_node.materials.append(name)

            elif record_type == ACT_RECORD_MODEL_NAME:
                if current_node:
                    current_node.model_name = read_null_terminated_string(f)

            else:
                # Skip unknown record types.
                if length > 0:
                    f.read(length)

        # Build hierarchy from flat list using parent indices.
        if all_nodes:
            # First node is always root.
            result.root = all_nodes[0]
            # Add children to their respective parents.
            for i in range(1, len(all_nodes)):
                pi = parent_indices[i]
                if pi >= 0 and pi < len(all_nodes):
                    all_nodes[pi].children.append(all_nodes[i])
                else:
                    # No valid parent, add to root's children.
                    result.root.children.append(all_nodes[i])

    return result
