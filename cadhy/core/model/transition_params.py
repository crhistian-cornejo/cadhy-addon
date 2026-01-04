"""
Transition Parameters Module
Defines data structures for channel transitions (varying geometry along path).
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .channel_params import ChannelParams


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t (0-1)."""
    return a + (b - a) * t


@dataclass
class StationParams:
    """
    Parameters at a specific station along the channel.

    Used to define the geometry at transition endpoints.
    None values inherit from base parameters.
    """

    station: float  # Distance from start (meters)
    bottom_width: Optional[float] = None
    side_slope: Optional[float] = None
    height: Optional[float] = None
    freeboard: Optional[float] = None
    lining_thickness: Optional[float] = None

    def get_value(self, param_name: str, base_value: float) -> float:
        """Get parameter value, falling back to base if not set."""
        value = getattr(self, param_name, None)
        return value if value is not None else base_value


@dataclass
class TransitionZone:
    """
    Defines a transition zone between two sections.

    The geometry interpolates linearly between start_params and end_params
    over the distance from start_station to end_station.
    """

    start_station: float
    end_station: float
    start_params: StationParams
    end_params: StationParams
    transition_type: str = "LINEAR"  # LINEAR or SMOOTH (future: spline)

    @property
    def length(self) -> float:
        """Length of transition zone."""
        return self.end_station - self.start_station

    def contains_station(self, station: float) -> bool:
        """Check if station is within this transition zone."""
        return self.start_station <= station <= self.end_station

    def get_t(self, station: float) -> float:
        """Get interpolation factor (0-1) for station."""
        if self.length <= 0:
            return 0.0
        return (station - self.start_station) / self.length


@dataclass
class ChannelAlignment:
    """
    Channel alignment with optional transitions.

    Defines a channel that can have varying geometry along its path.
    Base parameters apply where no transition is defined.
    """

    base_params: ChannelParams
    transitions: List[TransitionZone] = field(default_factory=list)

    def get_params_at_station(self, station: float) -> ChannelParams:
        """
        Get interpolated channel parameters at a specific station.

        Args:
            station: Distance along channel axis (meters)

        Returns:
            ChannelParams with interpolated values
        """
        # Check if we're in a transition zone
        for tz in self.transitions:
            if tz.contains_station(station):
                return self._interpolate_params(tz, station)

        # No transition at this station, return base params
        return self.base_params

    def _interpolate_params(self, tz: TransitionZone, station: float) -> ChannelParams:
        """Interpolate parameters within a transition zone."""
        t = tz.get_t(station)

        # Get interpolated values
        bottom_width = lerp(
            tz.start_params.get_value("bottom_width", self.base_params.bottom_width),
            tz.end_params.get_value("bottom_width", self.base_params.bottom_width),
            t,
        )

        side_slope = lerp(
            tz.start_params.get_value("side_slope", self.base_params.side_slope),
            tz.end_params.get_value("side_slope", self.base_params.side_slope),
            t,
        )

        height = lerp(
            tz.start_params.get_value("height", self.base_params.height),
            tz.end_params.get_value("height", self.base_params.height),
            t,
        )

        freeboard = lerp(
            tz.start_params.get_value("freeboard", self.base_params.freeboard),
            tz.end_params.get_value("freeboard", self.base_params.freeboard),
            t,
        )

        lining_thickness = lerp(
            tz.start_params.get_value("lining_thickness", self.base_params.lining_thickness),
            tz.end_params.get_value("lining_thickness", self.base_params.lining_thickness),
            t,
        )

        return ChannelParams(
            section_type=self.base_params.section_type,
            bottom_width=bottom_width,
            side_slope=side_slope,
            height=height,
            freeboard=freeboard,
            lining_thickness=lining_thickness,
            resolution_m=self.base_params.resolution_m,
            subdivide_profile=self.base_params.subdivide_profile,
            profile_resolution=self.base_params.profile_resolution,
        )

    def add_transition(
        self,
        start_station: float,
        end_station: float,
        target_bottom_width: Optional[float] = None,
        target_height: Optional[float] = None,
        target_side_slope: Optional[float] = None,
    ) -> TransitionZone:
        """
        Add a transition zone to the alignment.

        Args:
            start_station: Start of transition (meters)
            end_station: End of transition (meters)
            target_bottom_width: Target width at end (None = keep current)
            target_height: Target height at end (None = keep current)
            target_side_slope: Target slope at end (None = keep current)

        Returns:
            Created TransitionZone
        """
        # Get params at start station (may already be in a transition)
        start_params_full = self.get_params_at_station(start_station)

        start_params = StationParams(
            station=start_station,
            bottom_width=start_params_full.bottom_width,
            height=start_params_full.height,
            side_slope=start_params_full.side_slope,
            freeboard=start_params_full.freeboard,
            lining_thickness=start_params_full.lining_thickness,
        )

        end_params = StationParams(
            station=end_station,
            bottom_width=target_bottom_width if target_bottom_width else start_params_full.bottom_width,
            height=target_height if target_height else start_params_full.height,
            side_slope=target_side_slope if target_side_slope else start_params_full.side_slope,
            freeboard=start_params_full.freeboard,
            lining_thickness=start_params_full.lining_thickness,
        )

        tz = TransitionZone(
            start_station=start_station,
            end_station=end_station,
            start_params=start_params,
            end_params=end_params,
        )

        # Insert sorted by start_station
        self.transitions.append(tz)
        self.transitions.sort(key=lambda x: x.start_station)

        return tz

    def remove_transition(self, index: int) -> None:
        """Remove transition at index."""
        if 0 <= index < len(self.transitions):
            self.transitions.pop(index)

    def clear_transitions(self) -> None:
        """Remove all transitions."""
        self.transitions.clear()
