"""
Channel Parameters Module
Defines data structures for channel section parameters.
"""

from dataclasses import dataclass
from enum import Enum


class SectionType(Enum):
    """Types of hydraulic sections."""

    TRAPEZOIDAL = "TRAP"
    RECTANGULAR = "RECT"
    TRIANGULAR = "TRI"
    CIRCULAR = "CIRC"
    PIPE = "PIPE"  # Commercial pipe with wall thickness


# Commercial pipe data (HDPE PE100 SDR series)
# Format: (nominal_diameter_mm, outer_diameter_mm, sdr, wall_thickness_mm)
HDPE_PIPE_DATA = {
    # DN (mm): [(OD, SDR, wall_thickness), ...]
    110: [(110, 11, 10.0), (110, 17, 6.6)],
    160: [(160, 11, 14.6), (160, 17, 9.5)],
    200: [(200, 11, 18.2), (200, 17, 11.9)],
    250: [(250, 11, 22.7), (250, 17, 14.8)],
    315: [(315, 11, 28.6), (315, 17, 18.7)],
    400: [(400, 11, 36.4), (400, 17, 23.7)],
    500: [(500, 11, 45.5), (500, 17, 29.7)],
    630: [(630, 11, 57.3), (630, 17, 37.4)],
    800: [(800, 11, 72.7), (800, 17, 47.4)],
    1000: [(1000, 11, 90.9), (1000, 17, 59.3)],
    1200: [(1200, 11, 109.1), (1200, 17, 71.1)],
}

# PVC pipe data (SCH40 / SCH80)
PVC_PIPE_DATA = {
    # Nominal size (inches): (OD_mm, wall_sch40_mm, wall_sch80_mm)
    2: (60.3, 3.91, 5.54),
    3: (88.9, 5.49, 7.62),
    4: (114.3, 6.02, 8.56),
    6: (168.3, 7.11, 10.97),
    8: (219.1, 8.18, 12.70),
    10: (273.1, 9.27, 15.09),
    12: (323.9, 10.31, 17.48),
    14: (355.6, 11.13, 19.05),
    16: (406.4, 12.70, 21.44),
    18: (457.2, 14.27, 23.83),
    20: (508.0, 15.09, 26.19),
    24: (609.6, 17.48, 30.94),
}

# Concrete pipe data (standard diameters)
CONCRETE_PIPE_DATA = {
    # DN (mm): (inner_diameter_mm, wall_thickness_mm)
    300: (300, 44),
    400: (400, 51),
    500: (500, 57),
    600: (600, 64),
    800: (800, 76),
    1000: (1000, 89),
    1200: (1200, 102),
    1500: (1500, 127),
    1800: (1800, 152),
    2000: (2000, 165),
    2400: (2400, 191),
}


