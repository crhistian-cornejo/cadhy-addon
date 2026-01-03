"""
Export CFD Operator
Operator to export CFD domain mesh for CFD simulation.
"""

import os

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator

from ...core.geom.mesh_cleanup import cleanup_mesh_for_cfd
from ...core.geom.mesh_validate import validate_mesh
from ...core.io.export_mesh import ExportFormat, export_mesh
from ...core.util.logging import OperationLogger


class CADHY_OT_ExportCFD(Operator):
    """Export CFD domain mesh for simulation"""

    bl_idname = "cadhy.export_cfd"
    bl_label = "Export CFD Mesh"
    bl_description = "Export CFD domain mesh in formats suitable for CFD simulation"
    bl_options = {"REGISTER"}

    filepath: StringProperty(name="File Path", description="Path to export file", subtype="FILE_PATH")

    format: EnumProperty(
        name="Format",
        description="Export format",
        items=[
            ("STL", "STL", "Stereolithography format (recommended for CFD)"),
            ("OBJ", "OBJ", "Wavefront OBJ format"),
            ("PLY", "PLY", "Stanford PLY format"),
        ],
        default="STL",
    )

    cleanup_mesh: BoolProperty(
        name="Clean Up Mesh", description="Apply CFD cleanup (merge doubles, triangulate, fix normals)", default=True
    )

    validate_before_export: BoolProperty(
        name="Validate Before Export", description="Check mesh validity before exporting", default=True
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        obj = context.active_object
        if obj and obj.type == "MESH":
            # Check if it's a CADHY CFD domain
            if hasattr(obj, "cadhy_cfd") and obj.cadhy_cfd.is_cadhy_object:
                return True
            # Or any mesh in CFD collection
            for coll in obj.users_collection:
                if "CFD" in coll.name:
                    return True
            # Or just any selected mesh
            return True
        return False

    def execute(self, context):
        """Execute the operator."""
        obj = context.active_object

        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "No mesh object selected")
            return {"CANCELLED"}

        with OperationLogger("Export CFD Mesh", self) as logger:
            # Validate if requested
            if self.validate_before_export:
                validation = validate_mesh(obj)

                if not validation.is_valid:
                    warnings = []
                    if not validation.is_watertight:
                        warnings.append("Mesh is not watertight")
                    if validation.non_manifold_edges > 0:
                        warnings.append(f"{validation.non_manifold_edges} non-manifold edges")
                    if validation.degenerate_faces > 0:
                        warnings.append(f"{validation.degenerate_faces} degenerate faces")

                    self.report({"WARNING"}, f"Mesh has issues: {'; '.join(warnings)}")

            # Cleanup if requested
            if self.cleanup_mesh:
                # Work on a copy to not modify original
                cleanup_stats = cleanup_mesh_for_cfd(obj)
                if cleanup_stats.get("merged_verts", 0) > 0:
                    self.report({"INFO"}, f"Cleaned up mesh: merged {cleanup_stats['merged_verts']} vertices")

            # Export
            format_map = {
                "STL": ExportFormat.STL,
                "OBJ": ExportFormat.OBJ,
                "PLY": ExportFormat.PLY,
            }

            export_format = format_map.get(self.format, ExportFormat.STL)

            # Ensure filepath has correct extension
            filepath = self.filepath
            if not filepath.lower().endswith(f".{export_format.value}"):
                filepath = f"{filepath}.{export_format.value}"

            success = export_mesh(obj, filepath, export_format)

            if success:
                logger.set_success(f"Exported to {filepath}")
            else:
                self.report({"ERROR"}, "Failed to export mesh")
                return {"CANCELLED"}

        return {"FINISHED"}

    def invoke(self, context, event):
        """Show file browser."""
        settings = context.scene.cadhy

        # Set default path
        if not self.filepath:
            export_dir = bpy.path.abspath(settings.export_path)
            if not os.path.exists(export_dir):
                export_dir = bpy.path.abspath("//")

            obj_name = context.active_object.name if context.active_object else "cfd_domain"
            self.filepath = os.path.join(export_dir, f"{obj_name}.stl")

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        """Draw export options."""
        layout = self.layout
        layout.prop(self, "format")
        layout.prop(self, "cleanup_mesh")
        layout.prop(self, "validate_before_export")
