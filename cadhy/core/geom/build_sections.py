"""
Build Sections Module
Generate cross-section cuts along the channel axis.
"""

import math
from typing import List

from ..model.channel_params import ChannelParams
from ..model.sections_params import SectionCut, SectionsParams, SectionsReport
from .build_channel import evaluate_curve_at_parameter, generate_section_vertices, get_curve_length


def generate_sections(
    curve_obj, channel_params: ChannelParams, sections_params: SectionsParams, water_depth: float = None
) -> SectionsReport:
    """
    Generate cross-sections along the channel axis.

    Args:
        curve_obj: Blender curve object (axis)
        channel_params: Channel parameters
        sections_params: Section generation parameters
        water_depth: Water depth for hydraulic calculations (optional)

    Returns:
        SectionsReport containing all generated sections
    """
    # Get curve length
    total_length = get_curve_length(curve_obj)
    if total_length <= 0:
        return SectionsReport()

    # Calculate station positions
    stations = sections_params.get_stations(total_length)

    # Generate section profile
    section_verts_2d = generate_section_vertices(channel_params, include_outer=False)

    # Default water depth
    if water_depth is None:
        water_depth = channel_params.height * 0.75  # 75% of height

    sections = []

    for station in stations:
        # Calculate parameter t (0-1) for this station
        t = station / total_length if total_length > 0 else 0
        t = max(0, min(1, t))

        # Evaluate curve at this station
        pos, tangent, normal = evaluate_curve_at_parameter(curve_obj, t)
        binormal = tangent.cross(normal).normalized()

        # Transform 2D section to 3D world coordinates
        profile_points_3d = []
        for sx, sy in section_verts_2d:
            world_pos = pos + binormal * sx + normal * sy
            profile_points_3d.append((world_pos.x, world_pos.y, world_pos.z))

        # Calculate hydraulic properties
        hydraulic_area = channel_params.hydraulic_area(water_depth)
        wetted_perimeter = channel_params.wetted_perimeter(water_depth)
        hydraulic_radius = channel_params.hydraulic_radius(water_depth)

        # Calculate top width at water level
        if channel_params.section_type.value == "TRAP":
            top_width = channel_params.bottom_width + 2 * channel_params.side_slope * water_depth
        elif channel_params.section_type.value == "RECT":
            top_width = channel_params.bottom_width
        else:
            # Circular - approximate
            r = channel_params.bottom_width / 2
            if water_depth >= channel_params.bottom_width:
                top_width = 0
            else:
                top_width = 2 * math.sqrt(r * r - (r - water_depth) ** 2)

        section = SectionCut(
            station=station,
            position=(pos.x, pos.y, pos.z),
            tangent=(tangent.x, tangent.y, tangent.z),
            normal=(normal.x, normal.y, normal.z),
            profile_points=profile_points_3d,
            hydraulic_area=hydraulic_area,
            wetted_perimeter=wetted_perimeter,
            hydraulic_radius=hydraulic_radius,
            top_width=top_width,
            water_depth=water_depth,
        )
        sections.append(section)

    report = SectionsReport(
        sections=sections,
        axis_name=curve_obj.name,
        channel_name=f"CADHY_Channel_{curve_obj.name}",
        total_length=total_length,
    )

    return report


def create_section_curves(report: SectionsReport, collection_name: str = "CADHY_Sections") -> List["bpy.types.Object"]:
    """
    Create Blender curve objects for each section.

    Args:
        report: SectionsReport with section data
        collection_name: Collection to place curves in

    Returns:
        List of created curve objects
    """
    import bpy

    # Get or create collection
    if collection_name not in bpy.data.collections:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[collection_name]

    created_objects = []

    for section in report.sections:
        name = f"Section_{section.station:.1f}m"

        # Remove existing if present
        if name in bpy.data.objects:
            old_obj = bpy.data.objects[name]
            bpy.data.objects.remove(old_obj, do_unlink=True)

        # Create curve data
        curve_data = bpy.data.curves.new(name, type="CURVE")
        curve_data.dimensions = "3D"

        # Create spline
        spline = curve_data.splines.new("POLY")
        spline.points.add(len(section.profile_points) - 1)

        for i, (x, y, z) in enumerate(section.profile_points):
            spline.points[i].co = (x, y, z, 1)

        # Close the spline
        spline.use_cyclic_u = True

        # Create object
        obj = bpy.data.objects.new(name, curve_data)
        collection.objects.link(obj)

        # Store station as custom property
        obj["cadhy_station"] = section.station
        obj["cadhy_hydraulic_area"] = section.hydraulic_area
        obj["cadhy_wetted_perimeter"] = section.wetted_perimeter

        created_objects.append(obj)

    return created_objects


def create_section_meshes(report: SectionsReport, collection_name: str = "CADHY_Sections") -> List["bpy.types.Object"]:
    """
    Create Blender mesh objects (filled polygons) for each section.

    Args:
        report: SectionsReport with section data
        collection_name: Collection to place meshes in

    Returns:
        List of created mesh objects
    """
    import bpy

    # Get or create collection
    if collection_name not in bpy.data.collections:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[collection_name]

    created_objects = []

    for section in report.sections:
        name = f"SectionMesh_{section.station:.1f}m"

        # Remove existing if present
        if name in bpy.data.objects:
            old_obj = bpy.data.objects[name]
            bpy.data.objects.remove(old_obj, do_unlink=True)

        # Create mesh
        mesh = bpy.data.meshes.new(name)

        # Create vertices and face
        verts = section.profile_points
        if len(verts) >= 3:
            # Single n-gon face
            faces = [tuple(range(len(verts)))]
            mesh.from_pydata(verts, [], faces)
            mesh.update()

            # Create object
            obj = bpy.data.objects.new(name, mesh)
            collection.objects.link(obj)

            # Store properties
            obj["cadhy_station"] = section.station
            obj["cadhy_hydraulic_area"] = section.hydraulic_area

            created_objects.append(obj)

    return created_objects
