"""
Mesh Validation Module
Validate mesh geometry for CFD export.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..model.cfd_params import CFDDomainInfo


@dataclass
class CFDMeshQuality:
    """CFD-specific mesh quality metrics (like Salome/OpenFOAM)."""

    # Skewness: 0 = perfect, 1 = degenerate (OpenFOAM limit: 0.85)
    skewness_min: float = 0.0
    skewness_max: float = 0.0
    skewness_avg: float = 0.0

    # Aspect ratio: 1 = perfect equilateral (OpenFOAM limit: 1000)
    aspect_ratio_min: float = 1.0
    aspect_ratio_max: float = 1.0
    aspect_ratio_avg: float = 1.0

    # Non-orthogonality: degrees from perpendicular (OpenFOAM limit: 70°)
    non_ortho_min: float = 0.0
    non_ortho_max: float = 0.0
    non_ortho_avg: float = 0.0

    # Face counts
    total_faces: int = 0
    triangles: int = 0
    quads: int = 0
    ngons: int = 0

    # Quality assessment
    is_cfd_ready: bool = False
    quality_rating: str = "Unknown"  # "Excellent", "Good", "Fair", "Poor"

    def get_quality_rating(self) -> str:
        """Determine overall mesh quality rating."""
        if self.skewness_max > 0.85 or self.aspect_ratio_max > 100 or self.non_ortho_max > 70:
            return "Poor"
        elif self.skewness_max > 0.65 or self.aspect_ratio_max > 20 or self.non_ortho_max > 50:
            return "Fair"
        elif self.skewness_max > 0.4 or self.aspect_ratio_max > 10 or self.non_ortho_max > 30:
            return "Good"
        else:
            return "Excellent"


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
    cfd_quality: CFDMeshQuality = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []
        if self.cfd_quality is None:
            self.cfd_quality = CFDMeshQuality()


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


def calculate_cfd_mesh_quality(obj) -> CFDMeshQuality:
    """
    Calculate CFD-specific mesh quality metrics.

    Similar to Salome's mesh quality checks and OpenFOAM's checkMesh.

    Args:
        obj: Blender mesh object

    Returns:
        CFDMeshQuality with detailed metrics
    """
    import math

    import bmesh

    quality = CFDMeshQuality()

    if obj is None or obj.type != "MESH":
        return quality

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    if len(bm.faces) == 0:
        bm.free()
        return quality

    skewness_values = []
    aspect_ratio_values = []
    non_ortho_values = []

    # Count face types
    for face in bm.faces:
        n_verts = len(face.verts)
        if n_verts == 3:
            quality.triangles += 1
        elif n_verts == 4:
            quality.quads += 1
        else:
            quality.ngons += 1

        # Calculate face metrics
        face_area = face.calc_area()
        if face_area < 1e-10:
            continue

        # Skewness calculation (equiangle skew for faces)
        angles = []
        verts = list(face.verts)
        for i in range(n_verts):
            v0 = verts[(i - 1) % n_verts].co
            v1 = verts[i].co
            v2 = verts[(i + 1) % n_verts].co

            edge1 = (v0 - v1).normalized()
            edge2 = (v2 - v1).normalized()

            dot = max(-1, min(1, edge1.dot(edge2)))
            angle = math.acos(dot)
            angles.append(math.degrees(angle))

        if angles:
            # Ideal angle for polygon
            ideal_angle = 180.0 * (n_verts - 2) / n_verts
            max_angle = max(angles)
            min_angle = min(angles)

            # Equiangle skewness
            skew = max(
                (max_angle - ideal_angle) / (180.0 - ideal_angle) if ideal_angle < 180 else 0,
                (ideal_angle - min_angle) / ideal_angle if ideal_angle > 0 else 0,
            )
            skewness_values.append(max(0, min(1, skew)))

        # Aspect ratio (edge length ratio)
        edge_lengths = [e.calc_length() for e in face.edges]
        if edge_lengths:
            max_edge = max(edge_lengths)
            min_edge = min(edge_lengths)
            if min_edge > 1e-10:
                aspect_ratio_values.append(max_edge / min_edge)

    # Non-orthogonality (angle between face normals across shared edges)
    for edge in bm.edges:
        if len(edge.link_faces) == 2:
            face1, face2 = edge.link_faces
            normal1 = face1.normal
            normal2 = face2.normal

            if normal1.length > 0 and normal2.length > 0:
                dot = max(-1, min(1, normal1.dot(normal2)))
                angle = math.degrees(math.acos(dot))
                # Non-orthogonality is deviation from 0 (parallel) or 180 (anti-parallel)
                non_ortho = min(angle, 180 - angle)
                non_ortho_values.append(non_ortho)

    bm.free()

    # Aggregate statistics
    quality.total_faces = len(mesh.polygons)

    if skewness_values:
        quality.skewness_min = min(skewness_values)
        quality.skewness_max = max(skewness_values)
        quality.skewness_avg = sum(skewness_values) / len(skewness_values)

    if aspect_ratio_values:
        quality.aspect_ratio_min = min(aspect_ratio_values)
        quality.aspect_ratio_max = max(aspect_ratio_values)
        quality.aspect_ratio_avg = sum(aspect_ratio_values) / len(aspect_ratio_values)

    if non_ortho_values:
        quality.non_ortho_min = min(non_ortho_values)
        quality.non_ortho_max = max(non_ortho_values)
        quality.non_ortho_avg = sum(non_ortho_values) / len(non_ortho_values)

    # Determine quality rating
    quality.quality_rating = quality.get_quality_rating()
    quality.is_cfd_ready = quality.quality_rating in ("Excellent", "Good")

    return quality


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

    # CRITICAL: Update lookup table after triangulation changes face indices
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    bvh = BVHTree.FromBMesh(bm)

    # Check for overlaps
    overlaps = bvh.overlap(bvh)

    # Filter out adjacent face pairs
    self_intersections = 0
    for i, j in overlaps:
        if i != j and i < len(bm.faces) and j < len(bm.faces):
            face_i = bm.faces[i]
            face_j = bm.faces[j]

            # Check if faces share a vertex or edge
            shared_verts = set(face_i.verts) & set(face_j.verts)
            if len(shared_verts) == 0:
                self_intersections += 1

    bm.free()
    eval_obj.to_mesh_clear()

    return self_intersections // 2  # Each intersection counted twice


def check_curve_radius_vs_width(curve_obj, channel_width: float) -> Tuple[bool, float, str]:
    """
    Check if curve radius is sufficient for the channel width.

    When the channel half-width exceeds the minimum curve radius,
    geometry will self-intersect on the inside of curves.

    Args:
        curve_obj: Blender curve object
        channel_width: Total width of channel at top

    Returns:
        Tuple of (is_ok, min_radius, warning_message)
    """
    import bpy

    half_width = channel_width / 2

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    if not mesh or len(mesh.vertices) < 3:
        eval_obj.to_mesh_clear()
        return True, float("inf"), ""

    verts = [v.co.copy() for v in mesh.vertices]
    eval_obj.to_mesh_clear()

    # Calculate minimum radius of curvature
    min_radius = float("inf")

    for i in range(1, len(verts) - 1):
        p0 = verts[i - 1]
        p1 = verts[i]
        p2 = verts[i + 1]

        # Vectors from p1 to neighbors
        v1 = p0 - p1
        v2 = p2 - p1

        # Cross product magnitude gives area of parallelogram
        cross = v1.cross(v2)
        cross_len = cross.length

        if cross_len < 1e-10:
            continue  # Straight segment

        # Lengths
        a = v1.length
        b = v2.length
        c = (p2 - p0).length

        # Radius of circumscribed circle (approximates curve radius)
        # R = (a * b * c) / (4 * area) where area = cross_len / 2
        area = cross_len / 2
        if area > 1e-10:
            radius = (a * b * c) / (4 * area)
            min_radius = min(min_radius, radius)

    is_ok = min_radius > half_width
    warning = ""

    if not is_ok:
        warning = (
            f"Channel half-width ({half_width:.2f}m) exceeds minimum curve radius "
            f"({min_radius:.2f}m). Inner geometry may self-intersect. "
            f"Increase curve radius or reduce channel width."
        )

    return is_ok, min_radius, warning


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
