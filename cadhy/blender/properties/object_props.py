"""
Object Properties Module
Object-level settings for CADHY channels and CFD domains.
"""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup


class CADHYChannelSettings(PropertyGroup):
    """Settings stored on channel mesh objects."""

    # Link to source axis
    source_axis: PointerProperty(
        name="Source Axis",
        description="Curve used to generate this channel",
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

    # Section parameters (stored for regeneration)
    bottom_width: FloatProperty(
        name="Bottom Width", description="Width at bottom of channel", default=2.0, min=0.1, max=100.0, unit="LENGTH"
    )

    side_slope: FloatProperty(
        name="Side Slope", description="Horizontal to vertical ratio (Z:1)", default=1.5, min=0.0, max=10.0
    )

    height: FloatProperty(name="Height", description="Channel height", default=2.0, min=0.1, max=50.0, unit="LENGTH")

    freeboard: FloatProperty(
        name="Freeboard",
        description="Additional height above design water level",
        default=0.3,
        min=0.0,
        max=10.0,
        unit="LENGTH",
    )

    lining_thickness: FloatProperty(
        name="Lining Thickness",
        description="Thickness of channel lining",
        default=0.15,
        min=0.0,
        max=2.0,
        unit="LENGTH",
    )

    resolution_m: FloatProperty(
        name="Resolution", description="Sampling resolution along axis", default=1.0, min=0.1, max=100.0, unit="LENGTH"
    )

    # Computed properties (read-only, for display)
    total_length: FloatProperty(name="Total Length", description="Total length of channel", default=0.0, unit="LENGTH")

    # Slope info (from source axis)
    slope_avg: FloatProperty(name="Average Slope", description="Average slope (m/m)", default=0.0, precision=6)
    slope_percent: FloatProperty(name="Slope %", description="Average slope in percent", default=0.0, precision=3)
    elevation_start: FloatProperty(
        name="Start Elevation", description="Elevation at channel start", default=0.0, unit="LENGTH"
    )
    elevation_end: FloatProperty(
        name="End Elevation", description="Elevation at channel end", default=0.0, unit="LENGTH"
    )
    elevation_drop: FloatProperty(name="Elevation Drop", description="Total elevation drop", default=0.0, unit="LENGTH")

    # Hydraulic properties (at design depth)
    hydraulic_area: FloatProperty(
        name="Hydraulic Area", description="Cross-sectional flow area", default=0.0, unit="AREA"
    )
    wetted_perimeter: FloatProperty(
        name="Wetted Perimeter", description="Wetted perimeter length", default=0.0, unit="LENGTH"
    )
    hydraulic_radius: FloatProperty(
        name="Hydraulic Radius", description="Hydraulic radius (A/P)", default=0.0, unit="LENGTH"
    )
    top_width_water: FloatProperty(name="Top Width", description="Water surface width", default=0.0, unit="LENGTH")
    manning_velocity: FloatProperty(name="Velocity", description="Manning velocity (m/s)", default=0.0)
    manning_discharge: FloatProperty(name="Discharge", description="Manning discharge (m³/s)", default=0.0)
    manning_n: FloatProperty(
        name="Manning n", description="Manning roughness coefficient", default=0.015, min=0.001, max=0.1
    )

    # Mesh statistics
    mesh_vertices: IntProperty(name="Vertices", description="Number of mesh vertices", default=0)
    mesh_edges: IntProperty(name="Edges", description="Number of mesh edges", default=0)
    mesh_faces: IntProperty(name="Faces", description="Number of mesh faces", default=0)
    mesh_triangles: IntProperty(name="Triangles", description="Number of triangles", default=0)
    mesh_volume: FloatProperty(name="Volume", description="Mesh volume", default=0.0, unit="VOLUME")
    mesh_surface_area: FloatProperty(name="Surface Area", description="Mesh surface area", default=0.0, unit="AREA")
    mesh_is_manifold: BoolProperty(name="Is Manifold", description="Whether mesh is manifold", default=False)
    mesh_is_watertight: BoolProperty(name="Is Watertight", description="Whether mesh is watertight", default=False)
    mesh_non_manifold: IntProperty(name="Non-Manifold Edges", description="Number of non-manifold edges", default=0)

    # Version tracking
    cadhy_version: StringProperty(
        name="CADHY Version", description="Version of CADHY used to create this object", default=""
    )

    # Status
    is_cadhy_object: BoolProperty(
        name="Is CADHY Object", description="Whether this object was created by CADHY", default=True
    )


class CADHYCFDSettings(PropertyGroup):
    """Settings stored on CFD domain mesh objects."""

    # Link to source channel
    source_channel: PointerProperty(
        name="Source Channel",
        description="Channel this CFD domain was generated from",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "MESH",
    )

    # Link to source axis
    source_axis: PointerProperty(
        name="Source Axis",
        description="Curve used to generate this domain",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "CURVE",
    )

    # CFD parameters
    enabled: BoolProperty(name="Enabled", description="CFD domain generation enabled", default=True)

    inlet_extension_m: FloatProperty(
        name="Inlet Extension", description="Extension length at inlet", default=2.0, min=0.0, max=100.0, unit="LENGTH"
    )

    outlet_extension_m: FloatProperty(
        name="Outlet Extension",
        description="Extension length at outlet",
        default=5.0,
        min=0.0,
        max=100.0,
        unit="LENGTH",
    )

    water_level_m: FloatProperty(
        name="Water Level", description="Water level from channel bottom", default=1.5, min=0.0, max=50.0, unit="LENGTH"
    )

    fill_mode: EnumProperty(
        name="Fill Mode",
        description="How to fill the CFD domain",
        items=[
            ("WATER_LEVEL", "Water Level", "Fill to specified water level"),
            ("FULL", "Full", "Fill entire section"),
        ],
        default="WATER_LEVEL",
    )

    cap_inlet: BoolProperty(name="Cap Inlet", description="Close inlet with cap", default=True)

    cap_outlet: BoolProperty(name="Cap Outlet", description="Close outlet with cap", default=True)

    # Validation status
    is_watertight: BoolProperty(name="Is Watertight", description="Whether mesh is watertight", default=False)

    is_valid: BoolProperty(name="Is Valid", description="Whether mesh is valid for CFD", default=False)

    non_manifold_edges: IntProperty(name="Non-Manifold Edges", description="Number of non-manifold edges", default=0)

    volume: FloatProperty(name="Volume", description="Volume of CFD domain", default=0.0, unit="VOLUME")

    # Version tracking
    cadhy_version: StringProperty(
        name="CADHY Version", description="Version of CADHY used to create this object", default=""
    )

    is_cadhy_object: BoolProperty(
        name="Is CADHY Object", description="Whether this object was created by CADHY", default=True
    )
