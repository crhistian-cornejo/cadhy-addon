"""
CFD Mesh Quality Panel
Mesh quality operator for CFD simulation.
Similar to Salome/OpenFOAM checkMesh functionality.
"""

import bpy
from bpy.props import BoolProperty
from bpy.types import Operator

# Global cache for mesh quality results (shared with pt_unified)
_quality_cache = {}


def update_quality_cache(obj_name, quality):
    """Update quality cache (callable from external modules)."""
    _quality_cache[obj_name] = quality


def get_quality_cache():
    """Get the quality cache dictionary."""
    return _quality_cache


class CADHY_OT_AnalyzeMeshQuality(Operator):
    """Analyze mesh quality for CFD simulation"""

    bl_idname = "cadhy.analyze_mesh_quality"
    bl_label = "Analyze Mesh Quality"
    bl_description = "Calculate CFD mesh quality metrics (skewness, aspect ratio, non-orthogonality)"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def execute(self, context):
        from ...core.geom.mesh_validate import calculate_cfd_mesh_quality

        obj = context.active_object
        quality = calculate_cfd_mesh_quality(obj)

        # Store in cache
        update_quality_cache(obj.name, quality)

        # Report summary
        self.report(
            {"INFO"},
            f"Mesh Quality: {quality.quality_rating} | "
            f"Skewness: {quality.skewness_max:.3f} | "
            f"Aspect: {quality.aspect_ratio_max:.1f} | "
            f"Non-ortho: {quality.non_ortho_max:.1f}°",
        )

        return {"FINISHED"}


# Register a dummy property for the progress bar visualization
def register_quality_props():
    """Register properties for quality visualization."""
    if not hasattr(bpy.types.Scene, "cadhy_quality_skew_viz"):
        bpy.types.Scene.cadhy_quality_skew_viz = BoolProperty(
            name="Skewness",
            description="Visual indicator of skewness",
            default=False,
        )


def unregister_quality_props():
    """Unregister quality properties."""
    if hasattr(bpy.types.Scene, "cadhy_quality_skew_viz"):
        del bpy.types.Scene.cadhy_quality_skew_viz
