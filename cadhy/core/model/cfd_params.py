"""
CFD Parameters Module
Defines data structures for CFD domain generation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class FillMode(Enum):
    """Fill mode for CFD domain."""

    WATER_LEVEL = "WATER_LEVEL"  # Fill to specified water level
    FULL = "FULL"  # Fill entire section (pressurized)


class PatchType(Enum):
    """CFD boundary patch types."""

    INLET = "inlet"
    OUTLET = "outlet"
    WALLS = "walls"
    TOP = "top"  # Free surface (if applicable)
    BOTTOM = "bottom"


@dataclass
class CFDParams:
    """Parameters for CFD domain generation."""

    enabled: bool = True
    inlet_extension_m: float = 2.0  # meters
    outlet_extension_m: float = 5.0  # meters
    water_level_m: float = 1.5  # meters (from bottom)
    fill_mode: FillMode = FillMode.WATER_LEVEL
    cap_inlet: bool = True
    cap_outlet: bool = True
    generate_patches: bool = True

    @property
    def patch_names(self) -> List[str]:
        """Return list of patch names to generate."""
        patches = [PatchType.INLET.value, PatchType.OUTLET.value, PatchType.WALLS.value]
        if self.fill_mode == FillMode.WATER_LEVEL:
            patches.append(PatchType.TOP.value)
        return patches


@dataclass
class CFDDomainInfo:
    """Information about generated CFD domain."""

    volume: float = 0.0  # cubic meters
    is_watertight: bool = False
    non_manifold_edges: int = 0
    self_intersections: int = 0
    patch_areas: dict = None  # {patch_name: area}

    def __post_init__(self):
        if self.patch_areas is None:
            self.patch_areas = {}

    @property
    def is_valid(self) -> bool:
        """Check if domain is valid for CFD."""
        return self.is_watertight and self.non_manifold_edges == 0 and self.self_intersections == 0

    def get_validation_report(self) -> str:
        """Generate validation report string."""
        lines = [
            "=== CFD Domain Validation Report ===",
            f"Watertight: {'Yes' if self.is_watertight else 'No'}",
            f"Non-manifold edges: {self.non_manifold_edges}",
            f"Self-intersections: {self.self_intersections}",
            f"Volume: {self.volume:.3f} m³",
            "",
            "Patch Areas:",
        ]
        for patch, area in self.patch_areas.items():
            lines.append(f"  {patch}: {area:.3f} m²")

        lines.append("")
        lines.append(f"Status: {'VALID' if self.is_valid else 'INVALID - Fix issues before export'}")

        return "\n".join(lines)
