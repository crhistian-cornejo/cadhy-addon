"""
CADHY Addon Preferences
Global configuration accessible from Blender Preferences > Add-ons > CADHY.
"""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import AddonPreferences


class CADHYPreferences(AddonPreferences):
    """CADHY global preferences accessible from Edit > Preferences > Add-ons."""

    bl_idname = "cadhy"

    # Logging settings
    log_level: EnumProperty(
        name="Log Level",
        description="Logging verbosity level",
        items=[
            ("DEBUG", "Debug", "Detailed debugging information"),
            ("INFO", "Info", "General information messages"),
            ("WARNING", "Warning", "Warning messages only"),
            ("ERROR", "Error", "Error messages only"),
        ],
        default="INFO",
    )

    log_to_file: BoolProperty(
        name="Log to File",
        description="Write logs to ~/.cadhy/cadhy.log",
        default=True,
    )

    log_max_files: IntProperty(
        name="Max Log Files",
        description="Maximum number of log backup files to keep",
        default=3,
        min=1,
        max=10,
    )

    # Developer settings
    developer_mode: BoolProperty(
        name="Developer Mode",
        description="Enable developer features (reload scripts, debug info)",
        default=True,  # Enabled for development
    )

    show_debug_info: BoolProperty(
        name="Show Debug Info",
        description="Display additional debug information in panels",
        default=True,  # Enabled for development
    )

    # CFD Solver integration (future)
    cfd_solver_path: StringProperty(
        name="CFD Solver Path",
        description="Path to external CFD solver (e.g., OpenFOAM)",
        default="",
        subtype="DIR_PATH",
    )

    # Default units
    default_units: EnumProperty(
        name="Default Units",
        description="Default unit system for new projects",
        items=[
            ("METERS", "Meters", "Use meters as default"),
            ("FEET", "Feet", "Use feet as default"),
        ],
        default="METERS",
    )

    # Export settings
    default_export_format: EnumProperty(
        name="Default Export Format",
        description="Default format for mesh exports",
        items=[
            ("STL", "STL", "Stereolithography format"),
            ("OBJ", "OBJ", "Wavefront OBJ format"),
            ("PLY", "PLY", "Stanford PLY format"),
        ],
        default="STL",
    )

    auto_triangulate_export: BoolProperty(
        name="Auto-Triangulate on Export",
        description="Automatically triangulate meshes when exporting for CFD",
        default=True,
    )

    # Update settings
    auto_check_updates: BoolProperty(
        name="Auto-Check Updates",
        description="Automatically check for updates on startup",
        default=True,
    )

    update_channel: EnumProperty(
        name="Update Channel",
        description="Which releases to check for updates",
        items=[
            ("STABLE", "Stable", "Only stable releases"),
            ("BETA", "Beta", "Include beta/pre-releases"),
        ],
        default="STABLE",
    )

    def draw(self, context):
        """Draw the preferences panel."""
        layout = self.layout

        # Logging Section
        box = layout.box()
        box.label(text="Logging", icon="TEXT")
        col = box.column(align=True)
        col.prop(self, "log_level")
        col.prop(self, "log_to_file")
        if self.log_to_file:
            col.prop(self, "log_max_files")

            # Show log file location
            import os

            log_path = os.path.join(os.path.expanduser("~"), ".cadhy", "cadhy.log")
            row = col.row()
            row.label(text=f"Log file: {log_path}", icon="FILE_TEXT")

            # Button to open log file
            row = col.row()
            row.operator("cadhy.open_log_file", text="Open Log File", icon="FILEBROWSER")

        # Developer Section
        box = layout.box()
        box.label(text="Developer", icon="CONSOLE")
        col = box.column(align=True)
        col.prop(self, "developer_mode")
        if self.developer_mode:
            col.prop(self, "show_debug_info")
            col.separator()
            col.operator("cadhy.dev_reload", text="Reload Add-on", icon="FILE_REFRESH")

        # CFD Integration Section
        box = layout.box()
        box.label(text="CFD Integration", icon="MOD_FLUIDSIM")
        col = box.column(align=True)
        col.prop(self, "cfd_solver_path")

        # Defaults Section
        box = layout.box()
        box.label(text="Defaults", icon="PREFERENCES")
        col = box.column(align=True)
        col.prop(self, "default_units")
        col.prop(self, "default_export_format")
        col.prop(self, "auto_triangulate_export")

        # Updates Section
        box = layout.box()
        box.label(text="Updates", icon="URL")
        col = box.column(align=True)
        col.prop(self, "auto_check_updates")
        col.prop(self, "update_channel")

        # Version info
        layout.separator()
        from ..core.util.versioning import CADHY_VERSION_STRING

        row = layout.row()
        row.label(text=f"CADHY Version: {CADHY_VERSION_STRING}", icon="INFO")


class CADHY_OT_OpenLogFile(bpy.types.Operator):
    """Open the CADHY log file in the default text editor"""

    bl_idname = "cadhy.open_log_file"
    bl_label = "Open Log File"
    bl_description = "Open the CADHY log file in your default text editor"

    def execute(self, context):
        import os
        import platform
        import subprocess

        log_path = os.path.join(os.path.expanduser("~"), ".cadhy", "cadhy.log")

        if not os.path.exists(log_path):
            self.report({"WARNING"}, f"Log file not found: {log_path}")
            return {"CANCELLED"}

        # Open with default application based on platform
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", log_path])
            elif system == "Windows":
                os.startfile(log_path)
            else:  # Linux
                subprocess.run(["xdg-open", log_path])

            self.report({"INFO"}, f"Opened log file: {log_path}")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to open log file: {e}")
            return {"CANCELLED"}


def get_preferences() -> CADHYPreferences:
    """Get CADHY addon preferences.

    Returns:
        CADHYPreferences instance or None if addon not registered.
    """
    addon = bpy.context.preferences.addons.get("cadhy")
    if addon:
        return addon.preferences
    return None
