"""
CADHY Registration Module
Handles registration and unregistration of all Blender classes.
"""

import bpy

from .blender.operators.op_assign_materials import CADHY_OT_AssignMaterials
from .blender.operators.op_build_cfd_domain import CADHY_OT_BuildCFDDomain
from .blender.operators.op_build_channel import CADHY_OT_BuildChannel
from .blender.operators.op_dev_reload import CADHY_OT_DevReload
from .blender.operators.op_export_cfd import CADHY_OT_ExportCFD
from .blender.operators.op_export_report import CADHY_OT_ExportReport
from .blender.operators.op_generate_sections import CADHY_OT_GenerateSections
from .blender.operators.op_setup_render import CADHY_OT_SetupRender
from .blender.operators.op_validate_mesh import CADHY_OT_ValidateMesh
from .blender.panels.pt_cfd import CADHY_PT_CFD
from .blender.panels.pt_export import CADHY_OT_ExportAll, CADHY_PT_Export
from .blender.panels.pt_main import CADHY_PT_Main
from .blender.panels.pt_render import CADHY_OT_ToggleShading, CADHY_PT_Render
from .blender.panels.pt_sections import CADHY_PT_Sections
from .blender.panels.pt_updates import CADHY_OT_CheckUpdates, CADHY_OT_PrintSystemInfo, CADHY_PT_Updates
from .blender.properties.object_props import CADHYCFDSettings, CADHYChannelSettings
from .blender.properties.scene_props import CADHYSceneSettings

# Order matters for registration
classes = (
    # Properties (must be first)
    CADHYSceneSettings,
    CADHYChannelSettings,
    CADHYCFDSettings,
    # Operators
    CADHY_OT_BuildChannel,
    CADHY_OT_BuildCFDDomain,
    CADHY_OT_GenerateSections,
    CADHY_OT_ExportCFD,
    CADHY_OT_ExportReport,
    CADHY_OT_ValidateMesh,
    CADHY_OT_SetupRender,
    CADHY_OT_AssignMaterials,
    CADHY_OT_DevReload,
    CADHY_OT_ExportAll,
    CADHY_OT_CheckUpdates,
    CADHY_OT_PrintSystemInfo,
    CADHY_OT_ToggleShading,
    # Panels
    CADHY_PT_Main,
    CADHY_PT_CFD,
    CADHY_PT_Sections,
    CADHY_PT_Export,
    CADHY_PT_Render,
    CADHY_PT_Updates,
)


def is_registered(cls):
    """Check if a class is already registered."""
    try:
        # For PropertyGroups, check if bl_rna exists
        if hasattr(cls, "bl_rna"):
            return True
        return False
    except Exception:
        return False


def register():
    """Register all classes and attach properties."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            # Class already registered, skip
            if "already registered" in str(e):
                pass
            else:
                raise e

    # Attach property groups to Scene and Object (only if not already attached)
    if not hasattr(bpy.types.Scene, "cadhy"):
        bpy.types.Scene.cadhy = bpy.props.PointerProperty(type=CADHYSceneSettings)
    if not hasattr(bpy.types.Object, "cadhy_channel"):
        bpy.types.Object.cadhy_channel = bpy.props.PointerProperty(type=CADHYChannelSettings)
    if not hasattr(bpy.types.Object, "cadhy_cfd"):
        bpy.types.Object.cadhy_cfd = bpy.props.PointerProperty(type=CADHYCFDSettings)


def unregister():
    """Unregister all classes and remove properties."""
    # Remove properties first (with safety checks)
    if hasattr(bpy.types.Object, "cadhy_cfd"):
        del bpy.types.Object.cadhy_cfd
    if hasattr(bpy.types.Object, "cadhy_channel"):
        del bpy.types.Object.cadhy_channel
    if hasattr(bpy.types.Scene, "cadhy"):
        del bpy.types.Scene.cadhy

    # Unregister classes in reverse order
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            # Class not registered, skip
            pass
