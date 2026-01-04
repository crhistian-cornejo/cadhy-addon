"""
Presets System
Save and load channel configuration presets.
Now includes geometry generation (BezierCurves) for complete project templates.
"""

import json
from pathlib import Path
from typing import List

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from mathutils import Vector

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


# =============================================================================
# CURVE GENERATORS - Create BezierCurves for different scenarios
# =============================================================================


def create_straight_curve(name: str, length: float = 30.0, slope: float = 0.02) -> bpy.types.Object:
    """Create a straight Bezier curve with slope."""
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 12

    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(1)  # 2 points total

    # Start point
    spline.bezier_points[0].co = Vector((0, 0, length * slope))
    spline.bezier_points[0].handle_left = Vector((-2, 0, length * slope + 0.04))
    spline.bezier_points[0].handle_right = Vector((2, 0, length * slope - 0.04))

    # End point
    spline.bezier_points[1].co = Vector((0, length, 0))
    spline.bezier_points[1].handle_left = Vector((0, length - 2, 0.04))
    spline.bezier_points[1].handle_right = Vector((0, length + 2, -0.04))

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    return obj


def create_curved_channel(name: str, length: float = 30.0, slope: float = 0.015) -> bpy.types.Object:
    """Create an S-curve Bezier for meandering channel."""
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 24

    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(3)  # 4 points total

    total_drop = length * slope

    # Point 0 - Start
    spline.bezier_points[0].co = Vector((0, 0, total_drop))
    spline.bezier_points[0].handle_left = Vector((-2, -2, total_drop))
    spline.bezier_points[0].handle_right = Vector((2, 4, total_drop * 0.9))
    spline.bezier_points[0].handle_left_type = "FREE"
    spline.bezier_points[0].handle_right_type = "FREE"

    # Point 1 - First curve
    spline.bezier_points[1].co = Vector((5, length * 0.33, total_drop * 0.7))
    spline.bezier_points[1].handle_left = Vector((4, length * 0.25, total_drop * 0.75))
    spline.bezier_points[1].handle_right = Vector((6, length * 0.42, total_drop * 0.65))
    spline.bezier_points[1].handle_left_type = "FREE"
    spline.bezier_points[1].handle_right_type = "FREE"

    # Point 2 - Second curve (opposite direction)
    spline.bezier_points[2].co = Vector((-4, length * 0.66, total_drop * 0.35))
    spline.bezier_points[2].handle_left = Vector((-2, length * 0.55, total_drop * 0.45))
    spline.bezier_points[2].handle_right = Vector((-5, length * 0.75, total_drop * 0.25))
    spline.bezier_points[2].handle_left_type = "FREE"
    spline.bezier_points[2].handle_right_type = "FREE"

    # Point 3 - End
    spline.bezier_points[3].co = Vector((0, length, 0))
    spline.bezier_points[3].handle_left = Vector((-2, length - 4, 0.1))
    spline.bezier_points[3].handle_right = Vector((2, length + 2, -0.05))
    spline.bezier_points[3].handle_left_type = "FREE"
    spline.bezier_points[3].handle_right_type = "FREE"

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    return obj


def create_channel_with_drop(name: str, length: float = 30.0, drop_height: float = 1.5) -> bpy.types.Object:
    """Create channel with a vertical drop structure in the middle."""
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 12

    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(3)  # 4 points

    half = length / 2
    slope = 0.01

    # Start - upstream
    z_start = drop_height + half * slope
    spline.bezier_points[0].co = Vector((0, 0, z_start))
    spline.bezier_points[0].handle_right = Vector((0, 3, z_start - 0.03))
    spline.bezier_points[0].handle_left = Vector((0, -2, z_start))

    # Before drop
    z_before = drop_height + 0.05
    spline.bezier_points[1].co = Vector((0, half - 0.5, z_before))
    spline.bezier_points[1].handle_left = Vector((0, half - 4, z_before + 0.02))
    spline.bezier_points[1].handle_right = Vector((0, half - 0.2, z_before))
    spline.bezier_points[1].handle_left_type = "FREE"
    spline.bezier_points[1].handle_right_type = "FREE"

    # After drop
    z_after = 0.05 + (length - half) * slope
    spline.bezier_points[2].co = Vector((0, half + 0.5, z_after))
    spline.bezier_points[2].handle_left = Vector((0, half + 0.2, z_after))
    spline.bezier_points[2].handle_right = Vector((0, half + 4, z_after - 0.02))
    spline.bezier_points[2].handle_left_type = "FREE"
    spline.bezier_points[2].handle_right_type = "FREE"

    # End - downstream
    spline.bezier_points[3].co = Vector((0, length, 0))
    spline.bezier_points[3].handle_left = Vector((0, length - 3, 0.03))
    spline.bezier_points[3].handle_right = Vector((0, length + 2, 0))

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    return obj


