"""
Export CFD Template Operator
Export CFD domain using pre-configured solver templates.
"""

import os

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy.types import Operator

from ...core.geom.mesh_cleanup import cleanup_mesh_for_cfd
from ...core.io.cfd_templates import (
    CFDSolver,
    create_openfoam_structure,
    generate_blockmesh_dict,
    generate_openfoam_mesh_dict,
    get_template,
    get_template_list,
)
from ...core.io.export_mesh import ExportFormat, export_mesh
from ...core.util.logging import OperationLogger


def get_template_items(self, context):
    """Generate template enum items."""
    return get_template_list()


class CADHY_OT_ExportCFDTemplate(Operator):
    """Export CFD mesh using solver template"""

    bl_idname = "cadhy.export_cfd_template"
    bl_label = "Export CFD (Template)"
    bl_description = "Export CFD domain using pre-configured solver templates"
    bl_options = {"REGISTER"}

    directory: StringProperty(
        name="Directory",
        description="Output directory",
        subtype="DIR_PATH",
    )

    template: EnumProperty(
        name="Solver Template",
        description="Pre-configured export settings for CFD solver",
        items=get_template_items,
        default=0,
    )

    cell_size: FloatProperty(
        name="Cell Size",
        description="Target background mesh cell size (meters)",
        default=0.5,
        min=0.01,
        max=10.0,
        unit="LENGTH",
    )

    generate_mesh_dicts: BoolProperty(
        name="Generate Mesh Dictionaries",
        description="Generate OpenFOAM mesh configuration files",
        default=True,
    )

    cleanup_mesh: BoolProperty(
        name="Clean Up Mesh",
        description="Apply CFD cleanup before export",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        obj = context.active_object
        if obj and obj.type == "MESH":
            if hasattr(obj, "cadhy_cfd") and obj.cadhy_cfd.is_cadhy_object:
                return True
            for coll in obj.users_collection:
                if "CFD" in coll.name:
                    return True
            return True
        return False

    def execute(self, context):
        """Execute the operator."""
        obj = context.active_object

        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "No mesh object selected")
            return {"CANCELLED"}

        template = get_template(self.template)
        if not template:
            self.report({"ERROR"}, f"Template not found: {self.template}")
            return {"CANCELLED"}

        with OperationLogger("Export CFD Template", self) as logger:
            output_dir = bpy.path.abspath(self.directory)

            # Cleanup if requested
            if self.cleanup_mesh:
                cleanup_mesh_for_cfd(obj)

            # Create folder structure for OpenFOAM
            paths = {}
            if template.create_structure and template.solver == CFDSolver.OPENFOAM:
                paths = create_openfoam_structure(output_dir, obj.name)
                stl_dir = paths["triSurface"]
            else:
                os.makedirs(output_dir, exist_ok=True)
                stl_dir = output_dir

            # Get patch information from CFD object
            patch_files = []
            patch_info = {}

            if template.split_patches and hasattr(obj, "cadhy_cfd"):
                # Export each patch as separate file
                patch_files = self._export_patches(obj, stl_dir, template)
                patch_info = self._get_patch_types(obj)
            else:
                # Single file export
                format_map = {
                    "stl": ExportFormat.STL,
                    "obj": ExportFormat.OBJ,
                    "ply": ExportFormat.PLY,
                }
                export_format = format_map.get(template.format, ExportFormat.STL)
                filepath = os.path.join(stl_dir, f"{obj.name}.{template.format}")

                success = export_mesh(obj, filepath, export_format, ascii=template.ascii)
                if success:
                    patch_files.append(filepath)
                else:
                    self.report({"ERROR"}, "Failed to export mesh")
                    return {"CANCELLED"}

            # Generate OpenFOAM dictionaries
            if self.generate_mesh_dicts and template.solver == CFDSolver.OPENFOAM and paths:
                # Get bounding box
                bbox = self._get_world_bbox(obj)

                # Generate blockMeshDict
                blockmesh_path = os.path.join(paths["system"], "blockMeshDict")
                generate_blockmesh_dict(bbox, self.cell_size, blockmesh_path)

                # Generate snappyHexMeshDict
                snappy_path = os.path.join(paths["system"], "snappyHexMeshDict")
                generate_openfoam_mesh_dict(patch_files, patch_info, snappy_path)

                logger.set_success(f"Exported to {paths['case']} with OpenFOAM config files")
            else:
                logger.set_success(f"Exported {len(patch_files)} files to {output_dir}")

        return {"FINISHED"}

    def invoke(self, context, event):
        """Show file browser."""
        settings = context.scene.cadhy

        # Set default directory
        if not self.directory:
            export_dir = bpy.path.abspath(settings.export_path)
            if not os.path.exists(export_dir):
                export_dir = bpy.path.abspath("//")
            self.directory = export_dir

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        """Draw export options."""
        layout = self.layout

        # Template selection
        layout.prop(self, "template")

        # Show template info
        template = get_template(self.template)
        if template:
            box = layout.box()
            box.label(text=template.notes, icon="INFO")

            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text=f"Format: {template.format.upper()}")
            col.label(text=f"ASCII: {'Yes' if template.ascii else 'No (Binary)'}")
            if template.split_patches:
                col.label(text="Patches: Separate files")

        layout.separator()

        # OpenFOAM specific options
        if template and template.solver == CFDSolver.OPENFOAM:
            layout.prop(self, "cell_size")
            layout.prop(self, "generate_mesh_dicts")

        layout.separator()
        layout.prop(self, "cleanup_mesh")

    def _export_patches(self, obj, output_dir, template):
        """Export each material/patch as separate file."""
        import bmesh

        patch_files = []
        mesh = obj.data

        if not mesh.materials:
            # No materials, export as single file
            filepath = os.path.join(output_dir, f"{obj.name}.{template.format}")
            format_map = {
                "stl": ExportFormat.STL,
                "obj": ExportFormat.OBJ,
                "ply": ExportFormat.PLY,
            }
            export_format = format_map.get(template.format, ExportFormat.STL)
            if export_mesh(obj, filepath, export_format, ascii=template.ascii):
                patch_files.append(filepath)
            return patch_files

        # Create temporary objects for each material
        original_active = bpy.context.view_layer.objects.active
        original_selection = [o for o in bpy.context.selected_objects]

        try:
            for mat_idx, mat in enumerate(mesh.materials):
                if not mat:
                    continue

                # Get patch name from material
                patch_name = mat.name.replace("CADHY_", "")

                # Create bmesh and extract faces
                bm = bmesh.new()
                bm.from_mesh(mesh)
                bm.faces.ensure_lookup_table()

                # Delete faces not in this material
                faces_to_delete = [f for f in bm.faces if f.material_index != mat_idx]
                bmesh.ops.delete(bm, geom=faces_to_delete, context="FACES")

                if len(bm.faces) == 0:
                    bm.free()
                    continue

                # Create temporary mesh and object
                temp_mesh = bpy.data.meshes.new(f"temp_{patch_name}")
                bm.to_mesh(temp_mesh)
                bm.free()

                temp_obj = bpy.data.objects.new(f"temp_{patch_name}", temp_mesh)
                bpy.context.collection.objects.link(temp_obj)

                # Copy transform
                temp_obj.matrix_world = obj.matrix_world.copy()

                # Export
                filepath = os.path.join(output_dir, f"{patch_name}.{template.format}")
                format_map = {
                    "stl": ExportFormat.STL,
                    "obj": ExportFormat.OBJ,
                    "ply": ExportFormat.PLY,
                }
                export_format = format_map.get(template.format, ExportFormat.STL)

                # Select only temp object
                bpy.ops.object.select_all(action="DESELECT")
                temp_obj.select_set(True)
                bpy.context.view_layer.objects.active = temp_obj

                if export_mesh(temp_obj, filepath, export_format, ascii=template.ascii):
                    patch_files.append(filepath)

                # Cleanup temp object
                bpy.data.objects.remove(temp_obj, do_unlink=True)
                bpy.data.meshes.remove(temp_mesh)

        finally:
            # Restore selection
            bpy.ops.object.select_all(action="DESELECT")
            for o in original_selection:
                if o:
                    o.select_set(True)
            if original_active:
                bpy.context.view_layer.objects.active = original_active

        return patch_files

    def _get_patch_types(self, obj):
        """Get OpenFOAM patch types from materials."""
        patch_info = {}
        mesh = obj.data

        for mat in mesh.materials:
            if not mat:
                continue

            name = mat.name.replace("CADHY_", "")

            # Map to OpenFOAM patch types
            if "inlet" in name.lower():
                patch_info[name] = "patch"
            elif "outlet" in name.lower():
                patch_info[name] = "patch"
            elif "wall" in name.lower():
                patch_info[name] = "wall"
            elif "top" in name.lower():
                patch_info[name] = "patch"  # Free surface
            elif "bottom" in name.lower():
                patch_info[name] = "wall"
            else:
                patch_info[name] = "wall"

        return patch_info

    def _get_world_bbox(self, obj):
        """Get world-space bounding box."""
        import mathutils

        bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]

        xs = [c.x for c in bbox_corners]
        ys = [c.y for c in bbox_corners]
        zs = [c.z for c in bbox_corners]

        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))
