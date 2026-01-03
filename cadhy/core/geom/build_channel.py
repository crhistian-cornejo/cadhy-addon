"""
Build Channel Module
Core geometry generation for hydraulic channels.
"""

import math
from typing import List, Tuple

from mathutils import Vector

from ..model.channel_params import ChannelParams, SectionType


def sample_curve_points(curve_obj, resolution_m: float, adaptive: bool = True) -> List[dict]:
    """
    Sample points along a Blender curve at specified resolution.

    Args:
        curve_obj: Blender curve object
        resolution_m: Distance between samples in meters
        adaptive: If True, increase density in curved areas

    Returns:
        List of dicts with 'position', 'tangent', 'normal', 'station'
    """

    # Get curve data
    curve_data = curve_obj.data
    if not curve_data.splines:
        return []

    # Verify at least one spline exists
    if len(curve_data.splines) == 0:
        return []

    # Calculate total length
    total_length = get_curve_length(curve_obj)
    if total_length <= 0:
        return []

    if adaptive:
        # Adaptive sampling: more samples where curvature is higher
        return _sample_curve_adaptive(curve_obj, resolution_m, total_length)
    else:
        # Uniform sampling
        return _sample_curve_uniform(curve_obj, resolution_m, total_length)


def _sample_curve_uniform(curve_obj, resolution_m: float, total_length: float) -> List[dict]:
    """Uniform sampling along curve using RMF for consistent normals."""
    num_samples = max(2, int(total_length / resolution_m) + 1)

    t_values = [i / (num_samples - 1) for i in range(num_samples)]

    # Use RMF sampling for consistent normals
    return _sample_with_rmf(curve_obj, t_values, total_length)


def _sample_curve_adaptive(curve_obj, resolution_m: float, total_length: float) -> List[dict]:
    """
    Adaptive sampling: increase density where curvature is higher.

    Uses rotation-minimizing frames (RMF) to avoid geometry twisting at corners.
    """
    # First, get all curve vertices and tangents
    curve_data = _get_curve_polyline(curve_obj)
    if not curve_data:
        return []

    verts, distances, tangents = curve_data

    # Calculate curvature at each vertex
    curvatures = _calculate_curvatures(tangents, distances)

    # Determine adaptive t-values based on curvature
    t_values = [0.0]
    base_dt = resolution_m / total_length

    t = 0.0
    while t < 1.0:
        # Find curvature at current position
        idx = min(int(t * (len(curvatures) - 1)), len(curvatures) - 2)
        local_curvature = curvatures[max(0, idx)]

        # Adaptive step: smaller step where curvature is high
        max_curvature = 0.5  # radians/meter threshold
        curvature_factor = 1.0 + min(local_curvature / max_curvature, 2.0) * 2.0

        adaptive_dt = base_dt / curvature_factor
        t += adaptive_dt

        if t < 1.0:
            t_values.append(t)

    t_values.append(1.0)
    t_values = sorted(set(t_values))

    # Generate samples using rotation-minimizing frames
    samples = _sample_with_rmf(curve_obj, t_values, total_length)

    return samples


def _get_curve_polyline(curve_obj) -> Tuple[List[Vector], List[float], List[Vector]]:
    """Get curve as polyline with distances and tangents."""
    import bpy

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    if not mesh or len(mesh.vertices) < 2:
        eval_obj.to_mesh_clear()
        return None

    verts = [v.co.copy() for v in mesh.vertices]

    # Calculate cumulative distances
    distances = [0.0]
    for i in range(1, len(verts)):
        distances.append(distances[-1] + (verts[i] - verts[i - 1]).length)

    # Calculate tangents
    tangents = []
    for i in range(len(verts)):
        if i == 0:
            tangent = (verts[1] - verts[0]).normalized()
        elif i == len(verts) - 1:
            tangent = (verts[-1] - verts[-2]).normalized()
        else:
            # Average of previous and next segment tangents
            t1 = (verts[i] - verts[i - 1]).normalized()
            t2 = (verts[i + 1] - verts[i]).normalized()
            tangent = (t1 + t2).normalized()
        tangents.append(tangent)

    eval_obj.to_mesh_clear()
    return verts, distances, tangents


def _calculate_curvatures(tangents: List[Vector], distances: List[float]) -> List[float]:
    """Calculate curvature at each point."""
    curvatures = [0.0]
    for i in range(1, len(tangents)):
        dot = max(-1.0, min(1.0, tangents[i - 1].dot(tangents[i])))
        angle = math.acos(dot)
        segment_length = distances[i] - distances[i - 1]
        curvature = angle / segment_length if segment_length > 0 else 0
        curvatures.append(curvature)
    return curvatures


