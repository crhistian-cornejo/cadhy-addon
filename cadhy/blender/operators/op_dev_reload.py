"""
Dev Reload Operator
Operator to reload the addon during development.
"""

import bpy
import importlib
import sys
from bpy.types import Operator

from ...core.util.logging import log_info


class CADHY_OT_DevReload(Operator):
    """Reload CADHY addon for development"""
    bl_idname = "cadhy.dev_reload"
    bl_label = "Reload CADHY"
    bl_description = "Reload the CADHY addon (for development)"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return True
    
    def execute(self, context):
        """Execute the operator."""
        log_info("Reloading CADHY addon...")
        
        # Get all CADHY modules
        cadhy_modules = [name for name in sys.modules.keys() if name.startswith('cadhy')]
        
        # Sort by depth (deepest first) to reload in correct order
        cadhy_modules.sort(key=lambda x: x.count('.'), reverse=True)
        
        # Reload each module
        reloaded = 0
        for module_name in cadhy_modules:
            try:
                module = sys.modules[module_name]
                importlib.reload(module)
                reloaded += 1
            except Exception as e:
                self.report({'WARNING'}, f"Failed to reload {module_name}: {e}")
        
        self.report({'INFO'}, f"Reloaded {reloaded} CADHY modules")
        
        return {'FINISHED'}
