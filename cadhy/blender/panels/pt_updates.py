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
from ...updater.addon_updater import updater


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
            col.label(text="Compatible", icon="CHECKMARK")
        else:
            col.label(text="Compatibility Issue", icon="ERROR")
            col.label(text=message)

        layout.separator()

        # Update Check
        box = layout.box()
        box.label(text="Updates", icon="FILE_REFRESH")

        row = box.row()
        row.operator("cadhy.check_updates", text="Check for Updates", icon="URL")

        # Show update status
        if updater.update_available and updater.latest_release:
            col = box.column()
            col.alert = True
            col.label(text=f"New version: v{updater.latest_release.version_string}", icon="ERROR")

            row = box.row()
            row.operator("cadhy.download_update", text="Download Update", icon="IMPORT")

            # Show install button if downloaded
            if "cadhy_update_zip" in context.scene:
                row = box.row()
                row.operator("cadhy.install_update", text="Install Update", icon="FILE_REFRESH")

        elif updater.error:
            col = box.column()
            col.label(text=f"Error: {updater.error}", icon="ERROR")

        elif updater.latest_release:
            col = box.column()
            col.label(text="Up to date", icon="CHECKMARK")

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
        ).url = "https://github.com/crhistian-cornejo/cadhy-addon/issues"
        col.operator(
            "wm.url_open", text="Releases", icon="PACKAGE"
        ).url = "https://github.com/crhistian-cornejo/cadhy-addon/releases"


class CADHY_OT_CheckUpdates(bpy.types.Operator):
    """Check for CADHY addon updates"""

    bl_idname = "cadhy.check_updates"
    bl_label = "Check Updates"
    bl_description = "Check GitHub for available updates"
    bl_options = {"REGISTER"}

    def execute(self, context):
        success = updater.check_for_updates()

        if success:
            if updater.update_available:
                release = updater.latest_release
                self.report({"INFO"}, f"Update available: v{release.version_string} (current: v{CADHY_VERSION_STRING})")
            else:
                self.report({"INFO"}, f"CADHY is up to date (v{CADHY_VERSION_STRING})")
        else:
            self.report({"ERROR"}, updater.error or "Update check failed")

        return {"FINISHED"}


class CADHY_OT_DownloadUpdate(bpy.types.Operator):
    """Download the latest CADHY update"""

    bl_idname = "cadhy.download_update"
    bl_label = "Download Update"
    bl_description = "Download the latest version from GitHub"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return updater.update_available

    def execute(self, context):
        filepath = updater.download_update()

        if filepath:
            self.report({"INFO"}, f"Downloaded update to: {filepath}")
            context.scene["cadhy_update_zip"] = filepath
        else:
            self.report({"ERROR"}, updater.error or "Download failed")

        return {"FINISHED"}


class CADHY_OT_InstallUpdate(bpy.types.Operator):
    """Install downloaded CADHY update"""

    bl_idname = "cadhy.install_update"
    bl_label = "Install Update"
    bl_description = "Install the downloaded update (requires Blender restart)"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return "cadhy_update_zip" in context.scene

    def execute(self, context):
        zip_path = context.scene.get("cadhy_update_zip")

        if not zip_path:
            self.report({"ERROR"}, "No update downloaded")
            return {"CANCELLED"}

        success = updater.install_update(zip_path)

        if success:
            self.report({"WARNING"}, "Update installed! Please restart Blender.")
            del context.scene["cadhy_update_zip"]
        else:
            self.report({"ERROR"}, updater.error or "Installation failed")

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


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