def _sample_with_rmf(curve_obj, t_values: List[float], total_length: float) -> List[dict]:
    """
    Sample curve using Rotation Minimizing Frames (RMF).

    This prevents geometry twisting at corners by propagating the normal
    along the curve instead of recalculating it independently at each point.
    """
    import bpy
    from mathutils import Vector

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    if not mesh or len(mesh.vertices) < 2:
        eval_obj.to_mesh_clear()
        return []

    verts = [v.co.copy() for v in mesh.vertices]
    world_matrix = curve_obj.matrix_world

    # Calculate distances
    distances = [0.0]
    for i in range(1, len(verts)):
        distances.append(distances[-1] + (verts[i] - verts[i - 1]).length)
    curve_length = distances[-1]

    eval_obj.to_mesh_clear()

    # First pass: calculate position and tangent for each t
    raw_samples = []
    for t in t_values:
        target_dist = t * curve_length

        # Find segment
        pos = verts[0]
        tangent = (verts[1] - verts[0]).normalized() if len(verts) > 1 else Vector((1, 0, 0))

        for i in range(1, len(distances)):
            if distances[i] >= target_dist:
                seg_start = distances[i - 1]
                seg_end = distances[i]
                seg_t = (target_dist - seg_start) / (seg_end - seg_start) if seg_end > seg_start else 0

                pos = verts[i - 1].lerp(verts[i], seg_t)
                tangent = (verts[i] - verts[i - 1]).normalized()
                break
        else:
            pos = verts[-1]
            tangent = (verts[-1] - verts[-2]).normalized() if len(verts) > 1 else Vector((1, 0, 0))

        raw_samples.append({"t": t, "pos": pos, "tangent": tangent})

    # Second pass: propagate normals using RMF
    samples = []

    # Initial frame: use world up as reference
    up = Vector((0, 0, 1))
    first_tangent = raw_samples[0]["tangent"]

    # If first tangent is nearly vertical, use Y as reference
    if abs(first_tangent.dot(up)) > 0.99:
        up = Vector((0, 1, 0))

    # Calculate initial normal
    binormal = first_tangent.cross(up).normalized()
    prev_normal = binormal.cross(first_tangent).normalized()

    for i, raw in enumerate(raw_samples):
        pos = raw["pos"]
        tangent = raw["tangent"]
        station = raw["t"] * total_length

        if i == 0:
            normal = prev_normal
        else:
            # RMF: rotate previous normal to align with new tangent
            # This minimizes twist by keeping the normal as close as possible
            # to the previous normal while staying perpendicular to tangent

            # Project previous normal onto plane perpendicular to new tangent
            normal = prev_normal - tangent * prev_normal.dot(tangent)

            # Handle case where normal becomes too small (tangent reversal)
            if normal.length < 0.001:
                # Fall back to up-vector method
                test_up = Vector((0, 0, 1))
                if abs(tangent.dot(test_up)) > 0.99:
                    test_up = Vector((0, 1, 0))
                binormal = tangent.cross(test_up).normalized()
                normal = binormal.cross(tangent).normalized()
            else:
                normal = normal.normalized()

        prev_normal = normal

        # Transform to world space
        world_pos = world_matrix @ pos
        world_tangent = (world_matrix.to_3x3() @ tangent).normalized()
        world_normal = (world_matrix.to_3x3() @ normal).normalized()

        samples.append(
            {
                "position": world_pos,
                "tangent": world_tangent,
                "normal": world_normal,
                "station": station,
                "t": raw["t"],
            }
        )

    return samples


def get_curve_length(curve_obj) -> float:
    """Calculate total length of curve."""
    import bpy

    # Use depsgraph to get evaluated curve
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)

    # Convert to mesh temporarily to measure
    mesh = eval_obj.to_mesh()
    if not mesh or not mesh.edges:
        eval_obj.to_mesh_clear()
        return 0.0

    total_length = 0.0
    for edge in mesh.edges:
        v1 = mesh.vertices[edge.vertices[0]].co
        v2 = mesh.vertices[edge.vertices[1]].co
        total_length += (v2 - v1).length

    eval_obj.to_mesh_clear()
    return total_length


