"""
Scene Properties Module
Global scene-level settings for CADHY.
"""

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup


class CADHYTransitionItem(PropertyGroup):
    """Single transition zone definition."""

    start_station: FloatProperty(
        name="Start",
        description="Start station of transition (meters)",
        default=0.0,
        min=0.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    end_station: FloatProperty(
        name="End",
        description="End station of transition (meters)",
        default=10.0,
        min=0.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    # Target parameters (what to transition TO)
    target_bottom_width: FloatProperty(
        name="Target Width",
        description="Target bottom width at end of transition",
        default=2.0,
        min=0.1,
        max=100.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    target_height: FloatProperty(
        name="Target Height",
        description="Target height at end of transition",
        default=2.0,
        min=0.1,
        max=50.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    target_side_slope: FloatProperty(
        name="Target Slope",
        description="Target side slope at end of transition (H:V)",
        default=1.5,
        min=0.0,
        max=10.0,
    )

    # Which parameters to transition
    vary_width: BoolProperty(
        name="Vary Width",
        description="Transition the bottom width",
        default=True,
    )

    vary_height: BoolProperty(
        name="Vary Height",
        description="Transition the height",
        default=False,
    )

    vary_slope: BoolProperty(
        name="Vary Slope",
        description="Transition the side slope",
        default=False,
    )


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
            ("TRAP", "Trapezoidal", "Trapezoidal section with sloped sides"),
            ("RECT", "Rectangular", "Rectangular section with vertical walls"),
            ("TRI", "Triangular", "V-channel / triangular section"),
            ("CIRC", "Circular", "Open circular channel (half-pipe)"),
            ("PIPE", "Pipe", "Closed commercial pipe with wall thickness"),
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
        description="Thickness of channel lining (or wall thickness for pipes)",
        default=0.15,
        min=0.0,
        max=2.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    # Pipe-specific parameters
    pipe_material: EnumProperty(
        name="Pipe Material",
        description="Commercial pipe material type",
        items=[
            ("HDPE", "HDPE PE100", "High-density polyethylene PE100"),
            ("PVC", "PVC", "Polyvinyl chloride"),
            ("CONCRETE", "Concrete", "Reinforced concrete pipe"),
        ],
        default="HDPE",
    )

    pipe_diameter: EnumProperty(
        name="Nominal Diameter",
        description="Nominal pipe diameter",
        items=[
            # HDPE common sizes (mm)
            ("110", "DN 110 mm", "110 mm nominal diameter"),
            ("160", "DN 160 mm", "160 mm nominal diameter"),
            ("200", "DN 200 mm", "200 mm nominal diameter"),
            ("250", "DN 250 mm", "250 mm nominal diameter"),
            ("315", "DN 315 mm", "315 mm nominal diameter"),
            ("400", "DN 400 mm", "400 mm nominal diameter"),
            ("500", "DN 500 mm", "500 mm nominal diameter"),
            ("630", "DN 630 mm", "630 mm nominal diameter"),
            ("800", "DN 800 mm", "800 mm nominal diameter"),
            ("1000", "DN 1000 mm", "1000 mm nominal diameter"),
            ("1200", "DN 1200 mm", "1200 mm nominal diameter"),
        ],
        default="315",
    )

    pipe_sdr: EnumProperty(
        name="SDR",
        description="Standard Dimension Ratio (for HDPE)",
        items=[
            ("11", "SDR 11", "PN 16 bar pressure rating"),
            ("17", "SDR 17", "PN 10 bar pressure rating"),
        ],
        default="11",
    )

    pipe_schedule: EnumProperty(
        name="Schedule",
        description="Pipe schedule (for PVC)",
        items=[
            ("SCH40", "Schedule 40", "Standard wall thickness"),
            ("SCH80", "Schedule 80", "Extra heavy wall thickness"),
        ],
        default="SCH40",
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

    # CFD Mesh Settings
    cfd_mesh_type: EnumProperty(
        name="Mesh Type",
        description="Type of mesh elements for CFD domain",
        items=[
            ("TRI", "Triangular", "Triangular elements (universal compatibility)"),
            ("QUAD", "Quadrilateral", "Quadrilateral elements (structured mesh)"),
        ],
        default="TRI",
    )

    cfd_mesh_size: FloatProperty(
        name="Mesh Size",
        description="Target element size for CFD mesh",
        default=0.5,
        min=0.01,
        max=10.0,
        unit="LENGTH",
        subtype="DISTANCE",
    )

    cfd_mesh_preview: BoolProperty(
        name="Preview Mesh",
        description="Show mesh wireframe preview on CFD domain",
        default=False,
    )

    # Boundary Conditions
    bc_inlet_type: EnumProperty(
        name="Inlet BC",
        description="Boundary condition type for inlet",
        items=[
            ("VELOCITY", "Velocity Inlet", "Fixed velocity at inlet"),
            ("MASS_FLOW", "Mass Flow", "Fixed mass flow rate"),
            ("PRESSURE", "Pressure Inlet", "Fixed pressure at inlet"),
        ],
        default="VELOCITY",
    )

    bc_inlet_velocity: FloatProperty(
        name="Inlet Velocity",
        description="Inlet velocity (m/s)",
        default=1.0,
        min=0.0,
        max=50.0,
    )

    bc_outlet_type: EnumProperty(
        name="Outlet BC",
        description="Boundary condition type for outlet",
        items=[
            ("PRESSURE", "Pressure Outlet", "Fixed pressure at outlet"),
            ("OUTFLOW", "Outflow", "Zero gradient outflow"),
        ],
        default="PRESSURE",
    )

    bc_outlet_pressure: FloatProperty(
        name="Outlet Pressure",
        description="Outlet pressure (Pa gauge)",
        default=0.0,
        min=-100000.0,
        max=1000000.0,
    )

    bc_wall_type: EnumProperty(
        name="Wall BC",
        description="Boundary condition type for walls",
        items=[
            ("NO_SLIP", "No Slip", "Zero velocity at wall"),
            ("SLIP", "Slip", "Free slip wall"),
            ("ROUGH", "Rough Wall", "Wall with roughness"),
        ],
        default="NO_SLIP",
    )

    bc_wall_roughness: FloatProperty(
        name="Wall Roughness",
        description="Wall roughness height (m)",
        default=0.001,
        min=0.0,
        max=0.1,
    )

    bc_top_type: EnumProperty(
        name="Top BC",
        description="Boundary condition type for top surface (free surface)",
        items=[
            ("SYMMETRY", "Symmetry", "Symmetry plane (rigid lid)"),
            ("PRESSURE", "Pressure", "Atmospheric pressure"),
            ("VOF", "VOF Interface", "Volume of Fluid interface (multiphase)"),
        ],
        default="SYMMETRY",
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

    # Panel UI State (collapsible sections)
    ui_show_axis: BoolProperty(
        name="Show Axis Section",
        description="Expand axis selection section",
        default=True,
    )

    ui_show_section_params: BoolProperty(
        name="Show Section Parameters",
        description="Expand section parameters",
        default=True,
    )

    ui_show_cfd: BoolProperty(
        name="Show CFD Section",
        description="Expand CFD domain section",
        default=True,
    )

    ui_show_mesh_quality: BoolProperty(
        name="Show Mesh Quality",
        description="Expand mesh quality section",
        default=False,
    )

    ui_show_sections: BoolProperty(
        name="Show Cross-Sections",
        description="Expand cross-sections section",
        default=False,
    )

    ui_show_export: BoolProperty(
        name="Show Export",
        description="Expand export section",
        default=False,
    )

    ui_show_render: BoolProperty(
        name="Show Render",
        description="Expand render section",
        default=False,
    )

    ui_show_channel_info: BoolProperty(
        name="Show Channel Info",
        description="Expand channel info section",
        default=False,
    )

    ui_show_transitions: BoolProperty(
        name="Show Transitions",
        description="Expand transitions section",
        default=False,
    )

    # Transitions - enable/disable
    transitions_enabled: BoolProperty(
        name="Enable Transitions",
        description="Enable section transitions along channel",
        default=False,
    )

    active_transition_index: IntProperty(
        name="Active Transition",
        description="Index of active transition",
        default=0,
    )

    # Transitions collection
    transitions: CollectionProperty(
        type=CADHYTransitionItem,
        name="Transitions",
        description="List of section transitions",
    )
