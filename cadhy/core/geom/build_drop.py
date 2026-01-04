"""
Build Drop Module
Geometry generation for hydraulic drop structures.
"""

from typing import List, Set, Tuple

from mathutils import Vector

from ..model.channel_params import ChannelParams, SectionType
from ..model.drop_structures import DropStructure, DropType
from .build_channel import generate_section_vertices_with_lining


def _get_open_edges(params: ChannelParams, n_section: int) -> Set[int]:
    """
    Determine which edge indices should be skipped for open channels.

    For open channels (TRAP, RECT, TRIANGULAR), we skip the "top" edge
    that represents the open water surface. For closed sections (PIPE, CIRCULAR),
    we may skip different edges or none.

    Args:
        params: Channel parameters
        n_section: Number of vertices in the section profile

    Returns:
        Set of edge indices to skip (edge j connects vertex j to vertex (j+1) % n)
    """
    section_type = params.section_type

    if section_type in (SectionType.TRAPEZOIDAL, SectionType.RECTANGULAR):
        # Profile: BL(0), BR(1), TR(2), TL(3)
        # Edge 2: TR->TL (top edge) - SKIP (open channel)
        # For subdivided profiles, last 2 vertices are still TR, TL
        return {n_section - 2}  # Skip only the top edge (TR->TL)

    elif section_type == SectionType.TRIANGULAR:
        # Profile: apex(0), TR(1), TL(2)
        # Edge 1: TR->TL (top edge) - SKIP
        # For subdivided, last 2 vertices are TR, TL
        return {n_section - 2}  # Skip the top edge (TR->TL)

    elif section_type == SectionType.CIRCULAR:
        # Half-circle (open channel)
        # The top edge connects the two top vertices (at water level)
        return {n_section - 1}  # Skip the edge connecting last to first

    elif section_type == SectionType.PIPE:
        # Full circle (closed pipe) - no edges to skip for drop walls
        return set()

    else:
        return set()


def generate_drop_geometry(
    drop: DropStructure,
    params: ChannelParams,
    upstream_pos: Vector,
    tangent: Vector,
    normal: Vector,
) -> Tuple[List[Vector], List[Tuple[int, ...]]]:
    """
    Generate geometry for a drop structure.

    Args:
        drop: Drop structure parameters
        params: Channel section parameters
        upstream_pos: Position at top of drop
        tangent: Direction along channel
        normal: Up direction (perpendicular to channel bed)

    Returns:
        Tuple of (vertices, faces)
    """
    if drop.drop_type == DropType.VERTICAL:
        return _generate_vertical_drop(drop, params, upstream_pos, tangent, normal)
    elif drop.drop_type == DropType.INCLINED:
        return _generate_inclined_drop(drop, params, upstream_pos, tangent, normal)
    elif drop.drop_type == DropType.STEPPED:
        return _generate_stepped_drop(drop, params, upstream_pos, tangent, normal)
    else:
        return [], []