def create_steep_channel(name: str, length: float = 25.0) -> bpy.types.Object:
    """Create a steep mountain channel with high slope."""
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 16

    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(2)  # 3 points

    slope = 0.08  # 8% slope
    total_drop = length * slope

    # Start - high point
    spline.bezier_points[0].co = Vector((0, 0, total_drop))
    spline.bezier_points[0].handle_right = Vector((1, 4, total_drop * 0.85))
    spline.bezier_points[0].handle_left = Vector((-1, -2, total_drop))

    # Middle - slight curve
    spline.bezier_points[1].co = Vector((3, length * 0.5, total_drop * 0.5))
    spline.bezier_points[1].handle_left = Vector((2, length * 0.35, total_drop * 0.6))
    spline.bezier_points[1].handle_right = Vector((3.5, length * 0.65, total_drop * 0.4))
    spline.bezier_points[1].handle_left_type = "FREE"
    spline.bezier_points[1].handle_right_type = "FREE"

    # End
    spline.bezier_points[2].co = Vector((0, length, 0))
    spline.bezier_points[2].handle_left = Vector((1, length - 4, total_drop * 0.15))
    spline.bezier_points[2].handle_right = Vector((0, length + 2, 0))

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    return obj


def create_urban_drainage(name: str, length: float = 35.0) -> bpy.types.Object:
    """Create urban drainage with gentle curves."""
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 20

    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(4)  # 5 points - more complex path

    slope = 0.005  # 0.5% gentle slope
    total_drop = length * slope

    # Start
    spline.bezier_points[0].co = Vector((0, 0, total_drop))
    spline.bezier_points[0].handle_right = Vector((2, 3, total_drop * 0.95))
    spline.bezier_points[0].handle_left = Vector((-1, -1, total_drop))

    # Point 1
    spline.bezier_points[1].co = Vector((4, length * 0.25, total_drop * 0.8))
    spline.bezier_points[1].handle_left = Vector((3, length * 0.18, total_drop * 0.85))
    spline.bezier_points[1].handle_right = Vector((5, length * 0.32, total_drop * 0.75))
    spline.bezier_points[1].handle_left_type = "ALIGNED"
    spline.bezier_points[1].handle_right_type = "ALIGNED"

    # Point 2 - middle
    spline.bezier_points[2].co = Vector((0, length * 0.5, total_drop * 0.55))
    spline.bezier_points[2].handle_left = Vector((2, length * 0.42, total_drop * 0.62))
    spline.bezier_points[2].handle_right = Vector((-2, length * 0.58, total_drop * 0.48))
    spline.bezier_points[2].handle_left_type = "ALIGNED"
    spline.bezier_points[2].handle_right_type = "ALIGNED"

    # Point 3
    spline.bezier_points[3].co = Vector((-3, length * 0.75, total_drop * 0.25))
    spline.bezier_points[3].handle_left = Vector((-2, length * 0.67, total_drop * 0.35))
    spline.bezier_points[3].handle_right = Vector((-3.5, length * 0.83, total_drop * 0.18))
    spline.bezier_points[3].handle_left_type = "ALIGNED"
    spline.bezier_points[3].handle_right_type = "ALIGNED"

    # End
    spline.bezier_points[4].co = Vector((0, length, 0))
    spline.bezier_points[4].handle_left = Vector((-2, length - 3, 0.05))
    spline.bezier_points[4].handle_right = Vector((1, length + 2, 0))

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    return obj


def create_culvert_straight(name: str, length: float = 20.0, slope: float = 0.01) -> bpy.types.Object:
    """Create a straight culvert alignment."""
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 8

    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(1)  # 2 points - simple straight

    drop = length * slope

    spline.bezier_points[0].co = Vector((0, 0, drop))
    spline.bezier_points[0].handle_right = Vector((0, 3, drop - 0.03))
    spline.bezier_points[0].handle_left = Vector((0, -2, drop))

    spline.bezier_points[1].co = Vector((0, length, 0))
    spline.bezier_points[1].handle_left = Vector((0, length - 3, 0.03))
    spline.bezier_points[1].handle_right = Vector((0, length + 2, 0))

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    return obj


# =============================================================================
# BUILT-IN PRESETS with curve generators, transitions and drops
# =============================================================================

