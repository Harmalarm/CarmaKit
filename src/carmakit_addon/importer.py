"""
Carmageddon model importer for Blender.

This module handles importing Carmageddon DAT, ACT, and MAT files
into Blender as meshes, empties, and materials.

:author: CarmaKit Team
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

import bpy
import bmesh
from mathutils import Matrix, Vector

from .data_structures import (
    ActFile,
    ActorNode,
    DatFile,
    DatModel,
    Material as CarMaterial,
    MatFile,
)
from .parsers import (
    ParseError,
    find_related_files,
    parse_act_file,
    parse_dat_file,
    parse_mat_file,
)


def _log_verbose(message: str) -> None:
    """
    Log a verbose message if verbose import logging is enabled.

    :param message: The message to log.
    :type message: str
    :return: None.
    :rtype: None
    """
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs.verbose_import_logging:
            print(f"[CarmaKit Import] {message}")
    except (KeyError, AttributeError):
        # Addon preferences not available, skip logging.
        pass


def _find_model_in_dict(
    model_name: str,
    models: Dict[str, "DatModel"]
) -> Optional["DatModel"]:
    """
    Find a model in the models dictionary.

    Models are stored with uppercase names including .DAT extension.

    :param model_name: The model name to search for.
    :type model_name: str
    :param models: Dictionary of loaded models.
    :type models: Dict[str, DatModel]
    :return: The found model or None.
    :rtype: Optional[DatModel]
    """
    if not model_name:
        return None

    # Normalize to uppercase with .DAT extension.
    key = model_name.upper()
    if not key.endswith('.DAT'):
        key = key + '.DAT'

    if key in models:
        _log_verbose(f"    Found model with key '{key}'")
        return models[key]

    _log_verbose(f"    Model key '{key}' not found")
    return None


@dataclass
class ImportOptions:
    """
    Options for the import operation.

    :param filepath: Path to the file to import.
    :type filepath: str
    :param scale: Scale factor to apply to imported geometry.
    :type scale: float
    :param apply_transform: Whether to apply ACT transforms.
    :type apply_transform: bool
    :param import_materials: Whether to import materials.
    :type import_materials: bool
    :param import_textures: Whether to load textures.
    :type import_textures: bool
    """

    filepath: str
    scale: float = 1.0
    apply_transform: bool = True
    import_materials: bool = True
    import_textures: bool = True


@dataclass
class ImportResult:
    """
    Result of an import operation.

    :param success: Whether the import was successful.
    :type success: bool
    :param objects_created: Number of objects created.
    :type objects_created: int
    :param error_message: Error message if import failed.
    :type error_message: str
    """

    success: bool = True
    objects_created: int = 0
    error_message: str = ""


def import_carmageddon_model(
    context: bpy.types.Context,
    options: ImportOptions
) -> ImportResult:
    """
    Import a Carmageddon model into Blender.

    Handles importing from ACT or DAT files, automatically finding
    related files in the same directory.

    :param context: The Blender context.
    :type context: bpy.types.Context
    :param options: Import options.
    :type options: ImportOptions
    :return: Result of the import operation.
    :rtype: ImportResult
    """
    result = ImportResult()
    _log_verbose(f"Starting import of: {options.filepath}")
    _log_verbose(f"Options: scale={options.scale}, apply_transform={options.apply_transform}, "
                 f"import_materials={options.import_materials}, import_textures={options.import_textures}")

    try:
        # Find related files.
        _log_verbose("Searching for related files...")
        act_path, dat_path, mat_path = find_related_files(options.filepath)
        _log_verbose(f"  ACT file: {act_path or 'not found'}")
        _log_verbose(f"  DAT file: {dat_path or 'not found'}")
        _log_verbose(f"  MAT file: {mat_path or 'not found'}")

        # Determine which file was selected and adjust paths.
        ext = os.path.splitext(options.filepath)[1].lower()
        if ext == '.act':
            act_path = options.filepath
        elif ext == '.dat':
            dat_path = options.filepath

        # Load materials first.
        materials: Dict[str, bpy.types.Material] = {}
        if options.import_materials and mat_path:
            _log_verbose(f"Loading materials from: {mat_path}")
            try:
                mat_file = parse_mat_file(mat_path)
                _log_verbose(f"  Parsed {len(mat_file.materials)} materials from MAT file")
                materials = _create_blender_materials(
                    mat_file,
                    os.path.dirname(mat_path),
                    options.import_textures
                )
                _log_verbose(f"  Created {len(materials)} Blender materials")
            except Exception as e:
                print(f"Warning: Could not load materials: {e}")
                _log_verbose(f"  ERROR loading materials: {e}")

        # Load DAT models.
        models: Dict[str, DatModel] = {}
        if dat_path:
            _log_verbose(f"Loading models from: {dat_path}")
            try:
                dat_file = parse_dat_file(dat_path)
                _log_verbose(f"  Parsed DAT file with {len(dat_file.models)} models")
                for model in dat_file.models:
                    # Store with uppercase name including .DAT extension.
                    key = model.name.upper()
                    if not key.endswith('.DAT'):
                        key = key + '.DAT'
                    models[key] = model
                    _log_verbose(f"    Model '{model.name}': {len(model.vertices)} verts, {len(model.faces)} faces")
                    _log_verbose(f"      Registered key: '{key}'")
            except Exception as e:
                _log_verbose(f"  ERROR parsing DAT file: {e}")
                result.error_message = f"Failed to parse DAT file: {e}"
                result.success = False
                return result

        # Load ACT hierarchy or create simple scene from DAT.
        if act_path:
            _log_verbose(f"Loading ACT hierarchy from: {act_path}")
            try:
                act_file = parse_act_file(act_path)
                _log_verbose(f"  ACT file parsed, root node: {act_file.root.name if act_file.root else 'None'}")
                if act_file.root:
                    _log_verbose("  Creating Blender hierarchy from ACT...")
                    objects = _create_hierarchy_from_act(
                        context,
                        act_file.root,
                        models,
                        materials,
                        options,
                        None
                    )
                    result.objects_created = len(objects)
                    _log_verbose(f"  Created {len(objects)} objects from ACT hierarchy")
            except Exception as e:
                _log_verbose(f"  ERROR parsing ACT file: {e}")
                result.error_message = f"Failed to parse ACT file: {e}"
                result.success = False
                return result
        else:
            # No ACT file, just import DAT models directly.
            _log_verbose(f"No ACT file, importing {len(models)} models directly from DAT")
            for model in models.values():
                _log_verbose(f"  Creating mesh for model: {model.name}")
                _create_mesh_from_model(
                    context, model, materials, options, None
                )
                result.objects_created += 1
                _log_verbose(f"    Done creating mesh for {model.name}")

    except Exception as e:
        result.error_message = str(e)
        result.success = False
        _log_verbose(f"Import failed with exception: {e}")

    _log_verbose(f"Import complete: success={result.success}, objects_created={result.objects_created}")
    if result.error_message:
        _log_verbose(f"  Error message: {result.error_message}")
    return result


def _create_blender_materials(
    mat_file: MatFile,
    base_path: str,
    load_textures: bool
) -> Dict[str, bpy.types.Material]:
    """
    Create Blender materials from a MAT file.

    :param mat_file: Parsed MAT file.
    :type mat_file: MatFile
    :param base_path: Base path for finding textures.
    :type base_path: str
    :param load_textures: Whether to attempt loading textures.
    :type load_textures: bool
    :return: Dictionary mapping material names to Blender materials.
    :rtype: Dict[str, bpy.types.Material]
    """
    result: Dict[str, bpy.types.Material] = {}

    for car_mat in mat_file.materials:
        # Create or get existing material.
        mat_name = car_mat.name
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(name=mat_name)

        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes.
        nodes.clear()

        # Create principled BSDF shader.
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (300, 0)

        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)

        # Set base color from material color.
        r = car_mat.color[0] / 255.0
        g = car_mat.color[1] / 255.0
        b = car_mat.color[2] / 255.0
        bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)

        # Set specular.
        bsdf.inputs['Roughness'].default_value = 1.0 - car_mat.specular

        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        # Handle two-sided materials.
        if car_mat.is_two_sided:
            mat.use_backface_culling = False
        else:
            mat.use_backface_culling = True

        # Try to load texture.
        if load_textures and car_mat.texture_name:
            tex_path = _find_texture(base_path, car_mat.texture_name)
            if tex_path:
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.location = (-300, 0)

                try:
                    tex_node.image = bpy.data.images.load(tex_path)
                    links.new(
                        tex_node.outputs['Color'],
                        bsdf.inputs['Base Color']
                    )
                except Exception:
                    pass

        result[mat_name.lower()] = mat

    return result


def _find_texture(base_path: str, texture_name: str) -> Optional[str]:
    """
    Find a texture file by name.

    Searches for various image formats in the base path and common
    subdirectories.

    :param base_path: Base directory to search.
    :type base_path: str
    :param texture_name: Name of the texture (without extension).
    :type texture_name: str
    :return: Path to texture file if found, None otherwise.
    :rtype: Optional[str]
    """
    # Remove extension from texture name if present.
    base_name = os.path.splitext(texture_name)[0]

    # Extensions to try.
    extensions = ['.tif', '.TIF', '.tiff', '.TIFF', '.png', '.PNG',
                  '.jpg', '.JPG', '.jpeg', '.JPEG', '.bmp', '.BMP']

    # Directories to search.
    search_dirs = [
        base_path,
        os.path.join(base_path, 'tiffrgb'),
        os.path.join(base_path, 'TIFFRGB'),
        os.path.join(base_path, 'textures'),
        os.path.join(base_path, 'TEXTURES'),
    ]

    for directory in search_dirs:
        if not os.path.exists(directory):
            continue

        for ext in extensions:
            candidate = os.path.join(directory, base_name + ext)
            if os.path.exists(candidate):
                return candidate

    return None


def _create_hierarchy_from_act(
    context: bpy.types.Context,
    node: ActorNode,
    models: Dict[str, DatModel],
    materials: Dict[str, bpy.types.Material],
    options: ImportOptions,
    parent: Optional[bpy.types.Object]
) -> List[bpy.types.Object]:
    """
    Create Blender objects from an ACT hierarchy.

    :param context: The Blender context.
    :type context: bpy.types.Context
    :param node: The actor node to process.
    :type node: ActorNode
    :param models: Dictionary of loaded models.
    :type models: Dict[str, DatModel]
    :param materials: Dictionary of loaded materials.
    :type materials: Dict[str, bpy.types.Material]
    :param options: Import options.
    :type options: ImportOptions
    :param parent: Parent Blender object.
    :type parent: Optional[bpy.types.Object]
    :return: List of created Blender objects.
    :rtype: List[bpy.types.Object]
    """
    created_objects: List[bpy.types.Object] = []
    _log_verbose(f"Processing ACT node: '{node.name}' (model_name='{node.model_name}', children={len(node.children)})")

    # Check if this node references a model.
    if node.model_name:
        _log_verbose(f"  Looking for model: '{node.model_name}'")
        found_model = _find_model_in_dict(node.model_name, models)

        if found_model:
            _log_verbose(f"  Found model '{found_model.name}', creating mesh...")
            obj = _create_mesh_from_model(
                context,
                found_model,
                materials,
                options,
                parent
            )
            if obj:
                obj.name = node.name
                _log_verbose(f"  Created mesh object: '{obj.name}'")
                if options.apply_transform:
                    _log_verbose(f"    Applying transform to '{obj.name}'")
                    _apply_transform(obj, node, options.scale)
                created_objects.append(obj)
                parent = obj
            else:
                _log_verbose(f"  WARNING: _create_mesh_from_model returned None for '{found_model.name}'")
        else:
            _log_verbose(f"  Model '{node.model_name}' not found in loaded models, available: {list(models.keys())}")
            # Create empty for hierarchy node.
            _log_verbose(f"  Creating empty for missing model node: '{node.name}'")
            obj = _create_empty(context, node.name, parent)
            if options.apply_transform:
                _apply_transform(obj, node, options.scale)
            created_objects.append(obj)
            parent = obj
    else:
        # Create empty for hierarchy node without model.
        _log_verbose(f"  Node '{node.name}' has no model, creating empty")
        obj = _create_empty(context, node.name, parent)
        if options.apply_transform:
            _apply_transform(obj, node, options.scale)
        created_objects.append(obj)
        parent = obj

    # Process children recursively.
    if node.children:
        _log_verbose(f"  Processing {len(node.children)} children of '{node.name}'")
    for child in node.children:
        child_objects = _create_hierarchy_from_act(
            context, child, models, materials, options, parent
        )
        created_objects.extend(child_objects)

    _log_verbose(f"  Finished node '{node.name}', created {len(created_objects)} objects")
    return created_objects


def _create_mesh_from_model(
    context: bpy.types.Context,
    model: DatModel,
    materials: Dict[str, bpy.types.Material],
    options: ImportOptions,
    parent: Optional[bpy.types.Object]
) -> Optional[bpy.types.Object]:
    """
    Create a Blender mesh object from a DAT model.

    :param context: The Blender context.
    :type context: bpy.types.Context
    :param model: The DAT model to convert.
    :type model: DatModel
    :param materials: Dictionary of loaded materials.
    :type materials: Dict[str, bpy.types.Material]
    :param options: Import options.
    :type options: ImportOptions
    :param parent: Parent Blender object.
    :type parent: Optional[bpy.types.Object]
    :return: Created Blender object.
    :rtype: Optional[bpy.types.Object]
    """
    _log_verbose(f"  _create_mesh_from_model: '{model.name}' - {len(model.vertices)} verts, {len(model.faces)} faces")
    if not model.vertices or not model.faces:
        _log_verbose(f"    WARNING: Model '{model.name}' has no vertices or faces, skipping")
        return None

    # Create mesh.
    _log_verbose(f"    Creating Blender mesh...")
    mesh = bpy.data.meshes.new(name=model.name)
    obj = bpy.data.objects.new(model.name, mesh)

    # Link to scene.
    context.collection.objects.link(obj)

    # Set parent.
    if parent:
        obj.parent = parent

    # Create bmesh.
    _log_verbose(f"    Creating bmesh and adding vertices...")
    bm = bmesh.new()

    # Add vertices with axis conversion.
    # Carmageddon uses Y-up, Blender uses Z-up.
    # Convert: X stays, Y becomes Z, Z becomes -Y.
    scale = options.scale
    for v in model.vertices:
        bm.verts.new((v.x * scale, -v.z * scale, v.y * scale))

    bm.verts.ensure_lookup_table()
    _log_verbose(f"    Added {len(bm.verts)} vertices to bmesh (with Y-up to Z-up conversion)")

    # Add materials to mesh.
    mat_name_to_index: Dict[str, int] = {}
    for mat_name in model.materials:
        mat_key = mat_name.lower()
        if mat_key in materials:
            blender_mat = materials[mat_key]
        else:
            # Create placeholder material.
            blender_mat = bpy.data.materials.new(name=mat_name)
            blender_mat.use_nodes = True

        mesh.materials.append(blender_mat)
        mat_name_to_index[mat_key] = len(mesh.materials) - 1

    # Add faces.
    _log_verbose(f"    Adding {len(model.faces)} faces...")
    uv_layer = bm.loops.layers.uv.new("UVMap")
    faces_created = 0
    faces_failed = 0

    for face in model.faces:
        try:
            verts = [
                bm.verts[face.v1],
                bm.verts[face.v2],
                bm.verts[face.v3]
            ]
            bm_face = bm.faces.new(verts)

            # Set material index.
            if face.material_index > 0 and face.material_index <= len(
                model.materials
            ):
                mat_name = model.materials[face.material_index - 1].lower()
                if mat_name in mat_name_to_index:
                    bm_face.material_index = mat_name_to_index[mat_name]

            # Set UV coordinates.
            if model.tex_coords:
                for i, loop in enumerate(bm_face.loops):
                    vert_index = [face.v1, face.v2, face.v3][i]
                    if vert_index < len(model.tex_coords):
                        tc = model.tex_coords[vert_index]
                        loop[uv_layer].uv = (tc.u, 1.0 - tc.v)
            faces_created += 1

        except ValueError:
            # Face creation failed (e.g., duplicate face).
            faces_failed += 1
            continue

    _log_verbose(f"    Faces created: {faces_created}, failed: {faces_failed}")
    _log_verbose(f"    Converting bmesh to mesh...")
    bm.to_mesh(mesh)
    bm.free()

    # Update mesh.
    mesh.update()
    _log_verbose(f"    Mesh '{model.name}' created successfully")

    return obj


def _create_empty(
    context: bpy.types.Context,
    name: str,
    parent: Optional[bpy.types.Object]
) -> bpy.types.Object:
    """
    Create an empty object for hierarchy.

    :param context: The Blender context.
    :type context: bpy.types.Context
    :param name: Name for the empty.
    :type name: str
    :param parent: Parent object.
    :type parent: Optional[bpy.types.Object]
    :return: Created empty object.
    :rtype: bpy.types.Object
    """
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.empty_display_size = 0.1

    context.collection.objects.link(empty)

    if parent:
        empty.parent = parent

    return empty


def _apply_transform(
    obj: bpy.types.Object,
    node: ActorNode,
    scale: float
) -> None:
    """
    Apply transformation from ACT node to Blender object.

    Converts from Carmageddon Y-up to Blender Z-up coordinate system.

    :param obj: The Blender object to transform.
    :type obj: bpy.types.Object
    :param node: The actor node with transform data.
    :type node: ActorNode
    :param scale: Scale factor.
    :type scale: float
    :return: None.
    :rtype: None
    """
    # Build 4x4 matrix from 3x4 Carmageddon matrix.
    m = node.transform.values

    # Carmageddon matrix layout (Y-up):
    # Xx, Yx, Zx (row 0)
    # Xy, Yy, Zy (row 1)
    # Xz, Yz, Zz (row 2)
    # Px, Py, Pz (position)

    # Convert position from Y-up to Z-up: X stays, Y becomes Z, Z becomes -Y.
    pos_x = m[9] * scale
    pos_y = -m[11] * scale
    pos_z = m[10] * scale

    # Convert rotation matrix from Y-up to Z-up.
    # Apply axis swap to both rows and columns.
    matrix = Matrix((
        (m[0], -m[2], m[1], pos_x),
        (-m[6], m[8], -m[7], pos_y),
        (m[3], -m[5], m[4], pos_z),
        (0.0, 0.0, 0.0, 1.0)
    ))

    obj.matrix_local = matrix
