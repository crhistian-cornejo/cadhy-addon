"""
CADHY Pie Menu
Quick access to main CADHY operations via Alt+C.
"""

import bpy
from bpy.props import EnumProperty
from bpy.types import Menu, Operator


class CADHY_MT_ExportSubmenu(Menu):
    """Export format submenu"""

    bl_idname = "CADHY_MT_export_submenu"
    bl_label = "Export"

    def draw(self, context):
        layout = self.layout

        # 3D Mesh Export
        layout.label(text="3D Mesh:", icon="MESH_DATA")
        op = layout.operator("cadhy.quick_export_cfd", text="STL (OpenFOAM)", icon="EXPORT")
        op.format = "STL"
        op.target_mesh = "CFD"

        op = layout.operator("cadhy.quick_export_cfd", text="OBJ (Fluent)", icon="EXPORT")
        op.format = "OBJ"
        op.target_mesh = "CFD"

        op = layout.operator("cadhy.quick_export_cfd", text="STL - Channel", icon="MESH_DATA")
        op.format = "STL"
        op.target_mesh = "CHANNEL"

        layout.separator()

        # Report Export
        layout.label(text="Reports:", icon="FILE_TEXT")
        op = layout.operator("cadhy.quick_export_report", text="JSON Report", icon="FILE_TEXT")
        op.format = "JSON"

        op = layout.operator("cadhy.quick_export_report", text="TXT Report", icon="FILE_TEXT")
        op.format = "TXT"

        op = layout.operator("cadhy.quick_export_report", text="PDF Report", icon="FILE_TEXT")
        op.format = "PDF"

        layout.separator()

        # CFD Templates
        layout.label(text="CFD Templates:", icon="SETTINGS")
        layout.operator("cadhy.export_cfd_template", text="OpenFOAM Case", icon="SETTINGS")


class CADHY_OT_QuickExportCFD(Operator):
    """Quick export CFD/Channel mesh with format selection"""

    bl_idname = "cadhy.quick_export_cfd"
    bl_label = "Quick Export Mesh"
    bl_description = "Export mesh to specified format"
    bl_options = {"REGISTER"}

    format: EnumProperty(
        name="Format",
        items=[
            ("STL", "STL", "Stereolithography format"),
            ("OBJ", "OBJ", "Wavefront OBJ format"),
            ("PLY", "PLY", "Stanford PLY format"),
        ],
        default="STL",
    )

    target_mesh: EnumProperty(
        name="Target",
        items=[
            ("CFD", "CFD Domain", "Export CFD domain mesh"),
            ("CHANNEL", "Channel", "Export channel mesh"),
        ],
        default="CFD",
    )

    def execute(self, context):
        settings = context.scene.cadhy

        # Find target mesh
        target_obj = None

        if self.target_mesh == "CFD":
            # Look for CFD domain
            if settings.axis_object:
                from ...core.util.naming import get_cfd_domain_name

                cfd_name = get_cfd_domain_name(settings.axis_object.name)
                if cfd_name in bpy.data.objects:
                    target_obj = bpy.data.objects[cfd_name]
        else:
            # Look for channel
            if settings.axis_object:
                from ...core.util.naming import get_channel_name

                channel_name = get_channel_name(settings.axis_object.name)
                if channel_name in bpy.data.objects:
                    target_obj = bpy.data.objects[channel_name]

        if not target_obj:
            # Fall back to active object
            target_obj = context.active_object

        if not target_obj or target_obj.type != "MESH":
            self.report({"ERROR"}, "No valid mesh object found")
            return {"CANCELLED"}

        # Select and make active
        bpy.ops.object.select_all(action="DESELECT")
        target_obj.select_set(True)
        context.view_layer.objects.active = target_obj

        # Call the export operator with the format
        bpy.ops.cadhy.export_cfd("INVOKE_DEFAULT", format=self.format)

        return {"FINISHED"}


class CADHY_OT_QuickExportReport(Operator):
    """Quick export report with format selection"""

    bl_idname = "cadhy.quick_export_report"
    bl_label = "Quick Export Report"
    bl_description = "Export project report to specified format"
    bl_options = {"REGISTER"}

    format: EnumProperty(
        name="Format",
        items=[
            ("JSON", "JSON", "JSON format (machine-readable)"),
            ("TXT", "TXT", "Plain text format"),
            ("PDF", "PDF", "PDF document (requires reportlab)"),
        ],
        default="JSON",
    )

    def execute(self, context):
        if self.format == "PDF":
            # Call PDF export operator directly
            bpy.ops.cadhy.export_pdf_report("INVOKE_DEFAULT")
        else:
            # Use standard export
            bpy.ops.cadhy.export_report("INVOKE_DEFAULT")

        return {"FINISHED"}


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

        # NORTH (Top) - Export Menu (opens submenu)
        pie.menu("CADHY_MT_export_submenu", text="Export...", icon="EXPORT")

        # NORTHWEST (Top-Left) - Station Markers
        pie.operator("cadhy.create_station_markers", text="Markers", icon="FONT_DATA")

        # NORTHEAST (Top-Right) - Validate Mesh
        pie.operator("cadhy.validate_mesh", text="Validate", icon="CHECKMARK")

        # SOUTHWEST (Bottom-Left) - CFD Template
        pie.operator("cadhy.export_cfd_template", text="CFD Setup", icon="SETTINGS")

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
