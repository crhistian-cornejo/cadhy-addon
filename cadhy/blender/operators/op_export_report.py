"""
Export Report Operator
Operator to export project reports and section data.
"""

import os
import json
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, BoolProperty

from ...core.model.channel_params import ChannelParams, SectionType
from ...core.model.sections_params import SectionsReport
from ...core.io.export_reports import (
    export_sections_csv,
    export_sections_json,
    export_project_report,
    generate_project_report,
)
from ...core.util.logging import OperationLogger


class CADHY_OT_ExportReport(Operator):
    """Export CADHY project report"""
    bl_idname = "cadhy.export_report"
    bl_label = "Export Report"
    bl_description = "Export project report with channel parameters and section data"
    bl_options = {'REGISTER'}
    
    filepath: StringProperty(
        name="File Path",
        description="Path to export file",
        subtype='FILE_PATH'
    )
    
    format: EnumProperty(
        name="Format",
        description="Export format",
        items=[
            ('JSON', "JSON", "JSON format (for CADHY UI integration)"),
            ('CSV', "CSV", "CSV format (sections only)"),
            ('TXT', "Text", "Human-readable text report"),
        ],
        default='JSON'
    )
    
    include_sections: BoolProperty(
        name="Include Sections",
        description="Include section data in report",
        default=True
    )
    
    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        # Can export if we have scene settings
        return hasattr(context.scene, 'cadhy')
    
    def execute(self, context):
        """Execute the operator."""
        settings = context.scene.cadhy
        
        with OperationLogger("Export Report", self) as logger:
            # Build channel params from scene settings
            section_type_map = {
                'TRAP': SectionType.TRAPEZOIDAL,
                'RECT': SectionType.RECTANGULAR,
                'CIRC': SectionType.CIRCULAR,
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
            if self.include_sections and "cadhy_sections_report" in context.scene:
                try:
                    report_data = context.scene["cadhy_sections_report"]
                    # Reconstruct SectionsReport from stored data
                    from ...core.model.sections_params import SectionCut
                    sections = []
                    for sec_data in report_data.get("sections", []):
                        section = SectionCut(
                            station=sec_data["station_m"],
                            position=(sec_data["position"]["x"], sec_data["position"]["y"], sec_data["position"]["z"]),
                            tangent=(sec_data["tangent"]["x"], sec_data["tangent"]["y"], sec_data["tangent"]["z"]),
                            normal=(0, 0, 1),  # Simplified
                            hydraulic_area=sec_data.get("hydraulic_area_m2", 0),
                            wetted_perimeter=sec_data.get("wetted_perimeter_m", 0),
                            hydraulic_radius=sec_data.get("hydraulic_radius_m", 0),
                            top_width=sec_data.get("top_width_m", 0),
                            water_depth=sec_data.get("water_depth_m", 0),
                        )
                        sections.append(section)
                    
                    sections_report = SectionsReport(
                        sections=sections,
                        axis_name=report_data.get("axis_name", ""),
                        channel_name=report_data.get("channel_name", ""),
                        total_length=report_data.get("total_length_m", 0),
                    )
                except Exception as e:
                    self.report({'WARNING'}, f"Could not load sections data: {e}")
            
            # Get axis name
            axis_name = settings.axis_object.name if settings.axis_object else "Unknown"
            
            # Export based on format
            filepath = self.filepath
            
            if self.format == 'CSV':
                if sections_report:
                    if not filepath.lower().endswith('.csv'):
                        filepath += '.csv'
                    success = export_sections_csv(sections_report, filepath)
                else:
                    self.report({'ERROR'}, "No sections data available. Generate sections first.")
                    return {'CANCELLED'}
            
            elif self.format == 'JSON':
                if not filepath.lower().endswith('.json'):
                    filepath += '.json'
                
                report = generate_project_report(
                    channel_params=channel_params,
                    sections_report=sections_report,
                    axis_name=axis_name,
                    project_name=bpy.path.basename(bpy.data.filepath) or "CADHY Project"
                )
                success = export_project_report(report, filepath, format="json")
            
            elif self.format == 'TXT':
                if not filepath.lower().endswith('.txt'):
                    filepath += '.txt'
                
                report = generate_project_report(
                    channel_params=channel_params,
                    sections_report=sections_report,
                    axis_name=axis_name,
                    project_name=bpy.path.basename(bpy.data.filepath) or "CADHY Project"
                )
                success = export_project_report(report, filepath, format="txt")
            
            else:
                success = False
            
            if success:
                logger.set_success(f"Report exported to {filepath}")
            else:
                self.report({'ERROR'}, "Failed to export report")
                return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        """Show file browser."""
        settings = context.scene.cadhy
        
        if not self.filepath:
            export_dir = bpy.path.abspath(settings.export_path)
            if not os.path.exists(export_dir):
                export_dir = bpy.path.abspath("//")
            
            ext = {'JSON': '.json', 'CSV': '.csv', 'TXT': '.txt'}.get(self.format, '.json')
            self.filepath = os.path.join(export_dir, f"cadhy_report{ext}")
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def draw(self, context):
        """Draw export options."""
        layout = self.layout
        layout.prop(self, "format")
        layout.prop(self, "include_sections")
