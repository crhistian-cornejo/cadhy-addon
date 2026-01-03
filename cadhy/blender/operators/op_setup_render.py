"""
Setup Render Operator
Operator to set up rendering environment.
"""

import math

import bpy
from bpy.props import BoolProperty, FloatProperty
from bpy.types import Operator

from ...core.util.logging import OperationLogger


class CADHY_OT_SetupRender(Operator):
    """Set up rendering environment for visualization"""

    bl_idname = "cadhy.setup_render"
    bl_label = "Setup Render"
    bl_description = "Create camera, lights, and configure render settings"
    bl_options = {"REGISTER", "UNDO"}

    create_camera: BoolProperty(
        name="Create Camera", description="Create a camera positioned to view the channel", default=True
    )

    create_lights: BoolProperty(name="Create Lights", description="Create sun and fill lights", default=True)

    use_hdri: BoolProperty(name="Use HDRI", description="Set up HDRI environment (requires HDRI file)", default=False)

    camera_distance: FloatProperty(
        name="Camera Distance", description="Distance multiplier for camera placement", default=2.0, min=0.5, max=10.0
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return True

    def execute(self, context):
        """Execute the operator."""
        with OperationLogger("Setup Render", self) as logger:
            # Find CADHY objects to frame
            cadhy_objects = []
            for obj in bpy.data.objects:
                if obj.type == "MESH":
                    if hasattr(obj, "cadhy_channel") and obj.cadhy_channel.is_cadhy_object:
                        cadhy_objects.append(obj)
                    elif hasattr(obj, "cadhy_cfd") and obj.cadhy_cfd.is_cadhy_object:
                        cadhy_objects.append(obj)

            # Calculate bounding box of all CADHY objects
            if cadhy_objects:
                min_co = [float("inf")] * 3
                max_co = [float("-inf")] * 3

                for obj in cadhy_objects:
                    for corner in obj.bound_box:
                        world_corner = obj.matrix_world @ bpy.mathutils.Vector(corner)
                        for i in range(3):
                            min_co[i] = min(min_co[i], world_corner[i])
                            max_co[i] = max(max_co[i], world_corner[i])

                center = [(min_co[i] + max_co[i]) / 2 for i in range(3)]
                size = [max_co[i] - min_co[i] for i in range(3)]
                max_size = max(size)
            else:
                center = [0, 0, 0]
                max_size = 10

            # Create camera
            if self.create_camera:
                # Remove existing CADHY camera
                if "CADHY_Camera" in bpy.data.objects:
                    bpy.data.objects.remove(bpy.data.objects["CADHY_Camera"], do_unlink=True)

                # Create new camera
                cam_data = bpy.data.cameras.new("CADHY_Camera")
                cam_obj = bpy.data.objects.new("CADHY_Camera", cam_data)
                context.scene.collection.objects.link(cam_obj)

                # Position camera
                distance = max_size * self.camera_distance
                cam_obj.location = (center[0] + distance * 0.7, center[1] - distance, center[2] + distance * 0.5)

                # Point at center
                direction = bpy.mathutils.Vector(center) - cam_obj.location
                rot_quat = direction.to_track_quat("-Z", "Y")
                cam_obj.rotation_euler = rot_quat.to_euler()

                # Set as active camera
                context.scene.camera = cam_obj

                # Configure camera
                cam_data.lens = 35
                cam_data.clip_end = distance * 10

            # Create lights
            if self.create_lights:
                # Remove existing CADHY lights
                for name in ["CADHY_Sun", "CADHY_Fill"]:
                    if name in bpy.data.objects:
                        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

                # Create sun light
                sun_data = bpy.data.lights.new("CADHY_Sun", type="SUN")
                sun_obj = bpy.data.objects.new("CADHY_Sun", sun_data)
                context.scene.collection.objects.link(sun_obj)

                sun_obj.location = (center[0], center[1], center[2] + max_size * 2)
                sun_obj.rotation_euler = (math.radians(45), math.radians(30), math.radians(45))
                sun_data.energy = 3.0

                # Create fill light
                fill_data = bpy.data.lights.new("CADHY_Fill", type="AREA")
                fill_obj = bpy.data.objects.new("CADHY_Fill", fill_data)
                context.scene.collection.objects.link(fill_obj)

                fill_obj.location = (center[0] - max_size, center[1], center[2] + max_size * 0.5)
                fill_data.energy = 100.0
                fill_data.size = max_size * 0.5

            # Configure render settings
            context.scene.render.engine = "CYCLES"
            context.scene.cycles.samples = 128
            context.scene.render.resolution_x = 1920
            context.scene.render.resolution_y = 1080

            # Set up world if using HDRI
            if self.use_hdri:
                world = context.scene.world
                if not world:
                    world = bpy.data.worlds.new("CADHY_World")
                    context.scene.world = world

                world.use_nodes = True
                # Note: User needs to add HDRI manually
                self.report({"INFO"}, "HDRI setup prepared. Add your HDRI file to the Environment Texture node.")

            logger.set_success("Render environment set up successfully")

        return {"FINISHED"}

    def invoke(self, context, event):
        """Show options dialog."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw operator options."""
        layout = self.layout
        layout.prop(self, "create_camera")
        layout.prop(self, "create_lights")
        layout.prop(self, "camera_distance")
        layout.prop(self, "use_hdri")
