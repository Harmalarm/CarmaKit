"""
Setup export logic for separate car and track TXT files.
"""

import os
from typing import Iterable

import bpy

from ..writers.txt_writer_car import write_car_txt


def export_car_setup(
    filepath: str,
    objects: Iterable[bpy.types.Object]
) -> None:
    """
    Export a car setup TXT file.

    """
    write_car_txt(filepath, objects)


def export_track_setup(filepath: str) -> None:
    """
    Export a minimal track setup TXT file scaffold.

    """
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    lines = [
        "VERSION 1",
        "",
        "START OF FUNK",
        "",
        "END OF FUNK",
        "",
        "START OF GROOVE",
        "",
        "END OF GROOVE",
        "",
        "START OF OPPONENT PATHS",
        "0",
        "0",
        "0",
        "END OF OPPONENT PATHS",
        "",
        "START OF DRONE PATHS",
        "0",
        "0",
        "END OF DRONE PATHS",
        "",
        "1",
        "",
        f"{base_name}.TXT",
    ]

    content = "\n".join(lines) + "\n"
    with open(filepath, "w", encoding="ascii", errors="ignore") as f:
        f.write(content)
