"""
Build CFD Domain Module
Core geometry generation for CFD fluid domains.
"""

import math
from typing import List, Tuple, Optional, Dict
from mathutils import Vector

from ..model.channel_params import ChannelParams, SectionType
from ..model.cfd_params import CFDParams, FillMode, PatchType
from .build_channel import sample_curve_points, get_curve_length, evaluate_curve_at_parameter


def generate_cfd_section_vertices(channel_params: ChannelParams, cfd_params: CFDParams) -> List[Tuple[float, float]]:
    """
    Generate 2D section vertices for CFD domain (fluid volume).
    
    Args:
        channel_params: Channel geometry parameters
        cfd_params: CFD domain parameters
        
    Returns:
        List of (x, y) tuples for fluid section profile
    """
    # Determine water height
    if cfd_params.fill_mode == FillMode.FULL:
        water_height = channel_params.total_height
    else:
        water_height = min(cfd_params.water_level_m, channel_params.total_height)
    
    if channel_params.section_type == SectionType.TRAPEZOIDAL:
        bw = channel_params.bottom_width
        ss = channel_params.side_slope
        tw = bw + 2 * ss * water_height
        
        # Fluid profile (closed, counterclockwise)
        return [
            (-bw / 2, 0),
            (bw / 2, 0),
            (tw / 2, water_height),
            (-tw / 2, water_height),
        ]
    
    elif channel_params.section_type == SectionType.RECTANGULAR:
        bw = channel_params.bottom_width
        return [
            (-bw / 2, 0),
            (bw / 2, 0),
            (bw / 2, water_height),
            (-bw / 2, water_height),
        ]
    
    elif channel_params.section_type == SectionType.CIRCULAR:
        r = channel_params.bottom_width / 2
        segments = 32
        
        if cfd_params.fill_mode == FillMode.FULL or water_height >= channel_params.bottom_width:
            # Full circle
            verts = []
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = r * math.cos(angle)
                y = r * math.sin(angle) + r
                verts.append((x, y))
            return verts
        else:
            # Partial fill - circular segment
            # Calculate angle for water level
            if water_height <= 0:
                return []
            
            theta = 2 * math.acos((r - water_height) / r)
            start_angle = math.pi + (math.pi - theta / 2)
            end_angle = math.pi - (math.pi - theta / 2)
            
            verts = []
            for i in range(segments + 1):
                angle = start_angle + (end_angle - start_angle) * i / segments
                x = r * math.cos(angle)
                y = r * math.sin(angle) + r
                verts.append((x, y))
            
            return verts
    
    return []


