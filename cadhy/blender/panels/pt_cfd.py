"""
CFD Panel
Panel for CFD domain generation and validation.
"""

import bpy
from bpy.types import Panel


class CADHY_PT_CFD(Panel):
    """CFD domain generation panel"""

    bl_label = "CADHY - CFD Domain"
    bl_idname = "CADHY_PT_CFD"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CADHY"
    bl_order = 1
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        settings = context.scene.cadhy
        self.layout.prop(settings, "cfd_enabled", text="")

    def draw(self, context):
        layout = self.layout
        settings = context.scene.cadhy

        layout.enabled = settings.cfd_enabled

        # Check if CFD domain exists
        cfd_domain_exists = False
        cfd_domain_name = ""
        if settings.axis_object:
            from ...core.util.naming import get_cfd_domain_name

            cfd_domain_name = get_cfd_domain_name(settings.axis_object.name)
            cfd_domain_exists = cfd_domain_name in bpy.data.objects

        # Status indicator
        status_box = layout.box()
        if cfd_domain_exists:
            row = status_box.row()
            row.label(text=f"Domain: {cfd_domain_name}", icon="CHECKMARK")
        else:
            row = status_box.row()
            row.label(text="No CFD domain created", icon="INFO")

        layout.separator()

        # Fill Mode
        box = layout.box()
        box.label(text="Fill Mode", icon="MOD_FLUIDSIM")
        box.prop(settings, "cfd_fill_mode", text="")

        if settings.cfd_fill_mode == "WATER_LEVEL":
            col = box.column(align=True)
            col.prop(settings, "cfd_water_level", text="Water Level")

            # Warning if water level exceeds channel height
            if settings.cfd_water_level > settings.height:
                row = box.row()
                row.alert = True
                row.label(text="Water level > Channel height!", icon="ERROR")
            elif settings.cfd_water_level > settings.height * 0.95:
                row = box.row()
                row.label(text="Water level near max", icon="INFO")

        layout.separator()

        # Extensions
        box = layout.box()
        box.label(text="Flow Extensions", icon="ARROW_LEFTRIGHT")

        col = box.column(align=True)
        col.prop(settings, "cfd_inlet_extension", text="Inlet Extension")
        col.prop(settings, "cfd_outlet_extension", text="Outlet Extension")

        layout.separator()

        # Build Button
        row = layout.row(align=True)
        row.scale_y = 1.5
        if cfd_domain_exists:
            row.operator("cadhy.build_cfd_domain", text="Update CFD Domain", icon="FILE_REFRESH")
        else:
            row.operator("cadhy.build_cfd_domain", text="Build CFD Domain", icon="MOD_FLUIDSIM")

        layout.separator()

        # Validation
        box = layout.box()
        box.label(text="Validation", icon="CHECKMARK")

        # Show validation status if CFD object is selected
        obj = context.active_object
        if obj and obj.type == "MESH" and hasattr(obj, "cadhy_cfd") and obj.cadhy_cfd.is_cadhy_object:
            cfd = obj.cadhy_cfd

            col = box.column(align=True)

            # Watertight status
            if cfd.is_watertight:
                col.label(text="Watertight", icon="CHECKMARK")
            else:
                col.label(text="Not Watertight", icon="ERROR")

            # Manifold status
            if cfd.non_manifold_edges == 0:
                col.label(text="Manifold", icon="CHECKMARK")
            else:
                col.label(text=f"{cfd.non_manifold_edges} non-manifold edges", icon="ERROR")

            # Volume
            if cfd.volume > 0:
                col.label(text=f"Volume: {cfd.volume:.3f} m³")

            # Overall status
            col.separator()
            if cfd.is_valid:
                col.label(text="Ready for CFD Export", icon="FILE_TICK")
            else:
                col.label(text="Fix issues before export", icon="ERROR")
        elif cfd_domain_exists:
            box.label(text="Select CFD domain to see status")
        else:
            box.label(text="Build CFD domain first")

        row = box.row()
        row.enabled = cfd_domain_exists or (obj and obj.type == "MESH")
        row.operator("cadhy.validate_mesh", text="Validate Mesh", icon="VIEWZOOM")
