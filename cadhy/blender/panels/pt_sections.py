"""
Sections Panel
Panel for cross-section generation.
"""

import bpy
from bpy.types import Panel


class CADHY_PT_Sections(Panel):
    """Cross-sections generation panel"""
    bl_label = "CADHY - Sections"
    bl_idname = "CADHY_PT_Sections"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CADHY"
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.cadhy
        
        # Station Range
        box = layout.box()
        box.label(text="Station Range", icon='DRIVER_DISTANCE')
        
        col = box.column(align=True)
        col.prop(settings, "sections_start", text="Start (m)")
        col.prop(settings, "sections_end", text="End (m, 0=auto)")
        col.prop(settings, "sections_step", text="Step (m)")
        
        # Show curve length if available
        if settings.axis_object and settings.axis_object.type == 'CURVE':
            from ...core.geom.build_channel import get_curve_length
            try:
                length = get_curve_length(settings.axis_object)
                box.label(text=f"Curve Length: {length:.2f} m")
            except:
                pass
        
        layout.separator()
        
        # Generate Button
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("cadhy.generate_sections", text="Generate Sections", icon='SNAP_MIDPOINT')
        
        layout.separator()
        
        # Sections Info
        box = layout.box()
        box.label(text="Generated Sections", icon='OUTLINER_OB_CURVE')
        
        # Count sections in collection
        if "CADHY_Sections" in bpy.data.collections:
            collection = bpy.data.collections["CADHY_Sections"]
            count = len(collection.objects)
            box.label(text=f"Count: {count} sections")
            
            if count > 0:
                # Show first and last station
                stations = []
                for obj in collection.objects:
                    if "cadhy_station" in obj:
                        stations.append(obj["cadhy_station"])
                
                if stations:
                    stations.sort()
                    box.label(text=f"Range: {stations[0]:.1f}m - {stations[-1]:.1f}m")
        else:
            box.label(text="No sections generated yet")
        
        layout.separator()
        
        # Export Sections
        box = layout.box()
        box.label(text="Export", icon='EXPORT')
        
        row = box.row(align=True)
        row.operator("cadhy.export_report", text="Export CSV").format = 'CSV'
        row.operator("cadhy.export_report", text="Export JSON").format = 'JSON'