def evaluate_curve_at_parameter(curve_obj, t: float) -> Tuple[Vector, Vector, Vector]:
    """
    Evaluate curve position, tangent, and normal at parameter t (0-1).

    Uses a consistent normal calculation that handles sharp corners better
    by computing binormal from tangent change (Frenet-like frame).

    Returns:
        Tuple of (position, tangent, normal) as Vectors
    """
    import bpy
    from mathutils import Vector

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    if not mesh or not mesh.vertices:
        eval_obj.to_mesh_clear()
        return Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))

    # Get vertices in order
    verts = [v.co.copy() for v in mesh.vertices]

    # Find position along polyline
    if len(verts) < 2:
        eval_obj.to_mesh_clear()
        return verts[0] if verts else Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))

    # Calculate cumulative distances
    distances = [0.0]
    for i in range(1, len(verts)):
        distances.append(distances[-1] + (verts[i] - verts[i - 1]).length)

    total_length = distances[-1]
    target_dist = t * total_length

    # Find segment
    for i in range(1, len(distances)):
        if distances[i] >= target_dist:
            # Interpolate within segment
            seg_start = distances[i - 1]
            seg_end = distances[i]
            seg_t = (target_dist - seg_start) / (seg_end - seg_start) if seg_end > seg_start else 0

            pos = verts[i - 1].lerp(verts[i], seg_t)
            tangent = (verts[i] - verts[i - 1]).normalized()

            # Calculate normal using consistent "up" reference
            # For hydraulic channels, we want sections to stay as horizontal as possible
            up = Vector((0, 0, 1))

            # If tangent is nearly vertical, use Y as reference instead
            if abs(tangent.dot(up)) > 0.99:
                up = Vector((0, 1, 0))

            # Binormal is perpendicular to both tangent and up
            binormal = tangent.cross(up).normalized()

            # Normal is perpendicular to tangent in the plane containing up
            normal = binormal.cross(tangent).normalized()

            # Transform to world space
            world_matrix = curve_obj.matrix_world
            pos = world_matrix @ pos
            tangent = (world_matrix.to_3x3() @ tangent).normalized()
            normal = (world_matrix.to_3x3() @ normal).normalized()

            eval_obj.to_mesh_clear()
            return pos, tangent, normal

    eval_obj.to_mesh_clear()
    return verts[-1], Vector((1, 0, 0)), Vector((0, 0, 1))


def generate_section_vertices_with_lining(
    params: ChannelParams,
) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """
    Generate inner and outer section vertices for lining.

    Args:
        params: Channel parameters

    Returns:
        Tuple of (inner_profile, outer_profile) - outer may be empty if no lining
    """
    h = params.total_height
    lt = params.lining_thickness

    if params.section_type == SectionType.TRAPEZOIDAL:
        bw = params.bottom_width
        ss = params.side_slope
        tw = bw + 2 * ss * h

        # Inner profile (counterclockwise from bottom-left)
        inner = [
            (-bw / 2, 0),
            (bw / 2, 0),
            (tw / 2, h),
            (-tw / 2, h),
        ]

        if lt > 0:
            # Outer profile offset perpendicular to walls
            # For sloped walls, offset perpendicular distance is lt
            wall_offset = lt * math.sqrt(1 + ss * ss)  # Perpendicular offset on slope
            outer = [
                (-bw / 2 - lt, -lt),  # Bottom-left (offset down and left)
                (bw / 2 + lt, -lt),  # Bottom-right (offset down and right)
                (tw / 2 + wall_offset, h),  # Top-right (same height, offset outward)
                (-tw / 2 - wall_offset, h),  # Top-left (same height, offset outward)
            ]
            return inner, outer

        return inner, []

    elif params.section_type == SectionType.RECTANGULAR:
        bw = params.bottom_width
        inner = [
            (-bw / 2, 0),
            (bw / 2, 0),
            (bw / 2, h),
            (-bw / 2, h),
        ]

        if lt > 0:
            outer = [
                (-bw / 2 - lt, -lt),
                (bw / 2 + lt, -lt),
                (bw / 2 + lt, h),  # Same height at top
                (-bw / 2 - lt, h),  # Same height at top
            ]
            return inner, outer

        return inner, []

    elif params.section_type == SectionType.CIRCULAR:
        r = params.bottom_width / 2
        segments = 32
        inner = []
        for i in range(segments + 1):
            angle = math.pi + (math.pi * i / segments)
            x = r * math.cos(angle)
            y = r * math.sin(angle) + r
            inner.append((x, y))

        if lt > 0:
            outer_r = r + lt
            outer = []
            for i in range(segments + 1):
                angle = math.pi + (math.pi * i / segments)
                x = outer_r * math.cos(angle)
                y = outer_r * math.sin(angle) + r  # Same center
                outer.append((x, y))
            return inner, outer

        return inner, []

    return [], []


