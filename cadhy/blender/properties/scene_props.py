"""
Scene Properties Module
Global scene-level settings for CADHY.
"""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup


class CADHYSceneSettings(PropertyGroup):
    """Global CADHY settings stored at scene level."""

    # Unit settings
    units: EnumProperty(
        name="Units",
        description="Working units for CADHY",
        items=[
            ("METERS", "Meters", "Use meters"),
            ("FEET", "Feet", "Use feet"),
        ],
        default="METERS",
    )

    # Default resolution
    default_resolution_m: FloatProperty(
        name="Default Resolution",
        description="Default sampling resolution along axis (meters)",
        default=1.0,
        min=0.1,
        max=100.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    # Georeferencing
    georef_enabled: BoolProperty(
        name="Georeferencing Enabled", description="Enable georeferencing for coordinates", default=False
    )

    georef_crs: StringProperty(name="CRS", description="Coordinate Reference System (e.g., EPSG:32618)", default="")

    georef_offset: FloatVectorProperty(
        name="Offset",
        description="Local origin offset (X, Y, Z)",
        default=(0.0, 0.0, 0.0),
        size=3,
        subtype="TRANSLATION",
    )

    # Axis selection
    axis_object: PointerProperty(
        name="Axis Curve",
        description="Select the curve to use as channel axis",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "CURVE",
    )

    # Section type
    section_type: EnumProperty(
        name="Section Type",
        description="Type of hydraulic section",
        items=[
            ("TRAP", "Trapezoidal", "Trapezoidal section"),
            ("RECT", "Rectangular", "Rectangular section"),
            ("CIRC", "Circular", "Circular section"),
        ],
        default="TRAP",
    )

    # Section parameters
    bottom_width: FloatProperty(
        name="Bottom Width",
        description="Width at bottom of channel (or diameter for circular)",
        default=2.0,
        min=0.1,
        max=100.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    side_slope: FloatProperty(
        name="Side Slope", description="Horizontal to vertical ratio (Z:1)", default=1.5, min=0.0, max=10.0
    )

    height: FloatProperty(
        name="Height",
        description="Channel height (excluding freeboard)",
        default=2.0,
        min=0.1,
        max=50.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    freeboard: FloatProperty(
        name="Freeboard",
        description="Additional height above design water level",
        default=0.3,
        min=0.0,
        max=10.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    lining_thickness: FloatProperty(
        name="Lining Thickness",
        description="Thickness of channel lining",
        default=0.15,
        min=0.0,
        max=2.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    resolution_m: FloatProperty(
        name="Resolution",
        description="Sampling resolution along axis (meters)",
        default=1.0,
        min=0.1,
        max=100.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    # Profile subdivision for uniform mesh
    subdivide_profile: BoolProperty(
        name="Subdivide Profile",
        description="Subdivide section profile edges for uniform mesh density",
        default=True,
    )

    profile_resolution: FloatProperty(
        name="Profile Resolution",
        description="Maximum edge length in section profile (meters). Set to match axis resolution for square faces",
        default=1.0,
        min=0.1,
        max=10.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    # CFD Settings
    cfd_enabled: BoolProperty(
        name="Generate CFD Domain", description="Generate CFD fluid domain alongside channel", default=True
    )

    cfd_inlet_extension: FloatProperty(
        name="Inlet Extension",
        description="Extension length at inlet for flow development",
        default=2.0,
        min=0.0,
        max=100.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    cfd_outlet_extension: FloatProperty(
        name="Outlet Extension",
        description="Extension length at outlet for flow development",
        default=5.0,
        min=0.0,
        max=100.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    cfd_water_level: FloatProperty(
        name="Water Level",
        description="Water level from channel bottom",
        default=1.5,
        min=0.0,
        max=50.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    cfd_fill_mode: EnumProperty(
        name="Fill Mode",
        description="How to fill the CFD domain",
        items=[
            ("WATER_LEVEL", "Water Level", "Fill to specified water level"),
            ("FULL", "Full", "Fill entire section (pressurized)"),
        ],
        default="WATER_LEVEL",
    )

    # Sections settings
    sections_start: FloatProperty(
        name="Start Station",
        description="Starting station for sections",
        default=0.0,
        min=0.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    sections_end: FloatProperty(
        name="End Station",
        description="Ending station for sections (0 = end of curve)",
        default=0.0,
        min=0.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    sections_step: FloatProperty(
        name="Step",
        description="Distance between sections",
        default=10.0,
        min=0.1,
        max=1000.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    # Export settings
    export_format: EnumProperty(
        name="Export Format",
        description="Mesh export format",
        items=[
            ("STL", "STL", "Stereolithography format"),
            ("OBJ", "OBJ", "Wavefront OBJ format"),
            ("PLY", "PLY", "Stanford PLY format"),
        ],
        default="STL",
    )

    export_path: StringProperty(
        name="Export Path", description="Directory for exported files", default="//cadhy_export/", subtype="DIR_PATH"
    )
