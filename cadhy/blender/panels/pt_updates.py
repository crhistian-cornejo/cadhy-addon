"""
Updates Panel
Panel for addon updates and information.
"""

import bpy
from bpy.types import Panel

from ...core.util.versioning import (
    CADHY_VERSION_STRING,
    check_blender_compatibility,
    format_system_info,
    get_blender_version_string,
)


class CADHY_PT_Updates(Panel):
    """Updates and information panel"""

    bl_label = "CADHY - Updates"
    bl_idname = "CADHY_PT_Updates"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CADHY"
    bl_order = 5
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        # Version Info
        box = layout.box()
        box.label(text="Version Information", icon="INFO")

        col = box.column()
        col.label(text=f"CADHY Version: {CADHY_VERSION_STRING}")
        col.label(text=f"Blender Version: {get_blender_version_string()}")

        # Compatibility check
        is_compatible, message = check_blender_compatibility()
        if is_compatible:
            col.label(text="✓ Compatible", icon="CHECKMARK")
        else:
            col.label(text="✗ Compatibility Issue", icon="ERROR")
            col.label(text=message)

        layout.separator()

        # Update Check (placeholder for future updater integration)
        box = layout.box()
        box.label(text="Updates", icon="FILE_REFRESH")

        row = box.row()
        row.operator("cadhy.check_updates", text="Check for Updates", icon="URL")

        col = box.column()
        col.label(text="Auto-update coming soon")
        col.label(text="Visit cadhy.app for updates")

        layout.separator()

        # Development
        box = layout.box()
        box.label(text="Development", icon="CONSOLE")

        row = box.row()
        row.operator("cadhy.dev_reload", text="Reload Addon", icon="FILE_REFRESH")

        row = box.row()
        row.operator("cadhy.print_system_info", text="Print System Info", icon="INFO")

        layout.separator()

        # Links
        box = layout.box()
        box.label(text="Links", icon="URL")

        col = box.column(align=True)
        col.operator("wm.url_open", text="Documentation", icon="HELP").url = "https://cadhy.app/docs"
        col.operator(
            "wm.url_open", text="Report Issue", icon="ERROR"
        ).url = "https://github.com/cadhy/cadhy-addon/issues"
        col.operator("wm.url_open", text="Website", icon="WORLD").url = "https://cadhy.app"


class CADHY_OT_CheckUpdates(bpy.types.Operator):
    """Check for CADHY addon updates"""

    bl_idname = "cadhy.check_updates"
    bl_label = "Check Updates"
    bl_description = "Check for available updates"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # Placeholder - will integrate with updater module
        self.report(
            {"INFO"}, f"CADHY {CADHY_VERSION_STRING} - Update check not yet implemented. Visit cadhy.app for updates."
        )
        return {"FINISHED"}


class CADHY_OT_PrintSystemInfo(bpy.types.Operator):
    """Print system information to console"""

    bl_idname = "cadhy.print_system_info"
    bl_label = "Print System Info"
    bl_description = "Print system information to console"
    bl_options = {"REGISTER"}

    def execute(self, context):
        info = format_system_info()
        print(info)
        self.report({"INFO"}, "System info printed to console")
        return {"FINISHED"}
