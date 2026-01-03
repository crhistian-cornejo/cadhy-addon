"""
CADHY - Blender Add-on for Hydraulic Infrastructure Modeling
Toolkit for parametric modeling of hydraulic infrastructure within Blender.
"""

bl_info = {
    "name": "CADHY",
    "author": "CADHY Team",
    "version": (0, 1, 1),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > CADHY",
    "description": "Parametric modeling toolkit for hydraulic infrastructure and CFD domain generation",
    "warning": "",
    "doc_url": "https://cadhy.app/docs",
    "tracker_url": "https://github.com/cadhy/cadhy-addon/issues",
    "category": "3D View",
}

from . import register as reg


def register():
    """Register all addon classes and properties."""
    reg.register()


def unregister():
    """Unregister all addon classes and properties."""
    reg.unregister()


if __name__ == "__main__":
    register()
