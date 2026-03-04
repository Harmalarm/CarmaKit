"""
Track preprocessing operator for CarmaKit.
"""

from dataclasses import dataclass, field
import bisect
from typing import Dict, List, Optional, Set, Tuple

import bpy
import bmesh
from bpy.types import Context, Operator
from mathutils import Vector


_SPECIAL_NAME_PREFIXES = ('&', '%', '$', '!', '£', '#')


@dataclass
class _QuadNode:
    """
    Quadtree node for track chunks.
    """

    row_start: int
    row_end: int
    col_start: int
    col_end: int
    children: List["_QuadNode"] = field(default_factory=list)
    empty: Optional[bpy.types.Object] = None


def _is_excluded_object(obj: bpy.types.Object) -> bool:
    """
    Check if an object should be excluded from preprocessing.
    """
    return obj.name.startswith(_SPECIAL_NAME_PREFIXES)


def _collect_source_meshes(
    context: Context
) -> List[bpy.types.Object]:
    """
    Collect mesh objects for preprocessing.
    """
    return [
        obj for obj in context.scene.objects
        if obj.type == 'MESH' and not _is_excluded_object(obj)
    ]


def _collect_special_objects(context: Context) -> List[bpy.types.Object]:
    """
    Collect special-character objects excluded from mesh cutting.
    """
    return [
        obj for obj in context.scene.objects
        if _is_excluded_object(obj)
    ]


def _build_material_index(
    objects: List[bpy.types.Object]
) -> Tuple[List[bpy.types.Material], Dict[bpy.types.Material, int]]:
    """
    Build a global material list and index.
    """
    materials: List[bpy.types.Material] = []
    mat_index: Dict[bpy.types.Material, int] = {}
    for obj in objects:
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat not in mat_index:
                mat_index[mat] = len(materials)
                materials.append(mat)
    return materials, mat_index


def _remap_face_materials(
    bm: bmesh.types.BMesh,
    obj: bpy.types.Object,
    mat_index: Dict[bpy.types.Material, int]
) -> None:
    """
    Remap face material indices to a global material list.
    """
    slots = obj.material_slots
    for face in bm.faces:
        slot_index = face.material_index
        if 0 <= slot_index < len(slots):
            mat = slots[slot_index].material
            if mat and mat in mat_index:
                face.material_index = mat_index[mat]
                continue
        face.material_index = 0


def _merge_meshes_to_bmesh(
    context: Context,
    objects: List[bpy.types.Object],
    mat_index: Dict[bpy.types.Material, int]
) -> bmesh.types.BMesh:
    """
    Merge mesh objects into a single bmesh in world space.
    """
    depsgraph = context.evaluated_depsgraph_get()
    merged = bmesh.new()

    for obj in objects:
        obj_eval = obj.evaluated_get(depsgraph)
        mesh = obj_eval.to_mesh()
        if not mesh:
            continue

        try:
            verts_before = len(merged.verts)
            faces_before = len(merged.faces)

            merged.from_mesh(mesh)
            merged.verts.ensure_lookup_table()
            merged.faces.ensure_lookup_table()

            added_verts = merged.verts[verts_before:]
            if added_verts:
                bmesh.ops.transform(
                    merged,
                    matrix=obj.matrix_world,
                    verts=added_verts
                )

            added_faces = merged.faces[faces_before:]
            if added_faces:
                slots = obj.material_slots
                for face in added_faces:
                    slot_index = face.material_index
                    if 0 <= slot_index < len(slots):
                        mat = slots[slot_index].material
                        if mat and mat in mat_index:
                            face.material_index = mat_index[mat]
                            continue
                    face.material_index = 0
        finally:
            obj_eval.to_mesh_clear()

    return merged


def _compute_bounds(
    bm: bmesh.types.BMesh
) -> Tuple[float, float, float, float]:
    """
    Compute XY bounds for a bmesh.
    """
    if not bm.verts:
        return 0.0, 0.0, 0.0, 0.0

    min_x = min(v.co.x for v in bm.verts)
    max_x = max(v.co.x for v in bm.verts)
    min_y = min(v.co.y for v in bm.verts)
    max_y = max(v.co.y for v in bm.verts)
    return min_x, max_x, min_y, max_y