def build_cfd_domain_mesh(
    curve_obj,
    channel_params: ChannelParams,
    cfd_params: CFDParams
) -> Tuple[List[Vector], List[Tuple[int, ...]], Dict[str, List[int]]]:
    """
    Build CFD domain mesh geometry with inlet/outlet extensions.
    
    Args:
        curve_obj: Blender curve object (axis)
        channel_params: Channel parameters
        cfd_params: CFD domain parameters
        
    Returns:
        Tuple of (vertices, faces, patch_face_indices)
    """
    from mathutils import Vector
    
    # Sample curve
    samples = sample_curve_points(curve_obj, channel_params.resolution_m)
    if len(samples) < 2:
        return [], [], {}
    
    # Generate CFD section profile
    section_verts = generate_cfd_section_vertices(channel_params, cfd_params)
    if not section_verts:
        return [], [], {}
    
    num_section_verts = len(section_verts)
    
    # Add inlet extension
    extended_samples = []
    if cfd_params.inlet_extension_m > 0:
        first_sample = samples[0]
        tangent = first_sample['tangent']
        
        # Extend backwards
        num_ext_samples = max(2, int(cfd_params.inlet_extension_m / channel_params.resolution_m))
        for i in range(num_ext_samples, 0, -1):
            ext_dist = i * channel_params.resolution_m
            if ext_dist > cfd_params.inlet_extension_m:
                ext_dist = cfd_params.inlet_extension_m
            
            ext_pos = first_sample['position'] - tangent * ext_dist
            extended_samples.append({
                'position': ext_pos,
                'tangent': tangent,
                'normal': first_sample['normal'],
                'station': -ext_dist,
                'is_extension': True,
                'patch': 'inlet_ext'
            })
    
    # Add main samples
    for sample in samples:
        sample['is_extension'] = False
        sample['patch'] = 'main'
        extended_samples.append(sample)
    
    # Add outlet extension
    if cfd_params.outlet_extension_m > 0:
        last_sample = samples[-1]
        tangent = last_sample['tangent']
        
        num_ext_samples = max(2, int(cfd_params.outlet_extension_m / channel_params.resolution_m))
        for i in range(1, num_ext_samples + 1):
            ext_dist = i * channel_params.resolution_m
            if ext_dist > cfd_params.outlet_extension_m:
                ext_dist = cfd_params.outlet_extension_m
            
            ext_pos = last_sample['position'] + tangent * ext_dist
            extended_samples.append({
                'position': ext_pos,
                'tangent': tangent,
                'normal': last_sample['normal'],
                'station': last_sample['station'] + ext_dist,
                'is_extension': True,
                'patch': 'outlet_ext'
            })
    
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
    for sample in extended_samples:
        pos = sample['position']
        tangent = sample['tangent']
        normal = sample['normal']
        binormal = tangent.cross(normal).normalized()
        
        for sx, sy in section_verts:
            world_pos = pos + binormal * sx + normal * sy
            vertices.append(world_pos)
    
    # Generate side faces (walls)
    num_samples = len(extended_samples)
    face_idx = 0
    
    for i in range(num_samples - 1):
        base_current = i * num_section_verts
        base_next = (i + 1) * num_section_verts
        
        for j in range(num_section_verts):
            j_next = (j + 1) % num_section_verts
            
            v1 = base_current + j
            v2 = base_current + j_next
            v3 = base_next + j_next
            v4 = base_next + j
            
            faces.append((v1, v2, v3, v4))
            
            # Classify face by patch
            # Bottom faces (j == 0 for trap/rect, or bottom segment for circular)
            if j == 0 and channel_params.section_type != SectionType.CIRCULAR:
                patch_faces[PatchType.BOTTOM.value].append(face_idx)
            # Top faces (last segment before closing)
            elif j == num_section_verts - 1 and cfd_params.fill_mode == FillMode.WATER_LEVEL:
                patch_faces[PatchType.TOP.value].append(face_idx)
            else:
                patch_faces[PatchType.WALLS.value].append(face_idx)
            
            face_idx += 1
    
    # Generate inlet cap
    if cfd_params.cap_inlet:
        inlet_verts = list(range(num_section_verts))
        # Create triangulated cap
        for i in range(1, num_section_verts - 1):
            faces.append((inlet_verts[0], inlet_verts[i+1], inlet_verts[i]))
            patch_faces[PatchType.INLET.value].append(face_idx)
            face_idx += 1
    
    # Generate outlet cap
    if cfd_params.cap_outlet:
        base = (num_samples - 1) * num_section_verts
        outlet_verts = list(range(base, base + num_section_verts))
        for i in range(1, num_section_verts - 1):
            faces.append((outlet_verts[0], outlet_verts[i], outlet_verts[i+1]))
            patch_faces[PatchType.OUTLET.value].append(face_idx)
            face_idx += 1
    
    return vertices, faces, patch_faces


def create_cfd_domain_object(
    name: str,
    vertices: List[Vector],
    faces: List[Tuple[int, ...]],
    patch_faces: Dict[str, List[int]],
    collection_name: str = "CADHY_CFD"
) -> 'bpy.types.Object':
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
    import bpy
    import bmesh
    
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
        'inlet': (0.2, 0.4, 1.0, 1.0),    # Blue
        'outlet': (1.0, 0.4, 0.2, 1.0),   # Orange
        'walls': (0.5, 0.5, 0.5, 1.0),    # Gray
        'top': (0.2, 0.8, 1.0, 0.5),      # Cyan (transparent)
        'bottom': (0.4, 0.3, 0.2, 1.0),   # Brown
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
