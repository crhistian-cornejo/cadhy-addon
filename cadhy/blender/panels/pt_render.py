"""
Render Panel
Panel for visualization and rendering setup.
"""

import bpy
from bpy.types import Panel


class CADHY_PT_Render(Panel):
    """Render and visualization panel"""
    bl_label = "CADHY - Render"
    bl_idname = "CADHY_PT_Render"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CADHY"
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        # Materials
        box = layout.box()
        box.label(text="Materials", icon='MATERIAL')
        
        col = box.column(align=True)
        col.operator("cadhy.assign_materials", text="Assign Material", icon='MATERIAL')
        
        # Material presets as sub-buttons
        row = box.row(align=True)
        op = row.operator("cadhy.assign_materials", text="Concrete")
        op.material = 'CONCRETE'
        op = row.operator("cadhy.assign_materials", text="Water")
        op.material = 'WATER'
        
        row = box.row(align=True)
        op = row.operator("cadhy.assign_materials", text="Earth")
        op.material = 'EARTH'
        op = row.operator("cadhy.assign_materials", text="Steel")
        op.material = 'STEEL'
        
        layout.separator()
        
        # Render Setup
        box = layout.box()
        box.label(text="Render Setup", icon='RENDER_STILL')
        
        row = box.row()
        row.scale_y = 1.3
        row.operator("cadhy.setup_render", text="Setup Render Scene", icon='SCENE')
        
        # Current render info
        col = box.column()
        col.label(text=f"Engine: {context.scene.render.engine}")
        col.label(text=f"Resolution: {context.scene.render.resolution_x}x{context.scene.render.resolution_y}")
        
        if context.scene.camera:
            col.label(text=f"Camera: {context.scene.camera.name}")
        else:
            col.label(text="No camera set", icon='ERROR')
        
        layout.separator()
        
        # Quick Render
        box = layout.box()
        box.label(text="Quick Actions", icon='RENDER_ANIMATION')
        
        row = box.row(align=True)
        row.operator("render.render", text="Render Image", icon='RENDER_STILL')
        row.operator("render.view_show", text="View", icon='RESTRICT_RENDER_OFF')
        
        # Viewport shading
        layout.separator()
        box = layout.box()
        box.label(text="Viewport", icon='VIEW3D')
        
        row = box.row(align=True)
        row.operator("view3d.toggle_shading", text="Solid").type = 'SOLID'
        row.operator("view3d.toggle_shading", text="Material").type = 'MATERIAL'
        row.operator("view3d.toggle_shading", text="Rendered").type = 'RENDERED'


class VIEW3D_OT_toggle_shading(bpy.types.Operator):
    """Toggle viewport shading mode"""
    bl_idname = "view3d.toggle_shading"
    bl_label = "Toggle Shading"
    bl_options = {'REGISTER'}
    
    type: bpy.props.EnumProperty(
        items=[
            ('SOLID', "Solid", ""),
            ('MATERIAL', "Material", ""),
            ('RENDERED', "Rendered", ""),
        ],
        default='SOLID'
    )
    
    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = self.type
                        break
        return {'FINISHED'}
