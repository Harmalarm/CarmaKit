"""
Carmageddon model importer for Blender.

This module handles importing Carmageddon DAT, ACT, and MAT files
into Blender as meshes, empties, and materials.


"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

from .classes.act_classes import (
    ActFile,
    ActorNode,
)
from .classes.dat_classes import (
    DatFile,
    DatModel,
)
from .classes.mat_classes import (
    Material as CarMaterial,
    MatFile,
)
from .parsers.act_parser import parse_act_file
from .parsers.dat_parser import parse_dat_file
from .parsers.groove_parser import (
    normalize_actor_name,
    parse_groove_sections,
)
from .parsers.mat_parser import parse_mat_file
from .parsers.utils import ParseError, find_related_files
from .utils.general_utils import cleanup_scene
from .constants import BRU_SCALE_FACTOR


def _log_debug(message: str) -> None:
    """
    Log a debug message when debug logging is enabled.

    :param message: The message to log.
    :type message: str
    :return: None.
    :rtype: None
    """
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs.debug_logging:
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
        _log_debug(f"    Found model with key '{key}'")
        return models[key]

    _log_debug(f"    Model key '{key}' not found")
    return None


def _find_groove_txt_path(base_path: str, base_name: str) -> Optional[str]:
    """
    Locate a groove text file matching the base name.

    :param base_path: Directory containing the model files.
    :type base_path: str
    :param base_name: Base name for the model files.
    :type base_name: str
    :return: Path to the groove text file when found.
    :rtype: Optional[str]
    """
    for ext in [".txt", ".TXT"]:
        candidate = os.path.join(base_path, base_name + ext)
        if os.path.exists(candidate):
            return candidate

    return None


def _load_groove_map(
    filepath: str,
    act_path: Optional[str],
    dat_path: Optional[str]
) -> Dict[str, List["GrooveDefinition"]]:
    """
    Load groove definitions and map them by actor name.

    :param filepath: Original import filepath.
    :type filepath: str
    :param act_path: Related ACT file path.
    :type act_path: Optional[str]
    :param dat_path: Related DAT file path.
    :type dat_path: Optional[str]
    :return: Mapping of normalized actor names to groove definitions.
    :rtype: Dict[str, List[GrooveDefinition]]
    """
    reference_path = act_path or dat_path or filepath
    base_path = os.path.dirname(reference_path)
    base_name = os.path.splitext(os.path.basename(reference_path))[0]
    txt_path = _find_groove_txt_path(base_path, base_name)
    if not txt_path:
        return {}

    try:
        result = parse_groove_sections(txt_path)
    except Exception as exc:
        _log_debug(f"Failed to parse groove file: {exc}")
        return {}

    _log_debug(
        f"Parsed {len(result.grooves)} grooves from {txt_path}"
    )
    return result.by_actor_name()


def _apply_grooves_to_object(
    obj: bpy.types.Object,
    groove_map: Dict[str, List["GrooveDefinition"]]
) -> None:
    """
    Apply groove definitions to a Blender object as custom properties.

    :param obj: Blender object to update.
    :type obj: bpy.types.Object
    :param groove_map: Groove definitions mapped by actor name.
    :type groove_map: Dict[str, List[GrooveDefinition]]
    :return: None.
    :rtype: None
    """
    key = normalize_actor_name(obj.name)
    grooves = groove_map.get(key)
    if not grooves:
        return

    obj["carmakit_grooves"] = {
        str(groove.index): groove.to_custom_property()
        for groove in grooves
    }
    _log_debug(
        f"Attached {len(grooves)} grooves to object '{obj.name}'"
    )


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
    :param cleanup_scene: Whether to clean the scene before import.
    :type cleanup_scene: bool
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
    _apply_bru_import_scale(options)
    _log_debug(f"Starting import of: {options.filepath}")
    _log_debug(
        f"Options: scale={options.scale}, apply_transform={options.apply_transform}, "
        f"import_materials={options.import_materials}, import_textures={options.import_textures}, "
        f"cleanup_scene={options.cleanup_scene}"
    )

    try:
        if options.cleanup_scene:
            _log_debug("Cleaning up scene before import...")
            cleanup_scene(context)

        # Find related files.
        _log_debug("Searching for related files...")
        act_path, dat_path, mat_path = find_related_files(options.filepath)
        _log_debug(f"  ACT file: {act_path or 'not found'}")
        _log_debug(f"  DAT file: {dat_path or 'not found'}")
        _log_debug(f"  MAT file: {mat_path or 'not found'}")

        # Determine which file was selected and adjust paths.
        ext = os.path.splitext(options.filepath)[1].lower()
        if ext == '.act':
            act_path = options.filepath
        elif ext == '.dat':
            dat_path = options.filepath

        # Load materials first.
        materials: Dict[str, bpy.types.Material] = {}
        if options.import_materials and mat_path:
            _log_debug(f"Loading materials from: {mat_path}")
            try:
                mat_file = parse_mat_file(mat_path)
                _log_debug(
                    f"  Parsed {len(mat_file.materials)} materials from MAT file"
                )
                materials = _create_blender_materials(
                    mat_file,
                    os.path.dirname(mat_path),
                    options.import_textures
                )
                _log_debug(f"  Created {len(materials)} Blender materials")
            except Exception as e:
                print(f"Warning: Could not load materials: {e}")
                _log_debug(f"  ERROR loading materials: {e}")

        # Load DAT models.
        models: Dict[str, DatModel] = {}
        if dat_path:
            _log_debug(f"Loading models from: {dat_path}")
            try:
                dat_file = parse_dat_file(dat_path)
                _log_debug(
                    f"  Parsed DAT file with {len(dat_file.models)} models"
                )
                for model in dat_file.models:
                    # Store with uppercase name including .DAT extension.
                    key = model.name.upper()
                    if not key.endswith('.DAT'):
                        key = key + '.DAT'
                    models[key] = model
                    _log_debug(
                        f"    Model '{model.name}': {len(model.vertices)} "
                        f"verts, {len(model.faces)} faces"
                    )
                    _log_debug(f"      Registered key: '{key}'")
            except Exception as e:
                _log_debug(f"  ERROR parsing DAT file: {e}")
                result.error_message = f"Failed to parse DAT file: {e}"
                result.success = False
                return result

        groove_map = _load_groove_map(options.filepath, act_path, dat_path)

        # Load ACT hierarchy or create simple scene from DAT.
        if act_path:
            _log_debug(f"Loading ACT hierarchy from: {act_path}")
            try:
                act_file = parse_act_file(act_path)
                _log_debug(f"  ACT file parsed, root node: {act_file.root.name if act_file.root else 'None'}")
                if act_file.root:
                    _log_debug("  Creating Blender hierarchy from ACT...")
                    objects = _create_hierarchy_from_act(
                        context,
                        act_file.root,
                        models,
                        materials,
                        options,
                        None,
                        groove_map
                    )
                    result.objects_created = len(objects)
                    _log_debug(f"  Created {len(objects)} objects from ACT hierarchy")
            except Exception as e:
                _log_debug(f"  ERROR parsing ACT file: {e}")
                result.error_message = f"Failed to parse ACT file: {e}"
                result.success = False
                return result
        else:
            # No ACT file, just import DAT models directly.
            _log_debug(f"No ACT file, importing {len(models)} models directly from DAT")
            for model in models.values():
                _log_debug(f"  Creating mesh for model: {model.name}")
                obj = _create_mesh_from_model(
                    context, model, materials, options, None
                )
                if obj:
                    _apply_grooves_to_object(obj, groove_map)
                result.objects_created += 1
                _log_debug(f"    Done creating mesh for {model.name}")

    except Exception as e:
        result.error_message = str(e)
        result.success = False
        _log_debug(f"Import failed with exception: {e}")

    _log_debug(f"Import complete: success={result.success}, objects_created={result.objects_created}")
    if result.error_message:
        _log_debug(f"  Error message: {result.error_message}")
    return result


def _apply_bru_import_scale(options: ImportOptions) -> None:
    """
    Apply BRU unit conversion to the import scale when enabled.

    :param options: Import options to update.
    :type options: ImportOptions
    :return: None.
    :rtype: None
    """
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs.use_bru_scale:
            options.scale *= BRU_SCALE_FACTOR
            _log_debug(
                "BRU conversion enabled; import scale multiplied by "
                f"{BRU_SCALE_FACTOR}"
            )
    except (KeyError, AttributeError):
        # Addon preferences not available, skip scaling.
        pass


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

    # Get game folder from preferences for texture fallback search.
    game_folder = None
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs.game_folder:
            game_folder = prefs.game_folder
            _log_debug(f"  Game folder set: {game_folder}")
    except (KeyError, AttributeError):
        pass

    for car_mat in mat_file.materials:
        # Create or get existing material using case-insensitive lookup.
        mat_name = car_mat.name
        mat_key = mat_name.lower()

        # Check if material already exists (case-insensitive).
        existing_mat = None
        for existing in bpy.data.materials:
            if existing.name.lower() == mat_key:
                existing_mat = existing
                _log_debug(f"  Reusing existing material: '{existing.name}'")
                break

        if existing_mat:
            mat = existing_mat
        else:
            mat = bpy.data.materials.new(name=mat_name)
            _log_debug(f"  Created new material: '{mat_name}'")

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
            tex_path = _find_texture(base_path, car_mat.texture_name, game_folder)
            if tex_path:
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.location = (-300, 0)

                try:
                    # Check if image already exists to avoid duplicates.
                    existing_image = None
                    tex_basename = os.path.basename(tex_path)
                    for img in bpy.data.images:
                        if img.filepath and os.path.basename(img.filepath) == tex_basename:
                            existing_image = img
                            break

                    if existing_image:
                        tex_node.image = existing_image
                        _log_debug(f"    Reusing existing texture: {tex_basename}")
                    else:
                        tex_node.image = bpy.data.images.load(tex_path)
                        _log_debug(f"    Loaded texture: {tex_path}")

                    links.new(
                        tex_node.outputs['Color'],
                        bsdf.inputs['Base Color']
                    )

                    # Check if image has alpha channel with actual transparency.
                    img = tex_node.image
                    if img and img.channels == 4:
                        # Check if alpha channel has any non-opaque pixels.
                        # Skip transparency if alpha is completely white (255).
                        has_transparency = False
                        try:
                            pixels = img.pixels[:]
                            # Alpha is every 4th value starting at index 3.
                            for i in range(3, len(pixels), 4):
                                if pixels[i] < 1.0:  # Alpha values are 0.0-1.0.
                                    has_transparency = True
                                    break
                        except Exception:
                            # If we can't read pixels, assume no transparency.
                            has_transparency = False

                        if has_transparency:
                            # Connect alpha channel to BSDF alpha input.
                            links.new(
                                tex_node.outputs['Alpha'],
                                bsdf.inputs['Alpha']
                            )
                            # Set material blend mode to support transparency.
                            mat.blend_method = 'BLEND'
                            mat.shadow_method = 'CLIP'
                            _log_debug(f"    Enabled alpha transparency for texture")
                        else:
                            _log_debug(f"    Texture has alpha channel but is fully opaque, skipping transparency")

                except Exception as e:
                    _log_debug(f"    WARNING: Failed to load texture '{tex_path}': {e}")
            else:
                _log_debug(f"    WARNING: Texture '{car_mat.texture_name}' not found in tiffrgb or textures folders")

        result[mat_key] = mat

    return result


def _find_texture(
    base_path: str,
    texture_name: str,
    game_folder: Optional[str] = None
) -> Optional[str]:
    """
    Find a texture file by name.

    Searches for various image formats in the base path and common
    subdirectories. If not found and game_folder is set, also searches
    in the game's PIXELMAP/tiffrgb folder.

    :param base_path: Base directory to search.
    :type base_path: str
    :param texture_name: Name of the texture (without extension).
    :type texture_name: str
    :param game_folder: Path to Carmageddon game installation folder.
    :type game_folder: Optional[str]
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

    # Add neighboring folders that share the first 4 characters of the
    # current folder name. Some tracks store textures in sibling folders
    # (e.g., airport1 textures in airp/TIFFRGB).
    folder_name = os.path.basename(base_path.rstrip('/\\'))
    if len(folder_name) >= 4:
        prefix = folder_name[:4].lower()
        parent_dir = os.path.dirname(base_path.rstrip('/\\'))
        if os.path.isdir(parent_dir):
            try:
                for sibling in os.listdir(parent_dir):
                    sibling_lower = sibling.lower()
                    # Skip the current folder itself.
                    if sibling_lower == folder_name.lower():
                        continue
                    # Check if sibling starts with the same 4-character prefix.
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
                # Ignore permission errors when listing directories.
                pass

    # Add game folder pixelmap paths if game_folder is set.
    if game_folder:
        game_folder = game_folder.rstrip('/\\')  # Remove trailing slashes.
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


