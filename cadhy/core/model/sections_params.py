"""
Sections Parameters Module
Defines data structures for cross-section generation.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class SectionCut:
    """Represents a single cross-section cut."""
    station: float  # Chainage/distance along axis (meters)
    position: Tuple[float, float, float]  # World position (x, y, z)
    tangent: Tuple[float, float, float]  # Tangent direction at this point
    normal: Tuple[float, float, float]  # Normal direction (perpendicular to tangent)
    profile_points: List[Tuple[float, float, float]] = field(default_factory=list)
    
    # Computed metrics
    hydraulic_area: float = 0.0
    wetted_perimeter: float = 0.0
    hydraulic_radius: float = 0.0
    top_width: float = 0.0
    water_depth: float = 0.0


@dataclass
class SectionsParams:
    """Parameters for section generation."""
    start_station: float = 0.0  # meters
    end_station: Optional[float] = None  # None = end of curve
    step: float = 10.0  # meters between sections
    include_endpoints: bool = True
    export_format: str = "CSV"  # CSV, JSON
    
    def get_stations(self, curve_length: float) -> List[float]:
        """Calculate station positions along curve."""
        end = self.end_station if self.end_station is not None else curve_length
        end = min(end, curve_length)
        
        stations = []
        current = self.start_station
        
        while current <= end:
            stations.append(current)
            current += self.step
        
        # Ensure end point is included if requested
        if self.include_endpoints and stations[-1] < end:
            stations.append(end)
        
        return stations


@dataclass
class SectionsReport:
    """Report containing all generated sections."""
    sections: List[SectionCut] = field(default_factory=list)
    axis_name: str = ""
    channel_name: str = ""
    total_length: float = 0.0
    
    def to_csv(self) -> str:
        """Export sections to CSV format."""
        lines = [
            "station_m,x,y,z,hydraulic_area_m2,wetted_perimeter_m,hydraulic_radius_m,top_width_m,water_depth_m"
        ]
        for sec in self.sections:
            lines.append(
                f"{sec.station:.3f},{sec.position[0]:.6f},{sec.position[1]:.6f},{sec.position[2]:.6f},"
                f"{sec.hydraulic_area:.4f},{sec.wetted_perimeter:.4f},{sec.hydraulic_radius:.4f},"
                f"{sec.top_width:.4f},{sec.water_depth:.4f}"
            )
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Export sections to dictionary (for JSON)."""
        return {
            "axis_name": self.axis_name,
            "channel_name": self.channel_name,
            "total_length_m": self.total_length,
            "sections": [
                {
                    "station_m": sec.station,
                    "position": {"x": sec.position[0], "y": sec.position[1], "z": sec.position[2]},
                    "tangent": {"x": sec.tangent[0], "y": sec.tangent[1], "z": sec.tangent[2]},
                    "hydraulic_area_m2": sec.hydraulic_area,
                    "wetted_perimeter_m": sec.wetted_perimeter,
                    "hydraulic_radius_m": sec.hydraulic_radius,
                    "top_width_m": sec.top_width,
                    "water_depth_m": sec.water_depth,
                }
                for sec in self.sections
            ]
        }
