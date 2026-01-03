"""
Addon Updater Operators
Blender operators for update functionality.
"""

import bpy
from bpy.types import Operator

from ..core.util.versioning import CADHY_VERSION_STRING
from .addon_updater import updater


class CADHY_OT_CheckForUpdates(Operator):
    """Check for CADHY addon updates"""

    bl_idname = "cadhy.check_for_updates"
    bl_label = "Check for Updates"
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


class CADHY_OT_DownloadUpdate(Operator):
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
            # Store path for installation
            context.scene["cadhy_update_zip"] = filepath
        else:
            self.report({"ERROR"}, updater.error or "Download failed")

        return {"FINISHED"}


class CADHY_OT_InstallUpdate(Operator):
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


class CADHY_OT_OpenReleasePage(Operator):
    """Open CADHY releases page in browser"""

    bl_idname = "cadhy.open_release_page"
    bl_label = "Open Releases Page"
    bl_description = "Open GitHub releases page in web browser"
    bl_options = {"REGISTER"}

    def execute(self, context):
        import webbrowser

        webbrowser.open("https://github.com/cadhy/cadhy-addon/releases")
        return {"FINISHED"}


# Note: These classes are NOT registered here.
# Registration is handled by the main register.py
# which uses the operators defined in pt_updates.py instead.
