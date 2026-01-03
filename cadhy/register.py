"""
CADHY Registration Module
Handles registration and unregistration of all Blender classes.
"""

import bpy

from .blender.properties.scene_props import CADHYSceneSettings
from .blender.properties.object_props import CADHYChannelSettings, CADHYCFDSettings

from .blender.operators.op_build_channel import CADHY_OT_BuildChannel
from .blender.operators.op_build_cfd_domain import CADHY_OT_BuildCFDDomain
from .blender.operators.op_generate_sections import CADHY_OT_GenerateSections
from .blender.operators.op_export_cfd import CADHY_OT_ExportCFD
from .blender.operators.op_export_report import CADHY_OT_ExportReport
from .blender.operators.op_validate_mesh import CADHY_OT_ValidateMesh
from .blender.operators.op_setup_render import CADHY_OT_SetupRender
from .blender.operators.op_assign_materials import CADHY_OT_AssignMaterials
from .blender.operators.op_dev_reload import CADHY_OT_DevReload

from .blender.panels.pt_main import CADHY_PT_Main
from .blender.panels.pt_cfd import CADHY_PT_CFD
from .blender.panels.pt_sections import CADHY_PT_Sections
from .blender.panels.pt_export import CADHY_PT_Export
from .blender.panels.pt_render import CADHY_PT_Render
from .blender.panels.pt_updates import CADHY_PT_Updates, CADHY_OT_CheckUpdates, CADHY_OT_PrintSystemInfo
from .blender.panels.pt_export import CADHY_OT_ExportAll
from .blender.panels.pt_render import VIEW3D_OT_toggle_shading

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
    VIEW3D_OT_toggle_shading,
    # Panels
    CADHY_PT_Main,
    CADHY_PT_CFD,
    CADHY_PT_Sections,
    CADHY_PT_Export,
    CADHY_PT_Render,
    CADHY_PT_Updates,
)


def register():
    """Register all classes and attach properties."""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Attach property groups to Scene and Object
    bpy.types.Scene.cadhy = bpy.props.PointerProperty(type=CADHYSceneSettings)
    bpy.types.Object.cadhy_channel = bpy.props.PointerProperty(type=CADHYChannelSettings)
    bpy.types.Object.cadhy_cfd = bpy.props.PointerProperty(type=CADHYCFDSettings)


def unregister():
    """Unregister all classes and remove properties."""
    # Remove properties first
    del bpy.types.Object.cadhy_cfd
    del bpy.types.Object.cadhy_channel
    del bpy.types.Scene.cadhy
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
