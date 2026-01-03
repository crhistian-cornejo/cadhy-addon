"""
Hydraulic Calculations Module
Real-time hydraulic property calculations for CADHY channels.

This module provides functions to calculate:
- Channel slope from curve axis
- Hydraulic area, wetted perimeter, hydraulic radius
- Manning's flow capacity (theoretical)
- Mesh statistics
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    pass


@dataclass
class HydraulicInfo:
    """Container for hydraulic properties at design water depth."""

    # Geometric
    water_depth: float = 0.0  # m
    top_width: float = 0.0  # m at water surface
    total_height: float = 0.0  # m including freeboard

    # Hydraulic
    area: float = 0.0  # m^2
    wetted_perimeter: float = 0.0  # m
    hydraulic_radius: float = 0.0  # m

    # Flow (theoretical, Manning's)
    manning_n: float = 0.015  # concrete lined channel
    slope: float = 0.001  # m/m
    velocity: float = 0.0  # m/s
    discharge: float = 0.0  # m^3/s

    def calculate_manning(self) -> None:
        """Calculate velocity and discharge using Manning's equation."""
        if self.hydraulic_radius > 0 and self.slope > 0:
            # V = (1/n) * R^(2/3) * S^(1/2)
            self.velocity = (1.0 / self.manning_n) * (self.hydraulic_radius ** (2 / 3)) * (self.slope**0.5)
            self.discharge = self.velocity * self.area


@dataclass
class MeshStats:
    """Mesh statistics for a channel object."""

    vertices: int = 0
    edges: int = 0
    faces: int = 0
    triangles: int = 0
    volume: float = 0.0  # m^3
    surface_area: float = 0.0  # m^2
    is_manifold: bool = False
    is_watertight: bool = False
    non_manifold_edges: int = 0


@dataclass
class SlopeInfo:
    """Slope information from curve axis."""

    # Elevations
    start_elevation: float = 0.0  # m
    end_elevation: float = 0.0  # m
    elevation_drop: float = 0.0  # m

    # Lengths
    horizontal_length: float = 0.0  # m
    curve_length: float = 0.0  # m (3D length along curve)

    # Slopes
    average_slope: float = 0.0  # m/m (dimensionless)
    average_slope_percent: float = 0.0  # %
    min_slope: float = 0.0  # m/m
    max_slope: float = 0.0  # m/m


def get_curve_slope_info(curve_obj) -> Optional[SlopeInfo]:
    """
    Calculate slope information from a curve object.

    Args:
        curve_obj: Blender curve object (axis)

    Returns:
        SlopeInfo with slope data, or None if invalid
    """
    if curve_obj is None or curve_obj.type != "CURVE":
        return None

    curve = curve_obj.data
    if not curve.splines:
        return None

    # Get world matrix for accurate coordinates
    matrix = curve_obj.matrix_world

    info = SlopeInfo()
    all_slopes = []
    total_length = 0.0
    prev_point = None

    for spline in curve.splines:
        points = []

        if spline.type == "BEZIER":
            points = [bp.co for bp in spline.bezier_points]
        elif spline.type == "NURBS":
            points = [p.co[:3] for p in spline.points]
        else:  # POLY
            points = [p.co[:3] for p in spline.points]

        for i, co in enumerate(points):
            # Transform to world coordinates
            world_co = matrix @ co if len(co) == 3 else matrix @ co.to_3d()

            if prev_point is not None:
                dx = world_co.x - prev_point.x
                dy = world_co.y - prev_point.y
                dz = world_co.z - prev_point.z

                horizontal_dist = math.sqrt(dx * dx + dy * dy)
                segment_length = math.sqrt(dx * dx + dy * dy + dz * dz)

                total_length += segment_length

                if horizontal_dist > 0.001:  # Avoid division by zero
                    segment_slope = abs(dz) / horizontal_dist
                    all_slopes.append(segment_slope)

            if i == 0 and prev_point is None:
                info.start_elevation = world_co.z

            prev_point = world_co

    if prev_point is not None:
        info.end_elevation = prev_point.z

    info.elevation_drop = abs(info.start_elevation - info.end_elevation)
    info.curve_length = total_length

    # Calculate horizontal length (projected)
    first_point = None
    for spline in curve.splines:
        if spline.type == "BEZIER" and spline.bezier_points:
            first_point = matrix @ spline.bezier_points[0].co
            break
        elif spline.points:
            co = spline.points[0].co
            first_point = matrix @ (co.to_3d() if hasattr(co, "to_3d") else co[:3])
            break

    if first_point and prev_point:
        dx = prev_point.x - first_point.x
        dy = prev_point.y - first_point.y
        info.horizontal_length = math.sqrt(dx * dx + dy * dy)

    # Calculate slopes
    if info.horizontal_length > 0.001:
        info.average_slope = info.elevation_drop / info.horizontal_length
        info.average_slope_percent = info.average_slope * 100

    if all_slopes:
        info.min_slope = min(all_slopes)
        info.max_slope = max(all_slopes)

    return info


