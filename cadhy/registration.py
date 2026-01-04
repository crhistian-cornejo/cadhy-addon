"""
CADHY Registration Module
Handles registration and unregistration of all Blender classes.
Includes keyboard shortcuts registration similar to major addons.
"""

import bpy

from .blender.menus.pie_main import CADHY_MT_PieMenu, CADHY_OT_CallPieMenu
from .blender.operators.op_assign_materials import CADHY_OT_AssignMaterials
from .blender.operators.op_build_cfd_domain import CADHY_OT_BuildCFDDomain
from .blender.operators.op_build_channel import CADHY_OT_BuildChannel
from .blender.operators.op_dev_reload import CADHY_OT_DevReload
from .blender.operators.op_export_cfd import CADHY_OT_ExportCFD
from .blender.operators.op_export_cfd_template import CADHY_OT_ExportCFDTemplate
from .blender.operators.op_export_report import CADHY_OT_ExportReport
from .blender.operators.op_generate_sections import CADHY_OT_GenerateSections
from .blender.operators.op_help import CADHY_OT_OpenDocs, CADHY_OT_ShowHelp, CADHY_OT_ShowKeymap
from .blender.operators.op_presets import CADHY_OT_DeletePreset, CADHY_OT_LoadPreset, CADHY_OT_SavePreset
from .blender.operators.op_setup_render import CADHY_OT_SetupRender
from .blender.operators.op_setup_workspace import CADHY_OT_ResetWorkspace, CADHY_OT_SetupWorkspace
from .blender.operators.op_station_markers import CADHY_OT_ClearStationMarkers, CADHY_OT_CreateStationMarkers
from .blender.operators.op_update_cfd_domain import CADHY_OT_UpdateCFDDomain
from .blender.operators.op_update_channel import CADHY_OT_UpdateChannel
from .blender.operators.op_validate_mesh import CADHY_OT_ValidateMesh
from .blender.panels.pt_cfd import CADHY_PT_CFD
from .blender.panels.pt_channel_info import CADHY_OT_RefreshChannelInfo, CADHY_PT_ChannelInfo
from .blender.panels.pt_export import CADHY_OT_ExportAll, CADHY_PT_Export
from .blender.panels.pt_main import CADHY_PT_Main
from .blender.panels.pt_render import CADHY_OT_ToggleShading, CADHY_PT_Render
from .blender.panels.pt_sections import CADHY_PT_Sections
from .blender.panels.pt_updates import (
    CADHY_OT_CheckUpdates,
    CADHY_OT_DownloadUpdate,
    CADHY_OT_InstallUpdate,
    CADHY_OT_PrintSystemInfo,
    CADHY_PT_Updates,
)
from .blender.preferences import CADHY_OT_OpenLogFile, CADHYPreferences
from .blender.properties.object_props import CADHYCFDSettings, CADHYChannelSettings
from .blender.properties.scene_props import CADHYSceneSettings

# Keyboard shortcuts storage
addon_keymaps = []

# Order matters for registration
# Preferences must be registered first (before other classes reference it)
# PropertyGroups before Operators before Panels
classes = (
    # Addon Preferences (must be first for bl_idname to work)
    CADHYPreferences,
    # Properties
    CADHYSceneSettings,
    CADHYChannelSettings,
    CADHYCFDSettings,
    # Operators
    CADHY_OT_BuildChannel,
    CADHY_OT_UpdateChannel,
    CADHY_OT_BuildCFDDomain,
    CADHY_OT_UpdateCFDDomain,
    CADHY_OT_GenerateSections,
    CADHY_OT_ExportCFD,
    CADHY_OT_ExportCFDTemplate,
    CADHY_OT_ExportReport,
    CADHY_OT_ValidateMesh,
    CADHY_OT_SetupRender,
    CADHY_OT_SetupWorkspace,
    CADHY_OT_ResetWorkspace,
    CADHY_OT_AssignMaterials,
    CADHY_OT_CreateStationMarkers,
    CADHY_OT_ClearStationMarkers,
    CADHY_OT_DevReload,
    CADHY_OT_ExportAll,
    CADHY_OT_CheckUpdates,
    CADHY_OT_DownloadUpdate,
    CADHY_OT_InstallUpdate,
    CADHY_OT_PrintSystemInfo,
    CADHY_OT_ToggleShading,
    CADHY_OT_OpenLogFile,
    CADHY_OT_RefreshChannelInfo,
    CADHY_OT_OpenDocs,
    CADHY_OT_ShowHelp,
    CADHY_OT_ShowKeymap,
    CADHY_OT_SavePreset,
    CADHY_OT_LoadPreset,
    CADHY_OT_DeletePreset,
    # Menus
    CADHY_MT_PieMenu,
    CADHY_OT_CallPieMenu,
    # Panels
    CADHY_PT_Main,
    CADHY_PT_ChannelInfo,
    CADHY_PT_CFD,
    CADHY_PT_Sections,
    CADHY_PT_Export,
    CADHY_PT_Render,
    CADHY_PT_Updates,
)


