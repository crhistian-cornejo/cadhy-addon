"""
Generate Sections Operator
Operator to generate cross-section cuts along channel axis.
"""

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

from ...core.model.channel_params import ChannelParams, SectionType
from ...core.model.sections_params import SectionsParams
from ...core.geom.build_sections import generate_sections, create_section_curves, create_section_meshes
from ...core.geom.build_channel import get_curve_length
from ...core.util.naming import COLLECTION_SECTIONS
from ...core.util.logging import OperationLogger


class CADHY_OT_GenerateSections(Operator):
    """Generate cross-sections along channel axis"""
    bl_idname = "cadhy.generate_sections"
    bl_label = "Generate Sections"
    bl_description = "Generate cross-section cuts at specified intervals"
    bl_options = {'REGISTER', 'UNDO'}
    
    create_meshes: BoolProperty(
        name="Create Meshes",
        description="Create filled mesh sections instead of curves",
        default=False
    )
    
    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        settings = context.scene.cadhy
        if settings.axis_object and settings.axis_object.type == 'CURVE':
            return True
        if context.active_object and context.active_object.type == 'CURVE':
            return True
        return False
    
    def execute(self, context):
        """Execute the operator."""
        settings = context.scene.cadhy
        
        # Get axis curve
        axis_obj = settings.axis_object
        if not axis_obj:
            axis_obj = context.active_object
        
        if not axis_obj or axis_obj.type != 'CURVE':
            self.report({'ERROR'}, "No valid curve selected as axis")
            return {'CANCELLED'}
        
        with OperationLogger("Generate Sections", self) as logger:
            # Create channel parameters
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
                resolution_m=settings.resolution_m,
            )
            
            # Create sections parameters
            curve_length = get_curve_length(axis_obj)
            end_station = settings.sections_end if settings.sections_end > 0 else None
            
            sections_params = SectionsParams(
                start_station=settings.sections_start,
                end_station=end_station,
                step=settings.sections_step,
                include_endpoints=True,
            )
            
            # Generate sections report
            water_depth = settings.cfd_water_level if settings.cfd_water_level > 0 else channel_params.height * 0.75
            report = generate_sections(axis_obj, channel_params, sections_params, water_depth)
            
            if not report.sections:
                self.report({'ERROR'}, "No sections generated. Check curve and parameters.")
                return {'CANCELLED'}
            
            # Clear existing sections in collection
            if COLLECTION_SECTIONS in bpy.data.collections:
                collection = bpy.data.collections[COLLECTION_SECTIONS]
                for obj in list(collection.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
            
            # Create section objects
            if self.create_meshes:
                created = create_section_meshes(report, COLLECTION_SECTIONS)
            else:
                created = create_section_curves(report, COLLECTION_SECTIONS)
            
            # Store report in scene for export
            context.scene["cadhy_sections_report"] = report.to_dict()
            
            logger.set_success(f"Generated {len(created)} sections from {report.sections[0].station:.1f}m to {report.sections[-1].station:.1f}m")
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        """Show options dialog."""
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        """Draw operator options."""
        layout = self.layout
        layout.prop(self, "create_meshes")
