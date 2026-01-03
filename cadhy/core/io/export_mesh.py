"""
Export Mesh Module
Export mesh geometry to various formats for CFD.
"""

import os
from typing import Optional, List
from enum import Enum


class ExportFormat(Enum):
    """Supported export formats."""
    STL = "stl"
    OBJ = "obj"
    PLY = "ply"
    FBX = "fbx"


def export_mesh_stl(obj, filepath: str, ascii: bool = False) -> bool:
    """
    Export mesh to STL format.
    
    Args:
        obj: Blender mesh object
        filepath: Output file path
        ascii: Use ASCII format instead of binary
        
    Returns:
        True if successful
    """
    import bpy
    
    if obj is None or obj.type != 'MESH':
        return False
    
    # Ensure .stl extension
    if not filepath.lower().endswith('.stl'):
        filepath += '.stl'
    
    # Store current selection
    original_selection = bpy.context.selected_objects.copy()
    original_active = bpy.context.view_layer.objects.active
    
    try:
        # Select only target object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Export
        bpy.ops.wm.stl_export(
            filepath=filepath,
            export_selected_objects=True,
            ascii_format=ascii,
            apply_modifiers=True,
        )
        
        return True
        
    except Exception as e:
        print(f"STL export error: {e}")
        return False
        
    finally:
        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for o in original_selection:
            o.select_set(True)
        bpy.context.view_layer.objects.active = original_active


def export_mesh_obj(obj, filepath: str, include_materials: bool = True) -> bool:
    """
    Export mesh to OBJ format.
    
    Args:
        obj: Blender mesh object
        filepath: Output file path
        include_materials: Include material definitions
        
    Returns:
        True if successful
    """
    import bpy
    
    if obj is None or obj.type != 'MESH':
        return False
    
    if not filepath.lower().endswith('.obj'):
        filepath += '.obj'
    
    original_selection = bpy.context.selected_objects.copy()
    original_active = bpy.context.view_layer.objects.active
    
    try:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        bpy.ops.wm.obj_export(
            filepath=filepath,
            export_selected_objects=True,
            export_materials=include_materials,
            apply_modifiers=True,
        )
        
        return True
        
    except Exception as e:
        print(f"OBJ export error: {e}")
        return False
        
    finally:
        bpy.ops.object.select_all(action='DESELECT')
        for o in original_selection:
            o.select_set(True)
        bpy.context.view_layer.objects.active = original_active


def export_mesh_ply(obj, filepath: str, ascii: bool = False) -> bool:
    """
    Export mesh to PLY format.
    
    Args:
        obj: Blender mesh object
        filepath: Output file path
        ascii: Use ASCII format
        
    Returns:
        True if successful
    """
    import bpy
    
    if obj is None or obj.type != 'MESH':
        return False
    
    if not filepath.lower().endswith('.ply'):
        filepath += '.ply'
    
    original_selection = bpy.context.selected_objects.copy()
    original_active = bpy.context.view_layer.objects.active
    
    try:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        bpy.ops.wm.ply_export(
            filepath=filepath,
            export_selected_objects=True,
            ascii_format=ascii,
            apply_modifiers=True,
        )
        
        return True
        
    except Exception as e:
        print(f"PLY export error: {e}")
        return False
        
    finally:
        bpy.ops.object.select_all(action='DESELECT')
        for o in original_selection:
            o.select_set(True)
        bpy.context.view_layer.objects.active = original_active


def export_mesh(obj, filepath: str, format: ExportFormat = ExportFormat.STL, **kwargs) -> bool:
    """
    Export mesh to specified format.
    
    Args:
        obj: Blender mesh object
        filepath: Output file path
        format: Export format
        **kwargs: Format-specific options
        
    Returns:
        True if successful
    """
    if format == ExportFormat.STL:
        return export_mesh_stl(obj, filepath, ascii=kwargs.get('ascii', False))
    elif format == ExportFormat.OBJ:
        return export_mesh_obj(obj, filepath, include_materials=kwargs.get('include_materials', True))
    elif format == ExportFormat.PLY:
        return export_mesh_ply(obj, filepath, ascii=kwargs.get('ascii', False))
    else:
        return False


def export_cfd_package(
    obj,
    output_dir: str,
    base_name: str = "cfd_domain",
    formats: List[ExportFormat] = None
) -> dict:
    """
    Export CFD domain in multiple formats.
    
    Args:
        obj: Blender mesh object
        output_dir: Output directory
        base_name: Base filename
        formats: List of formats to export
        
    Returns:
        Dictionary with export results
    """
    import os
    
    if formats is None:
        formats = [ExportFormat.STL, ExportFormat.OBJ]
    
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    for fmt in formats:
        filepath = os.path.join(output_dir, f"{base_name}.{fmt.value}")
        success = export_mesh(obj, filepath, fmt)
        results[fmt.value] = {
            "success": success,
            "filepath": filepath if success else None
        }
    
    return results
