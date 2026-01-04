"""
Build Channel Module
Core geometry generation for hydraulic channels.
Fixed: Curve self-intersection prevention at tight corners.
"""

import math
from typing import List, Optional, Tuple

from mathutils import Vector

from ..model.channel_params import ChannelParams, SectionType


def subdivide_profile_edge(
    p1: Tuple[float, float], p2: Tuple[float, float], max_length: float
) -> List[Tuple[float, float]]:
    """
    Subdivide an edge between two points to ensure no segment exceeds max_length.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    edge_length = math.sqrt(dx * dx + dy * dy)

    if edge_length <= max_length or edge_length < 0.001:
        return [p1, p2]

    num_segments = math.ceil(edge_length / max_length)
    points = []

    for i in range(num_segments + 1):
        t = i / num_segments
        x = p1[0] + dx * t
        y = p1[1] + dy * t
        points.append((x, y))

    return points


def subdivide_profile(profile: List[Tuple[float, float]], max_edge_length: float) -> List[Tuple[float, float]]:
    """Subdivide all edges in a profile to ensure uniform mesh density."""
    if len(profile) < 2 or max_edge_length <= 0:
        return profile

    subdivided = []

    for i in range(len(profile)):
        p1 = profile[i]
        p2 = profile[(i + 1) % len(profile)]

        if i == len(profile) - 1:
            subdivided.append(p1)
            break

        edge_points = subdivide_profile_edge(p1, p2, max_edge_length)
        subdivided.extend(edge_points[:-1])

    return subdivided


def sample_curve_points(curve_obj, resolution_m: float, adaptive: bool = True) -> List[dict]:
    """
    Sample points along a Blender curve at specified resolution.
    Now includes curvature radius for self-intersection prevention.
    """
    curve_data = curve_obj.data
    if not curve_data.splines:
        return []

    if len(curve_data.splines) == 0:
        return []

    total_length = get_curve_length(curve_obj)
    if total_length <= 0:
        return []

    if adaptive:
        return _sample_curve_adaptive(curve_obj, resolution_m, total_length)
    else:
        return _sample_curve_uniform(curve_obj, resolution_m, total_length)


def _sample_curve_uniform(curve_obj, resolution_m: float, total_length: float) -> List[dict]:
    """Uniform sampling along curve using RMF for consistent normals."""
    num_samples = max(2, int(total_length / resolution_m) + 1)
    t_values = [i / (num_samples - 1) for i in range(num_samples)]
    return _sample_with_rmf(curve_obj, t_values, total_length)


def _sample_curve_adaptive(curve_obj, resolution_m: float, total_length: float) -> List[dict]:
    """Adaptive sampling with higher density at curves."""
    curve_data = _get_curve_polyline(curve_obj)
    if not curve_data:
        return []

    verts, distances, tangents = curve_data
    curvatures = _calculate_curvatures(tangents, distances)

    t_values = [0.0]
    base_dt = resolution_m / total_length

    t = 0.0
    while t < 1.0:
        idx = min(int(t * (len(curvatures) - 1)), len(curvatures) - 2)
        local_curvature = curvatures[max(0, idx)]

        max_curvature = 0.5
        curvature_factor = 1.0 + min(local_curvature / max_curvature, 2.0) * 2.0

        adaptive_dt = base_dt / curvature_factor
        t += adaptive_dt

        if t < 1.0:
            t_values.append(t)

    t_values.append(1.0)
    t_values = sorted(set(t_values))

    samples = _sample_with_rmf(curve_obj, t_values, total_length)
    return samples


def _get_curve_polyline(curve_obj) -> Optional[Tuple[List[Vector], List[float], List[Vector]]]:
    """Get curve as polyline with distances and tangents."""
    import bpy

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    if not mesh or len(mesh.vertices) < 2:
        eval_obj.to_mesh_clear()
        return None

    verts = [v.co.copy() for v in mesh.vertices]

    distances = [0.0]
    for i in range(1, len(verts)):
        distances.append(distances[-1] + (verts[i] - verts[i - 1]).length)

    tangents = []
    for i in range(len(verts)):
        if i == 0:
            tangent = (verts[1] - verts[0]).normalized()
        elif i == len(verts) - 1:
            tangent = (verts[-1] - verts[-2]).normalized()
        else:
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


def _calculate_curve_radius(samples: List[dict]) -> List[float]:
    """
    Calculate the curve radius at each sample point.
    Used to detect and prevent self-intersection at tight curves.

    Returns:
        List of radii (float). Very large values indicate straight sections.
    """
    radii = []

    for i, sample in enumerate(samples):
        if i == 0 or i == len(samples) - 1:
            # At endpoints, use adjacent sample's radius
            radii.append(float('inf'))
            continue

        # Get three consecutive positions
        p_prev = samples[i - 1]["position"]
        p_curr = sample["position"]
        p_next = samples[i + 1]["position"]

        # Calculate vectors
        v1 = p_curr - p_prev
        v2 = p_next - p_curr

        # Calculate angle change
        if v1.length < 0.0001 or v2.length < 0.0001:
            radii.append(float('inf'))
            continue

        v1_norm = v1.normalized()
        v2_norm = v2.normalized()

        dot = max(-1.0, min(1.0, v1_norm.dot(v2_norm)))
        angle = math.acos(dot)

        if angle < 0.001:  # Nearly straight
            radii.append(float('inf'))
            continue

        # Arc length and radius: R = arc_length / angle
        arc_length = (v1.length + v2.length) / 2
        radius = arc_length / angle if angle > 0 else float('inf')

        radii.append(radius)

    # Fix endpoints
    if len(radii) > 1:
        radii[0] = radii[1]
        radii[-1] = radii[-2]

    return radii


def _get_curve_turn_direction(samples: List[dict]) -> List[float]:
    """
    Determine turn direction at each sample.
    Positive = turning left (inner edge on left)
    Negative = turning right (inner edge on right)
    Zero = straight
    """
    directions = []

    for i, sample in enumerate(samples):
        if i == 0 or i == len(samples) - 1:
            directions.append(0.0)
            continue

        p_prev = samples[i - 1]["position"]
        p_curr = sample["position"]
        p_next = samples[i + 1]["position"]

        # Forward vectors
        v1 = (p_curr - p_prev).normalized()
        v2 = (p_next - p_curr).normalized()

        # Cross product in XY plane gives turn direction
        # Assuming Z is up, cross.z > 0 means left turn
        normal = sample["normal"]
        binormal = sample["tangent"].cross(normal)

        # Project v2 onto the binormal to get lateral offset
        lateral = v2.dot(binormal)

        directions.append(lateral)

    if len(directions) > 1:
        directions[0] = directions[1]
        directions[-1] = directions[-2]

    return directions


def _sample_with_rmf(curve_obj, t_values: List[float], total_length: float) -> List[dict]:
    """
    Sample curve using Rotation Minimizing Frames (RMF).
    Now also calculates curvature radius for each sample.
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

    distances = [0.0]
    for i in range(1, len(verts)):
        distances.append(distances[-1] + (verts[i] - verts[i - 1]).length)
    curve_length = distances[-1]

    eval_obj.to_mesh_clear()

    # First pass: calculate position and tangent for each t
    raw_samples = []
    for t in t_values:
        target_dist = t * curve_length

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

    up = Vector((0, 0, 1))
    first_tangent = raw_samples[0]["tangent"]

    if abs(first_tangent.dot(up)) > 0.99:
        up = Vector((0, 1, 0))

    binormal = first_tangent.cross(up).normalized()
    prev_normal = binormal.cross(first_tangent).normalized()

    for i, raw in enumerate(raw_samples):
        pos = raw["pos"]
        tangent = raw["tangent"]
        station = raw["t"] * total_length

        if i == 0:
            normal = prev_normal
        else:
            normal = prev_normal - tangent * prev_normal.dot(tangent)

            if normal.length < 0.001:
                test_up = Vector((0, 0, 1))
                if abs(tangent.dot(test_up)) > 0.99:
                    test_up = Vector((0, 1, 0))
                binormal = tangent.cross(test_up).normalized()
                normal = binormal.cross(tangent).normalized()
            else:
                normal = normal.normalized()

        prev_normal = normal

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

    # Calculate curve radii for self-intersection prevention
    radii = _calculate_curve_radius(samples)
    turn_dirs = _get_curve_turn_direction(samples)

    for i, sample in enumerate(samples):
        sample["curve_radius"] = radii[i]
        sample["turn_direction"] = turn_dirs[i]

    return samples


