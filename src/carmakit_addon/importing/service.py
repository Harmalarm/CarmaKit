"""
High-level import service orchestration.
"""

import os
from typing import Dict

import bpy

from ..classes.dat_classes import DatModel
from ..parsers.act_parser import parse_act_file
from ..parsers.dat_parser import parse_dat_file
from ..parsers.mat_parser import parse_mat_file
from ..parsers.utils import find_related_files
from ..utils.general_utils import cleanup_scene
from .act_import import create_hierarchy_from_act
from .common import (
    apply_bru_import_scale,
    apply_grooves_to_object,
    load_groove_map,
    log_debug,
)
from .dat_import import create_mesh_from_model
from .mat_import import create_blender_materials
from .types import ImportOptions, ImportResult


def import_carmageddon_model(
    context: bpy.types.Context,
    options: ImportOptions
) -> ImportResult:
    """
    Import a Carmageddon model into Blender.

    Handles importing from ACT or DAT files, automatically finding
    related files in the same directory.

    """
    result = ImportResult()
    apply_bru_import_scale(options)
    log_debug(f"Starting import of: {options.filepath}")
    log_debug(
        f"Options: scale={options.scale}, "
        f"apply_transform={options.apply_transform}, "
        f"import_materials={options.import_materials}, "
        f"import_textures={options.import_textures}, "
        f"cleanup_scene={options.cleanup_scene}"
    )

    try:
        if options.cleanup_scene:
            log_debug("Cleaning up scene before import...")
            cleanup_scene(context)

        log_debug("Searching for related files...")
        act_path, dat_path, mat_path = find_related_files(options.filepath)
        log_debug(f"  ACT file: {act_path or 'not found'}")
        log_debug(f"  DAT file: {dat_path or 'not found'}")
        log_debug(f"  MAT file: {mat_path or 'not found'}")

        ext = os.path.splitext(options.filepath)[1].lower()
        if ext == '.act':
            act_path = options.filepath
        elif ext == '.dat':
            dat_path = options.filepath

        materials: Dict[str, bpy.types.Material] = {}
        if options.import_materials and mat_path:
            log_debug(f"Loading materials from: {mat_path}")
            try:
                mat_file = parse_mat_file(mat_path)
                log_debug(
                    f"  Parsed {len(mat_file.materials)} materials from MAT file"
                )
                materials = create_blender_materials(
                    mat_file,
                    os.path.dirname(mat_path),
                    options.import_textures
                )
                log_debug(f"  Created {len(materials)} Blender materials")
            except Exception as e:
                print(f"Warning: Could not load materials: {e}")
                log_debug(f"  ERROR loading materials: {e}")

        models: Dict[str, DatModel] = {}
        if dat_path:
            log_debug(f"Loading models from: {dat_path}")
            try:
                dat_file = parse_dat_file(dat_path)
                log_debug(
                    f"  Parsed DAT file with {len(dat_file.models)} models"
                )
                for model in dat_file.models:
                    key = model.name.upper()
                    if not key.endswith('.DAT'):
                        key = key + '.DAT'
                    models[key] = model
                    log_debug(
                        f"    Model '{model.name}': {len(model.vertices)} "
                        f"verts, {len(model.faces)} faces"
                    )
                    log_debug(f"      Registered key: '{key}'")
            except Exception as e:
                log_debug(f"  ERROR parsing DAT file: {e}")
                result.error_message = f"Failed to parse DAT file: {e}"
                result.success = False
                return result

        groove_map = load_groove_map(options.filepath, act_path, dat_path)

        if act_path:
            log_debug(f"Loading ACT hierarchy from: {act_path}")
            try:
                act_file = parse_act_file(act_path)
                log_debug(
                    f"  ACT file parsed, root node: "
                    f"{act_file.root.name if act_file.root else 'None'}"
                )
                if act_file.root:
                    log_debug("  Creating Blender hierarchy from ACT...")
                    objects = create_hierarchy_from_act(
                        context,
                        act_file.root,
                        models,
                        materials,
                        options,
                        None,
                        groove_map
                    )
                    result.objects_created = len(objects)
                    log_debug(
                        f"  Created {len(objects)} objects from ACT hierarchy"
                    )
            except Exception as e:
                log_debug(f"  ERROR parsing ACT file: {e}")
                result.error_message = f"Failed to parse ACT file: {e}"
                result.success = False
                return result
        else:
            log_debug(
                f"No ACT file, importing {len(models)} models directly from DAT"
            )
            for model in models.values():
                log_debug(f"  Creating mesh for model: {model.name}")
                obj = create_mesh_from_model(
                    context,
                    model,
                    materials,
                    options,
                    None
                )
                if obj:
                    apply_grooves_to_object(obj, groove_map)
                result.objects_created += 1
                log_debug(f"    Done creating mesh for {model.name}")

    except Exception as e:
        result.error_message = str(e)
        result.success = False
        log_debug(f"Import failed with exception: {e}")

    log_debug(
        f"Import complete: success={result.success}, "
        f"objects_created={result.objects_created}"
    )
    if result.error_message:
        log_debug(f"  Error message: {result.error_message}")

    return result
