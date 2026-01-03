"""
Feature Flags Module
Enable/disable optional features at runtime.
Similar to BlenderGIS's conditional feature loading.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class FeatureFlag:
    """A feature flag with metadata."""

    name: str
    enabled: bool
    description: str
    requires_addon: str | None = None  # Optional dependency addon


class FeatureFlags:
    """
    Central feature flags management.

    Use this to conditionally enable/disable features:
    - BlenderGIS integration
    - Experimental features
    - Developer tools
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize default feature flags."""
        self._flags: Dict[str, FeatureFlag] = {}

        # Core features (always enabled)
        self.register("core_channel", True, "Core channel generation")
        self.register("core_cfd", True, "CFD domain generation")
        self.register("core_sections", True, "Section generation")
        self.register("core_export", True, "Export functionality")

        # Optional integrations
        self.register(
            "blendergis_integration",
            True,
            "BlenderGIS integration for SHP/DEM import",
            requires_addon="BlenderGIS",
        )

        # Experimental features
        self.register("experimental_transitions", False, "Section transitions (A→B)")
        self.register("experimental_bermas", False, "Bermas and compound channels")
        self.register("experimental_openfoam", False, "OpenFOAM export format")

        # Developer features
        self.register("dev_reload", True, "Developer reload operator")
        self.register("dev_profiling", False, "Performance profiling hooks")

    def register(
        self,
        name: str,
        enabled: bool,
        description: str,
        requires_addon: str | None = None,
    ) -> None:
        """Register a new feature flag."""
        self._flags[name] = FeatureFlag(
            name=name,
            enabled=enabled,
            description=description,
            requires_addon=requires_addon,
        )

    def is_enabled(self, name: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            name: Feature flag name

        Returns:
            True if feature is enabled and dependencies are met
        """
        flag = self._flags.get(name)
        if flag is None:
            return False

        if not flag.enabled:
            return False

        # Check addon dependency
        if flag.requires_addon:
            if not self._is_addon_available(flag.requires_addon):
                return False

        return True

    def _is_addon_available(self, addon_name: str) -> bool:
        """Check if a required addon is available."""
        try:
            import bpy

            return addon_name in bpy.context.preferences.addons
        except Exception:
            return False

    def enable(self, name: str) -> bool:
        """Enable a feature flag."""
        if name in self._flags:
            self._flags[name].enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a feature flag."""
        if name in self._flags:
            self._flags[name].enabled = False
            return True
        return False

    def get_all(self) -> Dict[str, FeatureFlag]:
        """Get all registered feature flags."""
        return self._flags.copy()

    def get_enabled(self) -> list[str]:
        """Get list of enabled feature names."""
        return [name for name, flag in self._flags.items() if self.is_enabled(name)]

    def get_disabled(self) -> list[str]:
        """Get list of disabled feature names."""
        return [name for name, flag in self._flags.items() if not self.is_enabled(name)]


# Global singleton instance
features = FeatureFlags()


# Convenience functions
def is_feature_enabled(name: str) -> bool:
    """Check if a feature is enabled."""
    return features.is_enabled(name)


def enable_feature(name: str) -> bool:
    """Enable a feature."""
    return features.enable(name)


def disable_feature(name: str) -> bool:
    """Disable a feature."""
    return features.disable(name)
