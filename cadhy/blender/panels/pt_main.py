"""
Main Panel
Primary CADHY panel for channel creation.
"""

import bpy
from bpy.types import Panel


class CADHY_PT_Main(Panel):
    """Main CADHY panel for channel generation"""
    bl_label = "CADHY - Main"
    bl_idname = "CADHY_PT_Main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CADHY"
    bl_order = 0
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.cadhy
        
        # Axis Selection
        box = layout.box()
        box.label(text="Axis (Alignment)", icon='CURVE_DATA')
        
        row = box.row()
        row.prop(settings, "axis_object", text="")
        
        if settings.axis_object:
            row = box.row()
            row.label(text=f"Type: {settings.axis_object.type}")
        elif context.active_object and context.active_object.type == 'CURVE':
            row = box.row()
            row.label(text=f"Active: {context.active_object.name}", icon='INFO')
        else:
            row = box.row()
            row.label(text="Select a curve as axis", icon='ERROR')
        
        layout.separator()
        
        # Section Type
        box = layout.box()
        box.label(text="Section Type", icon='MESH_PLANE')
        box.prop(settings, "section_type", text="")
        
        layout.separator()
        
        # Section Parameters
        box = layout.box()
        box.label(text="Section Parameters", icon='PREFERENCES')
        
        col = box.column(align=True)
        
        if settings.section_type == 'CIRC':
            col.prop(settings, "bottom_width", text="Diameter")
        else:
            col.prop(settings, "bottom_width", text="Bottom Width")
        
        if settings.section_type == 'TRAP':
            col.prop(settings, "side_slope", text="Side Slope (H:V)")
        
        col.prop(settings, "height", text="Height")
        col.prop(settings, "freeboard", text="Freeboard")
        
        col.separator()
        col.prop(settings, "lining_thickness", text="Lining Thickness")
        col.prop(settings, "resolution_m", text="Resolution (m)")
        
        # Calculated values
        if settings.section_type == 'TRAP':
            total_height = settings.height + settings.freeboard
            top_width = settings.bottom_width + 2 * settings.side_slope * total_height
            
            box.separator()
            row = box.row()
            row.label(text=f"Top Width: {top_width:.2f} m")
            row = box.row()
            row.label(text=f"Total Height: {total_height:.2f} m")
        
        layout.separator()
        
        # Build Button
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("cadhy.build_channel", text="Build Channel", icon='MOD_BUILD')
        
        # Quick CFD build
        if settings.cfd_enabled:
            row = layout.row(align=True)
            row.operator("cadhy.build_cfd_domain", text="Build CFD Domain", icon='MOD_FLUIDSIM')