BUILTIN_PRESETS = {
    # -------------------------------------------------------------------------
    # BASIC CHANNELS (no transitions)
    # -------------------------------------------------------------------------
    "Irrigation Small": {
        "section_type": "TRAP",
        "bottom_width": 0.5,
        "side_slope": 1.0,
        "height": 0.5,
        "freeboard": 0.15,
        "lining_thickness": 0.10,
        "resolution_m": 0.5,
        "description": "Small irrigation canal (0.5m base)",
        "curve_generator": "straight",
        "curve_length": 25.0,
        "curve_slope": 0.015,
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
        "curve_generator": "culvert",
        "curve_length": 15.0,
        "curve_slope": 0.01,
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
        "curve_generator": "culvert",
        "curve_length": 20.0,
        "curve_slope": 0.008,
    },
    # -------------------------------------------------------------------------
    # CHANNELS WITH WIDTH TRANSITIONS
    # -------------------------------------------------------------------------
    "Width Transition (Expansion)": {
        "section_type": "TRAP",
        "bottom_width": 1.5,
        "side_slope": 1.5,
        "height": 1.2,
        "freeboard": 0.25,
        "lining_thickness": 0.15,
        "resolution_m": 0.5,
        "description": "Canal 1.5m → 3.0m width transition",
        "curve_generator": "straight",
        "curve_length": 30.0,
        "curve_slope": 0.01,
        "transitions_enabled": True,
        "transitions": [
            {
                "start_station": 10.0,
                "end_station": 20.0,
                "target_bottom_width": 3.0,
                "target_height": 1.2,
                "target_side_slope": 1.5,
                "vary_width": True,
                "vary_height": False,
                "vary_slope": False,
            }
        ],
    },
    "Width Transition (Contraction)": {
        "section_type": "TRAP",
        "bottom_width": 4.0,
        "side_slope": 1.5,
        "height": 1.5,
        "freeboard": 0.30,
        "lining_thickness": 0.15,
        "resolution_m": 0.5,
        "description": "Canal 4.0m → 2.0m contraction",
        "curve_generator": "straight",
        "curve_length": 30.0,
        "curve_slope": 0.008,
        "transitions_enabled": True,
        "transitions": [
            {
                "start_station": 10.0,
                "end_station": 18.0,
                "target_bottom_width": 2.0,
                "target_height": 1.5,
                "target_side_slope": 1.5,
                "vary_width": True,
                "vary_height": False,
                "vary_slope": False,
            }
        ],
    },
    # -------------------------------------------------------------------------
    # CHANNELS WITH HEIGHT/SECTION TRANSITIONS
    # -------------------------------------------------------------------------
    "Section Change (Trap to Rect)": {
        "section_type": "TRAP",
        "bottom_width": 2.0,
        "side_slope": 1.5,
        "height": 1.5,
        "freeboard": 0.25,
        "lining_thickness": 0.15,
        "resolution_m": 0.5,
        "description": "Trapezoidal → Rectangular transition",
        "curve_generator": "straight",
        "curve_length": 30.0,
        "curve_slope": 0.01,
        "transitions_enabled": True,
        "transitions": [
            {
                "start_station": 12.0,
                "end_station": 18.0,
                "target_bottom_width": 2.0,
                "target_height": 1.5,
                "target_side_slope": 0.0,  # Rectangular = 0 side slope
                "vary_width": False,
                "vary_height": False,
                "vary_slope": True,
            }
        ],
    },
    "Multi-Transition Canal": {
        "section_type": "TRAP",
        "bottom_width": 1.0,
        "side_slope": 1.0,
        "height": 1.0,
        "freeboard": 0.20,
        "lining_thickness": 0.15,
        "resolution_m": 0.5,
        "description": "Multiple width changes along path",
        "curve_generator": "curved",
        "curve_length": 35.0,
        "curve_slope": 0.01,
        "transitions_enabled": True,
        "transitions": [
            {
                "start_station": 5.0,
                "end_station": 10.0,
                "target_bottom_width": 2.0,
                "target_height": 1.0,
                "target_side_slope": 1.0,
                "vary_width": True,
                "vary_height": False,
                "vary_slope": False,
            },
            {
                "start_station": 20.0,
                "end_station": 28.0,
                "target_bottom_width": 1.0,
                "target_height": 1.0,
                "target_side_slope": 1.0,
                "vary_width": True,
                "vary_height": False,
                "vary_slope": False,
            },
        ],
    },
    # -------------------------------------------------------------------------
    # CHANNELS WITH DROP STRUCTURES
    # -------------------------------------------------------------------------
    "Canal with Drop": {
        "section_type": "TRAP",
        "bottom_width": 1.5,
        "side_slope": 1.5,
        "height": 1.0,
        "freeboard": 0.25,
        "lining_thickness": 0.15,
        "resolution_m": 0.5,
        "description": "Channel with 1.5m vertical drop",
        "curve_generator": "drop",
        "curve_length": 30.0,
        "drop_height": 1.5,
        "drops_enabled": True,
        "drops": [
            {
                "station": 15.0,
                "drop_height": 1.5,
                "drop_type": "VERTICAL",
            }
        ],
    },
    "Canal with Multiple Drops": {
        "section_type": "TRAP",
        "bottom_width": 1.2,
        "side_slope": 1.0,
        "height": 0.8,
        "freeboard": 0.20,
        "lining_thickness": 0.15,
        "resolution_m": 0.5,
        "description": "Stepped channel with 2 drops",
        "curve_generator": "straight",
        "curve_length": 35.0,
        "curve_slope": 0.005,
        "drops_enabled": True,
        "drops": [
            {
                "station": 12.0,
                "drop_height": 0.8,
                "drop_type": "VERTICAL",
            },
            {
                "station": 24.0,
                "drop_height": 0.8,
                "drop_type": "VERTICAL",
            },
        ],
    },
    # -------------------------------------------------------------------------
    # COMPLEX CHANNELS (transitions + curves)
    # -------------------------------------------------------------------------
    "Drainage Urban": {
        "section_type": "RECT",
        "bottom_width": 2.0,
        "side_slope": 0.0,
        "height": 1.5,
        "freeboard": 0.30,
        "lining_thickness": 0.20,
        "resolution_m": 0.5,
        "description": "Urban drainage with curves",
        "curve_generator": "urban",
        "curve_length": 35.0,
        "curve_slope": 0.005,
    },
    "Drainage with Expansion": {
        "section_type": "RECT",
        "bottom_width": 1.5,
        "side_slope": 0.0,
        "height": 1.2,
        "freeboard": 0.25,
        "lining_thickness": 0.20,
        "resolution_m": 0.5,
        "description": "Urban drainage widening at outlet",
        "curve_generator": "urban",
        "curve_length": 35.0,
        "curve_slope": 0.005,
        "transitions_enabled": True,
        "transitions": [
            {
                "start_station": 25.0,
                "end_station": 33.0,
                "target_bottom_width": 3.0,
                "target_height": 1.2,
                "target_side_slope": 0.0,
                "vary_width": True,
                "vary_height": False,
                "vary_slope": False,
            }
        ],
    },
    "Earth Channel": {
        "section_type": "TRAP",
        "bottom_width": 2.0,
        "side_slope": 2.5,
        "height": 1.0,
        "freeboard": 0.30,
        "lining_thickness": 0.0,
        "resolution_m": 1.0,
        "description": "Unlined earth channel",
        "curve_generator": "curved",
        "curve_length": 30.0,
        "curve_slope": 0.01,
    },
    "Mountain Stream": {
        "section_type": "TRAP",
        "bottom_width": 1.0,
        "side_slope": 1.0,
        "height": 0.8,
        "freeboard": 0.20,
        "lining_thickness": 0.15,
        "resolution_m": 0.5,
        "description": "Steep channel (8% slope)",
        "curve_generator": "steep",
        "curve_length": 25.0,
    },
    # -------------------------------------------------------------------------
    # COMPLETE DEMO PROJECTS
    # -------------------------------------------------------------------------
    "Complete Demo (All Features)": {
        "section_type": "TRAP",
        "bottom_width": 1.5,
        "side_slope": 1.5,
        "height": 1.2,
        "freeboard": 0.25,
        "lining_thickness": 0.15,
        "resolution_m": 0.5,
        "description": "Demo: curves + transition + drop",
        "curve_generator": "curved",
        "curve_length": 35.0,
        "curve_slope": 0.01,
        "transitions_enabled": True,
        "transitions": [
            {
                "start_station": 8.0,
                "end_station": 14.0,
                "target_bottom_width": 2.5,
                "target_height": 1.2,
                "target_side_slope": 1.5,
                "vary_width": True,
                "vary_height": False,
                "vary_slope": False,
            },
        ],
        "drops_enabled": True,
        "drops": [
            {
                "station": 22.0,
                "drop_height": 1.0,
                "drop_type": "VERTICAL",
            },
        ],
    },
}


