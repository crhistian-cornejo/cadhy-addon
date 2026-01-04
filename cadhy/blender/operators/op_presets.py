"""
Presets System
Save and load channel configuration presets.
"""

import json
from pathlib import Path
from typing import List

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

# Presets directory in user config
PRESETS_DIR = Path(bpy.utils.user_resource("CONFIG")) / "cadhy" / "presets"


def get_presets_dir() -> Path:
    """Get or create presets directory."""
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    return PRESETS_DIR


def list_presets() -> List[str]:
    """List available preset names."""
    presets_dir = get_presets_dir()
    presets = []
    for f in presets_dir.glob("*.json"):
        presets.append(f.stem)
    return sorted(presets)


def get_preset_items(self, context):
    """Get preset items for EnumProperty."""
    items = [("", "Select Preset...", "Choose a preset to load")]
    for name in list_presets():
        items.append((name, name, f"Load preset: {name}"))
    return items


# Built-in presets
BUILTIN_PRESETS = {
    "Irrigation Small": {
        "section_type": "TRAP",
        "bottom_width": 0.5,
        "side_slope": 1.0,
        "height": 0.5,
        "freeboard": 0.15,
        "lining_thickness": 0.10,
        "resolution_m": 0.5,
        "description": "Small irrigation canal (0.5m base, 0.5m depth)",
    },
    "Irrigation Medium": {
        "section_type": "TRAP",
        "bottom_width": 1.5,
        "side_slope": 1.5,
        "height": 1.2,
        "freeboard": 0.25,
        "lining_thickness": 0.15,
        "resolution_m": 1.0,
        "description": "Medium irrigation canal (1.5m base, 1.2m depth)",
    },
    "Drainage Urban": {
        "section_type": "RECT",
        "bottom_width": 2.0,
        "side_slope": 0.0,
        "height": 1.5,
        "freeboard": 0.30,
        "lining_thickness": 0.20,
        "resolution_m": 1.0,
        "description": "Urban drainage channel (2m wide, 1.5m deep)",
    },
    "Drainage Large": {
        "section_type": "TRAP",
        "bottom_width": 5.0,
        "side_slope": 2.0,
        "height": 3.0,
        "freeboard": 0.50,
        "lining_thickness": 0.25,
        "resolution_m": 2.0,
        "description": "Large drainage channel (5m base, 3m depth)",
    },
    "Culvert Round 600": {
        "section_type": "CIRC",
        "bottom_width": 0.6,
        "side_slope": 0.0,
        "height": 0.6,
        "freeboard": 0.0,
        "lining_thickness": 0.0,
        "resolution_m": 0.5,
        "description": "Round culvert 600mm diameter",
    },
    "Culvert Round 1200": {
        "section_type": "CIRC",
        "bottom_width": 1.2,
        "side_slope": 0.0,
        "height": 1.2,
        "freeboard": 0.0,
        "lining_thickness": 0.0,
        "resolution_m": 0.5,
        "description": "Round culvert 1200mm diameter",
    },
    "Earth Channel": {
        "section_type": "TRAP",
        "bottom_width": 2.0,
        "side_slope": 2.5,
        "height": 1.0,
        "freeboard": 0.30,
        "lining_thickness": 0.0,
        "resolution_m": 1.0,
        "description": "Unlined earth channel (gentle slopes)",
    },
}


