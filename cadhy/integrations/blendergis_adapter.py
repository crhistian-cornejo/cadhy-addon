"""
BlenderGIS Adapter Module
Integration with BlenderGIS for geospatial data import.
"""

import bpy
from typing import Optional, Tuple


def is_blendergis_available() -> bool:
    """
    Check if BlenderGIS addon is installed and enabled.
    
    Returns:
        True if BlenderGIS is available
    """
    return "blendergis" in bpy.context.preferences.addons


def get_blendergis_version() -> Optional[str]:
    """
    Get BlenderGIS version if installed.
    
    Returns:
        Version string or None
    """
    if not is_blendergis_available():
        return None
    
    try:
        import blendergis
        if hasattr(blendergis, 'bl_info'):
            version = blendergis.bl_info.get('version', (0, 0, 0))
            return '.'.join(map(str, version))
    except:
        pass
    
    return "Unknown"


def import_shapefile(filepath: str, as_curve: bool = True) -> Optional[bpy.types.Object]:
    """
    Import a shapefile using BlenderGIS.
    
    Args:
        filepath: Path to .shp file
        as_curve: Import as curve (for axis) or mesh
        
    Returns:
        Imported object or None
    """
    if not is_blendergis_available():
        print("BlenderGIS not available")
        return None
    
    try:
        # Store current objects
        before = set(bpy.data.objects)
        
        # Call BlenderGIS import operator
        bpy.ops.importgis.shapefile(filepath=filepath)
        
        # Find new objects
        after = set(bpy.data.objects)
        new_objects = after - before
        
        if new_objects:
            obj = list(new_objects)[0]
            
            # Convert to curve if requested
            if as_curve and obj.type == 'MESH':
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.convert(target='CURVE')
            
            return obj
        
    except Exception as e:
        print(f"Shapefile import error: {e}")
    
    return None


def import_dem(filepath: str) -> Optional[bpy.types.Object]:
    """
    Import a DEM/GeoTIFF using BlenderGIS.
    
    Args:
        filepath: Path to DEM file
        
    Returns:
        Imported terrain object or None
    """
    if not is_blendergis_available():
        print("BlenderGIS not available")
        return None
    
    try:
        before = set(bpy.data.objects)
        
        # Call BlenderGIS DEM import
        bpy.ops.importgis.georaster(filepath=filepath)
        
        after = set(bpy.data.objects)
        new_objects = after - before
        
        if new_objects:
            return list(new_objects)[0]
        
    except Exception as e:
        print(f"DEM import error: {e}")
    
    return None


def get_georef_info() -> dict:
    """
    Get georeferencing information from BlenderGIS scene.
    
    Returns:
        Dictionary with CRS and origin information
    """
    info = {
        "crs": None,
        "origin_x": 0.0,
        "origin_y": 0.0,
        "origin_z": 0.0,
    }
    
    if not is_blendergis_available():
        return info
    
    try:
        # BlenderGIS stores georef info in scene
        scene = bpy.context.scene
        
        if hasattr(scene, 'geoscene'):
            geoscene = scene.geoscene
            
            if hasattr(geoscene, 'crs'):
                info["crs"] = geoscene.crs
            
            if hasattr(geoscene, 'origin'):
                info["origin_x"] = geoscene.origin.x
                info["origin_y"] = geoscene.origin.y
                info["origin_z"] = geoscene.origin.z
    except:
        pass
    
    return info


def set_georef_origin(x: float, y: float, z: float = 0.0) -> bool:
    """
    Set georeferencing origin in BlenderGIS.
    
    Args:
        x: X coordinate (easting)
        y: Y coordinate (northing)
        z: Z coordinate (elevation)
        
    Returns:
        True if successful
    """
    if not is_blendergis_available():
        return False
    
    try:
        scene = bpy.context.scene
        
        if hasattr(scene, 'geoscene') and hasattr(scene.geoscene, 'origin'):
            scene.geoscene.origin.x = x
            scene.geoscene.origin.y = y
            scene.geoscene.origin.z = z
            return True
    except:
        pass
    
    return False


class BlenderGISIntegration:
    """Helper class for BlenderGIS integration."""
    
    @staticmethod
    def check_availability() -> Tuple[bool, str]:
        """
        Check BlenderGIS availability and return status message.
        
        Returns:
            Tuple of (is_available, message)
        """
        if is_blendergis_available():
            version = get_blendergis_version()
            return (True, f"BlenderGIS {version} is available")
        else:
            return (False, "BlenderGIS is not installed. Install from https://github.com/domlysz/BlenderGIS")
    
    @staticmethod
    def import_axis_from_shapefile(filepath: str) -> Optional[bpy.types.Object]:
        """
        Import shapefile as CADHY axis curve.
        
        Args:
            filepath: Path to shapefile
            
        Returns:
            Curve object or None
        """
        obj = import_shapefile(filepath, as_curve=True)
        
        if obj:
            # Rename with CADHY prefix
            import os
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            obj.name = f"CADHY_Axis_{base_name}"
            
            # Move to CADHY collection
            from ..core.util.naming import ensure_collection, COLLECTION_AXES
            collection = ensure_collection(COLLECTION_AXES)
            
            for coll in obj.users_collection:
                coll.objects.unlink(obj)
            collection.objects.link(obj)
        
        return obj
    
    @staticmethod
    def import_terrain_from_dem(filepath: str) -> Optional[bpy.types.Object]:
        """
        Import DEM as terrain mesh.
        
        Args:
            filepath: Path to DEM file
            
        Returns:
            Terrain mesh object or None
        """
        obj = import_dem(filepath)
        
        if obj:
            import os
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            obj.name = f"CADHY_Terrain_{base_name}"
        
        return obj
