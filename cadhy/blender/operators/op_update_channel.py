"""
Update Channel Operator
Operator to regenerate channel mesh from stored parameters.
"""

import bpy
from bpy.types import Operator

from ...core.geom.build_channel import build_channel_mesh, get_curve_length, update_mesh_geometry
from ...core.model.channel_params import ChannelParams, SectionType
from ...core.util.logging import OperationLogger


class CADHY_OT_UpdateChannel(Operator):
    """Update channel mesh from its stored parameters"""

    bl_idname = "cadhy.update_channel"
    bl_label = "Update Channel"
    bl_description = "Regenerate channel mesh using current parameters (Alt+Shift+U)"
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

        # CRITICAL: Ensure we're in object mode before modifying mesh
        # mesh.from_pydata() fails if object is in edit mode
        if obj.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        with OperationLogger("Update Channel", self) as logger:
            # Map section type string to enum
            section_type_map = {
                "TRAP": SectionType.TRAPEZOIDAL,
                "RECT": SectionType.RECTANGULAR,
                "CIRC": SectionType.CIRCULAR,
                "TRI": SectionType.TRIANGULAR,
                "PIPE": SectionType.PIPE,
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
                subdivide_profile=getattr(ch, "subdivide_profile", True),
                profile_resolution=getattr(ch, "profile_resolution", ch.resolution_m),
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

            # Update linked CFD domains
            self._update_linked_cfd_domains(obj, context)

        return {"FINISHED"}

    def _update_linked_cfd_domains(self, channel_obj, context):
        """Update all CFD domains linked to this channel."""
        from ...core.geom.build_cfd_domain import build_cfd_domain_mesh, update_cfd_domain_geometry
        from ...core.geom.mesh_validate import get_cfd_domain_info
        from ...core.model.cfd_params import CFDParams, FillMode
        from ...core.model.channel_params import ChannelParams, SectionType

        updated_count = 0
        ch = channel_obj.cadhy_channel

        # Section type mapping
        section_type_map = {
            "TRAP": SectionType.TRAPEZOIDAL,
            "RECT": SectionType.RECTANGULAR,
            "CIRC": SectionType.CIRCULAR,
            "TRI": SectionType.TRIANGULAR,
            "PIPE": SectionType.PIPE,
        }

        for obj in bpy.data.objects:
            if obj.type != "MESH":
                continue

            cfd = getattr(obj, "cadhy_cfd", None)
            if not cfd or not cfd.is_cadhy_object or cfd.source_channel != channel_obj:
                continue

            # Update CFD domain directly without operators (avoids ViewLayer issues)
            try:
                # Build channel params from linked channel
                channel_params = ChannelParams(
                    section_type=section_type_map.get(ch.section_type, SectionType.TRAPEZOIDAL),
                    bottom_width=ch.bottom_width,
                    side_slope=ch.side_slope,
                    height=ch.height,
                    freeboard=ch.freeboard,
                    lining_thickness=ch.lining_thickness,
                    resolution_m=ch.resolution_m,
                )

                # Get CFD parameters from stored settings
                fill_mode_map = {
                    "WATER_LEVEL": FillMode.WATER_LEVEL,
                    "FULL": FillMode.FULL,
                }

                cfd_params = CFDParams(
                    enabled=True,
                    inlet_extension_m=cfd.inlet_extension_m,
                    outlet_extension_m=cfd.outlet_extension_m,
                    water_level_m=cfd.water_level_m,
                    fill_mode=fill_mode_map.get(cfd.fill_mode, FillMode.WATER_LEVEL),
                    cap_inlet=cfd.cap_inlet,
                    cap_outlet=cfd.cap_outlet,
                )

                # Get mesh type (with backward compatibility)
                mesh_type = getattr(cfd, "mesh_type", "QUAD")

                # Build new geometry
                vertices, faces, patch_faces = build_cfd_domain_mesh(
                    cfd.source_axis, channel_params, cfd_params, mesh_type=mesh_type
                )

                if vertices and faces:
                    # Update mesh in place
                    update_cfd_domain_geometry(obj, vertices, faces, patch_faces)

                    # Re-validate
                    cfd_info = get_cfd_domain_info(obj, patch_faces)
                    cfd.is_watertight = cfd_info.is_watertight
                    cfd.is_valid = cfd_info.is_valid
                    cfd.non_manifold_edges = cfd_info.non_manifold_edges
                    cfd.volume = cfd_info.volume

                    updated_count += 1

            except Exception as e:
                # Log but don't fail the channel update
                print(f"[CADHY] Failed to update CFD domain '{obj.name}': {e}")

        if updated_count > 0:
            self.report({"INFO"}, f"Also updated {updated_count} linked CFD domain(s)")
