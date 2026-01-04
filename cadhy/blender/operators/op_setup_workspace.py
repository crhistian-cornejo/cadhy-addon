"""
Workspace Setup Operator
Create an optimized CADHY workspace for channel design.
"""

import bpy
from bpy.types import Operator


class CADHY_OT_SetupWorkspace(Operator):
    """Setup CADHY workspace for channel design"""

    bl_idname = "cadhy.setup_workspace"
    bl_label = "Setup CADHY Workspace"
    bl_description = "Create an optimized workspace for channel design with CADHY"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Execute the operator."""
        workspace_name = "CADHY"

        # Check if workspace already exists
        if workspace_name in bpy.data.workspaces:
            # Switch to existing workspace
            context.window.workspace = bpy.data.workspaces[workspace_name]
            self.report({"INFO"}, f"Switched to existing '{workspace_name}' workspace")
            return {"FINISHED"}

        # Create new workspace by duplicating current
        bpy.ops.workspace.duplicate()
        new_workspace = context.window.workspace
        new_workspace.name = workspace_name

        # Configure the workspace screens/areas
        screen = new_workspace.screens[0]

        # Find main 3D view and configure it
        for area in screen.areas:
            if area.type == "VIEW_3D":
                # Configure 3D view
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        # Set shading to solid with cavity
                        space.shading.type = "SOLID"
                        space.shading.show_cavity = True
                        space.shading.cavity_type = "BOTH"

                        # Show overlays useful for engineering
                        space.overlay.show_floor = True
                        space.overlay.show_axis_x = True
                        space.overlay.show_axis_y = True
                        space.overlay.show_axis_z = False
                        space.overlay.show_text = True
                        space.overlay.show_stats = True
                        space.overlay.show_cursor = True
                        space.overlay.show_object_origins = True

                        # Set viewport display
                        space.show_region_ui = True  # Show N-panel (where CADHY is)
                        space.show_region_toolbar = True  # Show T-panel

                        # Camera settings for engineering view
                        space.clip_start = 0.01
                        space.clip_end = 10000.0

                        # Set view to top-down by default (good for channel layout)
                        region = None
                        for r in area.regions:
                            if r.type == "WINDOW":
                                region = r
                                break

                        if region:
                            # Override context for view operations
                            with context.temp_override(area=area, region=region):
                                bpy.ops.view3d.view_axis(type="TOP", align_active=False)

                break  # Only configure first 3D view

        # Set scene units to metric
        context.scene.unit_settings.system = "METRIC"
        context.scene.unit_settings.length_unit = "METERS"
        context.scene.unit_settings.scale_length = 1.0

        # Enable length display in viewport
        context.scene.tool_settings.use_snap = True
        context.scene.tool_settings.snap_elements = {"VERTEX", "EDGE"}

        self.report({"INFO"}, f"Created '{workspace_name}' workspace")
        return {"FINISHED"}


class CADHY_OT_ResetWorkspace(Operator):
    """Reset CADHY workspace to defaults"""

    bl_idname = "cadhy.reset_workspace"
    bl_label = "Reset CADHY Workspace"
    bl_description = "Reset CADHY workspace settings to defaults"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return "CADHY" in bpy.data.workspaces

    def execute(self, context):
        """Execute the operator."""
        workspace_name = "CADHY"

        if workspace_name not in bpy.data.workspaces:
            self.report({"ERROR"}, "CADHY workspace not found")
            return {"CANCELLED"}

        # Remove existing and recreate
        workspace = bpy.data.workspaces[workspace_name]

        # Switch to another workspace first
        for ws in bpy.data.workspaces:
            if ws.name != workspace_name:
                context.window.workspace = ws
                break

        # Remove old workspace
        bpy.data.workspaces.remove(workspace)

        # Create new one
        bpy.ops.cadhy.setup_workspace()

        self.report({"INFO"}, f"Reset '{workspace_name}' workspace")
        return {"FINISHED"}
