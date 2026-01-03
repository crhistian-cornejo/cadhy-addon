"""
Units Module
Unit conversion and handling utilities.
"""

from enum import Enum


class LengthUnit(Enum):
    """Length units."""

    METERS = "m"
    CENTIMETERS = "cm"
    MILLIMETERS = "mm"
    FEET = "ft"
    INCHES = "in"


class AreaUnit(Enum):
    """Area units."""

    SQUARE_METERS = "m²"
    SQUARE_CENTIMETERS = "cm²"
    SQUARE_FEET = "ft²"


class VolumeUnit(Enum):
    """Volume units."""

    CUBIC_METERS = "m³"
    LITERS = "L"
    CUBIC_FEET = "ft³"
    GALLONS = "gal"


# Conversion factors to meters
LENGTH_TO_METERS = {
    LengthUnit.METERS: 1.0,
    LengthUnit.CENTIMETERS: 0.01,
    LengthUnit.MILLIMETERS: 0.001,
    LengthUnit.FEET: 0.3048,
    LengthUnit.INCHES: 0.0254,
}

# Conversion factors to square meters
AREA_TO_SQ_METERS = {
    AreaUnit.SQUARE_METERS: 1.0,
    AreaUnit.SQUARE_CENTIMETERS: 0.0001,
    AreaUnit.SQUARE_FEET: 0.092903,
}

# Conversion factors to cubic meters
VOLUME_TO_CU_METERS = {
    VolumeUnit.CUBIC_METERS: 1.0,
    VolumeUnit.LITERS: 0.001,
    VolumeUnit.CUBIC_FEET: 0.0283168,
    VolumeUnit.GALLONS: 0.00378541,
}


def convert_length(value: float, from_unit: LengthUnit, to_unit: LengthUnit) -> float:
    """
    Convert length between units.

    Args:
        value: Value to convert
        from_unit: Source unit
        to_unit: Target unit

    Returns:
        Converted value
    """
    # Convert to meters first
    meters = value * LENGTH_TO_METERS[from_unit]
    # Convert from meters to target
    return meters / LENGTH_TO_METERS[to_unit]


def convert_area(value: float, from_unit: AreaUnit, to_unit: AreaUnit) -> float:
    """
    Convert area between units.

    Args:
        value: Value to convert
        from_unit: Source unit
        to_unit: Target unit

    Returns:
        Converted value
    """
    sq_meters = value * AREA_TO_SQ_METERS[from_unit]
    return sq_meters / AREA_TO_SQ_METERS[to_unit]


def convert_volume(value: float, from_unit: VolumeUnit, to_unit: VolumeUnit) -> float:
    """
    Convert volume between units.

    Args:
        value: Value to convert
        from_unit: Source unit
        to_unit: Target unit

    Returns:
        Converted value
    """
    cu_meters = value * VOLUME_TO_CU_METERS[from_unit]
    return cu_meters / VOLUME_TO_CU_METERS[to_unit]


def format_length(value: float, unit: LengthUnit = LengthUnit.METERS, decimals: int = 3) -> str:
    """Format length value with unit."""
    return f"{value:.{decimals}f} {unit.value}"


def format_area(value: float, unit: AreaUnit = AreaUnit.SQUARE_METERS, decimals: int = 4) -> str:
    """Format area value with unit."""
    return f"{value:.{decimals}f} {unit.value}"


def format_volume(value: float, unit: VolumeUnit = VolumeUnit.CUBIC_METERS, decimals: int = 3) -> str:
    """Format volume value with unit."""
    return f"{value:.{decimals}f} {unit.value}"


def get_blender_unit_scale() -> float:
    """
    Get Blender's current unit scale.

    Returns:
        Scale factor (1.0 if meters)
    """
    import bpy

    return bpy.context.scene.unit_settings.scale_length


def apply_unit_scale(value: float, inverse: bool = False) -> float:
    """
    Apply Blender's unit scale to a value.

    Args:
        value: Value to scale
        inverse: If True, divide instead of multiply

    Returns:
        Scaled value
    """
    scale = get_blender_unit_scale()
    if inverse:
        return value / scale
    return value * scale
