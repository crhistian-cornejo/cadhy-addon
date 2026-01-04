"""
Export PDF Report Operator
Operator to export project report as PDF.
"""

import os

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator

from ...core.io.export_pdf import export_pdf_fallback, generate_pdf_report, is_pdf_available
from ...core.io.export_reports import generate_project_report
from ...core.model.channel_params import ChannelParams, SectionType
from ...core.util.logging import OperationLogger


class CADHY_OT_ExportPDFReport(Operator):
    """Export project report as PDF"""

    bl_idname = "cadhy.export_pdf_report"
    bl_label = "Export PDF Report"
    bl_description = "Export pre-design report as PDF document"
    bl_options = {"REGISTER"}

    filepath: StringProperty(name="File Path", description="Path to export file", subtype="FILE_PATH")

    include_sections: BoolProperty(
        name="Include Sections Table", description="Include detailed sections data", default=True
    )

    include_hydraulics: BoolProperty(
        name="Include Hydraulics", description="Include hydraulic calculations", default=True
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        settings = context.scene.cadhy
        return settings.axis_object is not None

    def execute(self, context):
        """Execute the operator."""
        settings = context.scene.cadhy

        with OperationLogger("Export PDF Report", self) as logger:
            # Build channel params from scene settings
            section_type_map = {
                "TRAP": SectionType.TRAPEZOIDAL,
                "RECT": SectionType.RECTANGULAR,
                "CIRC": SectionType.CIRCULAR,
                "TRI": SectionType.TRIANGULAR,
                "PIPE": SectionType.PIPE,
            }

            channel_params = ChannelParams(
                section_type=section_type_map.get(settings.section_type, SectionType.TRAPEZOIDAL),
                bottom_width=settings.bottom_width,
                side_slope=settings.side_slope,
                height=settings.height,
                freeboard=settings.freeboard,
                lining_thickness=settings.lining_thickness,
                resolution_m=settings.resolution_m,
            )

            # Get sections report if available
            sections_report = None
            if "cadhy_sections_report" in context.scene:
                from ...core.model.sections_params import SectionsReport

                try:
                    sections_report = SectionsReport.from_dict(context.scene["cadhy_sections_report"])
                except Exception:
                    pass

            # Get CFD info if available
            cfd_info = None
            if settings.axis_object:
                from ...core.util.naming import get_cfd_domain_name

                cfd_name = get_cfd_domain_name(settings.axis_object.name)
                if cfd_name in bpy.data.objects:
                    cfd_obj = bpy.data.objects[cfd_name]
                    if hasattr(cfd_obj, "cadhy_cfd"):
                        from ...core.model.cfd_params import CFDDomainInfo

                        cfd = cfd_obj.cadhy_cfd
                        cfd_info = CFDDomainInfo(
                            volume=cfd.volume,
                            is_watertight=cfd.is_watertight,
                            is_valid=cfd.is_valid,
                            non_manifold_edges=cfd.non_manifold_edges,
                        )

            # Generate report data
            axis_name = settings.axis_object.name if settings.axis_object else "Unknown"
            report_data = generate_project_report(
                channel_params, cfd_info=cfd_info, sections_report=sections_report, axis_name=axis_name
            )

            # Export PDF
            if is_pdf_available():
                success = generate_pdf_report(
                    report_data,
                    self.filepath,
                    include_sections_table=self.include_sections,
                    include_hydraulics=self.include_hydraulics,
                )
            else:
                # Use HTML fallback
                self.report({"WARNING"}, "reportlab not installed. Generating HTML report instead.")
                success = export_pdf_fallback(report_data, self.filepath)

            if success:
                logger.set_success(f"Exported report to {self.filepath}")
            else:
                self.report({"ERROR"}, "Failed to export PDF report")
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

            axis_name = settings.axis_object.name if settings.axis_object else "project"
            self.filepath = os.path.join(export_dir, f"CADHY_Report_{axis_name}.pdf")

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        """Draw export options."""
        layout = self.layout

        if not is_pdf_available():
            box = layout.box()
            box.label(text="Note: reportlab not installed", icon="INFO")
            box.label(text="Will generate HTML report instead")

        layout.prop(self, "include_sections")
        layout.prop(self, "include_hydraulics")
