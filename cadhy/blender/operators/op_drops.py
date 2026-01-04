"""
Drop Structure Operators Module
Operators for adding and removing drop structures.
"""

from bpy.props import IntProperty
from bpy.types import Operator


class CADHY_OT_AddDrop(Operator):
    """Add a new drop structure at a station along the channel"""

    bl_idname = "cadhy.add_drop"
    bl_label = "Add Drop"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.cadhy

        # Add new drop
        drop = settings.drops.add()

        # Set default station based on existing drops
        if len(settings.drops) == 1:
            drop.station = 10.0
        else:
            # Place after last drop
            prev = settings.drops[-2]
            drop.station = prev.station + 20.0

        # Default values
        drop.drop_height = 1.0
        drop.drop_type = "VERTICAL"
        drop.length = 5.0
        drop.num_steps = 3

        # Set active index
        settings.active_drop_index = len(settings.drops) - 1

        self.report({"INFO"}, f"Added drop {len(settings.drops)} at station {drop.station:.1f}m")
        return {"FINISHED"}


class CADHY_OT_RemoveDrop(Operator):
    """Remove a drop structure"""

    bl_idname = "cadhy.remove_drop"
    bl_label = "Remove Drop"
    bl_options = {"REGISTER", "UNDO"}

    index: IntProperty(
        name="Index",
        description="Index of drop to remove",
        default=0,
    )

    def execute(self, context):
        settings = context.scene.cadhy

        if 0 <= self.index < len(settings.drops):
            settings.drops.remove(self.index)

            # Adjust active index
            if settings.active_drop_index >= len(settings.drops):
                settings.active_drop_index = max(0, len(settings.drops) - 1)

            self.report({"INFO"}, "Removed drop")
        else:
            self.report({"WARNING"}, "Invalid drop index")

        return {"FINISHED"}


class CADHY_OT_ClearDrops(Operator):
    """Remove all drop structures"""

    bl_idname = "cadhy.clear_drops"
    bl_label = "Clear All Drops"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.cadhy
        settings.drops.clear()
        settings.active_drop_index = 0
        self.report({"INFO"}, "Cleared all drops")
        return {"FINISHED"}
