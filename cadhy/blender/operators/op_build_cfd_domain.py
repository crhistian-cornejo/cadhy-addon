"""
Build CFD Domain Operator
Operator to generate CFD fluid domain mesh.
"""

import bpy
from bpy.types import Operator

from ...core.geom.build_cfd_domain import build_cfd_domain_mesh, create_cfd_domain_object
from ...core.geom.mesh_validate import get_cfd_domain_info
from ...core.model.cfd_params import CFDParams, FillMode
from ...core.model.channel_params import ChannelParams, SectionType
from ...core.util.logging import OperationLogger
from ...core.util.naming import COLLECTION_CFD, get_cfd_domain_name
from ...core.util.versioning import CADHY_VERSION_STRING


class CADHY_OT_BuildCFDDomain(Operator):
    """Build or update CFD domain mesh from axis curve"""

    bl_idname = "cadhy.build_cfd_domain"
    bl_label = "Build CFD Domain"
    bl_description = "Generate watertight CFD fluid domain mesh"
    bl_options = {"REGISTER", "UNDO"}

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

        with OperationLogger("Build CFD Domain", self) as logger:
            # Create channel parameters
            section_type_map = {
                "TRAP": SectionType.TRAPEZOIDAL,
                "RECT": SectionType.RECTANGULAR,
                "CIRC": SectionType.CIRCULAR,
            }

            channel_params = ChannelParams(
                section_type=section_type_map.get(settings.section_type, SectionType.TRAPEZOIDAL),
                bottom_width=settings.bottom_width,
                side_slope=settings.side_slope,
                height=settings.height,
                freeboard=settings.freeboard,
                lining_thickness=settings.lining_thickness,
                resolution_m=settings.resolution_m,
            )

            # Create CFD parameters
            fill_mode_map = {
                "WATER_LEVEL": FillMode.WATER_LEVEL,
                "FULL": FillMode.FULL,
            }

            cfd_params = CFDParams(
                enabled=True,
                inlet_extension_m=settings.cfd_inlet_extension,
                outlet_extension_m=settings.cfd_outlet_extension,
                water_level_m=settings.cfd_water_level,
                fill_mode=fill_mode_map.get(settings.cfd_fill_mode, FillMode.WATER_LEVEL),
                cap_inlet=True,
                cap_outlet=True,
            )

            # Build CFD domain mesh
            vertices, faces, patch_faces = build_cfd_domain_mesh(axis_obj, channel_params, cfd_params)

            if not vertices or not faces:
                self.report({"ERROR"}, "Failed to generate CFD domain geometry")
                return {"CANCELLED"}

            # Create CFD domain object
            domain_name = get_cfd_domain_name(axis_obj.name)
            domain_obj = create_cfd_domain_object(domain_name, vertices, faces, patch_faces, COLLECTION_CFD)

            # Validate mesh
            cfd_info = get_cfd_domain_info(domain_obj, patch_faces)

            # Store settings on object
            cfd_settings = domain_obj.cadhy_cfd
            cfd_settings.source_axis = axis_obj
            cfd_settings.enabled = True
            cfd_settings.inlet_extension_m = cfd_params.inlet_extension_m
            cfd_settings.outlet_extension_m = cfd_params.outlet_extension_m
            cfd_settings.water_level_m = cfd_params.water_level_m
            cfd_settings.fill_mode = settings.cfd_fill_mode
            cfd_settings.cap_inlet = cfd_params.cap_inlet
            cfd_settings.cap_outlet = cfd_params.cap_outlet
            cfd_settings.is_watertight = cfd_info.is_watertight
            cfd_settings.is_valid = cfd_info.is_valid
            cfd_settings.non_manifold_edges = cfd_info.non_manifold_edges
            cfd_settings.volume = cfd_info.volume
            cfd_settings.cadhy_version = CADHY_VERSION_STRING
            cfd_settings.is_cadhy_object = True

            # Select the created object
            bpy.ops.object.select_all(action="DESELECT")
            domain_obj.select_set(True)
            context.view_layer.objects.active = domain_obj

            # Report validation status
            if cfd_info.is_valid:
                logger.set_success(
                    f"CFD Domain '{domain_name}' created. Volume: {cfd_info.volume:.3f} m³. Mesh is valid for CFD."
                )
            else:
                warnings = []
                if not cfd_info.is_watertight:
                    warnings.append("not watertight")
                if cfd_info.non_manifold_edges > 0:
                    warnings.append(f"{cfd_info.non_manifold_edges} non-manifold edges")

                self.report({"WARNING"}, f"CFD Domain created but has issues: {', '.join(warnings)}")
                logger.set_success(f"CFD Domain '{domain_name}' created with warnings")

        return {"FINISHED"}
