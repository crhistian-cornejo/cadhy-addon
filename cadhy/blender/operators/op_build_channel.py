"""
Build Channel Operator
Operator to generate channel mesh from curve axis.
Includes progress indicator for long operations.
"""

from bpy.types import Operator

from ...core.geom.build_channel import build_channel_mesh, create_channel_object, get_curve_length
from ...core.model.channel_params import ChannelParams, SectionType
from ...core.util.logging import OperationLogger
from ...core.util.naming import COLLECTION_CHANNELS, get_channel_name
from ...core.util.versioning import CADHY_VERSION_STRING


class CADHY_OT_BuildChannel(Operator):
    """Build or update channel mesh from axis curve"""

    bl_idname = "cadhy.build_channel"
    bl_label = "Build Channel"
    bl_description = "Generate channel mesh from selected axis curve (Alt+Shift+B)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        settings = context.scene.cadhy
        # Need either selected curve or axis_object set
        if settings.axis_object and settings.axis_object.type == "CURVE":
            return True
        if context.active_object and context.active_object.type == "CURVE":
            return True
        return False

    def execute(self, context):
        """Execute the operator."""
        settings = context.scene.cadhy
        wm = context.window_manager

        # Get axis curve
        axis_obj = settings.axis_object
        if not axis_obj:
            axis_obj = context.active_object

        if not axis_obj or axis_obj.type != "CURVE":
            self.report({"ERROR"}, "No valid curve selected as axis")
            return {"CANCELLED"}

        # Start progress indicator
        wm.progress_begin(0, 100)

        with OperationLogger("Build Channel", self) as logger:
            try:
                # Create channel parameters from scene settings
                wm.progress_update(10)
                section_type_map = {
                    "TRAP": SectionType.TRAPEZOIDAL,
                    "RECT": SectionType.RECTANGULAR,
                    "CIRC": SectionType.CIRCULAR,
                    "TRI": SectionType.TRIANGULAR,
                    "PIPE": SectionType.PIPE,
                }

                params = ChannelParams(
                    section_type=section_type_map.get(settings.section_type, SectionType.TRAPEZOIDAL),
                    bottom_width=settings.bottom_width,
                    side_slope=settings.side_slope,
                    height=settings.height,
                    freeboard=settings.freeboard,
                    lining_thickness=settings.lining_thickness,
                    resolution_m=settings.resolution_m,
                    subdivide_profile=getattr(settings, "subdivide_profile", True),
                    profile_resolution=getattr(settings, "profile_resolution", settings.resolution_m),
                )

                # Build mesh geometry
                wm.progress_update(30)
                vertices, faces = build_channel_mesh(axis_obj, params)

                if not vertices or not faces:
                    wm.progress_end()
                    self.report({"ERROR"}, "Failed to generate channel geometry. Check curve has valid splines.")
                    return {"CANCELLED"}

                # Create or update channel object
                wm.progress_update(70)
                channel_name = get_channel_name(axis_obj.name)
                channel_obj = create_channel_object(channel_name, vertices, faces, COLLECTION_CHANNELS)

                # Store parameters on object for regeneration
                wm.progress_update(85)
                ch_settings = channel_obj.cadhy_channel
                ch_settings.source_axis = axis_obj
                ch_settings.section_type = settings.section_type
                ch_settings.bottom_width = settings.bottom_width
                ch_settings.side_slope = settings.side_slope
                ch_settings.height = settings.height
                ch_settings.freeboard = settings.freeboard
                ch_settings.lining_thickness = settings.lining_thickness
                ch_settings.resolution_m = settings.resolution_m
                ch_settings.subdivide_profile = getattr(settings, "subdivide_profile", True)
                ch_settings.profile_resolution = getattr(settings, "profile_resolution", settings.resolution_m)
                ch_settings.total_length = get_curve_length(axis_obj)
                ch_settings.cadhy_version = CADHY_VERSION_STRING
                ch_settings.is_cadhy_object = True

                # Select the created object (using direct API, not operators)
                wm.progress_update(95)
                for obj in context.selected_objects:
                    obj.select_set(False)
                channel_obj.select_set(True)
                context.view_layer.objects.active = channel_obj

                logger.set_success(
                    f"Channel '{channel_name}' created with {len(vertices)} vertices, {len(faces)} faces"
                )

            finally:
                wm.progress_end()

        return {"FINISHED"}
