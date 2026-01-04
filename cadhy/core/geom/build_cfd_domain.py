"""
Build CFD Domain Module
Core geometry generation for CFD fluid domains.
CFD domain follows exactly the channel geometry (full section, no extensions).
"""

import math
from typing import Dict, List, Tuple

from mathutils import Vector

from ..model.cfd_params import PatchType
from ..model.channel_params import ChannelParams, SectionType
from .build_channel import _is_curve_cyclic, sample_curve_points


def generate_cfd_section_vertices(channel_params: ChannelParams) -> List[Tuple[float, float]]:
    """
    Generate 2D section vertices for CFD domain (full fluid volume).

    Args:
        channel_params: Channel geometry parameters

    Returns:
        List of (x, y) tuples for fluid section profile
    """
    # Use full channel height (height + freeboard) to fill entire channel volume
    # This ensures CFD domain matches the physical channel completely
    total_height = channel_params.height + channel_params.freeboard

    if channel_params.section_type == SectionType.TRAPEZOIDAL:
        bw = channel_params.bottom_width
        ss = channel_params.side_slope
        tw = bw + 2 * ss * total_height

        # Fluid profile (closed, counterclockwise)
        return [
            (-bw / 2, 0),
            (bw / 2, 0),
            (tw / 2, total_height),
            (-tw / 2, total_height),
        ]

    elif channel_params.section_type == SectionType.RECTANGULAR:
        bw = channel_params.bottom_width
        return [
            (-bw / 2, 0),
            (bw / 2, 0),
            (bw / 2, total_height),
            (-bw / 2, total_height),
        ]

    elif channel_params.section_type == SectionType.TRIANGULAR:
        # Triangular/V-channel section
        ss = channel_params.side_slope
        tw = 2 * ss * total_height  # Top width based on side slope

        return [
            (0, 0),  # Bottom vertex (point)
            (tw / 2, total_height),
            (-tw / 2, total_height),
        ]

    elif channel_params.section_type == SectionType.CIRCULAR:
        # Open circular channel (half-pipe) - use diameter
        r = channel_params.bottom_width / 2
        segments = 32
        # Half circle for open channel
        verts = []
        for i in range(segments + 1):
            angle = math.pi + (math.pi * i / segments)
            x = r * math.cos(angle)
            y = r * math.sin(angle) + r
            verts.append((x, y))
        return verts

    elif channel_params.section_type == SectionType.PIPE:
        # Closed pipe - use inner diameter for flow
        outer_r = channel_params.bottom_width / 2
        wall_thickness = channel_params.lining_thickness
        inner_r = outer_r - wall_thickness
        segments = 32
        # Full circle for pipe flow
        verts = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = inner_r * math.cos(angle)
            y = inner_r * math.sin(angle) + outer_r  # Center at pipe center
            verts.append((x, y))
        return verts

    return []


def build_cfd_domain_mesh(
    curve_obj, channel_params: ChannelParams, cfd_params=None
) -> Tuple[List[Vector], List[Tuple[int, ...]], Dict[str, List[int]]]:
    """
    Build CFD domain mesh geometry following exactly the channel axis.
    No extensions - just the pure fluid volume matching the channel.

    Args:
        curve_obj: Blender curve object (axis)
        channel_params: Channel parameters
        cfd_params: Deprecated, kept for compatibility but ignored

    Returns:
        Tuple of (vertices, faces, patch_face_indices)
    """
    # Check if curve is cyclic
    is_cyclic = _is_curve_cyclic(curve_obj)

    # Sample curve - same as channel
    samples = sample_curve_points(curve_obj, channel_params.resolution_m)
    if len(samples) < 2:
        return [], [], {}

    # For cyclic curves, remove duplicate endpoint
    if is_cyclic and len(samples) > 2:
        start_pos = samples[0]["position"]
        end_pos = samples[-1]["position"]
        if (end_pos - start_pos).length < channel_params.resolution_m * 0.5:
            samples = samples[:-1]

    # Generate CFD section profile (always full)
    section_verts = generate_cfd_section_vertices(channel_params)
    if not section_verts:
        return [], [], {}

    num_section_verts = len(section_verts)

    vertices = []
    faces = []
    patch_faces = {
        PatchType.INLET.value: [],
        PatchType.OUTLET.value: [],
        PatchType.WALLS.value: [],
        PatchType.TOP.value: [],
        PatchType.BOTTOM.value: [],
    }

    # Generate vertices for each sample point
    for sample in samples:
        pos = sample["position"]
        tangent = sample["tangent"]
        normal = sample["normal"]
        binormal = tangent.cross(normal).normalized()

        for sx, sy in section_verts:
            world_pos = pos + binormal * sx + normal * sy
            vertices.append(world_pos)

    # Generate side faces
    num_samples = len(samples)
    face_idx = 0

    # For cyclic: connect last to first
    num_connections = num_samples if is_cyclic else num_samples - 1

    for i in range(num_connections):
        base_current = i * num_section_verts
        next_idx = (i + 1) % num_samples if is_cyclic else i + 1
        base_next = next_idx * num_section_verts

        for j in range(num_section_verts):
            j_next = (j + 1) % num_section_verts

            v1 = base_current + j
            v2 = base_current + j_next
            v3 = base_next + j_next
            v4 = base_next + j

            faces.append((v1, v2, v3, v4))

            # Classify face by patch
            if channel_params.section_type in (SectionType.CIRCULAR, SectionType.PIPE):
                # Circular/Pipe: all walls
                patch_faces[PatchType.WALLS.value].append(face_idx)
            elif channel_params.section_type == SectionType.TRIANGULAR:
                # Triangular: no bottom, just sloped walls and top
                if j == num_section_verts - 1:
                    patch_faces[PatchType.TOP.value].append(face_idx)
                else:
                    patch_faces[PatchType.WALLS.value].append(face_idx)
            else:
                # For trap/rect: bottom (j=0), walls, top (last)
                if j == 0:
                    patch_faces[PatchType.BOTTOM.value].append(face_idx)
                elif j == num_section_verts - 1:
                    patch_faces[PatchType.TOP.value].append(face_idx)
                else:
                    patch_faces[PatchType.WALLS.value].append(face_idx)

            face_idx += 1

    # Generate inlet/outlet caps only for non-cyclic curves
    if not is_cyclic:
        # Inlet cap (first section)
        inlet_verts = list(range(num_section_verts))
        for i in range(1, num_section_verts - 1):
            faces.append((inlet_verts[0], inlet_verts[i + 1], inlet_verts[i]))
            patch_faces[PatchType.INLET.value].append(face_idx)
            face_idx += 1

        # Outlet cap (last section)
        base = (num_samples - 1) * num_section_verts
        outlet_verts = list(range(base, base + num_section_verts))
        for i in range(1, num_section_verts - 1):
            faces.append((outlet_verts[0], outlet_verts[i], outlet_verts[i + 1]))
            patch_faces[PatchType.OUTLET.value].append(face_idx)
            face_idx += 1

    return vertices, faces, patch_faces


