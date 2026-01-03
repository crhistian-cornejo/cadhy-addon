"""
Main Panel
Primary CADHY panel for channel creation and parametric editing.
"""

import bpy
from bpy.types import Panel


def is_editing_channel(context):
    """Check if we're editing an existing CADHY channel."""
    obj = context.active_object
    if not obj or obj.type != "MESH":
        return False, None

    ch = getattr(obj, "cadhy_channel", None)
    if not ch:
        return False, None

    return ch.is_cadhy_object and ch.source_axis is not None, ch


class CADHY_PT_Main(Panel):
    """Main CADHY panel for channel generation"""

    bl_label = "CADHY - Main"
    bl_idname = "CADHY_PT_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CADHY"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        settings = context.scene.cadhy

        # Check if we're editing an existing channel
        is_editing, ch = is_editing_channel(context)

        if is_editing:
            # EDIT MODE: Show channel properties from object
            self.draw_edit_mode(context, layout, ch)
        else:
            # CREATE MODE: Show scene settings for new channel
            self.draw_create_mode(context, layout, settings)

    def draw_create_mode(self, context, layout, settings):
        """Draw UI for creating a new channel."""
        # Axis Selection
        box = layout.box()
        box.label(text="Axis (Alignment)", icon="CURVE_DATA")

        row = box.row()
        row.prop(settings, "axis_object", text="")

        if settings.axis_object:
            row = box.row()
            row.label(text=f"Type: {settings.axis_object.type}")

            # Check if channel exists for this axis
            from ...core.util.naming import get_channel_name

            channel_name = get_channel_name(settings.axis_object.name)
            channel_exists = channel_name in bpy.data.objects

            if channel_exists:
                row = box.row()
                row.label(text=f"Channel: {channel_name}", icon="CHECKMARK")
        elif context.active_object and context.active_object.type == "CURVE":
            row = box.row()
            row.label(text=f"Active: {context.active_object.name}", icon="INFO")
        else:
            row = box.row()
            row.label(text="Select a curve as axis", icon="ERROR")

        layout.separator()

        # Section Type
        box = layout.box()
        box.label(text="Section Type", icon="MESH_PLANE")
        box.prop(settings, "section_type", text="")

        layout.separator()

        # Section Parameters
        self.draw_section_params(layout, settings, settings.section_type)

        layout.separator()

        # Build Button
        channel_exists = False
        if settings.axis_object:
            from ...core.util.naming import get_channel_name

            channel_name = get_channel_name(settings.axis_object.name)
            channel_exists = channel_name in bpy.data.objects

        row = layout.row(align=True)
        row.scale_y = 1.5
        if channel_exists:
            row.operator("cadhy.build_channel", text="Rebuild Channel", icon="FILE_REFRESH")
        else:
            row.operator("cadhy.build_channel", text="Build Channel", icon="MOD_BUILD")

        # Quick CFD build
        if settings.cfd_enabled:
            row = layout.row(align=True)
            row.operator("cadhy.build_cfd_domain", text="Build CFD Domain", icon="MOD_FLUIDSIM")

    def draw_edit_mode(self, context, layout, ch):
        """Draw UI for editing an existing channel."""
        obj = context.active_object

        # Channel Info Header
        box = layout.box()
        row = box.row()
        row.label(text="Editing Channel", icon="MESH_DATA")

        col = box.column(align=True)
        col.label(text=f"Object: {obj.name}")

        if ch.source_axis:
            col.label(text=f"Axis: {ch.source_axis.name}")
            if ch.total_length > 0:
                col.label(text=f"Length: {ch.total_length:.2f} m")
        else:
            row = col.row()
            row.alert = True
            row.label(text="Source axis missing!", icon="ERROR")

        layout.separator()

        # Section Type (editable)
        box = layout.box()
        box.label(text="Section Type", icon="MESH_PLANE")
        box.prop(ch, "section_type", text="")

        layout.separator()

        # Section Parameters (from object)
        self.draw_section_params(layout, ch, ch.section_type)

        layout.separator()

        # Update Button
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("cadhy.update_channel", text="Update Channel", icon="FILE_REFRESH")

        # Option to select source axis
        if ch.source_axis:
            row = layout.row()
            row.operator("object.select_all", text="Select Axis", icon="CURVE_DATA")

            # Alternative: direct selection button
            row = layout.row()
            row.prop(ch, "source_axis", text="Axis")

    def draw_section_params(self, layout, source, section_type):
        """Draw section parameters from either scene settings or object properties."""
        box = layout.box()
        box.label(text="Section Parameters", icon="PREFERENCES")

        col = box.column(align=True)

        if section_type == "CIRC":
            col.prop(source, "bottom_width", text="Diameter")
        else:
            col.prop(source, "bottom_width", text="Bottom Width")

        if section_type == "TRAP":
            col.prop(source, "side_slope", text="Side Slope (H:V)")

        col.prop(source, "height", text="Height")
        col.prop(source, "freeboard", text="Freeboard")

        col.separator()
        col.prop(source, "lining_thickness", text="Lining Thickness")
        col.prop(source, "resolution_m", text="Resolution (m)")

        # Calculated values for trapezoidal
        if section_type == "TRAP":
            total_height = source.height + source.freeboard
            top_width = source.bottom_width + 2 * source.side_slope * total_height

            box.separator()
            sub = box.column(align=True)
            sub.label(text=f"Top Width: {top_width:.2f} m")
            sub.label(text=f"Total Height: {total_height:.2f} m")