def get_mesh_stats(mesh_obj) -> Optional[MeshStats]:
    """
    Calculate mesh statistics for a mesh object.

    Args:
        mesh_obj: Blender mesh object

    Returns:
        MeshStats with mesh data, or None if invalid
    """
    if mesh_obj is None or mesh_obj.type != "MESH":
        return None

    import bmesh

    mesh = mesh_obj.data
    stats = MeshStats()

    stats.vertices = len(mesh.vertices)
    stats.edges = len(mesh.edges)
    stats.faces = len(mesh.polygons)

    # Count triangles
    stats.triangles = sum(len(poly.vertices) - 2 for poly in mesh.polygons)

    # Use bmesh for detailed analysis
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        # Check manifold
        non_manifold = [e for e in bm.edges if not e.is_manifold]
        stats.non_manifold_edges = len(non_manifold)
        stats.is_manifold = len(non_manifold) == 0

        # Check watertight (manifold + no boundary edges)
        boundary = [e for e in bm.edges if e.is_boundary]
        stats.is_watertight = stats.is_manifold and len(boundary) == 0

        # Calculate volume (only valid for watertight meshes)
        if stats.is_watertight:
            stats.volume = bm.calc_volume()

        # Surface area
        stats.surface_area = sum(f.calc_area() for f in bm.faces)

    finally:
        bm.free()

    return stats


def calculate_hydraulic_info(
    section_type: str,
    bottom_width: float,
    side_slope: float,
    height: float,
    freeboard: float,
    water_depth: Optional[float] = None,
    slope: float = 0.001,
    manning_n: float = 0.015,
) -> HydraulicInfo:
    """
    Calculate hydraulic properties for a channel section.

    Args:
        section_type: "TRAP", "RECT", or "CIRC"
        bottom_width: Bottom width or diameter (m)
        side_slope: Side slope ratio H:V (for trapezoidal)
        height: Design water depth (m)
        freeboard: Freeboard height (m)
        water_depth: Actual water depth (defaults to height)
        slope: Channel slope (m/m)
        manning_n: Manning's roughness coefficient

    Returns:
        HydraulicInfo with calculated properties
    """
    info = HydraulicInfo()

    if water_depth is None:
        water_depth = height

    info.water_depth = water_depth
    info.total_height = height + freeboard
    info.slope = slope
    info.manning_n = manning_n

    if section_type == "TRAP":
        # Trapezoidal section
        info.area = (bottom_width + side_slope * water_depth) * water_depth
        info.wetted_perimeter = bottom_width + 2 * water_depth * math.sqrt(1 + side_slope**2)
        info.top_width = bottom_width + 2 * side_slope * water_depth

    elif section_type == "RECT":
        # Rectangular section
        info.area = bottom_width * water_depth
        info.wetted_perimeter = bottom_width + 2 * water_depth
        info.top_width = bottom_width

    elif section_type == "CIRC":
        # Circular section
        r = bottom_width / 2
        if water_depth >= bottom_width:
            # Full flow
            info.area = math.pi * r * r
            info.wetted_perimeter = math.pi * bottom_width
            info.top_width = 0.0
        else:
            # Partial flow
            theta = 2 * math.acos((r - water_depth) / r)
            info.area = r * r * (theta - math.sin(theta)) / 2
            info.wetted_perimeter = r * theta
            info.top_width = 2 * math.sqrt(water_depth * (bottom_width - water_depth))

    # Hydraulic radius
    if info.wetted_perimeter > 0:
        info.hydraulic_radius = info.area / info.wetted_perimeter

    # Manning's equation
    info.calculate_manning()

    return info


def get_channel_hydraulic_info(channel_obj) -> Tuple[Optional[HydraulicInfo], Optional[SlopeInfo], Optional[MeshStats]]:
    """
    Get complete hydraulic information for a CADHY channel object.

    Args:
        channel_obj: Blender mesh object with cadhy_channel properties

    Returns:
        Tuple of (HydraulicInfo, SlopeInfo, MeshStats) or (None, None, None)
    """
    if channel_obj is None or channel_obj.type != "MESH":
        return None, None, None

    ch = getattr(channel_obj, "cadhy_channel", None)
    if ch is None or not ch.is_cadhy_object:
        return None, None, None

    # Get slope from source axis
    slope_info = None
    slope = 0.001  # default

    if ch.source_axis:
        slope_info = get_curve_slope_info(ch.source_axis)
        if slope_info and slope_info.average_slope > 0:
            slope = slope_info.average_slope

    # Calculate hydraulics
    hydraulic_info = calculate_hydraulic_info(
        section_type=ch.section_type,
        bottom_width=ch.bottom_width,
        side_slope=ch.side_slope,
        height=ch.height,
        freeboard=ch.freeboard,
        slope=slope,
    )

    # Get mesh stats
    mesh_stats = get_mesh_stats(channel_obj)

    return hydraulic_info, slope_info, mesh_stats
