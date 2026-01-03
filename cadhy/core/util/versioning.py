"""
Versioning Module
Version information and compatibility checking.
"""

import sys
from typing import Optional, Tuple

# CADHY Version
CADHY_VERSION = (0, 1, 1)
CADHY_VERSION_STRING = "0.1.1"

# Minimum supported Blender version
MIN_BLENDER_VERSION = (4, 1, 0)

# Recommended Blender version
RECOMMENDED_BLENDER_VERSION = (4, 1, 0)


def get_version_string() -> str:
    """Get CADHY version as string."""
    return CADHY_VERSION_STRING


def get_version_tuple() -> Tuple[int, int, int]:
    """Get CADHY version as tuple."""
    return CADHY_VERSION


def get_blender_version() -> Tuple[int, int, int]:
    """
    Get current Blender version.

    Returns:
        Blender version tuple (major, minor, patch)
    """
    import bpy

    return bpy.app.version


def get_blender_version_string() -> str:
    """Get Blender version as string."""
    import bpy

    return bpy.app.version_string


def check_blender_compatibility() -> Tuple[bool, str]:
    """
    Check if current Blender version is compatible.

    Returns:
        Tuple of (is_compatible, message)
    """
    import bpy

    current = bpy.app.version

    if current < MIN_BLENDER_VERSION:
        return (
            False,
            f"CADHY requires Blender {'.'.join(map(str, MIN_BLENDER_VERSION))} or higher. "
            f"Current version: {bpy.app.version_string}",
        )

    if current < RECOMMENDED_BLENDER_VERSION:
        return (
            True,
            f"CADHY recommends Blender {'.'.join(map(str, RECOMMENDED_BLENDER_VERSION))} or higher. "
            f"Current version: {bpy.app.version_string}. Some features may not work correctly.",
        )

    return (True, "Blender version is compatible")


def get_python_version() -> str:
    """Get Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_system_info() -> dict:
    """
    Get system information for debugging.

    Returns:
        Dictionary with system info
    """
    import platform

    import bpy

    return {
        "cadhy_version": CADHY_VERSION_STRING,
        "blender_version": bpy.app.version_string,
        "python_version": get_python_version(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "machine": platform.machine(),
    }


def format_system_info() -> str:
    """Format system info for display or logging."""
    info = get_system_info()
    lines = [
        "=== CADHY System Information ===",
        f"CADHY Version: {info['cadhy_version']}",
        f"Blender Version: {info['blender_version']}",
        f"Python Version: {info['python_version']}",
        f"Platform: {info['platform']} {info['platform_version']}",
        f"Machine: {info['machine']}",
    ]
    return "\n".join(lines)


class VersionMigration:
    """Handle version migrations for saved data."""

    @staticmethod
    def get_data_version(obj) -> Optional[Tuple[int, int, int]]:
        """
        Get version of CADHY data stored on object.

        Args:
            obj: Blender object

        Returns:
            Version tuple or None
        """
        if "cadhy_version" in obj:
            version_str = obj["cadhy_version"]
            try:
                parts = version_str.split(".")
                return tuple(int(p) for p in parts)
            except Exception:
                return None
        return None

    @staticmethod
    def set_data_version(obj) -> None:
        """
        Set current CADHY version on object.

        Args:
            obj: Blender object
        """
        obj["cadhy_version"] = CADHY_VERSION_STRING

    @staticmethod
    def needs_migration(obj) -> bool:
        """
        Check if object data needs migration.

        Args:
            obj: Blender object

        Returns:
            True if migration needed
        """
        data_version = VersionMigration.get_data_version(obj)
        if data_version is None:
            return True
        return data_version < CADHY_VERSION

    @staticmethod
    def migrate(obj) -> bool:
        """
        Migrate object data to current version.

        Args:
            obj: Blender object

        Returns:
            True if migration successful
        """
        # Currently no migrations needed
        VersionMigration.set_data_version(obj)
        return True
