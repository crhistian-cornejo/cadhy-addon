"""
Unified CADHY Panel
Single consolidated panel with collapsible sections.
"""

import bpy
from bpy.types import Panel

from ..operators.op_presets import draw_presets_menu
from .pt_mesh_quality import get_quality_cache


def is_editing_channel(context):
    """Check if we're editing an existing CADHY channel."""
    obj = context.active_object
    if not obj or obj.type != "MESH":
        return False, None

    ch = getattr(obj, "cadhy_channel", None)
    if not ch:
        return False, None

    return ch.is_cadhy_object and ch.source_axis is not None, ch


def is_cadhy_channel(obj):
    """Check if object is a CADHY channel."""
    if not obj or obj.type != "MESH":
        return False
    ch = getattr(obj, "cadhy_channel", None)
    return ch is not None and ch.is_cadhy_object


class CADHY_PT_Unified(Panel):
    """Unified CADHY panel with collapsible sections"""

    bl_label = "CADHY"
    bl_idname = "CADHY_PT_Unified"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CADHY"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        settings = context.scene.cadhy
        obj = context.active_object

        # Check if we're editing an existing channel
        is_editing, ch = is_editing_channel(context)

        # ═══════════════════════════════════════════════════════════════════
        # SECTION: AXIS & BUILD
        # ═══════════════════════════════════════════════════════════════════
        self.draw_axis_section(context, layout, settings, is_editing, ch)

        # ═══════════════════════════════════════════════════════════════════
        # SECTION: SECTION PARAMETERS
        # ═══════════════════════════════════════════════════════════════════
        self.draw_section_params_section(context, layout, settings, is_editing, ch)

        # ═══════════════════════════════════════════════════════════════════
        # SECTION: CFD DOMAIN
        # ═══════════════════════════════════════════════════════════════════
        self.draw_cfd_section(context, layout, settings, obj)

        # ═══════════════════════════════════════════════════════════════════
        # SECTION: MESH QUALITY
        # ═══════════════════════════════════════════════════════════════════
        self.draw_mesh_quality_section(context, layout, settings, obj)

        # ═══════════════════════════════════════════════════════════════════
        # SECTION: CHANNEL INFO (only when channel selected)
        # ═══════════════════════════════════════════════════════════════════
        if is_cadhy_channel(obj):
            self.draw_channel_info_section(context, layout, settings, obj)

        # ═══════════════════════════════════════════════════════════════════
        # SECTION: CROSS-SECTIONS
        # ═══════════════════════════════════════════════════════════════════
        self.draw_sections_section(context, layout, settings)

        # ═══════════════════════════════════════════════════════════════════
        # SECTION: EXPORT
        # ═══════════════════════════════════════════════════════════════════
        self.draw_export_section(context, layout, settings, obj)

        # ═══════════════════════════════════════════════════════════════════
        # SECTION: RENDER
        # ═══════════════════════════════════════════════════════════════════
        self.draw_render_section(context, layout, settings)

    # ═══════════════════════════════════════════════════════════════════════
    # AXIS & BUILD SECTION
    # ═══════════════════════════════════════════════════════════════════════
    def draw_axis_section(self, context, layout, settings, is_editing, ch):
        """Draw axis selection and build section."""
        box = layout.box()

        # Header with collapse toggle
        row = box.row()
        row.prop(
            settings,
            "ui_show_axis",
            icon="TRIA_DOWN" if settings.ui_show_axis else "TRIA_RIGHT",
            icon_only=True,
            emboss=False,
        )
        row.label(text="Channel Build", icon="MOD_BUILD")

        if not settings.ui_show_axis:
            return

        col = box.column()

        if is_editing:
            # Edit mode info
            sub = col.box()
            sub.label(text=f"Editing: {context.active_object.name}", icon="MESH_DATA")
            if ch.source_axis:
                sub.label(text=f"Axis: {ch.source_axis.name}")
                if ch.total_length > 0:
                    sub.label(text=f"Length: {ch.total_length:.2f} m")

            # Update button
            row = col.row()
            row.scale_y = 1.3
            row.operator("cadhy.update_channel", text="Update Channel", icon="FILE_REFRESH")
        else:
            # Create mode
            sub = col.column(align=True)
            sub.label(text="Axis (Alignment):", icon="CURVE_DATA")
            sub.prop(settings, "axis_object", text="")

            if settings.axis_object:
                sub.label(text=f"Type: {settings.axis_object.type}")
            elif context.active_object and context.active_object.type == "CURVE":
                sub.label(text=f"Active: {context.active_object.name}", icon="INFO")
            else:
                sub.label(text="Select a curve as axis", icon="ERROR")

            col.separator()

            # Presets
            draw_presets_menu(col, context)

            col.separator()

            # Build buttons
            channel_exists = False
            if settings.axis_object:
                from ...core.util.naming import get_channel_name

                channel_name = get_channel_name(settings.axis_object.name)
                channel_exists = channel_name in bpy.data.objects

            row = col.row()
            row.scale_y = 1.3
            if channel_exists:
                row.operator("cadhy.build_channel", text="Rebuild Channel", icon="FILE_REFRESH")
            else:
                row.operator("cadhy.build_channel", text="Build Channel", icon="MOD_BUILD")

            # Station markers
            col.separator()
            row = col.row(align=True)
            row.operator("cadhy.create_station_markers", text="Stations", icon="ADD")
            row.operator("cadhy.clear_station_markers", text="", icon="X")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION PARAMETERS
    # ═══════════════════════════════════════════════════════════════════════
    def draw_section_params_section(self, context, layout, settings, is_editing, ch):
        """Draw section parameters."""
        box = layout.box()

        # Header with collapse toggle
        row = box.row()
        row.prop(
            settings,
            "ui_show_section_params",
            icon="TRIA_DOWN" if settings.ui_show_section_params else "TRIA_RIGHT",
            icon_only=True,
            emboss=False,
        )
        row.label(text="Section Parameters", icon="PREFERENCES")

        if not settings.ui_show_section_params:
            return

        # Source is either object properties (edit) or scene settings (create)
        source = ch if is_editing else settings
        section_type = ch.section_type if is_editing else settings.section_type

        col = box.column(align=True)

        # Section type
        col.prop(source, "section_type", text="Type")
        col.separator()

        # Type-specific parameters
        if section_type == "PIPE":
            col.prop(source, "pipe_material", text="Material")
            col.prop(source, "pipe_diameter", text="Diameter")
            if hasattr(source, "pipe_material"):
                if source.pipe_material == "HDPE":
                    col.prop(source, "pipe_sdr", text="SDR")
                elif source.pipe_material == "PVC":
                    col.prop(source, "pipe_schedule", text="Schedule")
        elif section_type == "CIRC":
            col.prop(source, "bottom_width", text="Diameter")
        elif section_type == "TRI":
            col.prop(source, "side_slope", text="Side Slope")
        else:
            col.prop(source, "bottom_width", text="Bottom Width")

        if section_type == "TRAP":
            col.prop(source, "side_slope", text="Side Slope")

        if section_type not in ("PIPE", "CIRC"):
            col.prop(source, "height", text="Height")
            col.prop(source, "freeboard", text="Freeboard")

        col.separator()

        if section_type != "PIPE":
            col.prop(source, "lining_thickness", text="Lining")

        col.prop(source, "resolution_m", text="Resolution")

        # Subdivide options
        col.separator()
        row = col.row(align=True)
        row.prop(source, "subdivide_profile", text="Subdivide")
        if getattr(source, "subdivide_profile", True):
            row.prop(source, "profile_resolution", text="")
            # Hint if profile_resolution differs from resolution_m
            res_m = getattr(source, "resolution_m", 1.0)
            prof_res = getattr(source, "profile_resolution", 1.0)
            if abs(res_m - prof_res) > 0.01:
                col.label(text=f"Match to {res_m:.1f}m for square faces", icon="INFO")

    # ═══════════════════════════════════════════════════════════════════════
    # CFD DOMAIN SECTION
    # ═══════════════════════════════════════════════════════════════════════
    def draw_cfd_section(self, context, layout, settings, obj):
        """Draw CFD domain section."""
        box = layout.box()

        # Header with collapse toggle and enable checkbox on right
        row = box.row()
        row.prop(
            settings,
            "ui_show_cfd",
            icon="TRIA_DOWN" if settings.ui_show_cfd else "TRIA_RIGHT",
            icon_only=True,
            emboss=False,
        )
        row.label(text="CFD Domain", icon="MOD_FLUIDSIM")
        row.prop(settings, "cfd_enabled", text="")

        if not settings.ui_show_cfd:
            return

        col = box.column()
        col.enabled = settings.cfd_enabled

        # CFD domain status
        cfd_domain_exists = False
        if settings.axis_object:
            from ...core.util.naming import get_cfd_domain_name

            cfd_domain_name = get_cfd_domain_name(settings.axis_object.name)
            cfd_domain_exists = cfd_domain_name in bpy.data.objects
            if cfd_domain_exists:
                col.label(text=f"Domain: {cfd_domain_name}", icon="CHECKMARK")

        # Build button
        row = col.row()
        row.scale_y = 1.2
        if cfd_domain_exists:
            row.operator("cadhy.build_cfd_domain", text="Rebuild CFD", icon="FILE_REFRESH")
        else:
            row.operator("cadhy.build_cfd_domain", text="Build CFD Domain", icon="MOD_FLUIDSIM")

        # Mesh settings
        col.separator()
        sub = col.column(align=True)
        sub.label(text="Mesh:", icon="MESH_GRID")
        sub.prop(settings, "cfd_mesh_type", text="")
        sub.prop(settings, "cfd_mesh_size", text="Size")

        # Note: mesh type applies when building/rebuilding CFD domain
        if cfd_domain_exists:
            cfd_obj = bpy.data.objects.get(cfd_domain_name)
            if cfd_obj and hasattr(cfd_obj, "cadhy_cfd"):
                current_type = cfd_obj.cadhy_cfd.mesh_type
                if current_type != settings.cfd_mesh_type:
                    sub.label(text="Rebuild to apply type", icon="INFO")

        # Boundary conditions (compact)
        col.separator()
        sub = col.column(align=True)
        sub.label(text="Boundary Conditions:", icon="OUTLINER_DATA_MESH")
        row = sub.row(align=True)
        row.prop(settings, "bc_inlet_type", text="")
        if settings.bc_inlet_type == "VELOCITY":
            row.prop(settings, "bc_inlet_velocity", text="")
        row = sub.row(align=True)
        row.prop(settings, "bc_outlet_type", text="")
        row = sub.row(align=True)
        row.prop(settings, "bc_wall_type", text="")
        row = sub.row(align=True)
        row.prop(settings, "bc_top_type", text="")

        # Validation status (if CFD domain selected)
        if obj and obj.type == "MESH" and hasattr(obj, "cadhy_cfd") and obj.cadhy_cfd.is_cadhy_object:
            cfd = obj.cadhy_cfd
            col.separator()
            sub = col.column(align=True)
            row = sub.row()
            if cfd.is_watertight:
                row.label(text="Watertight", icon="CHECKMARK")
            else:
                row.label(text="Not Watertight", icon="ERROR")
            row = sub.row()
            if cfd.non_manifold_edges == 0:
                row.label(text="Manifold", icon="CHECKMARK")
            else:
                row.label(text=f"{cfd.non_manifold_edges} non-manifold", icon="ERROR")
            if cfd.volume > 0:
                sub.label(text=f"Volume: {cfd.volume:.3f} m³")

    # ═══════════════════════════════════════════════════════════════════════
    # MESH QUALITY SECTION
    # ═══════════════════════════════════════════════════════════════════════
    def draw_mesh_quality_section(self, context, layout, settings, obj):
        """Draw CFD mesh quality section."""
        # Only show when mesh is selected
        if not obj or obj.type != "MESH":
            return

        box = layout.box()

        # Header with collapse toggle
        row = box.row()
        row.prop(
            settings,
            "ui_show_mesh_quality",
            icon="TRIA_DOWN" if settings.ui_show_mesh_quality else "TRIA_RIGHT",
            icon_only=True,
            emboss=False,
        )
        row.label(text="Mesh Quality", icon="MESH_GRID")

        if not settings.ui_show_mesh_quality:
            return

        col = box.column()

        # Analyze button
        row = col.row()
        row.operator("cadhy.analyze_mesh_quality", text="Analyze", icon="VIEWZOOM")

        # Check if we have cached results
        quality_cache = get_quality_cache()
        if obj.name not in quality_cache:
            col.label(text="Click Analyze to calculate", icon="INFO")
            return

        quality = quality_cache[obj.name]

        # Rating
        rating = quality.quality_rating
        if rating == "Excellent":
            icon = "CHECKMARK"
        elif rating == "Good":
            icon = "FILE_TICK"
        elif rating == "Fair":
            icon = "ERROR"
        else:
            icon = "CANCEL"

        row = col.row()
        row.label(text=f"Rating: {rating}", icon=icon)

        # Compact metrics
        sub = col.column(align=True)
        sub.scale_y = 0.9

        # Skewness
        skew_icon = "CHECKMARK" if quality.skewness_max < 0.65 else "ERROR" if quality.skewness_max > 0.85 else "INFO"
        sub.label(text=f"Skewness: {quality.skewness_max:.3f}", icon=skew_icon)

        # Aspect ratio
        if quality.aspect_ratio_max < 10:
            aspect_icon = "CHECKMARK"
        elif quality.aspect_ratio_max > 100:
            aspect_icon = "ERROR"
        else:
            aspect_icon = "INFO"
        sub.label(text=f"Aspect: {quality.aspect_ratio_max:.1f}", icon=aspect_icon)

        # Non-orthogonality
        ortho_icon = "CHECKMARK" if quality.non_ortho_max < 50 else "ERROR" if quality.non_ortho_max > 70 else "INFO"
        sub.label(text=f"Non-Ortho: {quality.non_ortho_max:.1f}°", icon=ortho_icon)

        # Face counts
        sub.separator()
        sub.label(text=f"Faces: {quality.total_faces} (T:{quality.triangles} Q:{quality.quads})")

    # ═══════════════════════════════════════════════════════════════════════
    # CHANNEL INFO SECTION
    # ═══════════════════════════════════════════════════════════════════════
    def draw_channel_info_section(self, context, layout, settings, obj):
        """Draw channel info section."""
        ch = obj.cadhy_channel

        box = layout.box()

        # Header with collapse toggle
        row = box.row()
        row.prop(
            settings,
            "ui_show_channel_info",
            icon="TRIA_DOWN" if settings.ui_show_channel_info else "TRIA_RIGHT",
            icon_only=True,
            emboss=False,
        )
        row.label(text="Channel Info", icon="INFO")

        if not settings.ui_show_channel_info:
            return

        col = box.column()

        # Refresh button
        row = col.row(align=True)
        row.operator("cadhy.refresh_channel_info", text="Refresh", icon="FILE_REFRESH")
        row.operator("cadhy.export_channel_excel", text="Excel", icon="FILE")

        # Geometry
        sub = col.column(align=True)
        sub.scale_y = 0.9
        sub.label(text=f"Section: {ch.section_type}")
        sub.label(text=f"Length: {ch.total_length:.2f} m")

        if ch.slope_percent > 0:
            sub.label(text=f"Slope: {ch.slope_percent:.3f} %")

        # Hydraulics
        if ch.hydraulic_area > 0:
            sub.separator()
            sub.label(text=f"Area: {ch.hydraulic_area:.3f} m²")
            sub.label(text=f"Velocity: {ch.manning_velocity:.3f} m/s")
            sub.label(text=f"Discharge: {ch.manning_discharge:.3f} m³/s")

        # Mesh stats
        if ch.mesh_vertices > 0:
            sub.separator()
            sub.label(text=f"Verts: {ch.mesh_vertices:,} | Faces: {ch.mesh_faces:,}")
            row = sub.row()
            if ch.mesh_is_manifold:
                row.label(text="Manifold", icon="CHECKMARK")
            else:
                row.label(text="Non-Manifold", icon="ERROR")

    # ═══════════════════════════════════════════════════════════════════════
    # CROSS-SECTIONS
    # ═══════════════════════════════════════════════════════════════════════
    def draw_sections_section(self, context, layout, settings):
        """Draw cross-sections generation section."""
        box = layout.box()

        # Header with collapse toggle
        row = box.row()
        row.prop(
            settings,
            "ui_show_sections",
            icon="TRIA_DOWN" if settings.ui_show_sections else "TRIA_RIGHT",
            icon_only=True,
            emboss=False,
        )
        row.label(text="Cross-Sections", icon="SNAP_MIDPOINT")

        if not settings.ui_show_sections:
            return

        col = box.column(align=True)

        # Station range
        col.prop(settings, "sections_start", text="Start")
        col.prop(settings, "sections_end", text="End (0=auto)")
        col.prop(settings, "sections_step", text="Step")

        # Generate button
        col.separator()
        row = col.row()
        row.scale_y = 1.2
        row.operator("cadhy.generate_sections", text="Generate", icon="SNAP_MIDPOINT")

        # Section count
        if "CADHY_Sections" in bpy.data.collections:
            collection = bpy.data.collections["CADHY_Sections"]
            count = len(collection.objects)
            col.label(text=f"Generated: {count} sections")

    # ═══════════════════════════════════════════════════════════════════════
    # EXPORT SECTION
    # ═══════════════════════════════════════════════════════════════════════
    def draw_export_section(self, context, layout, settings, obj):
        """Draw export section."""
        box = layout.box()

        # Header with collapse toggle
        row = box.row()
        row.prop(
            settings,
            "ui_show_export",
            icon="TRIA_DOWN" if settings.ui_show_export else "TRIA_RIGHT",
            icon_only=True,
            emboss=False,
        )
        row.label(text="Export", icon="EXPORT")

        if not settings.ui_show_export:
            return

        col = box.column()

        # Export path
        col.prop(settings, "export_path", text="")

        # Format selection
        col.prop(settings, "export_format", text="Format")

        # Export buttons - 3D mesh export only
        # PDF/JSON reports are in the Pie Menu (Alt+C) under Reports
        col.separator()
        row = col.row(align=True)
        row.operator("cadhy.export_cfd", text="CFD Mesh", icon="EXPORT")
        row.operator("cadhy.export_cfd_template", text="Template", icon="PRESET")

        col.separator()
        row = col.row()
        row.scale_y = 1.2
        row.operator("cadhy.export_all", text="Export All", icon="PACKAGE")

    # ═══════════════════════════════════════════════════════════════════════
    # RENDER SECTION
    # ═══════════════════════════════════════════════════════════════════════
    def draw_render_section(self, context, layout, settings):
        """Draw render section."""
        box = layout.box()

        # Header with collapse toggle
        row = box.row()
        row.prop(
            settings,
            "ui_show_render",
            icon="TRIA_DOWN" if settings.ui_show_render else "TRIA_RIGHT",
            icon_only=True,
            emboss=False,
        )
        row.label(text="Render", icon="RENDER_STILL")

        if not settings.ui_show_render:
            return

        col = box.column()

        # Material buttons
        row = col.row(align=True)
        op = row.operator("cadhy.assign_materials", text="Concrete")
        op.material = "CONCRETE"
        op = row.operator("cadhy.assign_materials", text="Water")
        op.material = "WATER"

        row = col.row(align=True)
        op = row.operator("cadhy.assign_materials", text="Earth")
        op.material = "EARTH"
        op = row.operator("cadhy.assign_materials", text="Steel")
        op.material = "STEEL"

        col.separator()

        # Render setup
        row = col.row()
        row.operator("cadhy.setup_render", text="Setup Scene", icon="SCENE")

        # Shading
        row = col.row(align=True)
        row.operator("cadhy.toggle_shading", text="Solid").type = "SOLID"
        row.operator("cadhy.toggle_shading", text="Material").type = "MATERIAL"
        row.operator("cadhy.toggle_shading", text="Rendered").type = "RENDERED"
