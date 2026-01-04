"""
CADHY Event Handlers
Handles automatic updates when parameters or curves change.
Uses Blender's dependency graph for efficient updates.
"""

import time
from typing import Optional, Set

import bpy
from bpy.app.handlers import depsgraph_update_post, load_post, persistent

# =============================================================================
# AUTO-REBUILD SYSTEM
# =============================================================================

# State tracking
_last_rebuild_time: float = 0.0
_pending_rebuild: bool = False
_rebuild_timer: Optional[float] = None
_tracked_curves: Set[str] = set()

# Configuration
REBUILD_DEBOUNCE_MS = 150  # Minimum ms between rebuilds
REBUILD_DELAY_MS = 100     # Delay before triggering rebuild


def _get_channel_for_axis(axis_name: str) -> Optional[bpy.types.Object]:
    """Find the channel object that uses this axis curve."""
    for obj in bpy.data.objects:
        if obj.type == "MESH" and hasattr(obj, "cadhy_channel"):
            ch = obj.cadhy_channel
            if ch.source_axis and ch.source_axis.name == axis_name:
                return obj
    return None


def _should_trigger_rebuild(context) -> bool:
    """Check if rebuild should be triggered based on settings."""
    if not hasattr(context, "scene") or not context.scene:
        return False

    settings = getattr(context.scene, "cadhy", None)
    if not settings:
        return False

    return getattr(settings, "auto_rebuild", False)


def _do_rebuild(channel_obj: bpy.types.Object) -> None:
    """Execute the channel rebuild."""
    global _last_rebuild_time

    try:
        # Use the update operator
        override = {"active_object": channel_obj, "selected_objects": [channel_obj]}
        with bpy.context.temp_override(**override):
            bpy.ops.cadhy.update_channel()
        _last_rebuild_time = time.time()
    except Exception as e:
        print(f"[CADHY] Auto-rebuild failed: {e}")


def _rebuild_timer_callback() -> Optional[float]:
    """Timer callback for debounced rebuild."""
    global _pending_rebuild, _rebuild_timer

    if not _pending_rebuild:
        _rebuild_timer = None
        return None

    _pending_rebuild = False

    # Find channel to rebuild
    context = bpy.context
    if not _should_trigger_rebuild(context):
        _rebuild_timer = None
        return None

    settings = context.scene.cadhy
    if settings.axis_object:
        channel = _get_channel_for_axis(settings.axis_object.name)
        if channel:
            _do_rebuild(channel)

    _rebuild_timer = None
    return None


def _schedule_rebuild() -> None:
    """Schedule a debounced rebuild."""
    global _pending_rebuild, _rebuild_timer

    _pending_rebuild = True

    # Check debounce
    now = time.time()
    if now - _last_rebuild_time < REBUILD_DEBOUNCE_MS / 1000:
        return

    # Schedule timer if not already scheduled
    if _rebuild_timer is None:
        _rebuild_timer = bpy.app.timers.register(
            _rebuild_timer_callback,
            first_interval=REBUILD_DELAY_MS / 1000,
            persistent=False
        )


@persistent
def on_depsgraph_update(scene, depsgraph):
    """
    Handler for dependency graph updates.
    Triggers auto-rebuild when tracked curves or settings change.
    """
    if not _should_trigger_rebuild(bpy.context):
        return

    settings = scene.cadhy
    axis_obj = settings.axis_object

    if not axis_obj:
        return

    # Check if axis curve was modified
    for update in depsgraph.updates:
        obj = update.id

        # Check for curve geometry changes
        if isinstance(obj, bpy.types.Object) and obj.name == axis_obj.name:
            if update.is_updated_geometry:
                _schedule_rebuild()
                return

        # Check for curve data changes
        if isinstance(obj, bpy.types.Curve):
            if axis_obj.data and obj.name == axis_obj.data.name:
                _schedule_rebuild()
                return


@persistent
def on_load_post(dummy):
    """Reset state when loading a new file."""
    global _last_rebuild_time, _pending_rebuild, _rebuild_timer, _tracked_curves

    _last_rebuild_time = 0.0
    _pending_rebuild = False
    _rebuild_timer = None
    _tracked_curves.clear()


# =============================================================================
# PROPERTY CHANGE CALLBACKS
# =============================================================================


def on_parameter_change(self, context):
    """
    Callback when any CADHY parameter changes.
    Triggers auto-rebuild if enabled.
    """
    if _should_trigger_rebuild(context):
        _schedule_rebuild()


def on_axis_change(self, context):
    """Callback when axis curve selection changes."""
    global _tracked_curves

    settings = context.scene.cadhy

    # Update tracked curves
    _tracked_curves.clear()
    if settings.axis_object:
        _tracked_curves.add(settings.axis_object.name)


# =============================================================================
# REGISTRATION
# =============================================================================


_handlers_registered = False


def register_handlers():
    """Register all CADHY event handlers."""
    global _handlers_registered

    if _handlers_registered:
        return

    # Register depsgraph handler
    if on_depsgraph_update not in depsgraph_update_post:
        depsgraph_update_post.append(on_depsgraph_update)

    # Register load handler
    if on_load_post not in load_post:
        load_post.append(on_load_post)

    _handlers_registered = True
    print("[CADHY] Event handlers registered")


def unregister_handlers():
    """Unregister all CADHY event handlers."""
    global _handlers_registered, _rebuild_timer

    # Cancel any pending timer
    if _rebuild_timer is not None:
        try:
            bpy.app.timers.unregister(_rebuild_timer)
        except Exception:
            pass
        _rebuild_timer = None

    # Remove handlers
    if on_depsgraph_update in depsgraph_update_post:
        depsgraph_update_post.remove(on_depsgraph_update)

    if on_load_post in load_post:
        load_post.remove(on_load_post)

    _handlers_registered = False
    print("[CADHY] Event handlers unregistered")
