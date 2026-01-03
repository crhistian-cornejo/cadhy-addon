"""
Build Channel Module
Core geometry generation for hydraulic channels.
"""

import math
from typing import List, Tuple

from mathutils import Vector

from ..model.channel_params import ChannelParams, SectionType


def sample_curve_points(curve_obj, resolution_m: float) -> List[dict]:
    """
    Sample points along a Blender curve at specified resolution.

    Args:
        curve_obj: Blender curve object
        resolution_m: Distance between samples in meters

    Returns:
        List of dicts with 'position', 'tangent', 'normal', 'station'
    """

    # Get curve data
    curve_data = curve_obj.data
    if not curve_data.splines:
        return []

    curve_data.splines[0]

    # Calculate total length
    total_length = get_curve_length(curve_obj)
    if total_length <= 0:
        return []

    # Number of samples
    num_samples = max(2, int(total_length / resolution_m) + 1)

    samples = []
    for i in range(num_samples):
        t = i / (num_samples - 1)  # Parameter 0 to 1
        station = t * total_length

        # Evaluate curve at parameter t
        pos, tangent, normal = evaluate_curve_at_parameter(curve_obj, t)

        samples.append({"position": pos, "tangent": tangent, "normal": normal, "station": station, "t": t})

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

            # Calculate normal (perpendicular to tangent, preferring up direction)
            up = Vector((0, 0, 1))
            if abs(tangent.dot(up)) > 0.99:
                up = Vector((0, 1, 0))

            binormal = tangent.cross(up).normalized()
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


def generate_section_vertices(params: ChannelParams, include_outer: bool = False) -> List[Tuple[float, float]]:
    """
    Generate 2D section vertices in local coordinates.

    Args:
        params: Channel parameters
        include_outer: Include outer lining vertices

    Returns:
        List of (x, y) tuples for section profile
    """
    h = params.total_height

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

        if include_outer and params.lining_thickness > 0:
            lt = params.lining_thickness
            # Outer profile (offset outward)
            outer_bw = bw + 2 * lt / math.sqrt(1 + ss * ss)
            outer_tw = tw + 2 * lt
            outer_h = h + lt
            outer = [
                (-outer_bw / 2, -lt),
                (outer_bw / 2, -lt),
                (outer_tw / 2, outer_h),
                (-outer_tw / 2, outer_h),
            ]
            return inner + outer

        return inner

    elif params.section_type == SectionType.RECTANGULAR:
        bw = params.bottom_width
        inner = [
            (-bw / 2, 0),
            (bw / 2, 0),
            (bw / 2, h),
            (-bw / 2, h),
        ]

        if include_outer and params.lining_thickness > 0:
            lt = params.lining_thickness
            outer = [
                (-bw / 2 - lt, -lt),
                (bw / 2 + lt, -lt),
                (bw / 2 + lt, h + lt),
                (-bw / 2 - lt, h + lt),
            ]
            return inner + outer

        return inner

    elif params.section_type == SectionType.CIRCULAR:
        r = params.bottom_width / 2
        segments = 32
        inner = []
        for i in range(segments + 1):
            angle = math.pi + (math.pi * i / segments)
            x = r * math.cos(angle)
            y = r * math.sin(angle) + r
            inner.append((x, y))

        return inner

    return []


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

    # Generate section profile
    section_verts = generate_section_vertices(params, include_outer=False)
    num_section_verts = len(section_verts)

    vertices = []
    faces = []

    # Generate vertices for each sample point
    for sample in samples:
        pos = sample["position"]
        tangent = sample["tangent"]
        normal = sample["normal"]

        # Calculate local coordinate system
        binormal = tangent.cross(normal).normalized()

        # Transform section vertices to world position
        for sx, sy in section_verts:
            # Local to world: x along binormal, y along normal
            world_pos = pos + binormal * sx + normal * sy
            vertices.append(world_pos)

    # Generate faces connecting sections
    num_samples = len(samples)
    for i in range(num_samples - 1):
        base_current = i * num_section_verts
        base_next = (i + 1) * num_section_verts

        for j in range(num_section_verts):
            j_next = (j + 1) % num_section_verts

            # Quad face
            v1 = base_current + j
            v2 = base_current + j_next
            v3 = base_next + j_next
            v4 = base_next + j

            faces.append((v1, v2, v3, v4))

    return vertices, faces


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
