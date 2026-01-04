"""
CFD Panel
Panel for CFD domain generation and validation.
CFD domain follows the channel exactly - no fill mode or extension options.
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

            # Show linked channel info
            cfd_obj = bpy.data.objects.get(cfd_domain_name)
            if cfd_obj and hasattr(cfd_obj, "cadhy_cfd"):
                cfd = cfd_obj.cadhy_cfd
                if cfd.source_channel:
                    row = status_box.row()
                    row.label(text=f"Channel: {cfd.source_channel.name}", icon="LINKED")
        else:
            row = status_box.row()
            row.label(text="No CFD domain created", icon="INFO")

        # Info about CFD domain
        info_box = layout.box()
        info_box.label(text="CFD Domain Info", icon="INFO")
        col = info_box.column(align=True)
        col.label(text="Fluid volume follows channel exactly")
        col.label(text="Height = Design water depth")
        col.label(text="Updates when channel updates")

        layout.separator()

        # Build Button
        row = layout.row(align=True)
        row.scale_y = 1.5
        if cfd_domain_exists:
            row.operator("cadhy.build_cfd_domain", text="Rebuild CFD Domain", icon="FILE_REFRESH")
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

        layout.separator()

        # Mesh Settings
        mesh_box = layout.box()
        mesh_box.label(text="Mesh Settings", icon="MESH_GRID")
        col = mesh_box.column(align=True)
        col.prop(settings, "cfd_mesh_type", text="Type")
        col.prop(settings, "cfd_mesh_size", text="Element Size")
        col.prop(settings, "cfd_mesh_preview", text="Preview Wireframe")

        layout.separator()

        # Boundary Conditions
        bc_box = layout.box()
        bc_box.label(text="Boundary Conditions", icon="OUTLINER_DATA_MESH")

        # Inlet
        col = bc_box.column(align=True)
        col.label(text="Inlet:", icon="FORWARD")
        col.prop(settings, "bc_inlet_type", text="")
        if settings.bc_inlet_type == "VELOCITY":
            col.prop(settings, "bc_inlet_velocity", text="Velocity (m/s)")

        bc_box.separator()

        # Outlet
        col = bc_box.column(align=True)
        col.label(text="Outlet:", icon="BACK")
        col.prop(settings, "bc_outlet_type", text="")
        if settings.bc_outlet_type == "PRESSURE":
            col.prop(settings, "bc_outlet_pressure", text="Pressure (Pa)")

        bc_box.separator()

        # Walls
        col = bc_box.column(align=True)
        col.label(text="Walls:", icon="MESH_PLANE")
        col.prop(settings, "bc_wall_type", text="")
        if settings.bc_wall_type == "ROUGH":
            col.prop(settings, "bc_wall_roughness", text="Roughness (m)")

        bc_box.separator()

        # Top Surface
        col = bc_box.column(align=True)
        col.label(text="Top Surface:", icon="TRIA_UP")
        col.prop(settings, "bc_top_type", text="")
