"""
CADHY - Blender Add-on for Hydraulic Infrastructure Modeling
Toolkit for parametric modeling of hydraulic infrastructure within Blender.
"""

import sys

bl_info = {
    "name": "CADHY",
    "author": "CADHY Team",
    "version": (0, 3, 3),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > CADHY",
    "description": "Parametric modeling toolkit for hydraulic infrastructure and CFD domain generation",
    "warning": "",
    "doc_url": "https://cadhy.app/docs",
    "tracker_url": "https://github.com/crhistian-cornejo/cadhy-addon/issues",
    "category": "3D View",
}

# Store original exception hook
_original_excepthook = sys.excepthook


def _cadhy_excepthook(exc_type, exc_value, exc_traceback):
    """Global exception hook to catch and log uncaught CADHY exceptions."""
    # Check if exception originates from CADHY
    tb = exc_traceback
    is_cadhy_exception = False

    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        if "cadhy" in filename.lower():
            is_cadhy_exception = True
            break
        tb = tb.tb_next

    if is_cadhy_exception:
        try:
            from .core.util.logging import log_exception

            log_exception(f"Uncaught CADHY exception: {exc_type.__name__}: {exc_value}")
        except Exception:
            # Logging failed, just print
            print(f"[CADHY] CRITICAL: Uncaught exception: {exc_type.__name__}: {exc_value}")

    # Call original exception hook
    _original_excepthook(exc_type, exc_value, exc_traceback)


def _validate_blender_version():
    """Validate that Blender version meets minimum requirements."""
    import bpy

    min_version = bl_info["blender"]
    current_version = bpy.app.version

    if current_version < min_version:
        min_str = ".".join(str(v) for v in min_version)
        current_str = bpy.app.version_string
        raise RuntimeError(
            f"CADHY requires Blender {min_str} or newer. "
            f"You are running Blender {current_str}. "
            f"Please upgrade Blender to use this add-on."
        )


def _setup_logging():
    """Initialize logging system."""
    try:
        from .core.util.logging import log_info, setup_logging

        setup_logging()
        log_info(f"CADHY v{'.'.join(str(v) for v in bl_info['version'])} initializing...")
    except Exception as e:
        print(f"[CADHY] Warning: Could not initialize logging: {e}")


def register():
    """Register all addon classes and properties."""
    # Validate Blender version first
    _validate_blender_version()

    # Setup logging
    _setup_logging()

    # Install global exception hook
    sys.excepthook = _cadhy_excepthook

    # Import and register all classes
    from . import registration

    registration.register()

    # Log successful registration
    try:
        from .core.util.logging import log_info

        log_info("CADHY registered successfully")
    except Exception:
        print("[CADHY] Registered successfully")


def unregister():
    """Unregister all addon classes and properties."""
    # Restore original exception hook
    sys.excepthook = _original_excepthook

    # Unregister all classes
    from . import registration

    registration.unregister()

    # Log unregistration
    try:
        from .core.util.logging import log_info

        log_info("CADHY unregistered")
    except Exception:
        print("[CADHY] Unregistered")


if __name__ == "__main__":
    register()