def _create_hierarchy_from_act(
    context: bpy.types.Context,
    node: ActorNode,
    models: Dict[str, DatModel],
    materials: Dict[str, bpy.types.Material],
    options: ImportOptions,
    parent: Optional[bpy.types.Object],
    groove_map: Dict[str, List["GrooveDefinition"]]
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
    :param groove_map: Groove definitions mapped by actor name.
    :type groove_map: Dict[str, List[GrooveDefinition]]
    :return: List of created Blender objects.
    :rtype: List[bpy.types.Object]
    """
    created_objects: List[bpy.types.Object] = []
    _log_debug(f"Processing ACT node: '{node.name}' (model_name='{node.model_name}', children={len(node.children)})")
    if node.materials:
        _log_debug(f"  ACT node has materials: {node.materials}")

    # Check if this node references a model.
    if node.model_name:
        _log_debug(f"  Looking for model: '{node.model_name}'")
        found_model = _find_model_in_dict(node.model_name, models)

        if found_model:
            _log_debug(f"  Found model '{found_model.name}', creating mesh...")
            # Use ACT node materials if specified, otherwise use DAT materials.
            act_materials = node.materials if node.materials else None
            obj = _create_mesh_from_model(
                context,
                found_model,
                materials,
                options,
                parent,
                act_materials
            )
            if obj:
                obj.name = node.name
                _log_debug(f"  Created mesh object: '{obj.name}'")
                if options.apply_transform:
                    _log_debug(f"    Applying transform to '{obj.name}'")
                    _apply_transform(obj, node, options.scale)
                _apply_grooves_to_object(obj, groove_map)
                created_objects.append(obj)
                parent = obj
            else:
                _log_debug(f"  WARNING: _create_mesh_from_model returned None for '{found_model.name}'")
        else:
            _log_debug(f"  Model '{node.model_name}' not found in loaded models, available: {list(models.keys())}")
            # Create empty for hierarchy node.
            _log_debug(f"  Creating empty for missing model node: '{node.name}'")
            obj = _create_empty(context, node.name, parent)
            if options.apply_transform:
                _apply_transform(obj, node, options.scale)
            _apply_grooves_to_object(obj, groove_map)
            created_objects.append(obj)
            parent = obj
    else:
        # Create empty for hierarchy node without model.
        _log_debug(f"  Node '{node.name}' has no model, creating empty")
        obj = _create_empty(context, node.name, parent)
        if options.apply_transform:
            _apply_transform(obj, node, options.scale)
        _apply_grooves_to_object(obj, groove_map)
        created_objects.append(obj)
        parent = obj

    # Process children recursively.
    if node.children:
        _log_debug(f"  Processing {len(node.children)} children of '{node.name}'")
    for child in node.children:
        child_objects = _create_hierarchy_from_act(
            context, child, models, materials, options, parent, groove_map
        )
        created_objects.extend(child_objects)

    _log_debug(f"  Finished node '{node.name}', created {len(created_objects)} objects")
    return created_objects


def _create_mesh_from_model(
    context: bpy.types.Context,
    model: DatModel,
    materials: Dict[str, bpy.types.Material],
    options: ImportOptions,
    parent: Optional[bpy.types.Object],
    act_materials: Optional[List[str]] = None
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
    :param act_materials: Material names from ACT file (overrides DAT).
    :type act_materials: Optional[List[str]]
    :return: Created Blender object.
    :rtype: Optional[bpy.types.Object]
    """
    _log_debug(f"  _create_mesh_from_model: '{model.name}' - {len(model.vertices)} verts, {len(model.faces)} faces")
    if not model.vertices or not model.faces:
        _log_debug(f"    WARNING: Model '{model.name}' has no vertices or faces, skipping")
        return None

    # Create mesh.
    _log_debug(f"    Creating Blender mesh...")
    mesh = bpy.data.meshes.new(name=model.name)
    obj = bpy.data.objects.new(model.name, mesh)

    # Link to scene.
    context.collection.objects.link(obj)

    # Set parent.
    if parent:
        obj.parent = parent

    # Create bmesh.
    _log_debug(f"    Creating bmesh and adding vertices...")
    bm = bmesh.new()

    # Add vertices with axis conversion.
    # Carmageddon uses Y-up, Blender uses Z-up.
    # Convert: X stays, Y becomes Z, Z becomes -Y.
    scale = options.scale
    for v in model.vertices:
        bm.verts.new((v.x * scale, -v.z * scale, v.y * scale))

    bm.verts.ensure_lookup_table()
    _log_debug(f"    Added {len(bm.verts)} vertices to bmesh (with Y-up to Z-up conversion)")

    # Determine which material list to use.
    # ACT materials override DAT materials when specified.
    material_names = act_materials if act_materials else model.materials
    if act_materials:
        _log_debug(f"    Using ACT materials: {act_materials}")
    else:
        _log_debug(f"    Using DAT materials: {model.materials}")

    # Add materials to mesh.
    mat_name_to_index: Dict[str, int] = {}
    for mat_name in material_names:
        mat_key = mat_name.lower()
        if mat_key in materials:
            blender_mat = materials[mat_key]
        else:
            # Check if material exists in bpy.data.materials (case-insensitive).
            existing_mat = None
            for existing in bpy.data.materials:
                if existing.name.lower() == mat_key:
                    existing_mat = existing
                    break

            if existing_mat:
                blender_mat = existing_mat
                _log_debug(f"    Reusing existing material: '{existing_mat.name}'")
            else:
                # Create placeholder material.
                blender_mat = bpy.data.materials.new(name=mat_name)
                blender_mat.use_nodes = True
                _log_debug(f"    Created placeholder material: '{mat_name}'")

        mesh.materials.append(blender_mat)
        mat_name_to_index[mat_key] = len(mesh.materials) - 1

    # Add faces.
    _log_debug(f"    Adding {len(model.faces)} faces...")
    uv_layer = bm.loops.layers.uv.new("UVMap")
    faces_created = 0
    faces_failed = 0

    # Track face smoothing groups for edge smoothing calculation.
    face_smoothing_groups: Dict[int, int] = {}  # bmesh face index -> smoothing group

    for face_idx, face in enumerate(model.faces):
        try:
            verts = [
                bm.verts[face.v1],
                bm.verts[face.v2],
                bm.verts[face.v3]
            ]
            bm_face = bm.faces.new(verts)

            # Store smoothing group for later edge processing.
            face_smoothing_groups[bm_face.index] = face.smoothing_group

            # Set material index.
            if face.material_index > 0 and face.material_index <= len(
                material_names
            ):
                mat_name = material_names[face.material_index - 1].lower()
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

    _log_debug(f"    Faces created: {faces_created}, failed: {faces_failed}")

    # Apply smoothing groups by marking edges as sharp or smooth.
    # An edge is sharp if adjacent faces have different smoothing groups.
    _log_debug(f"    Processing smoothing groups...")
    bm.edges.ensure_lookup_table()
    sharp_edges = 0
    smooth_edges = 0

    for edge in bm.edges:
        linked_faces = edge.link_faces
        if len(linked_faces) == 2:
            # Get smoothing groups of both adjacent faces.
            sg1 = face_smoothing_groups.get(linked_faces[0].index, 0)
            sg2 = face_smoothing_groups.get(linked_faces[1].index, 0)

            if sg1 != sg2:
                # Different smoothing groups -> sharp edge.
                edge.smooth = False
                sharp_edges += 1
            else:
                # Same smoothing group -> smooth edge.
                edge.smooth = True
                smooth_edges += 1
        elif len(linked_faces) == 1:
            # Boundary edge - mark as sharp.
            edge.smooth = False
            sharp_edges += 1
        else:
            # No faces or more than 2 faces - default to smooth.
            edge.smooth = True
            smooth_edges += 1

    _log_debug(f"    Smoothing: {sharp_edges} sharp edges, {smooth_edges} smooth edges")

    _log_debug(f"    Converting bmesh to mesh...")
    bm.to_mesh(mesh)
    bm.free()

    # Apply edge visibility (hidden edges) after bmesh conversion.
    # This must be done on the final mesh, not bmesh.
    _log_debug(f"    Processing edge visibility...")
    hidden_edges = 0
    for face_idx, face in enumerate(model.faces):
        if face_idx >= len(mesh.polygons):
            break

        edgevis = face.edge_visibility
        if edgevis == 0:
            continue  # All edges visible.

        poly = mesh.polygons[face_idx]
        loop_start = poly.loop_start

        # Get edge indices for this face's loops.
        # Each loop corresponds to an edge.
        for i in range(3):
            edge_hidden = False
            if i == 0 and (edgevis & 1):  # Bit 0: Edge 0
                edge_hidden = True
            elif i == 1 and (edgevis & 2):  # Bit 1: Edge 1
                edge_hidden = True
            elif i == 2 and (edgevis & 4):  # Bit 2: Edge 2
                edge_hidden = True

            if edge_hidden:
                loop_idx = loop_start + i
                if loop_idx < len(mesh.loops):
                    edge_idx = mesh.loops[loop_idx].edge_index
                    mesh.edges[edge_idx].hide = True
                    hidden_edges += 1

    _log_debug(f"    Hidden edges: {hidden_edges}")

    # Enable auto smooth for the mesh to respect sharp edges.
    # Note: use_auto_smooth was deprecated in Blender 4.1+.
    try:
        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = 3.14159  # 180 degrees - let sharp marks control.
    except AttributeError:
        # Blender 4.1+ uses sharp edges directly without auto_smooth.
        pass

    # Enable smooth shading on all polygons to show smoothing groups effect.
    for poly in mesh.polygons:
        poly.use_smooth = True
    _log_debug(f"    Enabled smooth shading on {len(mesh.polygons)} polygons")

    # Update mesh.
    mesh.update()
    _log_debug(f"    Mesh '{model.name}' created successfully")

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

    Converts from Carmageddon Y-up to Blender Z-up coordinate system by
    decomposing the matrix into rotation, translation, and scale, then
    re-arranging axes appropriately.

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
    # Layout: x1,x2,x3, y1,y2,y3, z1,z2,z3, p1,p2,p3
    m = node.transform.values

    # Build original matrix in Carmageddon format.
    act_matrix = Matrix((
        (m[0], m[1], m[2], m[9]),
        (m[3], m[4], m[5], m[10]),
        (m[6], m[7], m[8], m[11]),
        (0.0, 0.0, 0.0, 1.0)
    ))

    # Extract rotation as Euler and re-arrange for Y-up to Z-up conversion.
    euler = act_matrix.to_euler('XYZ')
    rotation_matrix = Euler(
        (-euler.x, euler.z, -euler.y), 'YZX'
    ).to_matrix().to_4x4()

    # Create translation matrix with axis swap: X stays, Y becomes -Z, Z becomes Y.
    p1 = m[9] * scale
    p2 = m[10] * scale
    p3 = m[11] * scale
    translation_matrix = Matrix.Translation(Vector((p1, -p3, p2)))

    # Extract scale from column lengths and re-arrange.
    scale_x = act_matrix.col[0].xyz.length
    scale_y = act_matrix.col[1].xyz.length
    scale_z = act_matrix.col[2].xyz.length
    scale_matrix = Matrix.Diagonal(
        Vector((scale_x, scale_z, scale_y, 1.0))
    )

    # Compose final transformation matrix.
    transformation_matrix = translation_matrix @ rotation_matrix @ scale_matrix

    # Apply using matrix_world to properly handle parent relationships.
    # When parent exists, multiply with parent's world matrix.
    if obj.parent is not None:
        obj.matrix_world = transformation_matrix @ obj.parent.matrix_world
    else:
        obj.matrix_world = transformation_matrix