def generate_curve_for_preset(preset_name: str, preset_data: dict) -> bpy.types.Object:
    """Generate the appropriate curve based on preset settings."""
    curve_type = preset_data.get("curve_generator", "straight")
    length = preset_data.get("curve_length", 30.0)
    slope = preset_data.get("curve_slope", 0.01)

    # Generate unique name
    base_name = f"CADHY_Axis_{preset_name.replace(' ', '_')}"

    # Check if similar curve exists and remove
    for obj in bpy.data.objects:
        if obj.name.startswith(base_name) and obj.type == "CURVE":
            bpy.data.objects.remove(obj, do_unlink=True)

    # Generate curve based on type
    if curve_type == "straight":
        curve_obj = create_straight_curve(base_name, length, slope)
    elif curve_type == "curved":
        curve_obj = create_curved_channel(base_name, length, slope)
    elif curve_type == "drop":
        drop_height = preset_data.get("drop_height", 1.5)
        curve_obj = create_channel_with_drop(base_name, length, drop_height)
    elif curve_type == "steep":
        curve_obj = create_steep_channel(base_name, length)
    elif curve_type == "urban":
        curve_obj = create_urban_drainage(base_name, length)
    elif curve_type == "culvert":
        curve_obj = create_culvert_straight(base_name, length, slope)
    else:
        curve_obj = create_straight_curve(base_name, length, slope)

    return curve_obj


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
            "curve_generator": "straight",
            "curve_length": 30.0,
            "curve_slope": 0.01,
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
    """Load a channel preset and generate curve geometry"""

    bl_idname = "cadhy.load_preset"
    bl_label = "Load Preset"
    bl_description = "Load channel settings and generate axis curve"
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

        # =================================================================
        # CONFIGURE TRANSITIONS
        # =================================================================
        # Clear existing transitions
        settings.transitions.clear()

        if preset_data.get("transitions_enabled", False):
            settings.transitions_enabled = True

            for trans_data in preset_data.get("transitions", []):
                trans = settings.transitions.add()
                trans.start_station = trans_data.get("start_station", 0.0)
                trans.end_station = trans_data.get("end_station", 10.0)
                trans.target_bottom_width = trans_data.get("target_bottom_width", settings.bottom_width)
                trans.target_height = trans_data.get("target_height", settings.height)
                trans.target_side_slope = trans_data.get("target_side_slope", settings.side_slope)
                trans.vary_width = trans_data.get("vary_width", True)
                trans.vary_height = trans_data.get("vary_height", False)
                trans.vary_slope = trans_data.get("vary_slope", False)
        else:
            settings.transitions_enabled = False

        # =================================================================
        # CONFIGURE DROPS
        # =================================================================
        # Clear existing drops
        if hasattr(settings, "drops"):
            settings.drops.clear()

            if preset_data.get("drops_enabled", False):
                settings.drops_enabled = True

                for drop_data in preset_data.get("drops", []):
                    drop = settings.drops.add()
                    drop.station = drop_data.get("station", 0.0)
                    drop.drop_height = drop_data.get("drop_height", 1.0)
                    drop.drop_type = drop_data.get("drop_type", "VERTICAL")
            else:
                settings.drops_enabled = False

        # Generate the curve geometry
        curve_obj = generate_curve_for_preset(self.preset_name, preset_data)

        # Set as active axis in scene settings
        settings.axis_object = curve_obj

        # Select the curve
        bpy.ops.object.select_all(action="DESELECT")
        curve_obj.select_set(True)
        context.view_layer.objects.active = curve_obj

        # Zoom to fit
        try:
            bpy.ops.view3d.view_selected(use_all_regions=False)
        except Exception:
            pass

        desc = preset_data.get("description", self.preset_name)
        self.report({"INFO"}, f"Loaded: {desc} - Click 'Build Channel' to generate")
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
    row.label(text="Project Templates", icon="PRESET")

    col = box.column(align=True)

    # Group presets by category
    categories = {
        "Basic Channels": [
            "Irrigation Small",
            "Culvert Round 600",
            "Culvert Round 1200",
        ],
        "With Transitions": [
            "Width Transition (Expansion)",
            "Width Transition (Contraction)",
            "Section Change (Trap to Rect)",
            "Multi-Transition Canal",
        ],
        "With Drops": [
            "Canal with Drop",
            "Canal with Multiple Drops",
        ],
        "Complex": [
            "Drainage Urban",
            "Drainage with Expansion",
            "Earth Channel",
            "Mountain Stream",
            "Complete Demo (All Features)",
        ],
    }

    for category, preset_names in categories.items():
        col.separator()
        col.label(text=category + ":")
        for name in preset_names:
            if name in BUILTIN_PRESETS:
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
