"""
Export dataclasses and option models.
"""

from dataclasses import dataclass


@dataclass
class ExportOptions:
    """
    Options for the export operation.

    """

    filepath: str
    scale: float = 1.0
    selected_only: bool = False
    apply_modifiers: bool = True
    triangulate: bool = True
    ignore_act_object_scale: bool = True
    generate_sdf: bool = True
    export_format: str = 'ALL'
    export_kind: str = 'AUTO'
    game_version: str = 'C2'


@dataclass
class ExportResult:
    """
    Result of an export operation.

    """

    success: bool = True
    files_written: int = 0
    error_message: str = ""