def register_keymaps():
    """Register keyboard shortcuts for CADHY operators."""
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc is None:
        return

    # 3D View keymap
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")

    # Alt+Shift+B: Build Channel (avoids Ctrl+Shift+B which is Set 3D Cursor)
    kmi = km.keymap_items.new(
        "cadhy.build_channel",
        type="B",
        value="PRESS",
        alt=True,
        shift=True,
    )
    addon_keymaps.append((km, kmi))

    # Alt+Shift+U: Update Channel
    kmi = km.keymap_items.new(
        "cadhy.update_channel",
        type="U",
        value="PRESS",
        alt=True,
        shift=True,
    )
    addon_keymaps.append((km, kmi))

    # Alt+Shift+D: Build CFD Domain (avoids Ctrl+Shift+D which is Make Links)
    kmi = km.keymap_items.new(
        "cadhy.build_cfd_domain",
        type="D",
        value="PRESS",
        alt=True,
        shift=True,
    )
    addon_keymaps.append((km, kmi))

    # Alt+Shift+S: Generate Sections (simpler than Ctrl+Shift+Alt+S)
    kmi = km.keymap_items.new(
        "cadhy.generate_sections",
        type="S",
        value="PRESS",
        alt=True,
        shift=True,
    )
    addon_keymaps.append((km, kmi))

    # Alt+C: CADHY Pie Menu (simple and memorable)
    kmi = km.keymap_items.new(
        "cadhy.call_pie_menu",
        type="C",
        value="PRESS",
        alt=True,
    )
    addon_keymaps.append((km, kmi))


def unregister_keymaps():
    """Unregister keyboard shortcuts."""
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def is_registered(cls):
    """Check if a class is already registered."""
    try:
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
            if "already registered" in str(e):
                pass
            else:
                raise e

    # Attach property groups to Scene and Object
    if not hasattr(bpy.types.Scene, "cadhy"):
        bpy.types.Scene.cadhy = bpy.props.PointerProperty(type=CADHYSceneSettings)
    if not hasattr(bpy.types.Object, "cadhy_channel"):
        bpy.types.Object.cadhy_channel = bpy.props.PointerProperty(type=CADHYChannelSettings)
    if not hasattr(bpy.types.Object, "cadhy_cfd"):
        bpy.types.Object.cadhy_cfd = bpy.props.PointerProperty(type=CADHYCFDSettings)

    # Register keyboard shortcuts
    register_keymaps()

    # Register internationalization
    try:
        from .i18n import register as register_i18n

        register_i18n()
    except Exception:
        pass

    # Reconfigure logging from preferences (after preferences are registered)
    try:
        from .core.util.logging import reconfigure_from_preferences

        reconfigure_from_preferences()
    except Exception:
        pass


def unregister():
    """Unregister all classes and remove properties."""
    # Unregister keyboard shortcuts first
    unregister_keymaps()

    # Unregister internationalization
    try:
        from .i18n import unregister as unregister_i18n

        unregister_i18n()
    except Exception:
        pass

    # Remove properties (with safety checks)
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
            pass