def generate_section_vertices(params: ChannelParams, include_outer: bool = False) -> List[Tuple[float, float]]:
    """
    Generate 2D section vertices in local coordinates.

    Args:
        params: Channel parameters
        include_outer: Include outer lining vertices (deprecated, use generate_section_vertices_with_lining)

    Returns:
        List of (x, y) tuples for section profile
    """
    inner, outer = generate_section_vertices_with_lining(params)
    if include_outer and outer:
        return inner + outer
    return inner


def build_channel_mesh(curve_obj, params: ChannelParams) -> Tuple[List[Vector], List[Tuple[int, ...]]]:
    """
    Build channel mesh geometry from curve and parameters.

    Args:
        curve_obj: Blender curve object (axis)
        params: Channel parameters

    Returns:
        Tuple of (vertices, faces) for mesh creation
    """

    # Sample curve
    samples = sample_curve_points(curve_obj, params.resolution_m)
    if len(samples) < 2:
        return [], []

    # Generate section profiles (inner and outer for lining)
    inner_verts, outer_verts = generate_section_vertices_with_lining(params)
    has_lining = len(outer_verts) > 0

    num_inner_verts = len(inner_verts)
    num_outer_verts = len(outer_verts) if has_lining else 0
    total_verts_per_section = num_inner_verts + num_outer_verts

    vertices = []
    faces = []

    # Generate vertices for each sample point
    for sample in samples:
        pos = sample["position"]
        tangent = sample["tangent"]
        normal = sample["normal"]

        # Calculate local coordinate system
        binormal = tangent.cross(normal).normalized()

        # Transform inner section vertices to world position
        for sx, sy in inner_verts:
            world_pos = pos + binormal * sx + normal * sy
            vertices.append(world_pos)

        # Transform outer section vertices (if lining)
        if has_lining:
            for sx, sy in outer_verts:
                world_pos = pos + binormal * sx + normal * sy
                vertices.append(world_pos)

    # Generate faces connecting sections
    num_samples = len(samples)

    # Determine face generation based on section type
    is_open_channel = params.section_type in (SectionType.TRAPEZOIDAL, SectionType.RECTANGULAR)

    for i in range(num_samples - 1):
        base_current = i * total_verts_per_section
        base_next = (i + 1) * total_verts_per_section

        if is_open_channel:
            # OPEN CHANNEL with lining
            # Inner vertices: [BL(0), BR(1), TR(2), TL(3)]
            # Outer vertices: [BL(4), BR(5), TR(6), TL(7)] if lining

            # Inner surface (water-facing): bottom, right_wall, left_wall
            inner_wall_edges = [(0, 1), (1, 2), (3, 0)]

            for j, j_next in inner_wall_edges:
                v1 = base_current + j
                v2 = base_current + j_next
                v3 = base_next + j_next
                v4 = base_next + j
                faces.append((v1, v2, v3, v4))

            if has_lining:
                # Outer surface (ground-facing): bottom, right_wall, left_wall
                outer_offset = num_inner_verts
                outer_wall_edges = [(0, 1), (1, 2), (3, 0)]

                for j, j_next in outer_wall_edges:
                    # Reverse winding for correct normals (facing outward)
                    v1 = base_current + outer_offset + j
                    v2 = base_next + outer_offset + j
                    v3 = base_next + outer_offset + j_next
                    v4 = base_current + outer_offset + j_next
                    faces.append((v1, v2, v3, v4))

                # Top edge caps (connect inner top edge to outer top edge)
                # Left cap: inner TL(3) to outer TL(7)
                v1 = base_current + 3  # Inner TL current
                v2 = base_next + 3  # Inner TL next
                v3 = base_next + outer_offset + 3  # Outer TL next
                v4 = base_current + outer_offset + 3  # Outer TL current
                faces.append((v1, v2, v3, v4))

                # Right cap: inner TR(2) to outer TR(6)
                v1 = base_current + outer_offset + 2  # Outer TR current
                v2 = base_next + outer_offset + 2  # Outer TR next
                v3 = base_next + 2  # Inner TR next
                v4 = base_current + 2  # Inner TR current
                faces.append((v1, v2, v3, v4))

        else:
            # CLOSED CHANNEL (circular pipe): wrap around for inner
            for j in range(num_inner_verts):
                j_next = (j + 1) % num_inner_verts

                v1 = base_current + j
                v2 = base_current + j_next
                v3 = base_next + j_next
                v4 = base_next + j
                faces.append((v1, v2, v3, v4))

            if has_lining:
                # Outer surface for circular (also wraps)
                outer_offset = num_inner_verts
                for j in range(num_outer_verts):
                    j_next = (j + 1) % num_outer_verts

                    # Reverse winding for outward normals
                    v1 = base_current + outer_offset + j
                    v2 = base_next + outer_offset + j
                    v3 = base_next + outer_offset + j_next
                    v4 = base_current + outer_offset + j_next
                    faces.append((v1, v2, v3, v4))

    # Add end caps for lining (close the start and end of the channel)
    if has_lining:
        _add_lining_end_caps(faces, num_samples, total_verts_per_section, num_inner_verts, is_open_channel)

    return vertices, faces


