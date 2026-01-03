"""CADHY Geometry Module - Mesh generation and manipulation."""

from .hydraulics import (
    HydraulicInfo,
    MeshStats,
    SlopeInfo,
    calculate_hydraulic_info,
    get_channel_hydraulic_info,
    get_curve_slope_info,
    get_mesh_stats,
)

__all__ = [
    "HydraulicInfo",
    "MeshStats",
    "SlopeInfo",
    "calculate_hydraulic_info",
    "get_channel_hydraulic_info",
    "get_curve_slope_info",
    "get_mesh_stats",
]
