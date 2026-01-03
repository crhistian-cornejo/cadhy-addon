"""
Update Channel Operator
Operator to regenerate channel mesh from stored parameters.
"""

from bpy.types import Operator

from ...core.geom.build_channel import build_channel_mesh, get_curve_length, update_mesh_geometry
from ...core.model.channel_params import ChannelParams, SectionType
from ...core.util.logging import OperationLogger


class CADHY_OT_UpdateChannel(Operator):
    """Update channel mesh from its stored parameters"""

    bl_idname = "cadhy.update_channel"
    bl_label = "Update Channel"
    bl_description = "Regenerate channel mesh using current parameters"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        obj = context.active_object
        if not obj or obj.type != "MESH":
            return False

        # Check if object has CADHY channel settings
        ch = getattr(obj, "cadhy_channel", None)
        if not ch:
            return False

        # Must be a CADHY object with a valid source axis
        return ch.is_cadhy_object and ch.source_axis is not None

    def execute(self, context):
        """Execute the operator."""
        obj = context.active_object
        ch = obj.cadhy_channel

        # Verify source axis still exists and is valid
        if not ch.source_axis:
            self.report({"ERROR"}, "Source axis curve not found")
            return {"CANCELLED"}

        if ch.source_axis.type != "CURVE":
            self.report({"ERROR"}, "Source axis is not a curve")
            return {"CANCELLED"}

        with OperationLogger("Update Channel", self) as logger:
            # Map section type string to enum
            section_type_map = {
                "TRAP": SectionType.TRAPEZOIDAL,
                "RECT": SectionType.RECTANGULAR,
                "CIRC": SectionType.CIRCULAR,
            }

            # Build params from object properties
            params = ChannelParams(
                section_type=section_type_map.get(ch.section_type, SectionType.TRAPEZOIDAL),
                bottom_width=ch.bottom_width,
                side_slope=ch.side_slope,
                height=ch.height,
                freeboard=ch.freeboard,
                lining_thickness=ch.lining_thickness,
                resolution_m=ch.resolution_m,
            )

            # Regenerate mesh geometry
            vertices, faces = build_channel_mesh(ch.source_axis, params)

            if not vertices or not faces:
                self.report({"ERROR"}, "Failed to generate channel geometry")
                return {"CANCELLED"}

            # Update mesh in place
            update_mesh_geometry(obj, vertices, faces)

            # Update stored length
            ch.total_length = get_curve_length(ch.source_axis)

            logger.set_success(f"Channel updated: {len(vertices)} vertices, {len(faces)} faces")

        return {"FINISHED"}
