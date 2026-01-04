"""
Station Markers Operator
Create station markers along the channel axis showing chainage (0+000 km format).
"""

import bpy
from bpy.props import FloatProperty
from bpy.types import Operator

from ...core.geom.build_channel import get_curve_length, sample_curve_points


class CADHY_OT_CreateStationMarkers(Operator):
    """Create station markers along the channel axis"""

    bl_idname = "cadhy.create_station_markers"
    bl_label = "Create Station Markers"
    bl_description = "Add station markers (0+000 format) along the axis curve"
    bl_options = {"REGISTER", "UNDO"}

    interval: FloatProperty(
        name="Interval",
        description="Distance between station markers (meters)",
        default=10.0,
        min=1.0,
        max=1000.0,
        unit="LENGTH",
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        settings = context.scene.cadhy
        if settings.axis_object and settings.axis_object.type == "CURVE":
            return True
        if context.active_object and context.active_object.type == "CURVE":
            return True
        return False

    def execute(self, context):
        """Execute the operator."""
        settings = context.scene.cadhy

        # Get axis curve
        axis_obj = settings.axis_object
        if not axis_obj:
            axis_obj = context.active_object

        if not axis_obj or axis_obj.type != "CURVE":
            self.report({"ERROR"}, "No valid curve selected as axis")
            return {"CANCELLED"}

        # Get or create markers collection
        collection_name = "CADHY_Station_Markers"
        if collection_name not in bpy.data.collections:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        else:
            collection = bpy.data.collections[collection_name]
            # Clear existing markers for this axis
            markers_to_remove = [obj for obj in collection.objects if obj.name.startswith(f"Station_{axis_obj.name}_")]
            for obj in markers_to_remove:
                bpy.data.objects.remove(obj, do_unlink=True)

        # Get curve length
        curve_length = get_curve_length(axis_obj)
        if curve_length <= 0:
            self.report({"ERROR"}, "Curve has zero length")
            return {"CANCELLED"}

        # Sample points at station intervals
        samples = sample_curve_points(axis_obj, self.interval)
        if not samples:
            self.report({"ERROR"}, "Failed to sample curve")
            return {"CANCELLED"}

        # Get channel height for proper offset
        channel_height = settings.height + settings.freeboard if hasattr(settings, "height") else 2.5

        # Track created stations to avoid duplicates
        created_stations = set()

        # Create markers (skip first and last which will have inlet/outlet)
        marker_count = 0
        import math

        for i, sample in enumerate(samples):
            station = sample["station"]

            # Round to avoid floating point issues
            station_key = round(station, 2)

            # Skip if already created (duplicate prevention)
            if station_key in created_stations:
                continue

            # Skip first and last (will be inlet/outlet)
            if i == 0 or i == len(samples) - 1:
                continue

            created_stations.add(station_key)

            pos = sample["position"]
            normal = sample["normal"]

            # Format station as 0+000.00 (km+meters)
            km = int(station / 1000)
            m = station % 1000
            station_text = f"{km}+{m:06.2f}"

            # Create text object
            text_name = f"Station_{axis_obj.name}_{marker_count:03d}"

            # Create font curve
            font_curve = bpy.data.curves.new(name=text_name, type="FONT")
            font_curve.body = station_text
            font_curve.size = max(0.5, curve_length / 100)  # Scale based on curve length
            font_curve.align_x = "CENTER"
            font_curve.align_y = "BOTTOM"

            # Create object
            text_obj = bpy.data.objects.new(text_name, font_curve)
            collection.objects.link(text_obj)

            # Position ABOVE the channel (height + offset)
            offset_height = channel_height + 1.0  # Above the channel top
            text_obj.location = pos + normal * offset_height

            # Rotate to face up and align with curve direction
            tangent = sample["tangent"]

            # Make text face upward (90 degrees on X)
            text_obj.rotation_euler = (1.5708, 0, 0)

            # Align with tangent direction
            angle_z = math.atan2(tangent.y, tangent.x)
            text_obj.rotation_euler.z = angle_z + math.pi / 2

            marker_count += 1

        # Create inlet and outlet markers (with station format above)
        if len(samples) >= 2:
            self._create_endpoint_marker(collection, axis_obj, samples[0], "INLET", curve_length, channel_height)
            self._create_endpoint_marker(collection, axis_obj, samples[-1], "OUTLET", curve_length, channel_height)

        self.report({"INFO"}, f"Created {marker_count} station markers")
        return {"FINISHED"}

    def _create_endpoint_marker(self, collection, axis_obj, sample, label, curve_length, channel_height):
        """Create inlet/outlet endpoint marker with station text above."""
        import math

        pos = sample["position"]
        normal = sample["normal"]
        tangent = sample["tangent"]
        station = sample["station"]

        # Format station as 0+000.00 (km+meters)
        km = int(station / 1000)
        m = station % 1000
        station_text = f"{km}+{m:06.2f}"

        # Combined text: label + station
        combined_text = f"{label}\n{station_text}"

        text_name = f"Station_{axis_obj.name}_{label}"

        # Check if already exists and remove
        if text_name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[text_name], do_unlink=True)

        # Create font curve
        font_curve = bpy.data.curves.new(name=text_name, type="FONT")
        font_curve.body = combined_text
        font_curve.size = max(0.8, curve_length / 80)
        font_curve.align_x = "CENTER"
        font_curve.align_y = "BOTTOM"

        # Create object
        text_obj = bpy.data.objects.new(text_name, font_curve)
        collection.objects.link(text_obj)

        # Position ABOVE the channel (height + offset)
        offset_height = channel_height + 1.5  # Higher than regular stations

        text_obj.location = pos + normal * offset_height

        # Rotate to face up
        text_obj.rotation_euler = (1.5708, 0, 0)

        angle_z = math.atan2(tangent.y, tangent.x)
        text_obj.rotation_euler.z = angle_z + math.pi / 2


class CADHY_OT_ClearStationMarkers(Operator):
    """Clear all station markers"""

    bl_idname = "cadhy.clear_station_markers"
    bl_label = "Clear Station Markers"
    bl_description = "Remove all station markers from the scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Execute the operator."""
        collection_name = "CADHY_Station_Markers"
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]

            # Remove all objects in collection
            objects_to_remove = list(collection.objects)
            for obj in objects_to_remove:
                bpy.data.objects.remove(obj, do_unlink=True)

            # Remove collection
            bpy.data.collections.remove(collection)

            self.report({"INFO"}, "Cleared all station markers")
        else:
            self.report({"INFO"}, "No station markers to clear")

        return {"FINISHED"}
