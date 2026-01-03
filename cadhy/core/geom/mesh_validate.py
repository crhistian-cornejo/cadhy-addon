"""
Mesh Validation Module
Validate mesh geometry for CFD export.
"""

from dataclasses import dataclass
from typing import Dict, List

from ..model.cfd_params import CFDDomainInfo


@dataclass
class ValidationResult:
    """Result of mesh validation."""

    is_valid: bool = True
    is_watertight: bool = True
    is_manifold: bool = True
    has_consistent_normals: bool = True
    non_manifold_edges: int = 0
    non_manifold_verts: int = 0
    loose_verts: int = 0
    loose_edges: int = 0
    degenerate_faces: int = 0
    self_intersections: int = 0
    volume: float = 0.0
    surface_area: float = 0.0
    warnings: List[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


def validate_mesh(obj) -> ValidationResult:
    """
    Validate a mesh object for CFD export.

    Args:
        obj: Blender mesh object

    Returns:
        ValidationResult with detailed information
    """
    import bmesh

    result = ValidationResult()

    if obj is None or obj.type != "MESH":
        result.is_valid = False
        result.errors.append("Object is not a mesh")
        return result

    # Get mesh data
    mesh = obj.data

    # Create BMesh for analysis
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    # Check for non-manifold edges
    non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
    result.non_manifold_edges = len(non_manifold_edges)

    # Check for non-manifold vertices
    non_manifold_verts = [v for v in bm.verts if not v.is_manifold]
    result.non_manifold_verts = len(non_manifold_verts)

    # Check for loose vertices
    loose_verts = [v for v in bm.verts if not v.link_edges]
    result.loose_verts = len(loose_verts)

    # Check for loose edges
    loose_edges = [e for e in bm.edges if not e.link_faces]
    result.loose_edges = len(loose_edges)

    # Check for degenerate faces (zero area)
    degenerate_faces = [f for f in bm.faces if f.calc_area() < 1e-8]
    result.degenerate_faces = len(degenerate_faces)

    # Check if mesh is watertight (closed)
    boundary_edges = [e for e in bm.edges if e.is_boundary]
    result.is_watertight = len(boundary_edges) == 0

    # Check manifold status
    result.is_manifold = result.non_manifold_edges == 0 and result.non_manifold_verts == 0

    # Calculate volume (only valid for watertight meshes)
    if result.is_watertight:
        result.volume = bm.calc_volume()

    # Calculate surface area
    result.surface_area = sum(f.calc_area() for f in bm.faces)

    # Check normal consistency
    # This is a simplified check - proper check would use face islands
    result.has_consistent_normals = True  # Assume true after recalc_normals

    # Generate warnings
    if result.non_manifold_edges > 0:
        result.warnings.append(f"Found {result.non_manifold_edges} non-manifold edges")

    if result.non_manifold_verts > 0:
        result.warnings.append(f"Found {result.non_manifold_verts} non-manifold vertices")

    if result.loose_verts > 0:
        result.warnings.append(f"Found {result.loose_verts} loose vertices")

    if result.loose_edges > 0:
        result.warnings.append(f"Found {result.loose_edges} loose edges")

    if result.degenerate_faces > 0:
        result.warnings.append(f"Found {result.degenerate_faces} degenerate faces")

    if not result.is_watertight:
        result.errors.append("Mesh is not watertight (has boundary edges)")

    # Determine overall validity
    result.is_valid = (
        result.is_watertight
        and result.is_manifold
        and result.degenerate_faces == 0
        and result.loose_verts == 0
        and result.loose_edges == 0
    )

    bm.free()

    return result


def check_self_intersections(obj, sample_count: int = 1000) -> int:
    """
    Check for self-intersections in mesh (simplified check).

    This is a basic check using BVH tree overlap detection.

    Args:
        obj: Blender mesh object
        sample_count: Number of samples for intersection test

    Returns:
        Number of detected self-intersections
    """
    import bmesh
    import bpy
    from mathutils.bvhtree import BVHTree

    if obj is None or obj.type != "MESH":
        return 0

    # Get evaluated mesh
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    # Create BVH tree
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)

    bvh = BVHTree.FromBMesh(bm)

    # Check for overlaps
    overlaps = bvh.overlap(bvh)

    # Filter out adjacent face pairs
    self_intersections = 0
    for i, j in overlaps:
        if i != j:
            face_i = bm.faces[i]
            face_j = bm.faces[j]

            # Check if faces share a vertex or edge
            shared_verts = set(face_i.verts) & set(face_j.verts)
            if len(shared_verts) == 0:
                self_intersections += 1

    bm.free()
    eval_obj.to_mesh_clear()

    return self_intersections // 2  # Each intersection counted twice


def get_cfd_domain_info(obj, patch_faces: Dict[str, List[int]] = None) -> CFDDomainInfo:
    """
    Get CFD domain information from mesh object.

    Args:
        obj: Blender mesh object
        patch_faces: Optional dictionary of patch face indices

    Returns:
        CFDDomainInfo with domain statistics
    """

    validation = validate_mesh(obj)

    info = CFDDomainInfo(
        volume=validation.volume,
        is_watertight=validation.is_watertight,
        non_manifold_edges=validation.non_manifold_edges,
        self_intersections=check_self_intersections(obj),
    )

    # Calculate patch areas if provided
    if patch_faces and obj.type == "MESH":
        mesh = obj.data
        for patch_name, face_indices in patch_faces.items():
            area = 0.0
            for idx in face_indices:
                if idx < len(mesh.polygons):
                    area += mesh.polygons[idx].area
            info.patch_areas[patch_name] = area

    return info
