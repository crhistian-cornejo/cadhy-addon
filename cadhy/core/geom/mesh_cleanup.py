"""
Mesh Cleanup Module
Clean and prepare meshes for CFD export.
"""

from typing import Optional


def cleanup_mesh_for_cfd(obj, merge_distance: float = 0.0001) -> dict:
    """
    Clean up mesh for CFD export.
    
    Operations:
    - Remove doubles (merge by distance)
    - Remove loose geometry
    - Triangulate
    - Recalculate normals
    - Make normals consistent
    
    Args:
        obj: Blender mesh object
        merge_distance: Distance threshold for merging vertices
        
    Returns:
        Dictionary with cleanup statistics
    """
    import bpy
    import bmesh
    
    if obj is None or obj.type != 'MESH':
        return {"error": "Object is not a mesh"}
    
    stats = {
        "merged_verts": 0,
        "removed_loose_verts": 0,
        "removed_loose_edges": 0,
        "removed_degenerate": 0,
        "triangulated_faces": 0,
    }
    
    # Work with BMesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    initial_verts = len(bm.verts)
    initial_edges = len(bm.edges)
    initial_faces = len(bm.faces)
    
    # Remove doubles
    result = bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge_distance)
    stats["merged_verts"] = initial_verts - len(bm.verts)
    
    # Remove loose vertices
    loose_verts = [v for v in bm.verts if not v.link_edges]
    if loose_verts:
        bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')
        stats["removed_loose_verts"] = len(loose_verts)
    
    # Remove loose edges
    loose_edges = [e for e in bm.edges if not e.link_faces]
    if loose_edges:
        bmesh.ops.delete(bm, geom=loose_edges, context='EDGES')
        stats["removed_loose_edges"] = len(loose_edges)
    
    # Remove degenerate faces
    degenerate = [f for f in bm.faces if f.calc_area() < 1e-8]
    if degenerate:
        bmesh.ops.delete(bm, geom=degenerate, context='FACES')
        stats["removed_degenerate"] = len(degenerate)
    
    # Triangulate
    non_tris = [f for f in bm.faces if len(f.verts) > 3]
    if non_tris:
        bmesh.ops.triangulate(bm, faces=non_tris)
        stats["triangulated_faces"] = len(non_tris)
    
    # Recalculate normals
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    # Update mesh
    bm.to_mesh(obj.data)
    bm.free()
    
    obj.data.update()
    
    return stats


def make_manifold(obj) -> dict:
    """
    Attempt to make mesh manifold by filling holes and fixing edges.
    
    Args:
        obj: Blender mesh object
        
    Returns:
        Dictionary with operation statistics
    """
    import bpy
    import bmesh
    
    if obj is None or obj.type != 'MESH':
        return {"error": "Object is not a mesh"}
    
    stats = {
        "filled_holes": 0,
        "fixed_non_manifold": 0,
    }
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    # Find boundary edges (holes)
    boundary_edges = [e for e in bm.edges if e.is_boundary]
    
    if boundary_edges:
        # Try to fill holes
        # Group boundary edges into loops
        filled = 0
        
        # Simple approach: use fill_holes operator
        result = bmesh.ops.holes_fill(bm, edges=boundary_edges, sides=100)
        filled = len(result.get('faces', []))
        stats["filled_holes"] = filled
    
    # Fix non-manifold edges by dissolving
    non_manifold = [e for e in bm.edges if not e.is_manifold and not e.is_boundary]
    if non_manifold:
        # Try to dissolve problematic edges
        try:
            bmesh.ops.dissolve_edges(bm, edges=non_manifold)
            stats["fixed_non_manifold"] = len(non_manifold)
        except:
            pass  # Some edges can't be dissolved
    
    # Recalculate normals
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    bm.to_mesh(obj.data)
    bm.free()
    
    obj.data.update()
    
    return stats


def flip_normals(obj, inside_out: bool = False) -> None:
    """
    Flip mesh normals.
    
    Args:
        obj: Blender mesh object
        inside_out: If True, flip all normals
    """
    import bpy
    import bmesh
    
    if obj is None or obj.type != 'MESH':
        return
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    if inside_out:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    else:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    bm.to_mesh(obj.data)
    bm.free()
    
    obj.data.update()


def decimate_mesh(obj, ratio: float = 0.5, min_faces: int = 100) -> dict:
    """
    Reduce mesh complexity while preserving shape.
    
    Args:
        obj: Blender mesh object
        ratio: Target ratio of faces to keep (0-1)
        min_faces: Minimum number of faces to keep
        
    Returns:
        Dictionary with decimation statistics
    """
    import bpy
    import bmesh
    
    if obj is None or obj.type != 'MESH':
        return {"error": "Object is not a mesh"}
    
    initial_faces = len(obj.data.polygons)
    target_faces = max(min_faces, int(initial_faces * ratio))
    
    if initial_faces <= target_faces:
        return {"initial_faces": initial_faces, "final_faces": initial_faces, "reduced": 0}
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    # Use collapse decimation
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)
    
    # Calculate how many edges to collapse
    while len(bm.faces) > target_faces:
        # Find shortest edge
        shortest = min(bm.edges, key=lambda e: e.calc_length())
        if shortest.calc_length() > 0.1:  # Don't collapse if edges are too long
            break
        
        try:
            bmesh.ops.collapse(bm, edges=[shortest])
        except:
            break
    
    bm.to_mesh(obj.data)
    bm.free()
    
    obj.data.update()
    
    final_faces = len(obj.data.polygons)
    
    return {
        "initial_faces": initial_faces,
        "final_faces": final_faces,
        "reduced": initial_faces - final_faces
    }
