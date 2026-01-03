"""
Channel Info Panel
Displays real-time geometric and hydraulic information for selected CADHY channels.
"""

import bpy
from bpy.types import Operator, Panel


def is_cadhy_channel(obj):
    """Check if object is a CADHY channel."""
    if not obj or obj.type != "MESH":
        return False
    ch = getattr(obj, "cadhy_channel", None)
    return ch is not None and ch.is_cadhy_object


class CADHY_OT_RefreshChannelInfo(Operator):
    """Refresh hydraulic and mesh calculations for the selected channel"""

    bl_idname = "cadhy.refresh_channel_info"
    bl_label = "Refresh Info"
    bl_description = "Recalculate hydraulic properties and mesh statistics"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_cadhy_channel(context.active_object)

    def execute(self, context):
        obj = context.active_object
        ch = obj.cadhy_channel

        try:
            from ...core.geom.hydraulics import (
                calculate_hydraulic_info,
                get_curve_slope_info,
                get_mesh_stats,
            )

            # Update slope info from axis
            if ch.source_axis:
                slope_info = get_curve_slope_info(ch.source_axis)
                if slope_info:
                    ch.slope_avg = slope_info.average_slope
                    ch.slope_percent = slope_info.average_slope_percent
                    ch.elevation_start = slope_info.start_elevation
                    ch.elevation_end = slope_info.end_elevation
                    ch.elevation_drop = slope_info.elevation_drop
                    ch.total_length = slope_info.curve_length

            # Calculate hydraulic properties
            slope = ch.slope_avg if ch.slope_avg > 0 else 0.001
            hydraulic = calculate_hydraulic_info(
                section_type=ch.section_type,
                bottom_width=ch.bottom_width,
                side_slope=ch.side_slope,
                height=ch.height,
                freeboard=ch.freeboard,
                slope=slope,
                manning_n=ch.manning_n,
            )

            ch.hydraulic_area = hydraulic.area
            ch.wetted_perimeter = hydraulic.wetted_perimeter
            ch.hydraulic_radius = hydraulic.hydraulic_radius
            ch.top_width_water = hydraulic.top_width
            ch.manning_velocity = hydraulic.velocity
            ch.manning_discharge = hydraulic.discharge

            # Update mesh stats
            mesh_stats = get_mesh_stats(obj)
            if mesh_stats:
                ch.mesh_vertices = mesh_stats.vertices
                ch.mesh_edges = mesh_stats.edges
                ch.mesh_faces = mesh_stats.faces
                ch.mesh_triangles = mesh_stats.triangles
                ch.mesh_volume = mesh_stats.volume
                ch.mesh_surface_area = mesh_stats.surface_area
                ch.mesh_is_manifold = mesh_stats.is_manifold
                ch.mesh_is_watertight = mesh_stats.is_watertight
                ch.mesh_non_manifold = mesh_stats.non_manifold_edges

            self.report({"INFO"}, "Channel info refreshed")

        except Exception as e:
            self.report({"ERROR"}, f"Failed to refresh: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}


class CADHY_PT_ChannelInfo(Panel):
    """Channel information panel showing hydraulic and mesh data"""

    bl_label = "Channel Info"
    bl_idname = "CADHY_PT_ChannelInfo"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CADHY"
    bl_order = 1
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return is_cadhy_channel(context.active_object)

    def draw_header(self, context):
        self.layout.label(text="", icon="INFO")

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        ch = obj.cadhy_channel

        # Refresh button
        row = layout.row(align=True)
        row.operator("cadhy.refresh_channel_info", icon="FILE_REFRESH")

        layout.separator()

        # === GEOMETRY ===
        self.draw_geometry_section(layout, ch)

        layout.separator()

        # === SLOPE / PROFILE ===
        self.draw_slope_section(layout, ch)

        layout.separator()

        # === HYDRAULICS ===
        self.draw_hydraulics_section(layout, ch)

        layout.separator()

        # === MESH STATS ===
        self.draw_mesh_section(layout, ch)

    def draw_geometry_section(self, layout, ch):
        """Draw geometry info box."""
        box = layout.box()
        row = box.row()
        row.label(text="Geometry", icon="MESH_CUBE")

        col = box.column(align=True)

        # Section type icon mapping
        type_icons = {"TRAP": "MOD_ARRAY", "RECT": "MESH_PLANE", "CIRC": "MESH_CIRCLE"}
        icon = type_icons.get(ch.section_type, "MESH_DATA")

        col.label(text=f"Section: {ch.section_type}", icon=icon)
        col.label(text=f"Bottom Width: {ch.bottom_width:.2f} m")

        if ch.section_type == "TRAP":
            col.label(text=f"Side Slope: {ch.side_slope:.2f} H:V")
            total_h = ch.height + ch.freeboard
            top_w = ch.bottom_width + 2 * ch.side_slope * total_h
            col.label(text=f"Top Width: {top_w:.2f} m")

        col.label(text=f"Height: {ch.height:.2f} m")
        col.label(text=f"Freeboard: {ch.freeboard:.2f} m")
        col.label(text=f"Total Height: {ch.height + ch.freeboard:.2f} m")

        if ch.lining_thickness > 0:
            col.label(text=f"Lining: {ch.lining_thickness * 100:.0f} cm")

    def draw_slope_section(self, layout, ch):
        """Draw slope/profile info box."""
        box = layout.box()
        row = box.row()
        row.label(text="Profile & Slope", icon="GRAPH")

        col = box.column(align=True)

        if ch.total_length > 0:
            col.label(text=f"Length: {ch.total_length:.2f} m")
        else:
            col.label(text="Length: -- (refresh)")

        if ch.slope_avg > 0:
            col.label(text=f"Slope: {ch.slope_percent:.3f} %")
            col.label(text=f"Slope: {ch.slope_avg:.6f} m/m")
            col.label(text=f"Slope: 1:{1 / ch.slope_avg:.0f}" if ch.slope_avg > 0 else "Slope: --")
        else:
            col.label(text="Slope: -- (refresh)")

        if ch.elevation_drop > 0:
            col.separator()
            col.label(text=f"Start Elev: {ch.elevation_start:.2f} m")
            col.label(text=f"End Elev: {ch.elevation_end:.2f} m")
            col.label(text=f"Drop: {ch.elevation_drop:.2f} m")

    def draw_hydraulics_section(self, layout, ch):
        """Draw hydraulic properties box."""
        box = layout.box()
        row = box.row()
        row.label(text="Hydraulics", icon="MOD_FLUIDSIM")

        col = box.column(align=True)

        # Manning's n (editable)
        row = col.row(align=True)
        row.prop(ch, "manning_n", text="Manning n")

        col.separator()

        # Section properties at design depth
        col.label(text=f"Water Depth: {ch.height:.2f} m")
        col.label(text=f"Area: {ch.hydraulic_area:.3f} m²")
        col.label(text=f"Wetted P: {ch.wetted_perimeter:.3f} m")
        col.label(text=f"Hydr. Radius: {ch.hydraulic_radius:.4f} m")

        if ch.top_width_water > 0:
            col.label(text=f"Top Width: {ch.top_width_water:.2f} m")

        col.separator()

        # Flow (Manning's equation)
        sub = col.column(align=True)
        sub.label(text="Manning's Flow:", icon="FORCE_VORTEX")
        sub.label(text=f"Velocity: {ch.manning_velocity:.3f} m/s")
        sub.label(text=f"Discharge: {ch.manning_discharge:.3f} m³/s")

        if ch.manning_discharge > 0:
            sub.label(text=f"Discharge: {ch.manning_discharge * 1000:.1f} L/s")

    def draw_mesh_section(self, layout, ch):
        """Draw mesh statistics box."""
        box = layout.box()
        row = box.row()
        row.label(text="Mesh Stats", icon="MESH_DATA")

        col = box.column(align=True)

        if ch.mesh_vertices > 0:
            col.label(text=f"Vertices: {ch.mesh_vertices:,}")
            col.label(text=f"Edges: {ch.mesh_edges:,}")
            col.label(text=f"Faces: {ch.mesh_faces:,}")
            col.label(text=f"Triangles: {ch.mesh_triangles:,}")

            col.separator()

            if ch.mesh_is_watertight:
                col.label(text=f"Volume: {ch.mesh_volume:.3f} m³")
            col.label(text=f"Surface: {ch.mesh_surface_area:.3f} m²")

            col.separator()

            # Status indicators
            row = col.row()
            if ch.mesh_is_manifold:
                row.label(text="Manifold", icon="CHECKMARK")
            else:
                row.label(text=f"Non-Manifold ({ch.mesh_non_manifold})", icon="ERROR")

            row = col.row()
            if ch.mesh_is_watertight:
                row.label(text="Watertight", icon="CHECKMARK")
            else:
                row.label(text="Not Watertight", icon="X")
        else:
            col.label(text="Click Refresh to calculate")


# Registration
classes = (
    CADHY_OT_RefreshChannelInfo,
    CADHY_PT_ChannelInfo,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
