"""
Drop Structures Module
Defines data structures for hydraulic drop structures (chutes, falls).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DropType(Enum):
    """Type of drop structure."""

    VERTICAL = "vertical"  # Vertical drop with wall
    INCLINED = "inclined"  # Inclined ramp/chute
    STEPPED = "stepped"  # Multiple steps


@dataclass
class DropStructure:
    """
    Defines a drop structure at a specific station.

    Drop structures create vertical or inclined transitions
    between different channel elevations.
    """

    station: float  # Position along channel axis (meters)
    drop_height: float  # Total height of drop (meters)
    drop_type: DropType = DropType.VERTICAL

    # For inclined drops
    length: float = 0.0  # Horizontal length of incline (meters)

    # For stepped drops
    num_steps: int = 1  # Number of steps

    # Optional basin (future feature)
    basin_length: float = 0.0  # Length of stilling basin after drop

    @property
    def slope(self) -> float:
        """Calculate slope for inclined drops (rise/run)."""
        if self.length > 0:
            return self.drop_height / self.length
        return float("inf")  # Vertical

    @property
    def step_height(self) -> float:
        """Height of each step for stepped drops."""
        if self.num_steps > 0:
            return self.drop_height / self.num_steps
        return self.drop_height

    @property
    def step_length(self) -> float:
        """Length of each step for stepped drops."""
        if self.num_steps > 0 and self.length > 0:
            return self.length / self.num_steps
        return 0.3  # Default step tread depth

    def get_end_station(self) -> float:
        """Get the station where the drop ends."""
        if self.drop_type == DropType.VERTICAL:
            return self.station + 0.1  # Small offset for vertical
        return self.station + self.length + self.basin_length

    def validate(self) -> Optional[str]:
        """Validate drop parameters. Returns error message or None."""
        if self.drop_height <= 0:
            return "Drop height must be positive"
        if self.drop_type == DropType.INCLINED and self.length <= 0:
            return "Inclined drop requires positive length"
        if self.drop_type == DropType.STEPPED and self.num_steps < 1:
            return "Stepped drop requires at least 1 step"
        return None
