"""
Import dataclasses and option models.
"""

from dataclasses import dataclass


@dataclass
class ImportOptions:
    """
    Options for the import operation.

    """

    filepath: str
    scale: float = 1.0
    apply_transform: bool = True
    import_materials: bool = True
    import_textures: bool = True
    cleanup_scene: bool = False


@dataclass
class ImportResult:
    """
    Result of an import operation.

    """

    success: bool = True
    objects_created: int = 0
    error_message: str = ""
