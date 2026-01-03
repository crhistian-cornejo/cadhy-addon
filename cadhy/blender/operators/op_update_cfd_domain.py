"""
Update CFD Domain Operator
Operator to regenerate CFD domain mesh from stored parameters.
"""

import bpy
from bpy.types import Operator

from ...core.geom.build_cfd_domain import build_cfd_domain_mesh, update_cfd_domain_geometry
from ...core.geom.mesh_validate import get_cfd_domain_info
from ...core.model.cfd_params import CFDParams, FillMode
from ...core.model.channel_params import ChannelParams, SectionType
from ...core.util.logging import OperationLogger


class CADHY_OT_UpdateCFDDomain(Operator):
    """Update CFD domain mesh from its stored parameters"""

    bl_idname = "cadhy.update_cfd_domain"
    bl_label = "Update CFD Domain"
    bl_description = "Regenerate CFD domain mesh using current parameters"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        obj = context.active_object
        if not obj or obj.type != "MESH":
            return False
        cfd = getattr(obj, "cadhy_cfd", None)
        return cfd and cfd.is_cadhy_object and cfd.source_axis

    def execute(self, context):
        """Execute the operator."""
        obj = context.active_object
        cfd = obj.cadhy_cfd

        # Verify axis still exists
        if not cfd.source_axis:
            self.report({"ERROR"}, "Source axis curve not found")
            return {"CANCELLED"}

        if cfd.source_axis.type != "CURVE":
            self.report({"ERROR"}, "Source axis is not a curve")
            return {"CANCELLED"}

        with OperationLogger("Update CFD Domain", self) as logger:
            # Section type mapping
            section_type_map = {
                "TRAP": SectionType.TRAPEZOIDAL,
                "RECT": SectionType.RECTANGULAR,
                "CIRC": SectionType.CIRCULAR,
            }

            # Get channel parameters from linked channel or scene settings
            if cfd.source_channel and cfd.source_channel.type == "MESH":
                ch = cfd.source_channel.cadhy_channel
                channel_params = ChannelParams(
                    section_type=section_type_map.get(ch.section_type, SectionType.TRAPEZOIDAL),
                    bottom_width=ch.bottom_width,
                    side_slope=ch.side_slope,
                    height=ch.height,
                    freeboard=ch.freeboard,
                    lining_thickness=ch.lining_thickness,
                    resolution_m=ch.resolution_m,
                )
            else:
                # Fall back to scene settings
                settings = context.scene.cadhy
                channel_params = ChannelParams(
                    section_type=section_type_map.get(settings.section_type, SectionType.TRAPEZOIDAL),
                    bottom_width=settings.bottom_width,
                    side_slope=settings.side_slope,
                    height=settings.height,
                    freeboard=settings.freeboard,
                    lining_thickness=settings.lining_thickness,
                    resolution_m=settings.resolution_m,
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

            # Build new geometry
            vertices, faces, patch_faces = build_cfd_domain_mesh(cfd.source_axis, channel_params, cfd_params)

            if not vertices or not faces:
                self.report({"ERROR"}, "Failed to regenerate CFD domain geometry")
                return {"CANCELLED"}

            # Update mesh in place
            update_cfd_domain_geometry(obj, vertices, faces, patch_faces)

            # Re-validate
            cfd_info = get_cfd_domain_info(obj, patch_faces)
            cfd.is_watertight = cfd_info.is_watertight
            cfd.is_valid = cfd_info.is_valid
            cfd.non_manifold_edges = cfd_info.non_manifold_edges
            cfd.volume = cfd_info.volume

            logger.set_success(f"CFD Domain updated. Volume: {cfd_info.volume:.3f} m³")

        return {"FINISHED"}


def find_cfd_domains_for_channel(channel_obj):
    """Find all CFD domain objects linked to a channel."""
    domains = []
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            cfd = getattr(obj, "cadhy_cfd", None)
            if cfd and cfd.is_cadhy_object and cfd.source_channel == channel_obj:
                domains.append(obj)
    return domains


def update_linked_cfd_domains(channel_obj, context):
    """Update all CFD domains linked to a channel."""
    domains = find_cfd_domains_for_channel(channel_obj)
    for domain in domains:
        # Temporarily select the domain to run the update
        original_active = context.view_layer.objects.active
        context.view_layer.objects.active = domain
        bpy.ops.cadhy.update_cfd_domain()
        context.view_layer.objects.active = original_active