def _generate_vertical_drop(
    drop: DropStructure,
    params: ChannelParams,
    upstream_pos: Vector,
    tangent: Vector,
    normal: Vector,
) -> Tuple[List[Vector], List[Tuple[int, ...]]]:
    """
    Generate a vertical drop structure.

    Creates a vertical wall connecting upper and lower channel sections.
    """
    vertices = []
    faces = []

    # Calculate binormal (horizontal perpendicular to tangent)
    binormal = tangent.cross(normal).normalized()

    # Get section profile
    inner_verts, outer_verts = generate_section_vertices_with_lining(params)

    # Upper section position (at drop start)
    upper_pos = upstream_pos.copy()

    # Lower section position (drop_height below, small forward offset)
    forward_offset = 0.05  # Small gap to avoid z-fighting
    lower_pos = upstream_pos + tangent * forward_offset - normal * drop.drop_height

    # Generate upper section vertices
    upper_start_idx = len(vertices)
    for sx, sy in inner_verts:
        world_pos = upper_pos + binormal * sx + normal * sy
        vertices.append(world_pos)

    # Generate lower section vertices
    lower_start_idx = len(vertices)
    for sx, sy in inner_verts:
        world_pos = lower_pos + binormal * sx + normal * sy
        vertices.append(world_pos)

    n_section = len(inner_verts)
    open_edges = _get_open_edges(params, n_section)

    # Create faces connecting upper to lower (the vertical drop wall)
    # This creates the inner face of the drop
    for j in range(n_section):
        j_next = (j + 1) % n_section

        # Skip the open channel top edge
        if j in open_edges:
            continue

        # Quad face: upper[j], upper[j+1], lower[j+1], lower[j]
        faces.append(
            (
                upper_start_idx + j,
                upper_start_idx + j_next,
                lower_start_idx + j_next,
                lower_start_idx + j,
            )
        )

    # If we have lining, also generate outer drop wall
    if outer_verts:
        outer_upper_start = len(vertices)
        for sx, sy in outer_verts:
            world_pos = upper_pos + binormal * sx + normal * sy
            vertices.append(world_pos)

        outer_lower_start = len(vertices)
        for sx, sy in outer_verts:
            world_pos = lower_pos + binormal * sx + normal * sy
            vertices.append(world_pos)

        n_outer = len(outer_verts)
        outer_open_edges = _get_open_edges(params, n_outer)

        # Outer wall faces (reversed winding for outward normal)
        for j in range(n_outer):
            j_next = (j + 1) % n_outer
            if j in outer_open_edges:
                continue
            faces.append(
                (
                    outer_upper_start + j_next,
                    outer_upper_start + j,
                    outer_lower_start + j,
                    outer_lower_start + j_next,
                )
            )

    return vertices, faces


def _generate_inclined_drop(
    drop: DropStructure,
    params: ChannelParams,
    upstream_pos: Vector,
    tangent: Vector,
    normal: Vector,
) -> Tuple[List[Vector], List[Tuple[int, ...]]]:
    """
    Generate an inclined ramp/chute drop.

    Creates a smooth inclined surface from upper to lower section.
    """
    vertices = []
    faces = []

    binormal = tangent.cross(normal).normalized()

    # Get section profile
    inner_verts, outer_verts = generate_section_vertices_with_lining(params)

    # Number of segments along the ramp
    num_segments = max(3, int(drop.length / params.resolution_m))

    n_section = len(inner_verts)
    open_edges = _get_open_edges(params, n_section)
    section_start_indices = []

    # Generate sections along the ramp
    for i in range(num_segments + 1):
        t = i / num_segments

        # Position interpolates along ramp
        pos = upstream_pos + tangent * (t * drop.length) - normal * (t * drop.drop_height)

        section_start = len(vertices)
        section_start_indices.append(section_start)

        for sx, sy in inner_verts:
            world_pos = pos + binormal * sx + normal * sy
            vertices.append(world_pos)

    # Connect adjacent sections with faces
    for i in range(num_segments):
        start_curr = section_start_indices[i]
        start_next = section_start_indices[i + 1]

        for j in range(n_section):
            j_next = (j + 1) % n_section

            # Skip open channel top edge
            if j in open_edges:
                continue

            faces.append(
                (
                    start_curr + j,
                    start_curr + j_next,
                    start_next + j_next,
                    start_next + j,
                )
            )

    # Add outer surface if lining exists
    if outer_verts:
        n_outer = len(outer_verts)
        outer_open_edges = _get_open_edges(params, n_outer)
        outer_section_starts = []

        for i in range(num_segments + 1):
            t = i / num_segments
            pos = upstream_pos + tangent * (t * drop.length) - normal * (t * drop.drop_height)

            section_start = len(vertices)
            outer_section_starts.append(section_start)

            for sx, sy in outer_verts:
                world_pos = pos + binormal * sx + normal * sy
                vertices.append(world_pos)

        for i in range(num_segments):
            start_curr = outer_section_starts[i]
            start_next = outer_section_starts[i + 1]

            for j in range(n_outer):
                j_next = (j + 1) % n_outer
                if j in outer_open_edges:
                    continue
                # Reversed winding for outer surface
                faces.append(
                    (
                        start_curr + j_next,
                        start_curr + j,
                        start_next + j,
                        start_next + j_next,
                    )
                )

    return vertices, faces


