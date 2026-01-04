"""
Project Wizard Operator
Guided step-by-step project creation for CADHY channels.
Provides a modal dialog that walks users through the setup process.
"""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import Operator

from ...core.util.naming import COLLECTION_CHANNELS


class CADHY_OT_ProjectWizard(Operator):
    """Guided wizard for creating new CADHY channel projects"""

    bl_idname = "cadhy.project_wizard"
    bl_label = "New Channel Project"
    bl_description = "Step-by-step wizard to create a new channel project"
    bl_options = {"REGISTER", "UNDO"}

    # =========================================================================
    # WIZARD STEP TRACKING
    # =========================================================================

    step: IntProperty(
        name="Step",
        default=1,
        min=1,
        max=4,
    )

    # =========================================================================
    # STEP 1: PROJECT INFO
    # =========================================================================

    project_name: StringProperty(
        name="Project Name",
        description="Name for the channel project",
        default="Canal_001",
    )

    project_description: StringProperty(
        name="Description",
        description="Brief description of the project",
        default="",
    )

    # =========================================================================
    # STEP 2: AXIS CREATION
    # =========================================================================

    axis_mode: EnumProperty(
        name="Axis Mode",
        description="How to create the channel axis",
        items=[
            ("NEW_STRAIGHT", "New Straight", "Create a new straight axis curve"),
            ("NEW_CURVED", "New Curved", "Create a new curved/meandering axis"),
            ("EXISTING", "Use Existing", "Use an existing curve in the scene"),
        ],
        default="NEW_STRAIGHT",
    )

    axis_length: FloatProperty(
        name="Length",
        description="Total length of the channel axis",
        default=100.0,
        min=1.0,
        max=10000.0,
        unit="LENGTH",
    )

    axis_slope: FloatProperty(
        name="Slope",
        description="Longitudinal slope (% grade)",
        default=1.0,
        min=0.0,
        max=50.0,
        subtype="PERCENTAGE",
    )

    axis_curves: IntProperty(
        name="Curves",
        description="Number of curves for meandering axis",
        default=2,
        min=0,
        max=10,
    )

    # =========================================================================
    # STEP 3: SECTION PARAMETERS
    # =========================================================================

    section_preset: EnumProperty(
        name="Preset",
        description="Quick section preset",
        items=[
            ("IRRIGATION_SMALL", "Irrigation (Small)", "0.5m x 0.5m trapezoidal"),
            ("IRRIGATION_MEDIUM", "Irrigation (Medium)", "1.5m x 1.0m trapezoidal"),
            ("DRAINAGE_URBAN", "Urban Drainage", "2.0m x 1.5m rectangular"),
            ("COLLECTOR_PIPE", "Collector Pipe", "600mm HDPE pipe"),
            ("CUSTOM", "Custom", "Define custom parameters"),
        ],
        default="IRRIGATION_MEDIUM",
    )

    custom_section_type: EnumProperty(
        name="Section Type",
        items=[
            ("TRAP", "Trapezoidal", ""),
            ("RECT", "Rectangular", ""),
            ("PIPE", "Pipe", ""),
        ],
        default="TRAP",
    )

    custom_width: FloatProperty(
        name="Width",
        default=2.0,
        min=0.1,
        max=50.0,
        unit="LENGTH",
    )

    custom_height: FloatProperty(
        name="Height",
        default=1.5,
        min=0.1,
        max=20.0,
        unit="LENGTH",
    )

    custom_slope: FloatProperty(
        name="Side Slope",
        default=1.5,
        min=0.0,
        max=5.0,
    )

    # =========================================================================
    # STEP 4: OPTIONS
    # =========================================================================

    create_cfd_domain: BoolProperty(
        name="Create CFD Domain",
        description="Also create CFD domain for simulation",
        default=False,
    )

    generate_sections: BoolProperty(
        name="Generate Cross-Sections",
        description="Generate cross-section curves",
        default=False,
    )

    auto_build: BoolProperty(
        name="Build Immediately",
        description="Build the channel after wizard completes",
        default=True,
    )

    # =========================================================================
    # OPERATOR METHODS
    # =========================================================================

    def invoke(self, context, event):
        self.step = 1
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout

        # Progress indicator
        row = layout.row()
        for i in range(1, 5):
            col = row.column()
            if i == self.step:
                col.label(text=f"[{i}]", icon="RADIOBUT_ON")
            elif i < self.step:
                col.label(text=f" {i} ", icon="CHECKMARK")
            else:
                col.label(text=f" {i} ", icon="RADIOBUT_OFF")

        layout.separator()

        if self.step == 1:
            self._draw_step1(layout)
        elif self.step == 2:
            self._draw_step2(layout)
        elif self.step == 3:
            self._draw_step3(layout)
        elif self.step == 4:
            self._draw_step4(layout)

        layout.separator()

        # Navigation buttons
        row = layout.row()
        if self.step > 1:
            row.operator("cadhy.wizard_prev", text="Back", icon="BACK")
        else:
            row.label(text="")  # Spacer

        if self.step < 4:
            row.operator("cadhy.wizard_next", text="Next", icon="FORWARD")
        else:
            row.operator("cadhy.wizard_finish", text="Create Project", icon="CHECKMARK")

    def _draw_step1(self, layout):
        """Draw Step 1: Project Info"""
        layout.label(text="Step 1: Project Information", icon="FILE_NEW")
        box = layout.box()
        box.prop(self, "project_name")
        box.prop(self, "project_description")

    def _draw_step2(self, layout):
        """Draw Step 2: Axis Creation"""
        layout.label(text="Step 2: Channel Axis", icon="CURVE_DATA")
        box = layout.box()
        box.prop(self, "axis_mode")

        if self.axis_mode in ("NEW_STRAIGHT", "NEW_CURVED"):
            box.prop(self, "axis_length")
            box.prop(self, "axis_slope")

            if self.axis_mode == "NEW_CURVED":
                box.prop(self, "axis_curves")
        else:
            box.label(text="Select curve after wizard completes", icon="INFO")

    def _draw_step3(self, layout):
        """Draw Step 3: Section Parameters"""
        layout.label(text="Step 3: Section Type", icon="MESH_PLANE")
        box = layout.box()
        box.prop(self, "section_preset")

        if self.section_preset == "CUSTOM":
            sub = box.box()
            sub.prop(self, "custom_section_type")
            sub.prop(self, "custom_width")
            sub.prop(self, "custom_height")
            if self.custom_section_type == "TRAP":
                sub.prop(self, "custom_slope")

    def _draw_step4(self, layout):
        """Draw Step 4: Options"""
        layout.label(text="Step 4: Additional Options", icon="PREFERENCES")
        box = layout.box()
        box.prop(self, "auto_build")
        box.prop(self, "create_cfd_domain")
        box.prop(self, "generate_sections")

        # Summary
        layout.label(text="Summary:", icon="INFO")
        summary = layout.box()
        summary.label(text=f"Project: {self.project_name}")
        summary.label(text=f"Axis: {self.axis_mode.replace('_', ' ').title()}")
        if self.axis_mode != "EXISTING":
            summary.label(text=f"Length: {self.axis_length:.1f}m @ {self.axis_slope:.1f}% slope")
        summary.label(text=f"Section: {self.section_preset.replace('_', ' ').title()}")

    def execute(self, context):
        """Execute the wizard - create the project."""
        settings = context.scene.cadhy

        # Apply section preset
        presets = {
            "IRRIGATION_SMALL": ("TRAP", 0.5, 0.5, 1.0, 0.1, 0.1),
            "IRRIGATION_MEDIUM": ("TRAP", 1.5, 1.0, 1.5, 0.2, 0.15),
            "DRAINAGE_URBAN": ("RECT", 2.0, 1.5, 0.0, 0.3, 0.2),
            "COLLECTOR_PIPE": ("PIPE", 0.6, 0.6, 0.0, 0.0, 0.03),
        }

        if self.section_preset in presets:
            sec_type, width, height, slope, fb, lining = presets[self.section_preset]
            settings.section_type = sec_type
            settings.bottom_width = width
            settings.height = height
            settings.side_slope = slope
            settings.freeboard = fb
            settings.lining_thickness = lining
        elif self.section_preset == "CUSTOM":
            settings.section_type = self.custom_section_type
            settings.bottom_width = self.custom_width
            settings.height = self.custom_height
            settings.side_slope = self.custom_slope

        # Create axis curve
        if self.axis_mode in ("NEW_STRAIGHT", "NEW_CURVED"):
            curve = self._create_axis_curve(context)
            if curve:
                settings.axis_object = curve

        # Build channel if requested
        if self.auto_build and settings.axis_object:
            bpy.ops.cadhy.build_channel()

            # Additional operations
            if self.create_cfd_domain:
                bpy.ops.cadhy.build_cfd_domain()

            if self.generate_sections:
                bpy.ops.cadhy.generate_sections()

        self.report({"INFO"}, f"Project '{self.project_name}' created successfully")
        return {"FINISHED"}

    def _create_axis_curve(self, context) -> bpy.types.Object:
        """Create axis curve based on wizard settings."""
        import math

        # Create curve data
        curve_data = bpy.data.curves.new(name=f"{self.project_name}_Axis", type="CURVE")
        curve_data.dimensions = "3D"

        # Create spline
        spline = curve_data.splines.new("BEZIER")

        length = self.axis_length
        slope_rad = math.atan(self.axis_slope / 100)
        drop = length * math.tan(slope_rad)

        if self.axis_mode == "NEW_STRAIGHT":
            # Simple straight line with slope
            spline.bezier_points.add(1)  # Start + 1 = 2 points

            spline.bezier_points[0].co = (0, 0, 0)
            spline.bezier_points[0].handle_left = (-length * 0.1, 0, 0)
            spline.bezier_points[0].handle_right = (length * 0.1, 0, 0)

            spline.bezier_points[1].co = (length, 0, -drop)
            spline.bezier_points[1].handle_left = (length - length * 0.1, 0, -drop)
            spline.bezier_points[1].handle_right = (length + length * 0.1, 0, -drop)

        elif self.axis_mode == "NEW_CURVED":
            # S-curve with multiple points
            n_curves = max(1, self.axis_curves)
            n_points = n_curves * 2 + 1
            spline.bezier_points.add(n_points - 1)

            segment_length = length / n_points
            amplitude = length * 0.1  # Curve amplitude

            for i in range(n_points):
                x = i * segment_length
                z = -x * math.tan(slope_rad)

                # Alternate Y for S-curve
                if i % 2 == 1:
                    y = amplitude * (1 if (i // 2) % 2 == 0 else -1)
                else:
                    y = 0

                pt = spline.bezier_points[i]
                pt.co = (x, y, z)
                pt.handle_type_left = "AUTO"
                pt.handle_type_right = "AUTO"

        # Create object
        curve_obj = bpy.data.objects.new(f"{self.project_name}_Axis", curve_data)

        # Add to collection
        if COLLECTION_CHANNELS in bpy.data.collections:
            bpy.data.collections[COLLECTION_CHANNELS].objects.link(curve_obj)
        else:
            context.collection.objects.link(curve_obj)

        return curve_obj


class CADHY_OT_WizardNext(Operator):
    """Go to next wizard step"""

    bl_idname = "cadhy.wizard_next"
    bl_label = "Next"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        # Find the wizard operator and increment step
        # This is a placeholder - actual implementation would use operator properties
        return {"FINISHED"}


class CADHY_OT_WizardPrev(Operator):
    """Go to previous wizard step"""

    bl_idname = "cadhy.wizard_prev"
    bl_label = "Back"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        return {"FINISHED"}


class CADHY_OT_WizardFinish(Operator):
    """Finish wizard and create project"""

    bl_idname = "cadhy.wizard_finish"
    bl_label = "Create Project"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        return {"FINISHED"}


# =============================================================================
# BATCH OPERATIONS
# =============================================================================


class CADHY_OT_BatchBuild(Operator):
    """Build multiple channel variants from current settings"""

    bl_idname = "cadhy.batch_build"
    bl_label = "Batch Build Channels"
    bl_description = "Generate multiple channel variants with different parameters"
    bl_options = {"REGISTER", "UNDO"}

    width_variants: IntProperty(
        name="Width Variants",
        description="Number of width variations to generate",
        default=3,
        min=1,
        max=10,
    )

    width_range: FloatProperty(
        name="Width Range (+/-)",
        description="Range of width variation (±)",
        default=0.5,
        min=0.1,
        max=5.0,
        unit="LENGTH",
    )

    height_variants: IntProperty(
        name="Height Variants",
        description="Number of height variations to generate",
        default=1,
        min=1,
        max=10,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        settings = context.scene.cadhy
        base_width = settings.bottom_width
        axis_obj = settings.axis_object

        if not axis_obj:
            self.report({"ERROR"}, "No axis curve selected")
            return {"CANCELLED"}

        variants_created = 0

        # Calculate width steps
        width_step = (2 * self.width_range) / max(1, self.width_variants - 1)
        widths = [base_width - self.width_range + i * width_step for i in range(self.width_variants)]

        for i, width in enumerate(widths):
            # Set width
            settings.bottom_width = width

            # Build channel
            bpy.ops.cadhy.build_channel()

            # Rename the created channel
            for obj in context.selected_objects:
                if obj.type == "MESH" and "CADHY" in obj.name:
                    obj.name = f"Channel_W{width:.2f}"
                    variants_created += 1
                    break

        # Restore original width
        settings.bottom_width = base_width

        self.report({"INFO"}, f"Created {variants_created} channel variants")
        return {"FINISHED"}


class CADHY_OT_BatchExport(Operator):
    """Export all CADHY channels in the scene"""

    bl_idname = "cadhy.batch_export"
    bl_label = "Batch Export Channels"
    bl_description = "Export all channels to selected formats"
    bl_options = {"REGISTER"}

    export_stl: BoolProperty(
        name="Export STL",
        default=True,
    )

    export_obj: BoolProperty(
        name="Export OBJ",
        default=False,
    )

    export_reports: BoolProperty(
        name="Export Reports",
        default=True,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        import os

        settings = context.scene.cadhy
        export_path = bpy.path.abspath(settings.export_path) if settings.export_path else "/tmp"

        exported = 0

        # Find all CADHY channels
        for obj in bpy.data.objects:
            if obj.type == "MESH" and hasattr(obj, "cadhy_channel"):
                ch = obj.cadhy_channel
                if ch.source_axis:  # Is a CADHY channel
                    base_name = obj.name.replace(" ", "_")

                    if self.export_stl:
                        filepath = os.path.join(export_path, f"{base_name}.stl")
                        bpy.ops.object.select_all(action="DESELECT")
                        obj.select_set(True)
                        context.view_layer.objects.active = obj
                        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)
                        exported += 1

                    if self.export_obj:
                        filepath = os.path.join(export_path, f"{base_name}.obj")
                        bpy.ops.object.select_all(action="DESELECT")
                        obj.select_set(True)
                        context.view_layer.objects.active = obj
                        bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True)
                        exported += 1

        self.report({"INFO"}, f"Exported {exported} files to {export_path}")
        return {"FINISHED"}


# =============================================================================
# REGISTRATION
# =============================================================================

classes = (
    CADHY_OT_ProjectWizard,
    CADHY_OT_WizardNext,
    CADHY_OT_WizardPrev,
    CADHY_OT_WizardFinish,
    CADHY_OT_BatchBuild,
    CADHY_OT_BatchExport,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
