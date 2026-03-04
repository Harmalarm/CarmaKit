"""
MAT export logic for Carmageddon formats.
"""

import os
from typing import Dict

import bpy

from ..classes.mat_classes import Material as CarMaterial
from ..classes.mat_classes import MatFile
from ..constants import MAT_FLAG_DEFAULT
from .common import log_debug


def create_mat_file(
    materials: Dict[str, bpy.types.Material],
    base_path: str,
    include_default: bool = False
) -> MatFile:
    """
    Create a MatFile from Blender materials.

    """
    del base_path
    mat_file = MatFile()

    log_debug(f"Creating MAT from {len(materials)} materials")

    if include_default and "default" not in materials:
        default_mat = CarMaterial()
        default_mat.name = "default"
        default_mat.color = (200, 200, 200, 255)
        default_mat.flags = MAT_FLAG_DEFAULT
        mat_file.materials.append(default_mat)
        log_debug("  Added default material")

    for name, blender_mat in materials.items():
        car_mat = CarMaterial()
        car_mat.name = name

        if blender_mat.use_nodes:
            for node in blender_mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    color = node.inputs['Base Color'].default_value
                    car_mat.color = (
                        int(color[0] * 255),
                        int(color[1] * 255),
                        int(color[2] * 255),
                        255
                    )
                    roughness = node.inputs['Roughness'].default_value
                    car_mat.specular = 1.0 - roughness
                    break

        if not blender_mat.use_backface_culling:
            car_mat.flags |= 0x00001000

        if blender_mat.use_nodes:
            for node in blender_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    tex_name = os.path.splitext(node.image.name)[0]
                    car_mat.texture_name = tex_name
                    break

        mat_file.materials.append(car_mat)
        log_debug(
            f"  Material '{car_mat.name}': texture="
            f"{car_mat.texture_name or 'none'}, flags=0x{car_mat.flags:08X}"
        )

    log_debug(f"MAT materials created: {len(mat_file.materials)}")

    return mat_file