def _generate_stepped_drop(
    drop: DropStructure,
    params: ChannelParams,
    upstream_pos: Vector,
    tangent: Vector,
    normal: Vector,
) -> Tuple[List[Vector], List[Tuple[int, ...]]]:
    """
    Generate a stepped drop with multiple steps.

    Creates a series of horizontal treads and vertical risers.
    """
    vertices = []
    faces = []

    binormal = tangent.cross(normal).normalized()

    inner_verts, outer_verts = generate_section_vertices_with_lining(params)
    n_section = len(inner_verts)
    open_edges = _get_open_edges(params, n_section)

    step_height = drop.step_height
    step_length = drop.step_length

    section_indices = []

    # Generate vertices for each step transition
    for step in range(drop.num_steps + 1):
        # Top of current step (or bottom of previous)
        step_z = -step * step_height
        step_x = step * step_length

        pos_top = upstream_pos + tangent * step_x + normal * step_z

        # Add section at top of step
        top_start = len(vertices)
        section_indices.append(("top", step, top_start))
        for sx, sy in inner_verts:
            world_pos = pos_top + binormal * sx + normal * sy
            vertices.append(world_pos)

        # If not last step, add section at bottom of riser
        if step < drop.num_steps:
            pos_bottom = upstream_pos + tangent * step_x + normal * (step_z - step_height)

            bottom_start = len(vertices)
            section_indices.append(("bottom", step, bottom_start))
            for sx, sy in inner_verts:
                world_pos = pos_bottom + binormal * sx + normal * sy
                vertices.append(world_pos)

    # Create faces
    # For each step: vertical riser face + horizontal tread face
    for step in range(drop.num_steps):
        # Find indices
        top_of_step = None
        bottom_of_riser = None
        top_of_next = None

        for kind, s, idx in section_indices:
            if kind == "top" and s == step:
                top_of_step = idx
            elif kind == "bottom" and s == step:
                bottom_of_riser = idx
            elif kind == "top" and s == step + 1:
                top_of_next = idx

        # Vertical riser: top_of_step to bottom_of_riser
        if top_of_step is not None and bottom_of_riser is not None:
            for j in range(n_section):
                j_next = (j + 1) % n_section
                if j in open_edges:
                    continue
                faces.append(
                    (
                        top_of_step + j,
                        top_of_step + j_next,
                        bottom_of_riser + j_next,
                        bottom_of_riser + j,
                    )
                )

        # Horizontal tread: bottom_of_riser to top_of_next
        if bottom_of_riser is not None and top_of_next is not None:
            for j in range(n_section):
                j_next = (j + 1) % n_section
                if j in open_edges:
                    continue
                faces.append(
                    (
                        bottom_of_riser + j,
                        bottom_of_riser + j_next,
                        top_of_next + j_next,
                        top_of_next + j,
                    )
                )

    return vertices, faces


def get_drop_end_position(
    drop: DropStructure,
    upstream_pos: Vector,
    tangent: Vector,
    normal: Vector,
) -> Vector:
    """
    Calculate the position at the end (downstream) of a drop structure.

    Args:
        drop: Drop structure
        upstream_pos: Starting position
        tangent: Direction along channel
        normal: Up direction

    Returns:
        Position at downstream end of drop
    """
    if drop.drop_type == DropType.VERTICAL:
        # Small forward offset
        return upstream_pos + tangent * 0.1 - normal * drop.drop_height
    elif drop.drop_type == DropType.INCLINED:
        return upstream_pos + tangent * drop.length - normal * drop.drop_height
    elif drop.drop_type == DropType.STEPPED:
        total_length = drop.num_steps * drop.step_length
        return upstream_pos + tangent * total_length - normal * drop.drop_height
    else:
        return upstream_pos - normal * drop.drop_height
