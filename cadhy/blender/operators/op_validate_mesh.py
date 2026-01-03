"""
Validate Mesh Operator
Operator to validate mesh geometry for CFD.
"""

import bpy
from bpy.types import Operator

from ...core.geom.mesh_validate import validate_mesh, check_self_intersections, get_cfd_domain_info
from ...core.util.logging import OperationLogger


class CADHY_OT_ValidateMesh(Operator):
    """Validate mesh for CFD export"""
    bl_idname = "cadhy.validate_mesh"
    bl_label = "Validate Mesh"
    bl_description = "Check mesh for CFD compatibility (watertight, manifold, etc.)"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return context.active_object and context.active_object.type == 'MESH'
    
    def execute(self, context):
        """Execute the operator."""
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        with OperationLogger("Validate Mesh", self) as logger:
            # Run validation
            result = validate_mesh(obj)
            
            # Check self-intersections (can be slow)
            result.self_intersections = check_self_intersections(obj)
            
            # Build report
            report_lines = [
                f"=== Mesh Validation: {obj.name} ===",
                f"Vertices: {len(obj.data.vertices)}",
                f"Faces: {len(obj.data.polygons)}",
                "",
                f"Watertight: {'✓ Yes' if result.is_watertight else '✗ No'}",
                f"Manifold: {'✓ Yes' if result.is_manifold else '✗ No'}",
                f"Non-manifold edges: {result.non_manifold_edges}",
                f"Non-manifold vertices: {result.non_manifold_verts}",
                f"Loose vertices: {result.loose_verts}",
                f"Loose edges: {result.loose_edges}",
                f"Degenerate faces: {result.degenerate_faces}",
                f"Self-intersections: {result.self_intersections}",
                "",
                f"Surface area: {result.surface_area:.4f} m²",
            ]
            
            if result.is_watertight:
                report_lines.append(f"Volume: {result.volume:.4f} m³")
            
            report_lines.append("")
            report_lines.append(f"CFD Valid: {'✓ Yes' if result.is_valid else '✗ No'}")
            
            # Print to console
            print("\n".join(report_lines))
            
            # Update object properties if it's a CADHY CFD object
            if hasattr(obj, 'cadhy_cfd') and obj.cadhy_cfd.is_cadhy_object:
                obj.cadhy_cfd.is_watertight = result.is_watertight
                obj.cadhy_cfd.is_valid = result.is_valid
                obj.cadhy_cfd.non_manifold_edges = result.non_manifold_edges
                obj.cadhy_cfd.volume = result.volume
            
            # Report to user
            if result.is_valid:
                self.report({'INFO'}, f"Mesh is valid for CFD. Volume: {result.volume:.3f} m³")
                logger.set_success("Mesh validation passed")
            else:
                issues = []
                if not result.is_watertight:
                    issues.append("not watertight")
                if result.non_manifold_edges > 0:
                    issues.append(f"{result.non_manifold_edges} non-manifold edges")
                if result.degenerate_faces > 0:
                    issues.append(f"{result.degenerate_faces} degenerate faces")
                if result.self_intersections > 0:
                    issues.append(f"{result.self_intersections} self-intersections")
                
                self.report({'WARNING'}, f"Mesh has issues: {', '.join(issues)}")
                logger.set_warning(f"Validation found issues: {', '.join(issues)}")
        
        return {'FINISHED'}