def _grid_edges(min_val: float, max_val: float, count: int) -> List[float]:
    """
    Build grid edge positions.
    """
    if count <= 0:
        return [min_val, max_val]
    if max_val == min_val:
        return [min_val + i for i in range(count + 1)]
    step = (max_val - min_val) / count
    return [min_val + step * i for i in range(count + 1)]


def _bisect_by_grid(
    bm: bmesh.types.BMesh,
    x_edges: List[float],
    y_edges: List[float]
) -> None:
    """
    Slice the mesh along grid boundaries.
    """
    for x in x_edges[1:-1]:
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(
            bm,
            geom=geom,
            plane_co=(x, 0.0, 0.0),
            plane_no=(1.0, 0.0, 0.0),
            clear_inner=False,
            clear_outer=False,
        )

    for y in y_edges[1:-1]:
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(
            bm,
            geom=geom,
            plane_co=(0.0, y, 0.0),
            plane_no=(0.0, 1.0, 0.0),
            clear_inner=False,
            clear_outer=False,
        )


def _assign_faces_to_cells(
    bm: bmesh.types.BMesh,
    x_edges: List[float],
    y_edges: List[float]
) -> Dict[Tuple[int, int], List[bmesh.types.BMFace]]:
    """
    Map faces to grid cells using their centroid.
    """
    faces_by_cell: Dict[Tuple[int, int], List[bmesh.types.BMFace]] = {}
    cols = max(1, len(x_edges) - 1)
    rows = max(1, len(y_edges) - 1)

    for face in bm.faces:
        center = face.calc_center_median()
        col = bisect.bisect_right(x_edges, center.x) - 1
        row = bisect.bisect_right(y_edges, center.y) - 1
        col = max(0, min(cols - 1, col))
        row = max(0, min(rows - 1, row))
        faces_by_cell.setdefault((row, col), []).append(face)

    return faces_by_cell