def create_cfd_domain_object(
    name: str,
    vertices: List[Vector],
    faces: List[Tuple[int, ...]],
    patch_faces: Dict[str, List[int]],
    collection_name: str = "CADHY_CFD",
) -> "bpy.types.Object":
    """
    Create CFD domain object with material slots for patches.

    Args:
        name: Object name
        vertices: List of vertex positions
        faces: List of face vertex indices
        patch_faces: Dictionary mapping patch names to face indices
        collection_name: Collection to place object in

    Returns:
        Created Blender object
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
        mesh.clear_geometry()
    else:
        mesh = bpy.data.meshes.new(name + "_mesh")
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)

    # Build mesh
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.update()

    # Recalculate normals
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    # Clear existing materials
    obj.data.materials.clear()

    # Create materials for patches and assign faces
    patch_colors = {
        "inlet": (0.2, 0.4, 1.0, 1.0),  # Blue
        "outlet": (1.0, 0.4, 0.2, 1.0),  # Orange
        "walls": (0.5, 0.5, 0.5, 1.0),  # Gray
        "top": (0.2, 0.8, 1.0, 0.5),  # Cyan (transparent)
        "bottom": (0.4, 0.3, 0.2, 1.0),  # Brown
    }

    for patch_name, face_indices in patch_faces.items():
        if not face_indices:
            continue

        # Create or get material
        mat_name = f"CADHY_{patch_name}"
        if mat_name not in bpy.data.materials:
            mat = bpy.data.materials.new(mat_name)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                color = patch_colors.get(patch_name, (0.5, 0.5, 0.5, 1.0))
                bsdf.inputs["Base Color"].default_value = color
        else:
            mat = bpy.data.materials[mat_name]

        # Add material to object
        obj.data.materials.append(mat)
        mat_idx = len(obj.data.materials) - 1

        # Assign faces to material
        for face_idx in face_indices:
            if face_idx < len(mesh.polygons):
                mesh.polygons[face_idx].material_index = mat_idx

    mesh.update()
    mesh.validate()

    return obj


def update_cfd_domain_geometry(
    obj,
    vertices: List[Vector],
    faces: List[Tuple[int, ...]],
    patch_faces: Dict[str, List[int]],
) -> None:
    """
    Update existing CFD domain object geometry.

    Args:
        obj: Existing Blender object
        vertices: New vertex positions
        faces: New face vertex indices
        patch_faces: New patch face assignments
    """
    import bmesh

    mesh = obj.data
    mesh.clear_geometry()

    # Build new mesh
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.update()

    # Recalculate normals
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    # Re-assign materials to faces (keep existing materials)
    for i, (patch_name, face_indices) in enumerate(patch_faces.items()):
        if i < len(obj.data.materials):
            for face_idx in face_indices:
                if face_idx < len(mesh.polygons):
                    mesh.polygons[face_idx].material_index = i

    mesh.update()
    mesh.validate()
