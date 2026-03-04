"""
MAT import logic for Carmageddon formats.
"""

import os
from typing import Dict, Optional

import bpy

from ..classes.mat_classes import MatFile
from .common import ADDON_PACKAGE, log_debug


def create_blender_materials(
    mat_file: MatFile,
    base_path: str,
    load_textures: bool
) -> Dict[str, bpy.types.Material]:
    """
    Create Blender materials from a MAT file.

    """
    result: Dict[str, bpy.types.Material] = {}

    game_folder = None
    try:
        prefs = bpy.context.preferences.addons[ADDON_PACKAGE].preferences
        if prefs.game_folder:
            game_folder = prefs.game_folder
            log_debug(f"  Game folder set: {game_folder}")
    except (KeyError, AttributeError):
        pass

    for car_mat in mat_file.materials:
        mat_name = car_mat.name
        mat_key = mat_name.lower()

        existing_mat = None
        for existing in bpy.data.materials:
            if existing.name.lower() == mat_key:
                existing_mat = existing
                log_debug(f"  Reusing existing material: '{existing.name}'")
                break

        if existing_mat:
            mat = existing_mat
        else:
            mat = bpy.data.materials.new(name=mat_name)
            log_debug(f"  Created new material: '{mat_name}'")

        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        nodes.clear()

        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (300, 0)

        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)

        r = car_mat.color[0] / 255.0
        g = car_mat.color[1] / 255.0
        b = car_mat.color[2] / 255.0
        bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
        bsdf.inputs['Roughness'].default_value = 1.0 - car_mat.specular

        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        if car_mat.is_two_sided:
            mat.use_backface_culling = False
        else:
            mat.use_backface_culling = True

        if load_textures and car_mat.texture_name:
            tex_path = find_texture(base_path, car_mat.texture_name, game_folder)
            if tex_path:
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.location = (-300, 0)

                try:
                    existing_image = None
                    tex_basename = os.path.basename(tex_path)
                    for img in bpy.data.images:
                        if img.filepath and os.path.basename(img.filepath) == tex_basename:
                            existing_image = img
                            break

                    if existing_image:
                        tex_node.image = existing_image
                        log_debug(f"    Reusing existing texture: {tex_basename}")
                    else:
                        tex_node.image = bpy.data.images.load(tex_path)
                        log_debug(f"    Loaded texture: {tex_path}")

                    links.new(
                        tex_node.outputs['Color'],
                        bsdf.inputs['Base Color']
                    )

                    img = tex_node.image
                    if img and img.channels == 4:
                        has_transparency = False
                        try:
                            pixels = img.pixels[:]
                            for i in range(3, len(pixels), 4):
                                if pixels[i] < 1.0:
                                    has_transparency = True
                                    break
                        except Exception:
                            has_transparency = False

                        if has_transparency:
                            links.new(
                                tex_node.outputs['Alpha'],
                                bsdf.inputs['Alpha']
                            )
                            mat.blend_method = 'BLEND'
                            mat.shadow_method = 'CLIP'
                            log_debug("    Enabled alpha transparency for texture")
                        else:
                            log_debug(
                                "    Texture has alpha channel but is fully "
                                "opaque, skipping transparency"
                            )

                except Exception as e:
                    log_debug(
                        f"    WARNING: Failed to load texture '{tex_path}': {e}"
                    )
            else:
                log_debug(
                    "    WARNING: Texture "
                    f"'{car_mat.texture_name}' not found in tiffrgb or "
                    "textures folders"
                )

        result[mat_key] = mat

    return result


def find_texture(
    base_path: str,
    texture_name: str,
    game_folder: Optional[str] = None
) -> Optional[str]:
    """
    Find a texture file by name.

    """
    base_name = os.path.splitext(texture_name)[0]

    extensions = ['.tif', '.TIF', '.tiff', '.TIFF', '.png', '.PNG',
                  '.jpg', '.JPG', '.jpeg', '.JPEG', '.bmp', '.BMP']

    search_dirs = [
        base_path,
        os.path.join(base_path, 'tiffrgb'),
        os.path.join(base_path, 'TIFFRGB'),
        os.path.join(base_path, 'textures'),
        os.path.join(base_path, 'TEXTURES'),
    ]

    folder_name = os.path.basename(base_path.rstrip('/\\'))
    if len(folder_name) >= 4:
        prefix = folder_name[:4].lower()
        parent_dir = os.path.dirname(base_path.rstrip('/\\'))
        if os.path.isdir(parent_dir):
            try:
                for sibling in os.listdir(parent_dir):
                    sibling_lower = sibling.lower()
                    if sibling_lower == folder_name.lower():
                        continue
                    if sibling_lower.startswith(prefix):
                        sibling_path = os.path.join(parent_dir, sibling)
                        if os.path.isdir(sibling_path):
                            search_dirs.extend([
                                os.path.join(sibling_path, 'tiffrgb'),
                                os.path.join(sibling_path, 'TIFFRGB'),
                                os.path.join(sibling_path, 'textures'),
                                os.path.join(sibling_path, 'TEXTURES'),
                            ])
            except OSError:
                pass

    if game_folder:
        game_folder = game_folder.rstrip('/\\')
        search_dirs.extend([
            os.path.join(game_folder, 'Data', 'Reg', 'PIXELMAP', 'tiffrgb'),
            os.path.join(game_folder, 'DATA', 'REG', 'PIXELMAP', 'TIFFRGB'),
            os.path.join(game_folder, 'data', 'reg', 'pixelmap', 'tiffrgb'),
        ])

    for directory in search_dirs:
        if not os.path.exists(directory):
            continue

        for ext in extensions:
            candidate = os.path.join(directory, base_name + ext)
            if os.path.exists(candidate):
                return candidate

    return None