def get_curve_length(curve_obj) -> float:
    """Calculate total length of curve."""
    import bpy

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)

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
    """Evaluate curve position, tangent, and normal at parameter t (0-1)."""
    import bpy
    from mathutils import Vector

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    if not mesh or not mesh.vertices:
        eval_obj.to_mesh_clear()
        return Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))

    verts = [v.co.copy() for v in mesh.vertices]

    if len(verts) < 2:
        eval_obj.to_mesh_clear()
        return verts[0] if verts else Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))

    distances = [0.0]
    for i in range(1, len(verts)):
        distances.append(distances[-1] + (verts[i] - verts[i - 1]).length)

    total_length = distances[-1]
    target_dist = t * total_length

    for i in range(1, len(distances)):
        if distances[i] >= target_dist:
            seg_start = distances[i - 1]
            seg_end = distances[i]
            seg_t = (target_dist - seg_start) / (seg_end - seg_start) if seg_end > seg_start else 0

            pos = verts[i - 1].lerp(verts[i], seg_t)
            tangent = (verts[i] - verts[i - 1]).normalized()

            up = Vector((0, 0, 1))
            if abs(tangent.dot(up)) > 0.99:
                up = Vector((0, 1, 0))

            binormal = tangent.cross(up).normalized()
            normal = binormal.cross(tangent).normalized()

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
    """
    h = params.total_height
    lt = params.lining_thickness
    subdivide = getattr(params, "subdivide_profile", True)
    max_edge = getattr(params, "profile_resolution", params.resolution_m)

    if params.section_type == SectionType.TRAPEZOIDAL:
        bw = params.bottom_width
        ss = params.side_slope
        tw = bw + 2 * ss * h

        # TRAPEZOIDAL profile: bottom_left -> bottom_right -> top_right -> top_left -> left_wall_points
        # Both walls are subdivided for uniform mesh quality at curves

        if subdivide and max_edge > 0:
            inner = []
            # Bottom edge: bottom_left to bottom_right
            edge_bottom = subdivide_profile_edge((-bw / 2, 0), (bw / 2, 0), max_edge)
            inner.extend(edge_bottom[:-1])
            # Right wall: bottom_right to top_right
            edge_right = subdivide_profile_edge((bw / 2, 0), (tw / 2, h), max_edge)
            inner.extend(edge_right[:-1])
            inner.append((tw / 2, h))  # Top right corner
            inner.append((-tw / 2, h))  # Top left corner
            # Left wall: top_left back to bottom_left (reversed for face winding)
            edge_left = subdivide_profile_edge((-tw / 2, h), (-bw / 2, 0), max_edge)
            inner.extend(edge_left[1:-1])  # Skip first (top_left) and last (bottom_left)
        else:
            inner = [(-bw / 2, 0), (bw / 2, 0), (tw / 2, h), (-tw / 2, h)]

        if lt > 0:
            wall_offset = lt * math.sqrt(1 + ss * ss)

            if subdivide and max_edge > 0:
                outer = []
                # Bottom edge outer
                edge_bottom = subdivide_profile_edge(
                    (-bw / 2 - lt, -lt), (bw / 2 + lt, -lt), max_edge
                )
                outer.extend(edge_bottom[:-1])
                # Right wall outer
                edge_right = subdivide_profile_edge(
                    (bw / 2 + lt, -lt), (tw / 2 + wall_offset, h), max_edge
                )
                outer.extend(edge_right[:-1])
                outer.append((tw / 2 + wall_offset, h))
                outer.append((-tw / 2 - wall_offset, h))
                # Left wall outer
                edge_left = subdivide_profile_edge(
                    (-tw / 2 - wall_offset, h), (-bw / 2 - lt, -lt), max_edge
                )
                outer.extend(edge_left[1:-1])
            else:
                outer = [
                    (-bw / 2 - lt, -lt),
                    (bw / 2 + lt, -lt),
                    (tw / 2 + wall_offset, h),
                    (-tw / 2 - wall_offset, h),
                ]

            return inner, outer

        return inner, []

    elif params.section_type == SectionType.RECTANGULAR:
        bw = params.bottom_width

        # RECTANGULAR profile: bottom_left -> bottom_right -> top_right -> top_left -> left_wall_points
        # Both walls are subdivided for uniform mesh quality at curves

        if subdivide and max_edge > 0:
            inner = []
            # Bottom edge
            edge_bottom = subdivide_profile_edge((-bw / 2, 0), (bw / 2, 0), max_edge)
            inner.extend(edge_bottom[:-1])
            # Right wall
            edge_right = subdivide_profile_edge((bw / 2, 0), (bw / 2, h), max_edge)
            inner.extend(edge_right[:-1])
            inner.append((bw / 2, h))  # Top right corner
            inner.append((-bw / 2, h))  # Top left corner
            # Left wall: top_left back to bottom_left
            edge_left = subdivide_profile_edge((-bw / 2, h), (-bw / 2, 0), max_edge)
            inner.extend(edge_left[1:-1])
        else:
            inner = [(-bw / 2, 0), (bw / 2, 0), (bw / 2, h), (-bw / 2, h)]

        if lt > 0:
            if subdivide and max_edge > 0:
                outer = []
                # Bottom edge outer
                edge_bottom = subdivide_profile_edge(
                    (-bw / 2 - lt, -lt), (bw / 2 + lt, -lt), max_edge
                )
                outer.extend(edge_bottom[:-1])
                # Right wall outer
                edge_right = subdivide_profile_edge(
                    (bw / 2 + lt, -lt), (bw / 2 + lt, h), max_edge
                )
                outer.extend(edge_right[:-1])
                outer.append((bw / 2 + lt, h))
                outer.append((-bw / 2 - lt, h))
                # Left wall outer
                edge_left = subdivide_profile_edge(
                    (-bw / 2 - lt, h), (-bw / 2 - lt, -lt), max_edge
                )
                outer.extend(edge_left[1:-1])
            else:
                outer = [
                    (-bw / 2 - lt, -lt),
                    (bw / 2 + lt, -lt),
                    (bw / 2 + lt, h),
                    (-bw / 2 - lt, h),
                ]

            return inner, outer

        return inner, []

    elif params.section_type == SectionType.TRIANGULAR:
        ss = params.side_slope
        tw = 2 * ss * h

        # Triangular V-channel: apex at bottom, two walls going up
        # Profile: apex -> right_slope_points -> top_right -> top_left -> left_slope_points
        # Both slopes are subdivided for uniform mesh density

        if subdivide and max_edge > 0:
            inner = []
            # Right slope: apex (0,0) to top_right (tw/2, h)
            edge_right = subdivide_profile_edge((0, 0), (tw / 2, h), max_edge)
            inner.extend(edge_right[:-1])  # All points except last (top_right)
            inner.append((tw / 2, h))  # Top right corner
            inner.append((-tw / 2, h))  # Top left corner
            # Left slope: top_left (-tw/2, h) back toward apex (0,0) - reversed for face winding
            edge_left = subdivide_profile_edge((-tw / 2, h), (0, 0), max_edge)
            inner.extend(edge_left[1:-1])  # Skip first (top_left) and last (apex)
        else:
            inner = [(0, 0), (tw / 2, h), (-tw / 2, h)]

        if lt > 0:
            slope_length = math.sqrt(h * h + (ss * h) ** 2)
            wall_offset = lt * slope_length / h if h > 0 else lt

            if subdivide and max_edge > 0:
                outer = []
                # Right slope outer
                edge_right = subdivide_profile_edge((0, -lt), (tw / 2 + wall_offset, h), max_edge)
                outer.extend(edge_right[:-1])
                outer.append((tw / 2 + wall_offset, h))
                outer.append((-tw / 2 - wall_offset, h))
                # Left slope outer
                edge_left = subdivide_profile_edge((-tw / 2 - wall_offset, h), (0, -lt), max_edge)
                outer.extend(edge_left[1:-1])
            else:
                outer = [(0, -lt), (tw / 2 + wall_offset, h), (-tw / 2 - wall_offset, h)]

            return inner, outer

        return inner, []

    elif params.section_type == SectionType.CIRCULAR:
        r = params.bottom_width / 2
        if subdivide and max_edge > 0:
            circumference = math.pi * r
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
        outer_r = params.bottom_width / 2
        inner_r = outer_r - lt

        if subdivide and max_edge > 0:
            circumference = 2 * math.pi * outer_r
            segments = max(24, int(circumference / max_edge))
        else:
            segments = 32

        inner = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = inner_r * math.cos(angle)
            y = inner_r * math.sin(angle) + outer_r
            inner.append((x, y))

        outer = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = outer_r * math.cos(angle)
            y = outer_r * math.sin(angle) + outer_r
            outer.append((x, y))

        return inner, outer

    return [], []


def generate_section_vertices(params: ChannelParams, include_outer: bool = False) -> List[Tuple[float, float]]:
    """Generate 2D section vertices in local coordinates."""
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
    """Get the vertex index ranges for each edge of the profile."""
    if params.section_type in (SectionType.TRAPEZOIDAL, SectionType.RECTANGULAR):
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

        # New vertex layout:
        # 0 to bottom_subdivs-1: bottom edge points (bottom_subdivs points)
        # bottom_subdivs to bottom_subdivs+wall_subdivs-1: right wall points (wall_subdivs points)
        # bottom_subdivs + wall_subdivs: top_right corner
        # bottom_subdivs + wall_subdivs + 1: top_left corner
        # bottom_subdivs + wall_subdivs + 2 onwards: left wall intermediate points (wall_subdivs - 1 points)
        bottom_end = bottom_subdivs
        right_wall_end = bottom_end + wall_subdivs
        tr_idx = right_wall_end
        tl_idx = right_wall_end + 1
        left_wall_start = right_wall_end + 2
        # Total verts = bottom_subdivs + wall_subdivs + 2 + (wall_subdivs - 1)
        #             = bottom_subdivs + 2*wall_subdivs + 1

        return {
            "bottom": (0, bottom_end),
            "right_wall": (bottom_end, right_wall_end),
            "top_right": tr_idx,
            "top_left": tl_idx,
            "left_wall": (left_wall_start, left_wall_start + wall_subdivs - 1),
            "wall_subdivs": wall_subdivs,
        }

    elif params.section_type == SectionType.TRIANGULAR:
        h = params.total_height
        ss = params.side_slope
        subdivide = getattr(params, "subdivide_profile", True)
        max_edge = getattr(params, "profile_resolution", params.resolution_m)

        slope_length = math.sqrt(h * h + (ss * h) ** 2)

        if subdivide and max_edge > 0:
            slope_subdivs = max(1, math.ceil(slope_length / max_edge))
        else:
            slope_subdivs = 1

        # New vertex layout:
        # 0 to slope_subdivs-1: apex + right slope intermediates (slope_subdivs points)
        # slope_subdivs: top_right
        # slope_subdivs + 1: top_left
        # slope_subdivs + 2 onwards: left slope intermediates (slope_subdivs - 1 points)
        right_slope_end = slope_subdivs
        tr_idx = slope_subdivs
        tl_idx = slope_subdivs + 1
        # Left slope goes from index slope_subdivs + 2 to end, connecting back to apex
        left_slope_start = slope_subdivs + 2
        # Total verts = 2 * slope_subdivs + 1

        return {
            "triangular": True,
            "right_slope": (0, right_slope_end),
            "top_right": tr_idx,
            "top_left": tl_idx,
            "left_slope": (left_slope_start, 2 * slope_subdivs + 1),
            "slope_subdivs": slope_subdivs,
        }

    elif params.section_type in (SectionType.CIRCULAR, SectionType.PIPE):
        return {"circular": True, "count": num_verts}

    return {"circular": True, "count": num_verts}


def _adjust_profile_for_curvature(
    profile_verts: List[Tuple[float, float]],
    curve_radius: float,
    turn_direction: float,
    channel_half_width: float,
) -> List[Tuple[float, float]]:
    """
    Adjust profile vertices to prevent self-intersection at tight curves.

    At tight curves, the inner edge of the channel would overlap.
    This function scales/moves vertices on the inner side to prevent crossing.
    """
    if curve_radius == float('inf') or abs(turn_direction) < 0.001:
        return profile_verts  # Straight section, no adjustment needed

    # Minimum safe radius is the channel half-width
    min_safe_radius = channel_half_width * 1.2  # 20% margin

    if curve_radius >= min_safe_radius:
        return profile_verts  # Radius is large enough

    # Calculate compression factor for inner edge
    # If radius < half_width, we need to compress the inner side
    compression = curve_radius / min_safe_radius
    compression = max(0.1, min(1.0, compression))  # Clamp between 0.1 and 1.0

    adjusted = []
    for sx, sy in profile_verts:
        # Determine if this vertex is on the inner or outer side of the turn
        # turn_direction > 0 means turning left, so positive X is outer
        # turn_direction < 0 means turning right, so negative X is outer

        if turn_direction > 0:
            # Turning left - negative X is inner
            if sx < 0:
                # Inner side - compress toward center
                new_sx = sx * compression
            else:
                # Outer side - keep or slightly expand
                new_sx = sx
        else:
            # Turning right - positive X is inner
            if sx > 0:
                # Inner side - compress toward center
                new_sx = sx * compression
            else:
                # Outer side - keep
                new_sx = sx

        adjusted.append((new_sx, sy))

    return adjusted


def build_channel_mesh(
    curve_obj, params: ChannelParams, alignment=None, drops=None
) -> Tuple[List[Vector], List[Tuple[int, ...]]]:
    """
    Build channel mesh geometry from curve and parameters.
    Now includes self-intersection prevention at tight curves.
    """
    if drops and len(drops) > 0:
        return _build_channel_with_drops(curve_obj, params, alignment, drops)

    is_cyclic = _is_curve_cyclic(curve_obj)

    samples = sample_curve_points(curve_obj, params.resolution_m)
    if len(samples) < 2:
        return [], []

    if is_cyclic and len(samples) > 2:
        start_pos = samples[0]["position"]
        end_pos = samples[-1]["position"]
        if (end_pos - start_pos).length < params.resolution_m * 0.5:
            samples = samples[:-1]

    has_transitions = alignment is not None and len(alignment.transitions) > 0

    if not has_transitions:
        inner_verts, outer_verts = generate_section_vertices_with_lining(params)
        has_lining = len(outer_verts) > 0
        num_inner_verts = len(inner_verts)
        num_outer_verts = len(outer_verts) if has_lining else 0
        total_verts_per_section = num_inner_verts + num_outer_verts
    else:
        inner_verts, outer_verts = generate_section_vertices_with_lining(params)
        has_lining = len(outer_verts) > 0
        num_inner_verts = len(inner_verts)
        num_outer_verts = len(outer_verts) if has_lining else 0
        total_verts_per_section = num_inner_verts + num_outer_verts

    # Calculate channel half-width for curvature adjustment
    if params.section_type == SectionType.TRAPEZOIDAL:
        channel_half_width = (params.bottom_width + 2 * params.side_slope * params.total_height) / 2
    elif params.section_type == SectionType.TRIANGULAR:
        channel_half_width = params.side_slope * params.total_height
    else:
        channel_half_width = params.bottom_width / 2

    vertices = []
    faces = []

    for sample in samples:
        pos = sample["position"]
        tangent = sample["tangent"]
        normal = sample["normal"]
        station = sample.get("station", 0.0)
        curve_radius = sample.get("curve_radius", float('inf'))
        turn_direction = sample.get("turn_direction", 0.0)

        binormal = tangent.cross(normal).normalized()

        if has_transitions:
            section_params = alignment.get_params_at_station(station)
            inner_verts, outer_verts = generate_section_vertices_with_lining(section_params)
            # Recalculate half-width for transitions
            if section_params.section_type == SectionType.TRAPEZOIDAL:
                channel_half_width = (section_params.bottom_width + 2 * section_params.side_slope * section_params.total_height) / 2
            elif section_params.section_type == SectionType.TRIANGULAR:
                channel_half_width = section_params.side_slope * section_params.total_height
            else:
                channel_half_width = section_params.bottom_width / 2

        # Adjust profile for tight curves to prevent self-intersection
        adjusted_inner = _adjust_profile_for_curvature(
            inner_verts, curve_radius, turn_direction, channel_half_width
        )

        for sx, sy in adjusted_inner:
            world_pos = pos + binormal * sx + normal * sy
            vertices.append(world_pos)

        if has_lining:
            adjusted_outer = _adjust_profile_for_curvature(
                outer_verts, curve_radius, turn_direction, channel_half_width * 1.2
            )
            for sx, sy in adjusted_outer:
                world_pos = pos + binormal * sx + normal * sy
                vertices.append(world_pos)

    # Generate faces
    num_samples = len(samples)
    is_open_channel = params.section_type in (SectionType.TRAPEZOIDAL, SectionType.RECTANGULAR, SectionType.TRIANGULAR)
    num_connections = num_samples if is_cyclic else num_samples - 1
    edge_info = _get_profile_edge_ranges(params, num_inner_verts)

    for i in range(num_connections):
        base_current = i * total_verts_per_section
        next_idx = (i + 1) % num_samples if is_cyclic else i + 1
        base_next = next_idx * total_verts_per_section

        if is_open_channel:
            if params.section_type == SectionType.TRIANGULAR:
                right_start, right_end = edge_info["right_slope"]
                tl_idx = edge_info["top_left"]
                left_start, left_end = edge_info.get("left_slope", (tl_idx, tl_idx))
                slope_subdivs = edge_info.get("slope_subdivs", 1)

                # Right slope faces (apex toward top_right)
                for j in range(right_start, right_end):
                    j_next = j + 1
                    v1 = base_current + j
                    v2 = base_current + j_next
                    v3 = base_next + j_next
                    v4 = base_next + j
                    faces.append((v1, v2, v3, v4))

                # Left slope faces (top_left toward apex)
                if left_start < left_end:
                    # First face: top_left to first left slope intermediate
                    v1 = base_current + tl_idx
                    v2 = base_current + left_start
                    v3 = base_next + left_start
                    v4 = base_next + tl_idx
                    faces.append((v1, v2, v3, v4))

                    # Intermediate left slope faces
                    for j in range(left_start, left_end - 1):
                        j_next = j + 1
                        v1 = base_current + j
                        v2 = base_current + j_next
                        v3 = base_next + j_next
                        v4 = base_next + j
                        faces.append((v1, v2, v3, v4))

                    # Last face: last left slope intermediate to apex
                    v1 = base_current + left_end - 1
                    v2 = base_current + 0  # apex
                    v3 = base_next + 0
                    v4 = base_next + left_end - 1
                    faces.append((v1, v2, v3, v4))
                else:
                    # No subdivision - single face from top_left to apex
                    v1 = base_current + tl_idx
                    v2 = base_current + 0
                    v3 = base_next + 0
                    v4 = base_next + tl_idx
                    faces.append((v1, v2, v3, v4))

            else:
                # TRAPEZOIDAL / RECTANGULAR face generation
                bottom_start, bottom_end = edge_info["bottom"]
                right_start, right_end = edge_info["right_wall"]
                tr_idx = edge_info["top_right"]
                tl_idx = edge_info["top_left"]
                left_wall_start, left_wall_end = edge_info.get("left_wall", (tl_idx, tl_idx))

                # Bottom faces
                for j in range(bottom_start, bottom_end):
                    j_next = j + 1
                    v1 = base_current + j
                    v2 = base_current + j_next
                    v3 = base_next + j_next
                    v4 = base_next + j
                    faces.append((v1, v2, v3, v4))

                # Right wall faces
                for j in range(right_start, right_end):
                    j_next = j + 1
                    v1 = base_current + j
                    v2 = base_current + j_next
                    v3 = base_next + j_next
                    v4 = base_next + j
                    faces.append((v1, v2, v3, v4))

                # Left wall faces (subdivided)
                if left_wall_start < left_wall_end:
                    # First face: top_left to first left wall intermediate
                    v1 = base_current + tl_idx
                    v2 = base_current + left_wall_start
                    v3 = base_next + left_wall_start
                    v4 = base_next + tl_idx
                    faces.append((v1, v2, v3, v4))

                    # Intermediate left wall faces
                    for j in range(left_wall_start, left_wall_end - 1):
                        j_next = j + 1
                        v1 = base_current + j
                        v2 = base_current + j_next
                        v3 = base_next + j_next
                        v4 = base_next + j
                        faces.append((v1, v2, v3, v4))

                    # Last face: last intermediate to bottom_left (index 0)
                    v1 = base_current + left_wall_end - 1
                    v2 = base_current + 0
                    v3 = base_next + 0
                    v4 = base_next + left_wall_end - 1
                    faces.append((v1, v2, v3, v4))
                else:
                    # No subdivision - single face from top_left to bottom_left
                    v1 = base_current + tl_idx
                    v2 = base_current + 0
                    v3 = base_next + 0
                    v4 = base_next + tl_idx
                    faces.append((v1, v2, v3, v4))

            if has_lining:
                outer_offset = num_inner_verts
                tr_idx = edge_info["top_right"]

                if params.section_type == SectionType.TRIANGULAR:
                    # Outer right slope faces (reversed winding)
                    for j in range(right_start, right_end):
                        j_next = j + 1
                        v1 = base_current + outer_offset + j
                        v2 = base_next + outer_offset + j
                        v3 = base_next + outer_offset + j_next
                        v4 = base_current + outer_offset + j_next
                        faces.append((v1, v2, v3, v4))

                    # Outer left slope faces
                    if left_start < left_end:
                        # First face: top_left to first left slope intermediate
                        v1 = base_current + outer_offset + tl_idx
                        v2 = base_next + outer_offset + tl_idx
                        v3 = base_next + outer_offset + left_start
                        v4 = base_current + outer_offset + left_start
                        faces.append((v1, v2, v3, v4))

                        # Intermediate faces
                        for j in range(left_start, left_end - 1):
                            j_next = j + 1
                            v1 = base_current + outer_offset + j
                            v2 = base_next + outer_offset + j
                            v3 = base_next + outer_offset + j_next
                            v4 = base_current + outer_offset + j_next
                            faces.append((v1, v2, v3, v4))

                        # Last face: last intermediate to apex
                        v1 = base_current + outer_offset + left_end - 1
                        v2 = base_next + outer_offset + left_end - 1
                        v3 = base_next + outer_offset + 0
                        v4 = base_current + outer_offset + 0
                        faces.append((v1, v2, v3, v4))
                    else:
                        # No subdivision
                        v1 = base_current + outer_offset + tl_idx
                        v2 = base_next + outer_offset + tl_idx
                        v3 = base_next + outer_offset + 0
                        v4 = base_current + outer_offset + 0
                        faces.append((v1, v2, v3, v4))

                    # Top edge connection faces (inner to outer at top_left and top_right)
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
                    # TRAPEZOIDAL / RECTANGULAR outer lining faces
                    for j in range(bottom_start, bottom_end):
                        j_next = j + 1
                        v1 = base_current + outer_offset + j
                        v2 = base_next + outer_offset + j
                        v3 = base_next + outer_offset + j_next
                        v4 = base_current + outer_offset + j_next
                        faces.append((v1, v2, v3, v4))

                    for j in range(right_start, right_end):
                        j_next = j + 1
                        v1 = base_current + outer_offset + j
                        v2 = base_next + outer_offset + j
                        v3 = base_next + outer_offset + j_next
                        v4 = base_current + outer_offset + j_next
                        faces.append((v1, v2, v3, v4))

                    # Outer left wall faces (subdivided)
                    if left_wall_start < left_wall_end:
                        # First face: outer top_left to first left wall intermediate
                        v1 = base_current + outer_offset + tl_idx
                        v2 = base_next + outer_offset + tl_idx
                        v3 = base_next + outer_offset + left_wall_start
                        v4 = base_current + outer_offset + left_wall_start
                        faces.append((v1, v2, v3, v4))

                        # Intermediate faces
                        for j in range(left_wall_start, left_wall_end - 1):
                            j_next = j + 1
                            v1 = base_current + outer_offset + j
                            v2 = base_next + outer_offset + j
                            v3 = base_next + outer_offset + j_next
                            v4 = base_current + outer_offset + j_next
                            faces.append((v1, v2, v3, v4))

                        # Last face: last intermediate to bottom_left
                        v1 = base_current + outer_offset + left_wall_end - 1
                        v2 = base_next + outer_offset + left_wall_end - 1
                        v3 = base_next + outer_offset + 0
                        v4 = base_current + outer_offset + 0
                        faces.append((v1, v2, v3, v4))
                    else:
                        # No subdivision
                        v1 = base_current + outer_offset + tl_idx
                        v2 = base_next + outer_offset + tl_idx
                        v3 = base_next + outer_offset + 0
                        v4 = base_current + outer_offset + 0
                        faces.append((v1, v2, v3, v4))

                    # Top edge connection faces
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
            is_full_circle = params.section_type == SectionType.PIPE

            if is_full_circle:
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
                # CIRCULAR (semicircle U-shape) - open channel
                for j in range(num_inner_verts - 1):
                    j_next = j + 1

                    v1 = base_current + j
                    v2 = base_current + j_next
                    v3 = base_next + j_next
                    v4 = base_next + j
                    faces.append((v1, v2, v3, v4))

                if has_lining:
                    outer_offset = num_inner_verts
                    # Outer surface faces
                    for j in range(num_outer_verts - 1):
                        j_next = j + 1

                        v1 = base_current + outer_offset + j
                        v2 = base_next + outer_offset + j
                        v3 = base_next + outer_offset + j_next
                        v4 = base_current + outer_offset + j_next
                        faces.append((v1, v2, v3, v4))

                    # Wall top connection faces (roof) at both open ends of the U
                    # Left wall top (index 0)
                    v1 = base_current + 0
                    v2 = base_next + 0
                    v3 = base_next + outer_offset + 0
                    v4 = base_current + outer_offset + 0
                    faces.append((v1, v2, v3, v4))

                    # Right wall top (last index)
                    last_inner = num_inner_verts - 1
                    last_outer = num_outer_verts - 1
                    v1 = base_current + outer_offset + last_outer
                    v2 = base_next + outer_offset + last_outer
                    v3 = base_next + last_inner
                    v4 = base_current + last_inner
                    faces.append((v1, v2, v3, v4))

    if has_lining and not is_cyclic:
        if params.section_type == SectionType.PIPE:
            _add_pipe_end_caps(faces, num_samples, total_verts_per_section, num_inner_verts, num_outer_verts)
        elif params.section_type == SectionType.CIRCULAR:
            _add_circular_end_caps(faces, num_samples, total_verts_per_section, num_inner_verts, num_outer_verts)
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
    """Add annular end caps to close a pipe section."""
    outer_offset = num_inner_verts

    base_start = 0
    for j in range(num_inner_verts):
        j_next = (j + 1) % num_inner_verts
        faces.append(
            (
                base_start + j,
                base_start + j_next,
                base_start + outer_offset + j_next,
                base_start + outer_offset + j,
            )
        )

    base_end = (num_samples - 1) * total_verts_per_section
    for j in range(num_inner_verts):
        j_next = (j + 1) % num_inner_verts
        faces.append(
            (
                base_end + j,
                base_end + outer_offset + j,
                base_end + outer_offset + j_next,
                base_end + j_next,
            )
        )


def _add_circular_end_caps(
    faces: List[Tuple[int, ...]],
    num_samples: int,
    total_verts_per_section: int,
    num_inner_verts: int,
    num_outer_verts: int,
) -> None:
    """Add semi-annular end caps for CIRCULAR (semicircle U) section."""
    outer_offset = num_inner_verts

    # Start end cap - connects inner to outer along the semicircle arc
    base_start = 0
    for j in range(num_inner_verts - 1):
        j_next = j + 1
        faces.append(
            (
                base_start + j,
                base_start + j_next,
                base_start + outer_offset + j_next,
                base_start + outer_offset + j,
            )
        )

    # End end cap
    base_end = (num_samples - 1) * total_verts_per_section
    for j in range(num_inner_verts - 1):
        j_next = j + 1
        faces.append(
            (
                base_end + j,
                base_end + outer_offset + j,
                base_end + outer_offset + j_next,
                base_end + j_next,
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

    base_start = 0

    if is_open_channel:
        if edge_info.get("triangular", False):
            right_start, right_end = edge_info["right_slope"]
            tl_idx = edge_info["top_left"]
            apex_idx = 0

            for j in range(right_start, right_end):
                j_next = j + 1
                faces.append(
                    (
                        base_start + j,
                        base_start + j_next,
                        base_start + outer_offset + j_next,
                        base_start + outer_offset + j,
                    )
                )

            faces.append(
                (
                    base_start + apex_idx,
                    base_start + outer_offset + apex_idx,
                    base_start + outer_offset + tl_idx,
                    base_start + tl_idx,
                )
            )
        else:
            bottom_start, bottom_end = edge_info["bottom"]
            right_start, right_end = edge_info["right_wall"]
            tl_idx = edge_info["top_left"]
            bl_idx = 0

            for j in range(bottom_start, bottom_end):
                j_next = j + 1
                faces.append(
                    (
                        base_start + j,
                        base_start + outer_offset + j,
                        base_start + outer_offset + j_next,
                        base_start + j_next,
                    )
                )

            for j in range(right_start, right_end):
                j_next = j + 1
                faces.append(
                    (
                        base_start + j,
                        base_start + j_next,
                        base_start + outer_offset + j_next,
                        base_start + outer_offset + j,
                    )
                )

            faces.append(
                (
                    base_start + bl_idx,
                    base_start + tl_idx,
                    base_start + outer_offset + tl_idx,
                    base_start + outer_offset + bl_idx,
                )
            )

    base_end = (num_samples - 1) * total_verts_per_section

    if is_open_channel:
        if edge_info.get("triangular", False):
            right_start, right_end = edge_info["right_slope"]
            tl_idx = edge_info["top_left"]
            apex_idx = 0

            for j in range(right_start, right_end):
                j_next = j + 1
                faces.append(
                    (
                        base_end + j,
                        base_end + outer_offset + j,
                        base_end + outer_offset + j_next,
                        base_end + j_next,
                    )
                )

            faces.append(
                (
                    base_end + tl_idx,
                    base_end + outer_offset + tl_idx,
                    base_end + outer_offset + apex_idx,
                    base_end + apex_idx,
                )
            )
        else:
            bottom_start, bottom_end = edge_info["bottom"]
            right_start, right_end = edge_info["right_wall"]
            tl_idx = edge_info["top_left"]
            bl_idx = 0

            for j in range(bottom_start, bottom_end):
                j_next = j + 1
                faces.append(
                    (
                        base_end + j_next,
                        base_end + outer_offset + j_next,
                        base_end + outer_offset + j,
                        base_end + j,
                    )
                )

            for j in range(right_start, right_end):
                j_next = j + 1
                faces.append(
                    (
                        base_end + j,
                        base_end + outer_offset + j,
                        base_end + outer_offset + j_next,
                        base_end + j_next,
                    )
                )

            faces.append(
                (
                    base_end + outer_offset + bl_idx,
                    base_end + outer_offset + tl_idx,
                    base_end + tl_idx,
                    base_end + bl_idx,
                )
            )


def _build_channel_with_drops(
    curve_obj, params: ChannelParams, alignment, drops
) -> Tuple[List[Vector], List[Tuple[int, ...]]]:
    """Build channel mesh with drop structures inserted at specified stations."""
    from .build_drop import generate_drop_geometry

    total_length = get_curve_length(curve_obj)
    if total_length <= 0:
        return [], []

    sorted_drops = sorted(drops, key=lambda d: d.station)
    valid_drops = [d for d in sorted_drops if 0 < d.station < total_length]

    if not valid_drops:
        return build_channel_mesh(curve_obj, params, alignment, drops=None)

    all_vertices = []
    all_faces = []

    segment_starts = [0.0] + [d.station for d in valid_drops]
    segment_ends = [d.station for d in valid_drops] + [total_length]

    z_offset = 0.0
    vertex_offset = 0

    for seg_idx, (start, end) in enumerate(zip(segment_starts, segment_ends)):
        samples = _sample_segment(curve_obj, params.resolution_m, start, end, total_length)

        if len(samples) < 2:
            continue

        for sample in samples:
            sample["position"] = sample["position"] - Vector((0, 0, z_offset))

        segment_verts, segment_faces = _build_segment_mesh(samples, params, alignment)

        for face in segment_faces:
            all_faces.append(tuple(v + vertex_offset for v in face))

        all_vertices.extend(segment_verts)
        vertex_offset += len(segment_verts)

        if seg_idx < len(valid_drops):
            drop = valid_drops[seg_idx]

            t = drop.station / total_length
            pos, tangent, normal = evaluate_curve_at_parameter(curve_obj, t)

            pos = pos - Vector((0, 0, z_offset))

            if alignment:
                section_params = alignment.get_params_at_station(drop.station)
            else:
                section_params = params

            drop_verts, drop_faces = generate_drop_geometry(drop, section_params, pos, tangent, normal)

            for face in drop_faces:
                all_faces.append(tuple(v + vertex_offset for v in face))

            all_vertices.extend(drop_verts)
            vertex_offset += len(drop_verts)

            z_offset += drop.drop_height

    return all_vertices, all_faces


def _sample_segment(
    curve_obj, resolution_m: float, start_station: float, end_station: float, total_length: float
) -> List[dict]:
    """Sample curve points for a segment between two stations."""
    t_start = start_station / total_length
    t_end = end_station / total_length

    segment_length = end_station - start_station
    num_samples = max(2, int(segment_length / resolution_m) + 1)

    t_values = [t_start + (t_end - t_start) * i / (num_samples - 1) for i in range(num_samples)]

    return _sample_with_rmf(curve_obj, t_values, total_length)


def _build_segment_mesh(
    samples: List[dict], params: ChannelParams, alignment
) -> Tuple[List[Vector], List[Tuple[int, ...]]]:
    """Build mesh for a channel segment from samples."""
    vertices = []
    faces = []

    has_transitions = alignment is not None and len(alignment.transitions) > 0

    inner_verts, outer_verts = generate_section_vertices_with_lining(params)
    has_lining = len(outer_verts) > 0
    num_inner_verts = len(inner_verts)
    num_outer_verts = len(outer_verts) if has_lining else 0
    total_verts_per_section = num_inner_verts + num_outer_verts

    # Calculate channel half-width
    if params.section_type == SectionType.TRAPEZOIDAL:
        channel_half_width = (params.bottom_width + 2 * params.side_slope * params.total_height) / 2
    elif params.section_type == SectionType.TRIANGULAR:
        channel_half_width = params.side_slope * params.total_height
    else:
        channel_half_width = params.bottom_width / 2

    for sample in samples:
        pos = sample["position"]
        tangent = sample["tangent"]
        normal = sample["normal"]
        station = sample.get("station", 0.0)
        curve_radius = sample.get("curve_radius", float('inf'))
        turn_direction = sample.get("turn_direction", 0.0)

        binormal = tangent.cross(normal).normalized()

        if has_transitions:
            section_params = alignment.get_params_at_station(station)
            inner_verts, outer_verts = generate_section_vertices_with_lining(section_params)

        # Adjust profile for tight curves
        adjusted_inner = _adjust_profile_for_curvature(
            inner_verts, curve_radius, turn_direction, channel_half_width
        )

        for sx, sy in adjusted_inner:
            world_pos = pos + binormal * sx + normal * sy
            vertices.append(world_pos)

        if has_lining:
            adjusted_outer = _adjust_profile_for_curvature(
                outer_verts, curve_radius, turn_direction, channel_half_width * 1.2
            )
            for sx, sy in adjusted_outer:
                world_pos = pos + binormal * sx + normal * sy
                vertices.append(world_pos)

    num_samples = len(samples)
    is_open_channel = params.section_type in (SectionType.TRAPEZOIDAL, SectionType.RECTANGULAR, SectionType.TRIANGULAR)
    edge_info = _get_profile_edge_ranges(params, num_inner_verts)

    for i in range(num_samples - 1):
        base_current = i * total_verts_per_section
        base_next = (i + 1) * total_verts_per_section

        if is_open_channel:
            if params.section_type == SectionType.TRIANGULAR:
                right_start, right_end = edge_info["right_slope"]
                tl_idx = edge_info["top_left"]
                left_start, left_end = edge_info.get("left_slope", (tl_idx, tl_idx))

                # Right slope faces
                for j in range(right_start, right_end):
                    j_next = j + 1
                    faces.append((base_current + j, base_current + j_next, base_next + j_next, base_next + j))

                # Left slope faces
                if left_start < left_end:
                    # First face: top_left to first left slope intermediate
                    faces.append((base_current + tl_idx, base_current + left_start,
                                  base_next + left_start, base_next + tl_idx))
                    # Intermediate faces
                    for j in range(left_start, left_end - 1):
                        j_next = j + 1
                        faces.append((base_current + j, base_current + j_next, base_next + j_next, base_next + j))
                    # Last face: last intermediate to apex
                    faces.append((base_current + left_end - 1, base_current + 0,
                                  base_next + 0, base_next + left_end - 1))
                else:
                    faces.append((base_current + tl_idx, base_current + 0, base_next + 0, base_next + tl_idx))
            else:
                # TRAPEZOIDAL / RECTANGULAR
                bottom_start, bottom_end = edge_info["bottom"]
                right_start, right_end = edge_info["right_wall"]
                tl_idx = edge_info["top_left"]
                left_wall_start, left_wall_end = edge_info.get("left_wall", (tl_idx, tl_idx))

                for j in range(bottom_start, bottom_end):
                    j_next = j + 1
                    faces.append((base_current + j, base_current + j_next, base_next + j_next, base_next + j))

                for j in range(right_start, right_end):
                    j_next = j + 1
                    faces.append((base_current + j, base_current + j_next, base_next + j_next, base_next + j))

                # Left wall faces (subdivided)
                if left_wall_start < left_wall_end:
                    faces.append((base_current + tl_idx, base_current + left_wall_start,
                                  base_next + left_wall_start, base_next + tl_idx))
                    for j in range(left_wall_start, left_wall_end - 1):
                        j_next = j + 1
                        faces.append((base_current + j, base_current + j_next, base_next + j_next, base_next + j))
                    faces.append((base_current + left_wall_end - 1, base_current + 0,
                                  base_next + 0, base_next + left_wall_end - 1))
                else:
                    faces.append((base_current + tl_idx, base_current + 0, base_next + 0, base_next + tl_idx))
        else:
            is_full_circle = params.section_type == SectionType.PIPE
            if is_full_circle:
                for j in range(num_inner_verts):
                    j_next = (j + 1) % num_inner_verts
                    faces.append((base_current + j, base_current + j_next, base_next + j_next, base_next + j))
            else:
                for j in range(num_inner_verts - 1):
                    j_next = j + 1
                    faces.append((base_current + j, base_current + j_next, base_next + j_next, base_next + j))

        if has_lining:
            outer_offset = num_inner_verts
            if params.section_type == SectionType.PIPE:
                for j in range(num_outer_verts):
                    j_next = (j + 1) % num_outer_verts
                    faces.append(
                        (
                            base_current + outer_offset + j,
                            base_next + outer_offset + j,
                            base_next + outer_offset + j_next,
                            base_current + outer_offset + j_next,
                        )
                    )
            else:
                for j in range(num_outer_verts - 1):
                    j_next = j + 1
                    faces.append(
                        (
                            base_current + outer_offset + j,
                            base_next + outer_offset + j,
                            base_next + outer_offset + j_next,
                            base_current + outer_offset + j_next,
                        )
                    )

    return vertices, faces


def create_channel_object(
    name: str, vertices: List[Vector], faces: List[Tuple[int, ...]], collection_name: str = "CADHY_Channels"
):
    """Create or update a Blender mesh object from vertices and faces."""
    import bmesh
    import bpy

    if collection_name not in bpy.data.collections:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[collection_name]

    if name in bpy.data.objects:
        obj = bpy.data.objects[name]
        mesh = obj.data

        bm = bmesh.new()
        bm.to_mesh(mesh)
        bm.free()
    else:
        mesh = bpy.data.meshes.new(name + "_mesh")
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)

    mesh.clear_geometry()
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.update()
    mesh.validate()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    return obj


def update_mesh_geometry(obj, vertices: List[Vector], faces: List[Tuple[int, ...]]) -> None:
    """Update an existing mesh object with new geometry."""
    import bmesh

    mesh = obj.data

    mesh.clear_geometry()
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.update()
    mesh.validate()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