def _add_lining_end_caps(
    faces: List[Tuple[int, ...]],
    num_samples: int,
    total_verts_per_section: int,
    num_inner_verts: int,
    is_open_channel: bool,
) -> None:
    """Add end caps to close the lining at start and end of channel."""
    outer_offset = num_inner_verts

    # Start cap (first section)
    base_start = 0

    if is_open_channel:
        # For open channels, cap the bottom and walls but not the top
        # Bottom cap: connect inner bottom edge to outer bottom edge
        faces.append(
            (
                base_start + 0,  # Inner BL
                base_start + outer_offset + 0,  # Outer BL
                base_start + outer_offset + 1,  # Outer BR
                base_start + 1,  # Inner BR
            )
        )

        # Left wall cap
        faces.append(
            (
                base_start + 0,  # Inner BL
                base_start + 3,  # Inner TL
                base_start + outer_offset + 3,  # Outer TL
                base_start + outer_offset + 0,  # Outer BL
            )
        )

        # Right wall cap
        faces.append(
            (
                base_start + 1,  # Inner BR
                base_start + outer_offset + 1,  # Outer BR
                base_start + outer_offset + 2,  # Outer TR
                base_start + 2,  # Inner TR
            )
        )

    # End cap (last section)
    base_end = (num_samples - 1) * total_verts_per_section

    if is_open_channel:
        # Bottom cap
        faces.append(
            (
                base_end + 1,  # Inner BR
                base_end + outer_offset + 1,  # Outer BR
                base_end + outer_offset + 0,  # Outer BL
                base_end + 0,  # Inner BL
            )
        )

        # Left wall cap
        faces.append(
            (
                base_end + outer_offset + 0,  # Outer BL
                base_end + outer_offset + 3,  # Outer TL
                base_end + 3,  # Inner TL
                base_end + 0,  # Inner BL
            )
        )

        # Right wall cap
        faces.append(
            (
                base_end + 2,  # Inner TR
                base_end + outer_offset + 2,  # Outer TR
                base_end + outer_offset + 1,  # Outer BR
                base_end + 1,  # Inner BR
            )
        )


def create_channel_object(
    name: str, vertices: List[Vector], faces: List[Tuple[int, ...]], collection_name: str = "CADHY_Channels"
) -> "bpy.types.Object":
    """
    Create or update a Blender mesh object from vertices and faces.

    Args:
        name: Object name
        vertices: List of vertex positions
        faces: List of face vertex indices
        collection_name: Collection to place object in

    Returns:
        Created/updated Blender object
    """
    import bmesh
    import bpy

    # Get or create collection
    if collection_name not in bpy.data.collections:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[collection_name]

    # Check if object exists
    if name in bpy.data.objects:
        obj = bpy.data.objects[name]
        mesh = obj.data

        # Clear existing geometry
        bm = bmesh.new()
        bm.to_mesh(mesh)
        bm.free()
    else:
        # Create new mesh and object
        mesh = bpy.data.meshes.new(name + "_mesh")
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)

    # Build mesh
    mesh.clear_geometry()
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.update()
    mesh.validate()

    # Recalculate normals
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    return obj


def update_mesh_geometry(obj, vertices: List[Vector], faces: List[Tuple[int, ...]]) -> None:
    """
    Update an existing mesh object with new geometry.

    Args:
        obj: Blender mesh object to update
        vertices: List of vertex positions
        faces: List of face vertex indices
    """
    import bmesh

    mesh = obj.data

    # Clear existing geometry and rebuild
    mesh.clear_geometry()
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.update()
    mesh.validate()

    # Recalculate normals
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
