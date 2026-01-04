"""
UI Helper Operators
Simple operators to support the improved UI workflow.
"""

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator


class CADHY_OT_SetSectionType(Operator):
    """Set the channel section type"""

    bl_idname = "cadhy.set_section_type"
    bl_label = "Set Section Type"
    bl_description = "Set the channel section type"
    bl_options = {"REGISTER", "UNDO"}

    section_type: EnumProperty(
        name="Section Type",
        items=[
            ("TRAP", "Trapezoidal", ""),
            ("RECT", "Rectangular", ""),
            ("TRI", "Triangular", ""),
            ("CIRC", "Circular", ""),
            ("PIPE", "Pipe", ""),
        ],
        default="TRAP",
    )

    def execute(self, context):
        settings = context.scene.cadhy
        settings.section_type = self.section_type

        # Set to custom size when changing type manually
        if hasattr(settings, "quick_size"):
            settings.quick_size = "CUSTOM"

        return {"FINISHED"}


class CADHY_OT_ToggleUIMode(Operator):
    """Toggle between Simple and Advanced UI modes"""

    bl_idname = "cadhy.toggle_ui_mode"
    bl_label = "Toggle UI Mode"
    bl_description = "Switch between Simple and Advanced interface modes"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = context.scene.cadhy
        if hasattr(settings, "ui_mode"):
            settings.ui_mode = "ADVANCED" if settings.ui_mode == "SIMPLE" else "SIMPLE"
            mode_name = "Advanced" if settings.ui_mode == "ADVANCED" else "Simple"
            self.report({"INFO"}, f"Switched to {mode_name} mode")
        return {"FINISHED"}


class CADHY_OT_ApplyQuickPreset(Operator):
    """Apply a quick design preset"""

    bl_idname = "cadhy.apply_quick_preset"
    bl_label = "Apply Quick Preset"
    bl_description = "Apply a predefined channel configuration"
    bl_options = {"REGISTER", "UNDO"}

    preset_name: StringProperty(
        name="Preset",
        description="Name of the preset to apply",
        default="",
    )

    def execute(self, context):
        settings = context.scene.cadhy

        # Quick presets for common use cases
        presets = {
            "irrigation_small": {
                "section_type": "TRAP",
                "bottom_width": 0.5,
                "height": 0.5,
                "side_slope": 1.0,
                "freeboard": 0.15,
                "lining_thickness": 0.10,
            },
            "drainage_medium": {
                "section_type": "RECT",
                "bottom_width": 1.5,
                "height": 1.2,
                "side_slope": 0.0,
                "freeboard": 0.25,
                "lining_thickness": 0.20,
            },
            "collector_pipe": {
                "section_type": "PIPE",
                "pipe_diameter": "630",
                "pipe_material": "HDPE",
                "pipe_sdr": "11",
            },
        }

        if self.preset_name in presets:
            preset = presets[self.preset_name]
            for key, value in preset.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            self.report({"INFO"}, f"Applied preset: {self.preset_name}")
            return {"FINISHED"}

        self.report({"WARNING"}, f"Unknown preset: {self.preset_name}")
        return {"CANCELLED"}


# Registration
classes = (
    CADHY_OT_SetSectionType,
    CADHY_OT_ToggleUIMode,
    CADHY_OT_ApplyQuickPreset,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
