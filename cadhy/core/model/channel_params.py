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
    CIRCULAR = "CIRC"


@dataclass
class ChannelParams:
    """Parameters for channel generation."""

    section_type: SectionType = SectionType.TRAPEZOIDAL
    bottom_width: float = 2.0  # meters
    side_slope: float = 1.5  # horizontal:vertical (Z:1)
    height: float = 2.0  # meters
    freeboard: float = 0.3  # meters
    lining_thickness: float = 0.15  # meters
    resolution_m: float = 1.0  # sampling resolution along axis

    # Profile subdivision for uniform mesh density
    subdivide_profile: bool = True  # Whether to subdivide profile edges
    profile_resolution: float = 1.0  # Max edge length in profile (meters)

    @property
    def total_height(self) -> float:
        """Total height including freeboard."""
        return self.height + self.freeboard

    @property
    def top_width(self) -> float:
        """Calculate top width for trapezoidal section."""
        if self.section_type == SectionType.TRAPEZOIDAL:
            return self.bottom_width + 2 * self.side_slope * self.total_height
        elif self.section_type == SectionType.RECTANGULAR:
            return self.bottom_width
        else:
            return self.bottom_width  # For circular, this is diameter

    def hydraulic_area(self, water_depth: float) -> float:
        """Calculate hydraulic area for given water depth."""
        if self.section_type == SectionType.TRAPEZOIDAL:
            return (self.bottom_width + self.side_slope * water_depth) * water_depth
        elif self.section_type == SectionType.RECTANGULAR:
            return self.bottom_width * water_depth
        elif self.section_type == SectionType.CIRCULAR:
            import math

            r = self.bottom_width / 2
            if water_depth >= self.bottom_width:
                return math.pi * r * r
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
        elif self.section_type == SectionType.CIRCULAR:
            r = self.bottom_width / 2
            if water_depth >= self.bottom_width:
                return math.pi * self.bottom_width
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
