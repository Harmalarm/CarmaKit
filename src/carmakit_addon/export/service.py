"""
High-level export service orchestration.
"""

import os
from typing import Dict, List

import bpy

from ..writers.act_writer import write_act_file
from ..writers.dat_writer import write_dat_file
from ..writers.mat_writer import write_mat_file
from ..writers.sdf_writer import write_sdf_file
from .act_export import create_act_file
from .common import (
    apply_bru_export_scale,
    is_preprocessed_track,
    log_debug,
)
from .dat_export import create_dat_file
from .mat_export import create_mat_file
from .types import ExportOptions, ExportResult


def export_carmageddon_model(
    context: bpy.types.Context,
    options: ExportOptions
) -> ExportResult:
    """
    Export Blender objects to Carmageddon format.

    """
    result = ExportResult()
    apply_bru_export_scale(options)
    log_debug(f"Starting export to: {options.filepath}")
    options_summary = ", ".join([
        f"scale={options.scale}",
        f"selected_only={options.selected_only}",
        f"apply_modifiers={options.apply_modifiers}",
        f"triangulate={options.triangulate}",
        f"ignore_act_object_scale={options.ignore_act_object_scale}",
        f"generate_sdf={options.generate_sdf}",
        f"export_format={options.export_format}",
        "export_kind=AUTO",
        f"game_version={options.game_version}",
    ])
    log_debug(f"Options: {options_summary}")

    try:
        base_path = os.path.dirname(options.filepath)
        base_name = os.path.splitext(os.path.basename(options.filepath))[0]

        if options.selected_only:
            scene_objects = list(context.selected_objects)
        else:
            scene_objects = list(context.scene.objects)

        act_objects = [
            obj for obj in scene_objects
            if obj.type in {'MESH', 'EMPTY'}
        ]
        mesh_objects = [obj for obj in act_objects if obj.type == 'MESH']

        if not mesh_objects:
            result.error_message = "No mesh objects to export"
            result.success = False
            return result

        log_debug(
            f"Objects: {len(act_objects)} total, {len(mesh_objects)} meshes"
        )

        all_materials: Dict[str, bpy.types.Material] = {}
        needs_default_material = False
        for obj in mesh_objects:
            if not obj.material_slots:
                needs_default_material = True
                continue
            for slot in obj.material_slots:
                if slot.material:
                    all_materials[slot.material.name] = slot.material
                else:
                    needs_default_material = True

        dat_file = create_dat_file(context, mesh_objects, options)
        mat_file = create_mat_file(
            all_materials,
            base_path,
            include_default=needs_default_material
        )

        is_preprocessed = is_preprocessed_track(act_objects)
        if is_preprocessed:
            log_debug("Detected preprocessed hierarchy (PP01)")
        else:
            log_debug("No PP01 hierarchy detected; using legacy ACT hierarchy")

        act_file = create_act_file(
            act_objects,
            base_name,
            options,
            is_preprocessed
        )

        if options.export_format in ['ALL', 'ACT_DAT']:
            act_path = os.path.join(base_path, base_name + '.act')
            write_act_file(
                act_path,
                act_file,
                legacy_hierarchy=True
            )
            result.files_written += 1
            log_debug(f"Wrote ACT: {act_path}")

        if options.export_format in ['ALL', 'ACT_DAT', 'DAT_ONLY']:
            dat_path = os.path.join(base_path, base_name + '.dat')
            write_dat_file(dat_path, dat_file)
            result.files_written += 1
            log_debug(f"Wrote DAT: {dat_path}")

        if options.export_format == 'ALL':
            mat_path = os.path.join(base_path, base_name + '.mat')
            write_mat_file(
                mat_path,
                mat_file,
                game_version=options.game_version
            )
            result.files_written += 1
            log_debug(f"Wrote MAT: {mat_path}")

        if options.generate_sdf:
            sdf_path = os.path.join(base_path, base_name + '.sdf')
            write_sdf_file(sdf_path)
            result.files_written += 1
            log_debug(f"Wrote SDF: {sdf_path}")

    except Exception as e:
        result.error_message = str(e)
        result.success = False
        log_debug(f"Export failed with exception: {e}")

    log_debug(
        f"Export complete: success={result.success}, "
        f"files_written={result.files_written}"
    )
    if not result.success:
        log_debug(f"  Error message: {result.error_message}")

    return result
