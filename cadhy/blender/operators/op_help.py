"""
Help Operator
Provides in-app documentation and contextual help.
"""

import webbrowser

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator

# Documentation URLs
DOCS_BASE_URL = "https://github.com/crhistian-cornejo/cadhy-addon/wiki"
DOCS_URLS = {
    "main": f"{DOCS_BASE_URL}",
    "installation": f"{DOCS_BASE_URL}/Installation",
    "quick_start": f"{DOCS_BASE_URL}/Quick-Start",
    "channel": f"{DOCS_BASE_URL}/Channel-Creation",
    "cfd": f"{DOCS_BASE_URL}/CFD-Domain",
    "sections": f"{DOCS_BASE_URL}/Cross-Sections",
    "export": f"{DOCS_BASE_URL}/Export",
    "troubleshooting": f"{DOCS_BASE_URL}/Troubleshooting",
    "api": f"{DOCS_BASE_URL}/API-Reference",
    "changelog": "https://github.com/crhistian-cornejo/cadhy-addon/blob/main/CHANGELOG.md",
    "issues": "https://github.com/crhistian-cornejo/cadhy-addon/issues",
}


# Help texts for tooltips and inline help
HELP_TEXTS = {
    "bottom_width": (
        "Width at the bottom of the channel section. "
        "For circular sections, this is the diameter. "
        "Typical values: 0.5-10m for irrigation, 2-20m for drainage."
    ),
    "side_slope": (
        "Horizontal to vertical ratio (Z:1) for trapezoidal sections. "
        "Common values: 0.5 (steep), 1.0-1.5 (standard), 2.0+ (gentle). "
        "Steeper slopes require more stable soil or lining."
    ),
    "height": (
        "Design water depth (normal depth) of the channel. "
        "This is the depth at which the channel is designed to flow. "
        "Does not include freeboard."
    ),
    "freeboard": (
        "Additional height above design water level for safety. "
        "Prevents overtopping during surges or waves. "
        "Typical: 0.15-0.30m for small channels, 0.5-1.0m for large channels."
    ),
    "lining_thickness": (
        "Thickness of channel lining (concrete, geomembrane, etc.). "
        "Set to 0 for unlined (earth) channels. "
        "Typical concrete lining: 0.10-0.20m."
    ),
    "resolution_m": (
        "Sampling resolution along the channel axis in meters. "
        "Smaller values create denser mesh (more accurate but slower). "
        "Recommended: 0.5-2.0m for most channels."
    ),
    "subdivide_profile": (
        "Enable profile subdivision for uniform mesh density. "
        "When enabled, the section profile edges are subdivided to match "
        "the axis resolution, creating more uniform quad faces."
    ),
    "profile_resolution": (
        "Maximum edge length in the section profile. "
        "Set equal to axis resolution for approximately square faces. "
        "Smaller values create denser mesh across the section."
    ),
    "manning_n": (
        "Manning's roughness coefficient for flow calculations. "
        "Concrete: 0.012-0.015, Earth: 0.020-0.035, "
        "Vegetated: 0.030-0.050, Rock: 0.035-0.050."
    ),
    "cfd_water_level": (
        "Water level from channel bottom for CFD domain. "
        "Should not exceed channel height. "
        "The CFD domain will be filled to this level."
    ),
    "cfd_inlet_extension": (
        "Extension length at inlet for flow development. "
        "Allows flow to develop before reaching the study area. "
        "Typical: 2-5x hydraulic diameter."
    ),
    "cfd_outlet_extension": (
        "Extension length at outlet to prevent backflow. "
        "Prevents boundary condition issues at outlet. "
        "Typical: 5-10x hydraulic diameter."
    ),
}


class CADHY_OT_OpenDocs(Operator):
    """Open CADHY documentation in web browser"""

    bl_idname = "cadhy.open_docs"
    bl_label = "Open Documentation"
    bl_description = "Open CADHY documentation in your web browser"
    bl_options = {"REGISTER"}

    page: EnumProperty(
        name="Page",
        description="Documentation page to open",
        items=[
            ("main", "Main Wiki", "Open main documentation wiki"),
            ("installation", "Installation", "Installation guide"),
            ("quick_start", "Quick Start", "Quick start tutorial"),
            ("channel", "Channel Creation", "Channel creation guide"),
            ("cfd", "CFD Domain", "CFD domain generation guide"),
            ("sections", "Cross Sections", "Cross sections guide"),
            ("export", "Export", "Export options guide"),
            ("troubleshooting", "Troubleshooting", "Common issues and solutions"),
            ("api", "API Reference", "Python API documentation"),
            ("changelog", "Changelog", "Version history"),
            ("issues", "Report Issue", "Report a bug or request feature"),
        ],
        default="main",
    )

    def execute(self, context):
        url = DOCS_URLS.get(self.page, DOCS_BASE_URL)
        webbrowser.open(url)
        self.report({"INFO"}, f"Opened: {url}")
        return {"FINISHED"}


class CADHY_OT_ShowHelp(Operator):
    """Show help text for a specific topic"""

    bl_idname = "cadhy.show_help"
    bl_label = "Show Help"
    bl_description = "Show detailed help for this setting"
    bl_options = {"REGISTER"}

    topic: StringProperty(
        name="Topic",
        description="Help topic to display",
        default="",
    )

    def execute(self, context):
        if self.topic in HELP_TEXTS:
            # Show in info area
            self.report({"INFO"}, HELP_TEXTS[self.topic])
        else:
            self.report({"WARNING"}, f"No help available for: {self.topic}")
        return {"FINISHED"}

    def invoke(self, context, event):
        if self.topic in HELP_TEXTS:
            # Show popup dialog with help text
            return context.window_manager.invoke_popup(self, width=400)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        if self.topic in HELP_TEXTS:
            # Word wrap the help text
            text = HELP_TEXTS[self.topic]
            words = text.split()
            line = ""
            for word in words:
                if len(line) + len(word) > 50:
                    layout.label(text=line)
                    line = word
                else:
                    line = f"{line} {word}" if line else word
            if line:
                layout.label(text=line)


class CADHY_OT_ShowKeymap(Operator):
    """Show CADHY keyboard shortcuts"""

    bl_idname = "cadhy.show_keymap"
    bl_label = "Keyboard Shortcuts"
    bl_description = "Show all CADHY keyboard shortcuts"
    bl_options = {"REGISTER"}

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=350)

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=350)

    def draw(self, context):
        layout = self.layout
        layout.label(text="CADHY Keyboard Shortcuts", icon="KEYINGSET")
        layout.separator()

        col = layout.column(align=True)

        shortcuts = [
            ("Alt+C", "CADHY Pie Menu"),
            ("Alt+Shift+B", "Build Channel"),
            ("Alt+Shift+U", "Update Channel"),
            ("Alt+Shift+D", "Build CFD Domain"),
            ("Alt+Shift+S", "Generate Sections"),
        ]

        for key, action in shortcuts:
            row = col.row()
            row.label(text=key, icon="EVENT_RETURN")
            row.label(text=action)

        layout.separator()
        layout.operator("cadhy.open_docs", text="Full Documentation", icon="URL")


def get_help_text(topic: str) -> str:
    """Get help text for a topic."""
    return HELP_TEXTS.get(topic, "")


def draw_help_button(layout, topic: str):
    """Draw a small help button that shows help for the topic."""
    op = layout.operator("cadhy.show_help", text="", icon="QUESTION", emboss=False)
    op.topic = topic


# Registration
classes = (
    CADHY_OT_OpenDocs,
    CADHY_OT_ShowHelp,
    CADHY_OT_ShowKeymap,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
