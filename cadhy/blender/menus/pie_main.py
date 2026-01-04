"""
CADHY Pie Menu
Quick access to main CADHY operations via Alt+C.
"""

import bpy
from bpy.types import Menu, Operator


class CADHY_MT_PieMenu(Menu):
    """CADHY quick access pie menu"""

    bl_idname = "CADHY_MT_pie_menu"
    bl_label = "CADHY"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        settings = context.scene.cadhy
        obj = context.active_object

        # Detect context for smart button labels
        has_axis = settings.axis_object and settings.axis_object.type == "CURVE"
        has_curve_selected = obj and obj.type == "CURVE"
        can_build_channel = has_axis or has_curve_selected

        is_channel = obj and obj.type == "MESH" and hasattr(obj, "cadhy_channel") and obj.cadhy_channel.is_cadhy_object
        is_cfd = obj and obj.type == "MESH" and hasattr(obj, "cadhy_cfd") and obj.cadhy_cfd.is_cadhy_object

        # Check if CFD domain exists
        cfd_exists = False
        if settings.axis_object:
            from ...core.util.naming import get_cfd_domain_name

            cfd_name = get_cfd_domain_name(settings.axis_object.name)
            cfd_exists = cfd_name in bpy.data.objects

        # PIE POSITIONS:
        # West (4) - Left
        # East (6) - Right
        # South (2) - Bottom
        # North (8) - Top
        # Northwest (7) - Top-Left
        # Northeast (9) - Top-Right
        # Southwest (1) - Bottom-Left
        # Southeast (3) - Bottom-Right

        # WEST (Left) - Build/Update Channel
        if is_channel:
            pie.operator("cadhy.update_channel", text="Update Channel", icon="FILE_REFRESH")
        elif can_build_channel:
            pie.operator("cadhy.build_channel", text="Build Channel", icon="MOD_BUILD")
        else:
            pie.operator("cadhy.build_channel", text="Build Channel", icon="MOD_BUILD")

        # EAST (Right) - Build/Update CFD Domain
        if is_cfd:
            pie.operator("cadhy.update_cfd_domain", text="Update CFD", icon="FILE_REFRESH")
        elif cfd_exists:
            pie.operator("cadhy.build_cfd_domain", text="Rebuild CFD", icon="MOD_FLUIDSIM")
        else:
            pie.operator("cadhy.build_cfd_domain", text="Build CFD", icon="MOD_FLUIDSIM")

        # SOUTH (Bottom) - Generate Sections
        pie.operator("cadhy.generate_sections", text="Sections", icon="SNAP_EDGE")

        # NORTH (Top) - Export CFD
        pie.operator("cadhy.export_cfd", text="Export CFD", icon="EXPORT")

        # NORTHWEST (Top-Left) - Station Markers
        pie.operator("cadhy.create_station_markers", text="Markers", icon="FONT_DATA")

        # NORTHEAST (Top-Right) - Export Report
        pie.operator("cadhy.export_report", text="Report", icon="FILE_TEXT")

        # SOUTHWEST (Bottom-Left) - Validate Mesh
        pie.operator("cadhy.validate_mesh", text="Validate", icon="CHECKMARK")

        # SOUTHEAST (Bottom-Right) - Assign Materials
        pie.operator("cadhy.assign_materials", text="Materials", icon="MATERIAL")


class CADHY_OT_CallPieMenu(Operator):
    """Call CADHY pie menu"""

    bl_idname = "cadhy.call_pie_menu"
    bl_label = "CADHY Pie Menu"
    bl_description = "Open CADHY quick access pie menu (Alt+C)"

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="CADHY_MT_pie_menu")
        return {"FINISHED"}