@dataclass
class ChannelParams:
    """Parameters for channel generation."""

    section_type: SectionType = SectionType.TRAPEZOIDAL
    bottom_width: float = 2.0  # meters (or diameter for circular/pipe)
    side_slope: float = 1.5  # horizontal:vertical (Z:1)
    height: float = 2.0  # meters
    freeboard: float = 0.3  # meters
    lining_thickness: float = 0.15  # meters (or wall thickness for pipes)
    resolution_m: float = 1.0  # sampling resolution along axis

    # Profile subdivision for uniform mesh density
    subdivide_profile: bool = True  # Whether to subdivide profile edges
    profile_resolution: float = 1.0  # Max edge length in profile (meters)

    # Pipe-specific parameters
    pipe_material: str = "HDPE"  # HDPE, PVC, CONCRETE
    pipe_sdr: int = 11  # Standard Dimension Ratio (for HDPE)
    pipe_schedule: str = "SCH40"  # SCH40, SCH80 (for PVC)

    @property
    def total_height(self) -> float:
        """Total height including freeboard."""
        if self.section_type in (SectionType.CIRCULAR, SectionType.PIPE):
            return self.bottom_width  # Diameter is the total height
        return self.height + self.freeboard

    @property
    def inner_diameter(self) -> float:
        """Get inner diameter for pipes."""
        if self.section_type == SectionType.PIPE:
            # Outer diameter - 2 * wall thickness
            return self.bottom_width - 2 * self.lining_thickness
        return self.bottom_width

    @property
    def top_width(self) -> float:
        """Calculate top width for trapezoidal section."""
        if self.section_type == SectionType.TRAPEZOIDAL:
            return self.bottom_width + 2 * self.side_slope * self.total_height
        elif self.section_type == SectionType.TRIANGULAR:
            return 2 * self.side_slope * self.total_height
        elif self.section_type == SectionType.RECTANGULAR:
            return self.bottom_width
        else:
            return self.bottom_width  # For circular/pipe, this is diameter

    def hydraulic_area(self, water_depth: float) -> float:
        """Calculate hydraulic area for given water depth."""
        import math

        if self.section_type == SectionType.TRAPEZOIDAL:
            return (self.bottom_width + self.side_slope * water_depth) * water_depth
        elif self.section_type == SectionType.RECTANGULAR:
            return self.bottom_width * water_depth
        elif self.section_type == SectionType.TRIANGULAR:
            # V-channel: A = z * y^2 where z is side slope, y is depth
            return self.side_slope * water_depth * water_depth
        elif self.section_type in (SectionType.CIRCULAR, SectionType.PIPE):
            r = self.inner_diameter / 2 if self.section_type == SectionType.PIPE else self.bottom_width / 2
            if water_depth >= r * 2:
                return math.pi * r * r
            if water_depth <= 0:
                return 0.0
            theta = 2 * math.acos((r - water_depth) / r)
            return r * r * (theta - math.sin(theta)) / 2
        return 0.0

    def wetted_perimeter(self, water_depth: float) -> float:
        """Calculate wetted perimeter for given water depth."""
        import math

        if self.section_type == SectionType.TRAPEZOIDAL:
            return self.bottom_width + 2 * water_depth * math.sqrt(1 + self.side_slope**2)
        elif self.section_type == SectionType.RECTANGULAR:
            return self.bottom_width + 2 * water_depth
        elif self.section_type == SectionType.TRIANGULAR:
            # V-channel: P = 2 * y * sqrt(1 + z^2)
            return 2 * water_depth * math.sqrt(1 + self.side_slope**2)
        elif self.section_type in (SectionType.CIRCULAR, SectionType.PIPE):
            r = self.inner_diameter / 2 if self.section_type == SectionType.PIPE else self.bottom_width / 2
            if water_depth >= r * 2:
                return math.pi * r * 2
            if water_depth <= 0:
                return 0.0
            theta = 2 * math.acos((r - water_depth) / r)
            return r * theta
        return 0.0

    def hydraulic_radius(self, water_depth: float) -> float:
        """Calculate hydraulic radius for given water depth."""
        wp = self.wetted_perimeter(water_depth)
        if wp > 0:
            return self.hydraulic_area(water_depth) / wp
        return 0.0


@dataclass
class SectionProfile:
    """Represents a 2D section profile (local coordinates)."""

    points: list  # List of (x, y) tuples representing the section outline
    is_closed: bool = False

    @classmethod
    def from_channel_params(cls, params: ChannelParams, include_lining: bool = False) -> "SectionProfile":
        """Generate section profile from channel parameters."""
        points = []
        h = params.total_height

        if params.section_type == SectionType.TRAPEZOIDAL:
            bw = params.bottom_width
            tw = params.top_width

            # Inner profile (bottom to top, counterclockwise)
            points = [
                (-bw / 2, 0),  # Bottom left
                (bw / 2, 0),  # Bottom right
                (tw / 2, h),  # Top right
                (-tw / 2, h),  # Top left
            ]

        elif params.section_type == SectionType.RECTANGULAR:
            bw = params.bottom_width
            points = [
                (-bw / 2, 0),
                (bw / 2, 0),
                (bw / 2, h),
                (-bw / 2, h),
            ]

        elif params.section_type == SectionType.CIRCULAR:
            import math

            r = params.bottom_width / 2
            segments = 32
            for i in range(segments + 1):
                angle = math.pi + (math.pi * i / segments)  # Bottom half circle
                x = r * math.cos(angle)
                y = r * math.sin(angle) + r
                points.append((x, y))

        return cls(points=points, is_closed=True)
