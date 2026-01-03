"""
Export Panel
Panel for mesh and report export.
"""

import bpy
from bpy.types import Panel


class CADHY_PT_Export(Panel):
    """Export panel for meshes and reports"""

    bl_label = "CADHY - Export"
    bl_idname = "CADHY_PT_Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CADHY"
    bl_order = 3
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.cadhy

        # Export Path
        box = layout.box()
        box.label(text="Export Location", icon="FILE_FOLDER")
        box.prop(settings, "export_path", text="")

        layout.separator()

        # Mesh Export
        box = layout.box()
        box.label(text="Mesh Export", icon="MESH_DATA")

        box.prop(settings, "export_format", text="Format")

        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator("cadhy.export_cfd", text="Export CFD Mesh", icon="EXPORT")

        # Show selected object info
        obj = context.active_object
        if obj and obj.type == "MESH":
            col = box.column()
            col.label(text=f"Selected: {obj.name}")
            col.label(text=f"Vertices: {len(obj.data.vertices)}")
            col.label(text=f"Faces: {len(obj.data.polygons)}")

        layout.separator()

        # Report Export
        box = layout.box()
        box.label(text="Report Export", icon="FILE_TEXT")

        col = box.column(align=True)
        col.operator("cadhy.export_report", text="Export JSON Report", icon="FILE").format = "JSON"
        col.operator("cadhy.export_report", text="Export Text Report", icon="FILE_TEXT").format = "TXT"

        layout.separator()

        # Quick Export All
        box = layout.box()
        box.label(text="Quick Export", icon="PACKAGE")

        row = box.row()
        row.scale_y = 1.5
        row.operator("cadhy.export_all", text="Export All", icon="EXPORT")


class CADHY_OT_ExportAll(bpy.types.Operator):
    """Export all CADHY data (meshes and reports)"""

    bl_idname = "cadhy.export_all"
    bl_label = "Export All"
    bl_description = "Export all CADHY meshes and generate report"
    bl_options = {"REGISTER"}

    def execute(self, context):
        import os

        settings = context.scene.cadhy

        export_dir = bpy.path.abspath(settings.export_path)
        os.makedirs(export_dir, exist_ok=True)

        exported = 0

        # Export all CADHY meshes
        for obj in bpy.data.objects:
            if obj.type != "MESH":
                continue

            is_cadhy = False
            if hasattr(obj, "cadhy_channel") and obj.cadhy_channel.is_cadhy_object:
                is_cadhy = True
            elif hasattr(obj, "cadhy_cfd") and obj.cadhy_cfd.is_cadhy_object:
                is_cadhy = True

            if is_cadhy:
                from ...core.io.export_mesh import ExportFormat, export_mesh

                format_map = {
                    "STL": ExportFormat.STL,
                    "OBJ": ExportFormat.OBJ,
                    "PLY": ExportFormat.PLY,
                }
                fmt = format_map.get(settings.export_format, ExportFormat.STL)

                filepath = os.path.join(export_dir, f"{obj.name}.{fmt.value}")
                if export_mesh(obj, filepath, fmt):
                    exported += 1

        # Export report
        from ...core.io.export_reports import export_project_report, generate_project_report
        from ...core.model.channel_params import ChannelParams, SectionType

        section_type_map = {
            "TRAP": SectionType.TRAPEZOIDAL,
            "RECT": SectionType.RECTANGULAR,
            "CIRC": SectionType.CIRCULAR,
        }

        channel_params = ChannelParams(
            section_type=section_type_map.get(settings.section_type, SectionType.TRAPEZOIDAL),
            bottom_width=settings.bottom_width,
            side_slope=settings.side_slope,
            height=settings.height,
            freeboard=settings.freeboard,
        )

        axis_name = settings.axis_object.name if settings.axis_object else "Unknown"
        report = generate_project_report(channel_params, axis_name=axis_name)

        report_path = os.path.join(export_dir, "cadhy_report.json")
        export_project_report(report, report_path)

        self.report({"INFO"}, f"Exported {exported} meshes and report to {export_dir}")

        return {"FINISHED"}