class CADHY_OT_SavePreset(Operator):
    """Save current channel settings as a preset"""

    bl_idname = "cadhy.save_preset"
    bl_label = "Save Preset"
    bl_description = "Save current channel settings as a reusable preset"
    bl_options = {"REGISTER"}

    preset_name: StringProperty(
        name="Preset Name",
        description="Name for the new preset",
        default="My Channel Preset",
    )

    def execute(self, context):
        settings = context.scene.cadhy

        preset_data = {
            "section_type": settings.section_type,
            "bottom_width": settings.bottom_width,
            "side_slope": settings.side_slope,
            "height": settings.height,
            "freeboard": settings.freeboard,
            "lining_thickness": settings.lining_thickness,
            "resolution_m": settings.resolution_m,
            "subdivide_profile": getattr(settings, "subdivide_profile", True),
            "profile_resolution": getattr(settings, "profile_resolution", 1.0),
            "description": f"Custom preset: {self.preset_name}",
        }

        # Save to file
        presets_dir = get_presets_dir()
        preset_file = presets_dir / f"{self.preset_name}.json"

        with open(preset_file, "w") as f:
            json.dump(preset_data, f, indent=2)

        self.report({"INFO"}, f"Preset saved: {self.preset_name}")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class CADHY_OT_LoadPreset(Operator):
    """Load a channel preset"""

    bl_idname = "cadhy.load_preset"
    bl_label = "Load Preset"
    bl_description = "Load channel settings from a preset"
    bl_options = {"REGISTER", "UNDO"}

    preset_name: StringProperty(
        name="Preset Name",
        description="Name of the preset to load",
        default="",
    )

    def execute(self, context):
        if not self.preset_name:
            self.report({"WARNING"}, "No preset selected")
            return {"CANCELLED"}

        # Try built-in presets first
        if self.preset_name in BUILTIN_PRESETS:
            preset_data = BUILTIN_PRESETS[self.preset_name]
        else:
            # Load from file
            presets_dir = get_presets_dir()
            preset_file = presets_dir / f"{self.preset_name}.json"

            if not preset_file.exists():
                self.report({"ERROR"}, f"Preset not found: {self.preset_name}")
                return {"CANCELLED"}

            with open(preset_file, "r") as f:
                preset_data = json.load(f)

        # Apply preset to scene settings
        settings = context.scene.cadhy

        if "section_type" in preset_data:
            settings.section_type = preset_data["section_type"]
        if "bottom_width" in preset_data:
            settings.bottom_width = preset_data["bottom_width"]
        if "side_slope" in preset_data:
            settings.side_slope = preset_data["side_slope"]
        if "height" in preset_data:
            settings.height = preset_data["height"]
        if "freeboard" in preset_data:
            settings.freeboard = preset_data["freeboard"]
        if "lining_thickness" in preset_data:
            settings.lining_thickness = preset_data["lining_thickness"]
        if "resolution_m" in preset_data:
            settings.resolution_m = preset_data["resolution_m"]
        if "subdivide_profile" in preset_data:
            settings.subdivide_profile = preset_data["subdivide_profile"]
        if "profile_resolution" in preset_data:
            settings.profile_resolution = preset_data["profile_resolution"]

        desc = preset_data.get("description", self.preset_name)
        self.report({"INFO"}, f"Loaded preset: {desc}")
        return {"FINISHED"}


class CADHY_OT_DeletePreset(Operator):
    """Delete a custom preset"""

    bl_idname = "cadhy.delete_preset"
    bl_label = "Delete Preset"
    bl_description = "Delete a custom preset (built-in presets cannot be deleted)"
    bl_options = {"REGISTER"}

    preset_name: StringProperty(
        name="Preset Name",
        description="Name of the preset to delete",
        default="",
    )

    def execute(self, context):
        if not self.preset_name:
            self.report({"WARNING"}, "No preset selected")
            return {"CANCELLED"}

        if self.preset_name in BUILTIN_PRESETS:
            self.report({"WARNING"}, "Cannot delete built-in presets")
            return {"CANCELLED"}

        presets_dir = get_presets_dir()
        preset_file = presets_dir / f"{self.preset_name}.json"

        if preset_file.exists():
            preset_file.unlink()
            self.report({"INFO"}, f"Deleted preset: {self.preset_name}")
        else:
            self.report({"WARNING"}, f"Preset not found: {self.preset_name}")

        return {"FINISHED"}


def draw_presets_menu(layout, context):
    """Draw presets dropdown in a layout."""
    box = layout.box()
    row = box.row(align=True)
    row.label(text="Presets", icon="PRESET")

    # Builtin presets submenu
    col = box.column(align=True)
    col.label(text="Built-in:")
    for name in sorted(BUILTIN_PRESETS.keys()):
        op = col.operator("cadhy.load_preset", text=name, icon="IMPORT")
        op.preset_name = name

    # Custom presets
    custom = list_presets()
    if custom:
        col.separator()
        col.label(text="Custom:")
        for name in custom:
            row = col.row(align=True)
            op = row.operator("cadhy.load_preset", text=name, icon="IMPORT")
            op.preset_name = name
            op = row.operator("cadhy.delete_preset", text="", icon="X")
            op.preset_name = name

    box.separator()
    box.operator("cadhy.save_preset", text="Save Current as Preset", icon="ADD")


# Registration
classes = (
    CADHY_OT_SavePreset,
    CADHY_OT_LoadPreset,
    CADHY_OT_DeletePreset,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
