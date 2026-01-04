"""
Build Channel Module
Core geometry generation for hydraulic channels.
"""

import math
from typing import List, Tuple

from mathutils import Vector

from ..model.channel_params import ChannelParams, SectionType


def subdivide_profile_edge(
    p1: Tuple[float, float], p2: Tuple[float, float], max_length: float
) -> List[Tuple[float, float]]:
    """
    Subdivide an edge between two points to ensure no segment exceeds max_length.

    Args:
        p1: Start point (x, y)
        p2: End point (x, y)
        max_length: Maximum allowed edge length

    Returns:
        List of points from p1 to p2 (inclusive) with subdivisions
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    edge_length = math.sqrt(dx * dx + dy * dy)

    if edge_length <= max_length or edge_length < 0.001:
        return [p1, p2]

    # Calculate number of subdivisions needed
    num_segments = math.ceil(edge_length / max_length)
    points = []

    for i in range(num_segments + 1):
        t = i / num_segments
        x = p1[0] + dx * t
        y = p1[1] + dy * t
        points.append((x, y))

    return points


def subdivide_profile(profile: List[Tuple[float, float]], max_edge_length: float) -> List[Tuple[float, float]]:
    """
    Subdivide all edges in a profile to ensure uniform mesh density.

    Args:
        profile: List of (x, y) points defining the section profile
        max_edge_length: Maximum allowed edge length

    Returns:
        Subdivided profile with more points
    """
    if len(profile) < 2 or max_edge_length <= 0:
        return profile

    subdivided = []

    for i in range(len(profile)):
        p1 = profile[i]
        p2 = profile[(i + 1) % len(profile)]

        # For open channels, don't connect last to first
        if i == len(profile) - 1:
            subdivided.append(p1)
            break

        edge_points = subdivide_profile_edge(p1, p2, max_edge_length)
        # Add all points except last (will be added as next edge's first)
        subdivided.extend(edge_points[:-1])

    return subdivided


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
    subdivide = getattr(params, "subdivide_profile", True)
    max_edge = getattr(params, "profile_resolution", params.resolution_m)

    if params.section_type == SectionType.TRAPEZOIDAL:
        bw = params.bottom_width
        ss = params.side_slope
        tw = bw + 2 * ss * h

        # Inner profile (counterclockwise from bottom-left)
        # For open channels: BL -> BR -> TR -> TL (water-facing surfaces)
        inner_base = [
            (-bw / 2, 0),
            (bw / 2, 0),
            (tw / 2, h),
            (-tw / 2, h),
        ]

        if subdivide and max_edge > 0:
            # Subdivide each edge separately to maintain structure
            inner = []
            # Edge 0: BL -> BR (bottom)
            edge0 = subdivide_profile_edge(inner_base[0], inner_base[1], max_edge)
            inner.extend(edge0[:-1])
            # Edge 1: BR -> TR (right wall)
            edge1 = subdivide_profile_edge(inner_base[1], inner_base[2], max_edge)
            inner.extend(edge1[:-1])
            # Edge 2: TR -> TL (top edge - not a face for open channel, but vertex needed)
            inner.append(inner_base[2])
            inner.append(inner_base[3])
        else:
            inner = inner_base

        if lt > 0:
            # Outer profile offset perpendicular to walls
            wall_offset = lt * math.sqrt(1 + ss * ss)
            outer_base = [
                (-bw / 2 - lt, -lt),
                (bw / 2 + lt, -lt),
                (tw / 2 + wall_offset, h),
                (-tw / 2 - wall_offset, h),
            ]

            if subdivide and max_edge > 0:
                outer = []
                edge0 = subdivide_profile_edge(outer_base[0], outer_base[1], max_edge)
                outer.extend(edge0[:-1])
                edge1 = subdivide_profile_edge(outer_base[1], outer_base[2], max_edge)
                outer.extend(edge1[:-1])
                outer.append(outer_base[2])
                outer.append(outer_base[3])
            else:
                outer = outer_base

            return inner, outer

        return inner, []

    elif params.section_type == SectionType.RECTANGULAR:
        bw = params.bottom_width
        inner_base = [
            (-bw / 2, 0),
            (bw / 2, 0),
            (bw / 2, h),
            (-bw / 2, h),
        ]

        if subdivide and max_edge > 0:
            inner = []
            # Bottom edge
            edge0 = subdivide_profile_edge(inner_base[0], inner_base[1], max_edge)
            inner.extend(edge0[:-1])
            # Right wall
            edge1 = subdivide_profile_edge(inner_base[1], inner_base[2], max_edge)
            inner.extend(edge1[:-1])
            # Top vertices
            inner.append(inner_base[2])
            inner.append(inner_base[3])
        else:
            inner = inner_base

        if lt > 0:
            outer_base = [
                (-bw / 2 - lt, -lt),
                (bw / 2 + lt, -lt),
                (bw / 2 + lt, h),
                (-bw / 2 - lt, h),
            ]

            if subdivide and max_edge > 0:
                outer = []
                edge0 = subdivide_profile_edge(outer_base[0], outer_base[1], max_edge)
                outer.extend(edge0[:-1])
                edge1 = subdivide_profile_edge(outer_base[1], outer_base[2], max_edge)
                outer.extend(edge1[:-1])
                outer.append(outer_base[2])
                outer.append(outer_base[3])
            else:
                outer = outer_base

            return inner, outer

        return inner, []

    elif params.section_type == SectionType.TRIANGULAR:
        # V-channel / triangular section
        ss = params.side_slope
        tw = 2 * ss * h  # Top width based on side slope

        # Inner profile: apex at bottom, expands upward
        # Profile order: BL -> apex -> BR -> TR -> TL
        # Simplified to 3 vertices: apex (bottom), top-right, top-left
        inner_base = [
            (0, 0),  # Apex (bottom point)
            (tw / 2, h),  # Top right
            (-tw / 2, h),  # Top left
        ]

        if subdivide and max_edge > 0:
            # Subdivide edges
            inner = []
            # Edge: apex -> TR (right slope)
            edge0 = subdivide_profile_edge(inner_base[0], inner_base[1], max_edge)
            inner.extend(edge0[:-1])
            # Top vertices
            inner.append(inner_base[1])  # TR
            inner.append(inner_base[2])  # TL
        else:
            inner = inner_base

        if lt > 0:
            # Outer profile offset
            slope_length = math.sqrt(h * h + (ss * h) ** 2)
            wall_offset = lt * slope_length / h if h > 0 else lt

            outer_base = [
                (0, -lt),  # Apex offset down
                (tw / 2 + wall_offset, h),  # Top right offset
                (-tw / 2 - wall_offset, h),  # Top left offset
            ]

            if subdivide and max_edge > 0:
                outer = []
                edge0 = subdivide_profile_edge(outer_base[0], outer_base[1], max_edge)
                outer.extend(edge0[:-1])
                outer.append(outer_base[1])
                outer.append(outer_base[2])
            else:
                outer = outer_base

            return inner, outer

        return inner, []

    elif params.section_type == SectionType.CIRCULAR:
        r = params.bottom_width / 2
        # For circular, calculate segments based on resolution
        if subdivide and max_edge > 0:
            circumference = math.pi * r  # Half circle
            segments = max(16, int(circumference / max_edge))
        else:
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
                y = outer_r * math.sin(angle) + r
                outer.append((x, y))
            return inner, outer

        return inner, []

    elif params.section_type == SectionType.PIPE:
        # Commercial pipe: full circle with wall thickness
        # bottom_width is outer diameter, lining_thickness is wall thickness
        outer_r = params.bottom_width / 2
        inner_r = outer_r - lt  # Inner radius (flow area)

        # For pipes, calculate segments based on resolution
        if subdivide and max_edge > 0:
            circumference = 2 * math.pi * outer_r
            segments = max(24, int(circumference / max_edge))
        else:
            segments = 32

        # Inner surface (flow boundary) - full circle
        inner = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = inner_r * math.cos(angle)
            y = inner_r * math.sin(angle) + outer_r  # Center at outer_r height
            inner.append((x, y))

        # Outer surface (pipe exterior)
        outer = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = outer_r * math.cos(angle)
            y = outer_r * math.sin(angle) + outer_r
            outer.append((x, y))

        return inner, outer

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


def _is_curve_cyclic(curve_obj) -> bool:
    """Check if any spline in the curve is cyclic (closed loop)."""
    if curve_obj.type != "CURVE":
        return False
    for spline in curve_obj.data.splines:
        if spline.use_cyclic_u:
            return True
    return False


def _get_profile_edge_ranges(params: ChannelParams, num_verts: int) -> dict:
    """
    Get the vertex index ranges for each edge of the profile.

    For a subdivided trapezoidal profile, we need to know which vertices
    belong to which edge (bottom, right wall, top, left wall).

    Returns:
        Dictionary with edge names and their (start_idx, end_idx) ranges
    """
    if params.section_type in (SectionType.TRAPEZOIDAL, SectionType.RECTANGULAR):
        # Calculate expected subdivisions based on params
        h = params.total_height
        subdivide = getattr(params, "subdivide_profile", True)
        max_edge = getattr(params, "profile_resolution", params.resolution_m)

        if params.section_type == SectionType.TRAPEZOIDAL:
            bw = params.bottom_width
            ss = params.side_slope
            wall_length = math.sqrt(h * h + (ss * h) ** 2)
        else:
            bw = params.bottom_width
            wall_length = h

        if subdivide and max_edge > 0:
            bottom_subdivs = max(1, math.ceil(bw / max_edge))
            wall_subdivs = max(1, math.ceil(wall_length / max_edge))
        else:
            bottom_subdivs = 1
            wall_subdivs = 1

        # Profile order: bottom edge points, right wall points, TR, TL
        # BL(0) -> ... -> BR -> ... -> TR -> TL
        bottom_end = bottom_subdivs  # Vertices 0 to bottom_subdivs-1 are bottom, then BR
        right_wall_end = bottom_end + wall_subdivs  # Then right wall points up to TR

        return {
            "bottom": (0, bottom_end),  # BL to BR (inclusive)
            "right_wall": (bottom_end, right_wall_end),  # BR to TR
            "top_right": right_wall_end,  # TR index
            "top_left": right_wall_end + 1,  # TL index (last vertex)
        }

    elif params.section_type == SectionType.TRIANGULAR:
        # Triangular: apex -> TR -> TL (3 vertices base, possibly subdivided)
        h = params.total_height
        ss = params.side_slope
        subdivide = getattr(params, "subdivide_profile", True)
        max_edge = getattr(params, "profile_resolution", params.resolution_m)

        slope_length = math.sqrt(h * h + (ss * h) ** 2)

        if subdivide and max_edge > 0:
            slope_subdivs = max(1, math.ceil(slope_length / max_edge))
        else:
            slope_subdivs = 1

        # Profile: apex(0) -> ... -> TR -> TL
        right_slope_end = slope_subdivs  # apex to TR
        tr_idx = right_slope_end
        tl_idx = right_slope_end + 1

        return {
            "triangular": True,
            "right_slope": (0, right_slope_end),  # apex to TR
            "top_right": tr_idx,
            "top_left": tl_idx,
        }

    elif params.section_type in (SectionType.CIRCULAR, SectionType.PIPE):
        return {"circular": True, "count": num_verts}

    return {"circular": True, "count": num_verts}


def build_channel_mesh(curve_obj, params: ChannelParams, alignment=None) -> Tuple[List[Vector], List[Tuple[int, ...]]]:
    """
    Build channel mesh geometry from curve and parameters.

    Args:
        curve_obj: Blender curve object (axis)
        params: Channel parameters (base parameters)
        alignment: Optional ChannelAlignment for transitions

    Returns:
        Tuple of (vertices, faces) for mesh creation
    """

    # Check if curve is cyclic (closed loop)
    is_cyclic = _is_curve_cyclic(curve_obj)

    # Sample curve
    samples = sample_curve_points(curve_obj, params.resolution_m)
    if len(samples) < 2:
        return [], []

    # For cyclic curves, remove duplicate endpoint if it's very close to start
    if is_cyclic and len(samples) > 2:
        start_pos = samples[0]["position"]
        end_pos = samples[-1]["position"]
        if (end_pos - start_pos).length < params.resolution_m * 0.5:
            samples = samples[:-1]  # Remove last point (it's a duplicate of first)

    # Check if we have transitions
    has_transitions = alignment is not None and len(alignment.transitions) > 0

    # For uniform channels (no transitions), generate profile once
    if not has_transitions:
        inner_verts, outer_verts = generate_section_vertices_with_lining(params)
        has_lining = len(outer_verts) > 0
        num_inner_verts = len(inner_verts)
        num_outer_verts = len(outer_verts) if has_lining else 0
        total_verts_per_section = num_inner_verts + num_outer_verts
    else:
        # With transitions: we need consistent vertex counts
        # Generate profile for base params to get vertex count
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
        station = sample.get("station", 0.0)

        # Calculate local coordinate system
        binormal = tangent.cross(normal).normalized()

        # Get parameters for this station (may be interpolated)
        if has_transitions:
            section_params = alignment.get_params_at_station(station)
            inner_verts, outer_verts = generate_section_vertices_with_lining(section_params)
        # else: use pre-generated inner_verts, outer_verts

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
    is_open_channel = params.section_type in (SectionType.TRAPEZOIDAL, SectionType.RECTANGULAR, SectionType.TRIANGULAR)

    # For cyclic curves, we loop back to connect last section to first
    num_connections = num_samples if is_cyclic else num_samples - 1

    # Get edge ranges for the profile
    edge_info = _get_profile_edge_ranges(params, num_inner_verts)

    for i in range(num_connections):
        base_current = i * total_verts_per_section
        next_idx = (i + 1) % num_samples if is_cyclic else i + 1
        base_next = next_idx * total_verts_per_section

        if is_open_channel:
            # OPEN CHANNEL with subdivided profile
            # Generate faces for each edge of the profile

            if params.section_type == SectionType.TRIANGULAR:
                # Triangular: apex(0) -> ... -> TR -> TL
                right_start, right_end = edge_info["right_slope"]
                tr_idx = edge_info["top_right"]
                tl_idx = edge_info["top_left"]

                # Right slope (from apex to TR)
                for j in range(right_start, right_end):
                    j_next = j + 1
                    v1 = base_current + j
                    v2 = base_current + j_next
                    v3 = base_next + j_next
                    v4 = base_next + j
                    faces.append((v1, v2, v3, v4))

                # Left slope (from TL back to apex)
                v1 = base_current + tl_idx
                v2 = base_current + 0  # apex
                v3 = base_next + 0  # apex next
                v4 = base_next + tl_idx
                faces.append((v1, v2, v3, v4))

            else:
                # TRAPEZOIDAL / RECTANGULAR
                bottom_start, bottom_end = edge_info["bottom"]
                right_start, right_end = edge_info["right_wall"]
                tr_idx = edge_info["top_right"]
                tl_idx = edge_info["top_left"]

                # Bottom surface (from BL to BR)
                for j in range(bottom_start, bottom_end):
                    j_next = j + 1
                    v1 = base_current + j
                    v2 = base_current + j_next
                    v3 = base_next + j_next
                    v4 = base_next + j
                    faces.append((v1, v2, v3, v4))

                # Right wall (from BR to TR)
                for j in range(right_start, right_end):
                    j_next = j + 1
                    v1 = base_current + j
                    v2 = base_current + j_next
                    v3 = base_next + j_next
                    v4 = base_next + j
                    faces.append((v1, v2, v3, v4))

                # Left wall (from TL to BL) - reversed direction
                # TL -> BL means we go from tl_idx back to 0
                v1 = base_current + tl_idx
                v2 = base_current + 0  # BL
                v3 = base_next + 0  # BL next
                v4 = base_next + tl_idx
                faces.append((v1, v2, v3, v4))

            if has_lining:
                outer_offset = num_inner_verts

                if params.section_type == SectionType.TRIANGULAR:
                    # Triangular lining - outer right slope
                    for j in range(right_start, right_end):
                        j_next = j + 1
                        v1 = base_current + outer_offset + j
                        v2 = base_next + outer_offset + j
                        v3 = base_next + outer_offset + j_next
                        v4 = base_current + outer_offset + j_next
                        faces.append((v1, v2, v3, v4))

                    # Outer left slope
                    v1 = base_current + outer_offset + tl_idx
                    v2 = base_next + outer_offset + tl_idx
                    v3 = base_next + outer_offset + 0
                    v4 = base_current + outer_offset + 0
                    faces.append((v1, v2, v3, v4))

                    # Top edge caps
                    v1 = base_current + tl_idx
                    v2 = base_next + tl_idx
                    v3 = base_next + outer_offset + tl_idx
                    v4 = base_current + outer_offset + tl_idx
                    faces.append((v1, v2, v3, v4))

                    v1 = base_current + outer_offset + tr_idx
                    v2 = base_next + outer_offset + tr_idx
                    v3 = base_next + tr_idx
                    v4 = base_current + tr_idx
                    faces.append((v1, v2, v3, v4))

                else:
                    # TRAPEZOIDAL / RECTANGULAR lining
                    # Outer bottom surface
                    for j in range(bottom_start, bottom_end):
                        j_next = j + 1
                        # Reverse winding for outward normals
                        v1 = base_current + outer_offset + j
                        v2 = base_next + outer_offset + j
                        v3 = base_next + outer_offset + j_next
                        v4 = base_current + outer_offset + j_next
                        faces.append((v1, v2, v3, v4))

                    # Outer right wall
                    for j in range(right_start, right_end):
                        j_next = j + 1
                        v1 = base_current + outer_offset + j
                        v2 = base_next + outer_offset + j
                        v3 = base_next + outer_offset + j_next
                        v4 = base_current + outer_offset + j_next
                        faces.append((v1, v2, v3, v4))

                    # Outer left wall
                    v1 = base_current + outer_offset + tl_idx
                    v2 = base_next + outer_offset + tl_idx
                    v3 = base_next + outer_offset + 0
                    v4 = base_current + outer_offset + 0
                    faces.append((v1, v2, v3, v4))

                    # Top edge caps (connect inner top to outer top)
                    # Left cap: inner TL to outer TL
                    v1 = base_current + tl_idx
                    v2 = base_next + tl_idx
                    v3 = base_next + outer_offset + tl_idx
                    v4 = base_current + outer_offset + tl_idx
                    faces.append((v1, v2, v3, v4))

                    # Right cap: inner TR to outer TR
                    v1 = base_current + outer_offset + tr_idx
                    v2 = base_next + outer_offset + tr_idx
                    v3 = base_next + tr_idx
                    v4 = base_current + tr_idx
                    faces.append((v1, v2, v3, v4))

        else:
            # CLOSED CHANNEL (circular/pipe): wrap around for inner
            is_full_circle = params.section_type == SectionType.PIPE

            if is_full_circle:
                # Full circle - wrap around (last vertex connects to first)
                for j in range(num_inner_verts):
                    j_next = (j + 1) % num_inner_verts

                    v1 = base_current + j
                    v2 = base_current + j_next
                    v3 = base_next + j_next
                    v4 = base_next + j
                    faces.append((v1, v2, v3, v4))

                if has_lining:
                    outer_offset = num_inner_verts
                    for j in range(num_outer_verts):
                        j_next = (j + 1) % num_outer_verts

                        v1 = base_current + outer_offset + j
                        v2 = base_next + outer_offset + j
                        v3 = base_next + outer_offset + j_next
                        v4 = base_current + outer_offset + j_next
                        faces.append((v1, v2, v3, v4))
            else:
                # Half circle (open circular channel) - don't wrap
                for j in range(num_inner_verts - 1):
                    j_next = j + 1

                    v1 = base_current + j
                    v2 = base_current + j_next
                    v3 = base_next + j_next
                    v4 = base_next + j
                    faces.append((v1, v2, v3, v4))

                if has_lining:
                    outer_offset = num_inner_verts
                    for j in range(num_outer_verts - 1):
                        j_next = j + 1

                        v1 = base_current + outer_offset + j
                        v2 = base_next + outer_offset + j
                        v3 = base_next + outer_offset + j_next
                        v4 = base_current + outer_offset + j_next
                        faces.append((v1, v2, v3, v4))

    # Add end caps for lining (close the start and end of the channel)
    # Skip end caps for cyclic curves - they form a complete loop
    if has_lining and not is_cyclic:
        if params.section_type == SectionType.PIPE:
            # PIPE: add annular end caps (ring between inner and outer circles)
            _add_pipe_end_caps(faces, num_samples, total_verts_per_section, num_inner_verts, num_outer_verts)
        else:
            _add_lining_end_caps(
                faces, num_samples, total_verts_per_section, num_inner_verts, is_open_channel, edge_info
            )

    return vertices, faces


def _add_pipe_end_caps(
    faces: List[Tuple[int, ...]],
    num_samples: int,
    total_verts_per_section: int,
    num_inner_verts: int,
    num_outer_verts: int,
) -> None:
    """
    Add annular end caps to close a pipe section.

    Creates ring faces connecting inner circle to outer circle at both ends.
    This makes the pipe a solid closed mesh suitable for CFD.
    """
    outer_offset = num_inner_verts

    # Start cap (first section) - connect inner to outer with annular ring
    base_start = 0
    for j in range(num_inner_verts):
        j_next = (j + 1) % num_inner_verts
        # Create quad from inner edge to outer edge
        # Winding: inner_j -> inner_j_next -> outer_j_next -> outer_j
        faces.append(
            (
                base_start + j,  # Inner j
                base_start + j_next,  # Inner j+1
                base_start + outer_offset + j_next,  # Outer j+1
                base_start + outer_offset + j,  # Outer j
            )
        )

    # End cap (last section) - reversed winding for outward normals
    base_end = (num_samples - 1) * total_verts_per_section
    for j in range(num_inner_verts):
        j_next = (j + 1) % num_inner_verts
        # Reversed winding: inner_j -> outer_j -> outer_j_next -> inner_j_next
        faces.append(
            (
                base_end + j,  # Inner j
                base_end + outer_offset + j,  # Outer j
                base_end + outer_offset + j_next,  # Outer j+1
                base_end + j_next,  # Inner j+1
            )
        )


def _add_lining_end_caps(
    faces: List[Tuple[int, ...]],
    num_samples: int,
    total_verts_per_section: int,
    num_inner_verts: int,
    is_open_channel: bool,
    edge_info: dict,
) -> None:
    """Add end caps to close the lining at start and end of channel."""
    outer_offset = num_inner_verts

    # Start cap (first section)
    base_start = 0

    if is_open_channel:
        bottom_start, bottom_end = edge_info["bottom"]
        right_start, right_end = edge_info["right_wall"]
        tl_idx = edge_info["top_left"]
        bl_idx = 0
        # Note: tr_idx = edge_info["top_right"], br_idx = bottom_end (unused but documented)

        # For open channels with subdivision, we need to create caps that
        # connect inner to outer at each edge

        # Bottom cap: connect inner bottom edge to outer bottom edge
        # This creates a strip of quads along the bottom
        for j in range(bottom_start, bottom_end):
            j_next = j + 1
            faces.append(
                (
                    base_start + j,  # Inner
                    base_start + outer_offset + j,  # Outer
                    base_start + outer_offset + j_next,  # Outer next
                    base_start + j_next,  # Inner next
                )
            )

        # Right wall cap: connect inner right wall to outer right wall
        for j in range(right_start, right_end):
            j_next = j + 1
            faces.append(
                (
                    base_start + j,  # Inner
                    base_start + j_next,  # Inner next
                    base_start + outer_offset + j_next,  # Outer next
                    base_start + outer_offset + j,  # Outer
                )
            )

        # Left wall cap: from BL to TL
        faces.append(
            (
                base_start + bl_idx,  # Inner BL
                base_start + tl_idx,  # Inner TL
                base_start + outer_offset + tl_idx,  # Outer TL
                base_start + outer_offset + bl_idx,  # Outer BL
            )
        )

    # End cap (last section)
    base_end = (num_samples - 1) * total_verts_per_section

    if is_open_channel:
        bottom_start, bottom_end = edge_info["bottom"]
        right_start, right_end = edge_info["right_wall"]
        tl_idx = edge_info["top_left"]
        bl_idx = 0
        # tr_idx and br_idx are implicitly: tr_idx = edge_info["top_right"], br_idx = bottom_end

        # Bottom cap (reversed winding)
        for j in range(bottom_start, bottom_end):
            j_next = j + 1
            faces.append(
                (
                    base_end + j_next,  # Inner next
                    base_end + outer_offset + j_next,  # Outer next
                    base_end + outer_offset + j,  # Outer
                    base_end + j,  # Inner
                )
            )

        # Right wall cap (reversed)
        for j in range(right_start, right_end):
            j_next = j + 1
            faces.append(
                (
                    base_end + j,  # Inner
                    base_end + outer_offset + j,  # Outer
                    base_end + outer_offset + j_next,  # Outer next
                    base_end + j_next,  # Inner next
                )
            )

        # Left wall cap (reversed)
        faces.append(
            (
                base_end + outer_offset + bl_idx,  # Outer BL
                base_end + outer_offset + tl_idx,  # Outer TL
                base_end + tl_idx,  # Inner TL
                base_end + bl_idx,  # Inner BL
            )
        )


def create_channel_object(
    name: str, vertices: List[Vector], faces: List[Tuple[int, ...]], collection_name: str = "CADHY_Channels"
):
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
