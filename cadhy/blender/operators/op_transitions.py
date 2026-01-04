"""
Transition Operators Module
Operators for adding and removing section transitions.
"""

from bpy.props import IntProperty
from bpy.types import Operator


class CADHY_OT_AddTransition(Operator):
    """Add a new transition zone to vary section parameters along the channel"""

    bl_idname = "cadhy.add_transition"
    bl_label = "Add Transition"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.cadhy

        # Add new transition
        trans = settings.transitions.add()

        # Set default values based on existing transitions or channel length
        if len(settings.transitions) == 1:
            # First transition - start at beginning
            trans.start_station = 0.0
            trans.end_station = 10.0
        else:
            # Start after previous transition ends
            prev = settings.transitions[-2]
            trans.start_station = prev.end_station
            trans.end_station = prev.end_station + 10.0

        # Copy current section parameters as targets
        trans.target_bottom_width = settings.bottom_width
        trans.target_height = settings.height
        trans.target_side_slope = settings.side_slope

        # Set active index
        settings.active_transition_index = len(settings.transitions) - 1

        self.report({"INFO"}, f"Added transition {len(settings.transitions)}")
        return {"FINISHED"}


class CADHY_OT_RemoveTransition(Operator):
    """Remove a transition zone"""

    bl_idname = "cadhy.remove_transition"
    bl_label = "Remove Transition"
    bl_options = {"REGISTER", "UNDO"}

    index: IntProperty(
        name="Index",
        description="Index of transition to remove",
        default=0,
    )

    def execute(self, context):
        settings = context.scene.cadhy

        if 0 <= self.index < len(settings.transitions):
            settings.transitions.remove(self.index)

            # Adjust active index
            if settings.active_transition_index >= len(settings.transitions):
                settings.active_transition_index = max(0, len(settings.transitions) - 1)

            self.report({"INFO"}, "Removed transition")
        else:
            self.report({"WARNING"}, "Invalid transition index")

        return {"FINISHED"}


class CADHY_OT_ClearTransitions(Operator):
    """Remove all transition zones"""

    bl_idname = "cadhy.clear_transitions"
    bl_label = "Clear All Transitions"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.cadhy
        settings.transitions.clear()
        settings.active_transition_index = 0
        self.report({"INFO"}, "Cleared all transitions")
        return {"FINISHED"}