def _build_quadtree(
    row_start: int,
    row_end: int,
    col_start: int,
    col_end: int
) -> _QuadNode:
    """
    Build a quadtree node range.
    """
    node = _QuadNode(row_start, row_end, col_start, col_end)
    rows = row_end - row_start
    cols = col_end - col_start

    if rows <= 1 and cols <= 1:
        return node

    if rows >= cols and rows > 1:
        row_mid = row_start + max(1, rows // 2)
        ranges = [
            (row_start, row_mid, col_start, col_end),
            (row_mid, row_end, col_start, col_end),
        ]
    elif cols > 1:
        col_mid = col_start + max(1, cols // 2)
        ranges = [
            (row_start, row_end, col_start, col_mid),
            (row_start, row_end, col_mid, col_end),
        ]
    else:
        return node

    for r0, r1, c0, c1 in ranges:
        if r1 <= r0 or c1 <= c0:
            continue
        node.children.append(_build_quadtree(r0, r1, c0, c1))

    return node


def _unique_collection_name(base_name: str) -> str:
    """
    Create a unique collection name.
    """
    name = base_name
    index = 1
    while name in bpy.data.collections:
        name = f"{base_name} {index}"
        index += 1
    return name


def _create_empty(
    collection: bpy.types.Collection,
    name: str,
    location: Tuple[float, float, float],
    parent: Optional[bpy.types.Object] = None
) -> bpy.types.Object:
    """
    Create an empty object in a collection.
    """
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.location = location
    collection.objects.link(empty)

    if parent:
        world_matrix = empty.matrix_world.copy()
        empty.parent = parent
        empty.matrix_world = world_matrix

    return empty


def _node_center(
    node: _QuadNode,
    x_edges: List[float],
    y_edges: List[float]
) -> Tuple[float, float, float]:
    """
    Compute node center for empty placement.
    """
    x0 = x_edges[node.col_start]
    x1 = x_edges[node.col_end]
    y0 = y_edges[node.row_start]
    y1 = y_edges[node.row_end]
    return (x0 + x1) * 0.5, (y0 + y1) * 0.5, 0.0


def _create_quadtree_empties(
    collection: bpy.types.Collection,
    node: _QuadNode,
    x_edges: List[float],
    y_edges: List[float],
    root_name: str,
    cells_with_special: Set[Tuple[int, int]],
    unnamed_counter: List[int],
    parent: Optional[bpy.types.Object] = None,
) -> None:
    """
    Create empties for quadtree nodes.
    """
    if parent is None:
        name = root_name
    elif node.children:
        name = f"NO_IDENTIFIER.{unnamed_counter[0]:03d}"
        unnamed_counter[0] += 1
    else:
        if (node.row_start, node.col_start) not in cells_with_special:
            node.empty = parent
            return
        name = _leaf_node_name(node.row_start, node.col_start)

    center = _node_center(node, x_edges, y_edges)
    node.empty = _create_empty(collection, name, center, parent)

    for child in node.children:
        _create_quadtree_empties(
            collection,
            child,
            x_edges,
            y_edges,
            root_name,
            cells_with_special,
            unnamed_counter,
            node.empty,
        )


def _create_mesh_from_faces(
    bm: bmesh.types.BMesh,
    faces: List[bmesh.types.BMFace],
    name: str
) -> bpy.types.Mesh:
    """
    Build a new mesh from a face subset.
    """
    new_bm = bmesh.new()
    vert_map: Dict[bmesh.types.BMVert, bmesh.types.BMVert] = {}
    src_uv = bm.loops.layers.uv.active
    dst_uv = None
    if src_uv:
        dst_uv = new_bm.loops.layers.uv.new(src_uv.name)

    for face in faces:
        new_verts = []
        for vert in face.verts:
            if vert not in vert_map:
                vert_map[vert] = new_bm.verts.new(vert.co)
            new_verts.append(vert_map[vert])
        new_face = new_bm.faces.new(new_verts)
        new_face.material_index = face.material_index
        if src_uv and dst_uv:
            for src_loop, dst_loop in zip(face.loops, new_face.loops):
                dst_loop[dst_uv].uv = src_loop[src_uv].uv.copy()

    new_mesh = bpy.data.meshes.new(name)
    new_bm.to_mesh(new_mesh)
    new_bm.free()
    new_mesh.update()
    return new_mesh


def _leaf_node_name(row: int, col: int) -> str:
    """
    Build a leaf helper node name.
    """
    return f"{row} {col}"


def _collect_special_cells(
    special_objects: List[bpy.types.Object],
    x_edges: List[float],
    y_edges: List[float]
) -> Set[Tuple[int, int]]:
    """
    Collect grid cells that contain special objects.
    """
    cells: Set[Tuple[int, int]] = set()
    for obj in special_objects:
        leaf = _find_leaf_by_origin(obj, x_edges, y_edges)
        if leaf is not None:
            cells.add((leaf.row_start, leaf.col_start))
    return cells


def _find_leaf_empty(
    node: _QuadNode,
    row: int,
    col: int
) -> Optional[bpy.types.Object]:
    """
    Find the leaf empty for a given cell.
    """
    if not node.children:
        if node.row_start == row and node.col_start == col:
            return node.empty
        return None

    for child in node.children:
        if child.row_start <= row < child.row_end:
            if child.col_start <= col < child.col_end:
                return _find_leaf_empty(child, row, col)
    return None


def _create_chunk_objects(
    collection: bpy.types.Collection,
    bm: bmesh.types.BMesh,
    faces_by_cell: Dict[Tuple[int, int], List[bmesh.types.BMFace]],
    materials: List[bpy.types.Material],
    root: _QuadNode,
    cols: int,
) -> int:
    """
    Create mesh objects for each populated cell.
    """
    created = 0
    for (row, col), faces in sorted(faces_by_cell.items()):
        if not faces:
            continue

        leaf_empty = _find_leaf_empty(root, row, col)
        mesh_name = f"{row} {col}"
        if leaf_empty and leaf_empty.name == mesh_name:
            object_name = f"{(row * cols) + col:08d}"
        else:
            object_name = mesh_name
        mesh = _create_mesh_from_faces(bm, faces, mesh_name)
        for mat in materials:
            mesh.materials.append(mat)

        obj = bpy.data.objects.new(object_name, mesh)
        collection.objects.link(obj)

        if leaf_empty:
            world_matrix = obj.matrix_world.copy()
            obj.parent = leaf_empty
            obj.matrix_world = world_matrix

        created += 1

    return created


def _contains_origin_in_node(
    origin: Vector,
    node: _QuadNode,
    x_edges: List[float],
    y_edges: List[float]
) -> bool:
    """
    Check whether an origin lies inside a node's XY bounds.
    """
    x0 = x_edges[node.col_start]
    x1 = x_edges[node.col_end]
    y0 = y_edges[node.row_start]
    y1 = y_edges[node.row_end]

    in_x = x0 <= origin.x <= x1
    in_y = y0 <= origin.y <= y1
    return in_x and in_y


def _find_leaf_by_origin(
    obj: bpy.types.Object,
    x_edges: List[float],
    y_edges: List[float],
) -> Optional[_QuadNode]:
    """
    Find the quadtree leaf that contains the object's origin.
    """
    rows = max(1, len(y_edges) - 1)
    cols = max(1, len(x_edges) - 1)
    root = _build_quadtree(0, rows, 0, cols)

    origin = obj.matrix_world.translation
    node = root
    while node.children:
        next_child: Optional[_QuadNode] = None
        for child in node.children:
            if _contains_origin_in_node(origin, child, x_edges, y_edges):
                next_child = child
                break

        if next_child is None:
            break

        node = next_child

    if _contains_origin_in_node(origin, node, x_edges, y_edges):
        return node

    return None


def _parent_special_objects_to_quadtree(
    special_objects: List[bpy.types.Object],
    root: _QuadNode,
    x_edges: List[float],
    y_edges: List[float]
) -> int:
    """
    Parent special-character objects to their quadtree leaf helper.
    """
    parented = 0
    for obj in special_objects:
        leaf_node = _find_leaf_by_origin(obj, x_edges, y_edges)
        if not leaf_node:
            continue

        leaf_empty = _find_leaf_empty(
            root,
            leaf_node.row_start,
            leaf_node.col_start
        )
        if not leaf_empty:
            continue

        world_matrix = obj.matrix_world.copy()
        obj.parent = leaf_empty
        obj.matrix_world = world_matrix
        parented += 1

    return parented


def _remove_source_meshes(objects: List[bpy.types.Object]) -> int:
    """
    Remove original source mesh objects after chunk generation.
    """
    removed = 0
    for obj in objects:
        if obj and obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1
    return removed


class CARMAKIT_OT_preprocess_track(Operator):
    """
    Preprocess track geometry into quadtree chunks.
    """

    bl_idname = "carmakit.preprocess_track"
    bl_label = "Preprocess Track"
    bl_description = "Cut track geometry into quadtree chunks"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: Context) -> Set[str]:
        """
        Execute the preprocessing operation.
        """
        cols = max(1, int(context.scene.carmakit_pp_cols_x))
        rows = max(1, int(context.scene.carmakit_pp_cols_y))

        sources = _collect_source_meshes(context)
        special_objects = _collect_special_objects(context)
        if not sources:
            self.report({'ERROR'}, "No valid mesh objects found")
            return {'CANCELLED'}

        materials, mat_index = _build_material_index(sources)
        merged = _merge_meshes_to_bmesh(context, sources, mat_index)
        if not merged.verts:
            merged.free()
            self.report({'ERROR'}, "Merged mesh has no geometry")
            return {'CANCELLED'}

        min_x, max_x, min_y, max_y = _compute_bounds(merged)
        x_edges = _grid_edges(min_x, max_x, cols)
        y_edges = _grid_edges(min_y, max_y, rows)

        _bisect_by_grid(merged, x_edges, y_edges)
        faces_by_cell = _assign_faces_to_cells(merged, x_edges, y_edges)
        cells_with_special = _collect_special_cells(
            special_objects,
            x_edges,
            y_edges
        )

        noncars = len(special_objects)
        root_name = f"PP01 {cols} {rows} 0 {noncars}"
        root = _build_quadtree(0, rows, 0, cols)
        unnamed_counter = [0]
        _create_quadtree_empties(
            context.scene.collection,
            root,
            x_edges,
            y_edges,
            root_name,
            cells_with_special,
            unnamed_counter
        )
        created = _create_chunk_objects(
            context.scene.collection,
            merged,
            faces_by_cell,
            materials,
            root,
            cols
        )
        special_parented = _parent_special_objects_to_quadtree(
            special_objects,
            root,
            x_edges,
            y_edges
        )
        removed_sources = _remove_source_meshes(sources)

        merged.free()

        self.report(
            {'INFO'},
            f"Created {created} chunk meshes and parented "
            f"{special_parented} special objects; removed "
            f"{removed_sources} source meshes"
        )
        return {'FINISHED'}
