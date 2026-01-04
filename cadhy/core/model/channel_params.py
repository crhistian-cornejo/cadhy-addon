"""
Channel Parameters Module
Defines data structures for channel section parameters.
Includes validation system for engineering constraints.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class SectionType(Enum):
    """Types of hydraulic sections."""

    TRAPEZOIDAL = "TRAP"
    RECTANGULAR = "RECT"
    TRIANGULAR = "TRI"
    CIRCULAR = "CIRC"
    PIPE = "PIPE"  # Commercial pipe with wall thickness


# =============================================================================
# VALIDATION SYSTEM
# =============================================================================


class ValidationLevel(Enum):
    """Severity levels for validation messages."""
    ERROR = "error"      # Prevents generation
    WARNING = "warning"  # Allows generation with caution
    INFO = "info"        # Informational only


@dataclass
class ValidationResult:
    """Single validation result."""
    level: ValidationLevel
    code: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None

    @property
    def is_error(self) -> bool:
        return self.level == ValidationLevel.ERROR

    @property
    def is_warning(self) -> bool:
        return self.level == ValidationLevel.WARNING


class ParameterValidator:
    """
    Validates channel parameters against engineering constraints.

    Validation rules are based on hydraulic engineering best practices:
    - Geometric feasibility
    - Material constraints (pipe standards)
    - Hydraulic efficiency ranges
    - Mesh quality recommendations
    """

    # Parameter limits (min, max, recommended_min, recommended_max)
    LIMITS = {
        "bottom_width": (0.1, 100.0, 0.3, 50.0),
        "side_slope": (0.0, 10.0, 0.5, 3.0),
        "height": (0.1, 50.0, 0.3, 10.0),
        "freeboard": (0.0, 10.0, 0.1, 2.0),
        "lining_thickness": (0.0, 2.0, 0.05, 0.5),
        "resolution_m": (0.05, 100.0, 0.1, 5.0),
        "profile_resolution": (0.05, 10.0, 0.1, 2.0),
    }

    # Recommended side slopes by soil type (for info messages)
    RECOMMENDED_SLOPES = {
        "rock": (0.0, 0.25),
        "stiff_clay": (0.5, 1.0),
        "firm_clay": (1.0, 1.5),
        "sandy_loam": (1.5, 2.0),
        "sandy_soil": (2.0, 3.0),
        "loose_sand": (3.0, 4.0),
    }

    @classmethod
    def validate(cls, params: "ChannelParams") -> List[ValidationResult]:
        """
        Validate all parameters and return list of issues.

        Returns:
            List of ValidationResult objects (empty if valid)
        """
        results = []

        # Basic geometric validation
        results.extend(cls._validate_geometry(params))

        # Section-specific validation
        results.extend(cls._validate_section_type(params))

        # Hydraulic efficiency checks
        results.extend(cls._validate_hydraulics(params))

        # Mesh quality recommendations
        results.extend(cls._validate_mesh_settings(params))

        return results

    @classmethod
    def _validate_geometry(cls, params: "ChannelParams") -> List[ValidationResult]:
        """Validate basic geometric parameters."""
        results = []

        # Check each parameter against limits
        for field_name, limits in cls.LIMITS.items():
            if not hasattr(params, field_name):
                continue

            value = getattr(params, field_name)
            min_val, max_val, rec_min, rec_max = limits

            if value < min_val:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    code=f"{field_name}_below_min",
                    message=f"{field_name} ({value:.3f}) is below minimum ({min_val})",
                    field=field_name,
                    suggestion=f"Set {field_name} >= {min_val}"
                ))
            elif value > max_val:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    code=f"{field_name}_above_max",
                    message=f"{field_name} ({value:.3f}) exceeds maximum ({max_val})",
                    field=field_name,
                    suggestion=f"Set {field_name} <= {max_val}"
                ))
            elif value < rec_min:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    code=f"{field_name}_below_recommended",
                    message=f"{field_name} ({value:.3f}) is below recommended ({rec_min})",
                    field=field_name,
                    suggestion=f"Consider {field_name} >= {rec_min} for stability"
                ))
            elif value > rec_max:
                results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    code=f"{field_name}_above_recommended",
                    message=f"{field_name} ({value:.3f}) is above typical ({rec_max})",
                    field=field_name
                ))

        return results

    @classmethod
    def _validate_section_type(cls, params: "ChannelParams") -> List[ValidationResult]:
        """Validate section-specific parameters."""
        results = []

        if params.section_type == SectionType.TRAPEZOIDAL:
            # Check side slope feasibility
            if params.side_slope == 0:
                results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    code="trap_zero_slope",
                    message="Trapezoidal with 0 slope is equivalent to Rectangular",
                    field="side_slope",
                    suggestion="Use RECT section type for vertical walls"
                ))

            # Check top width doesn't get unreasonably large
            top_width = params.bottom_width + 2 * params.side_slope * params.total_height
            if top_width > 50:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    code="trap_wide_top",
                    message=f"Top width ({top_width:.1f}m) is very large",
                    field="side_slope",
                    suggestion="Consider reducing height or side slope"
                ))

        elif params.section_type == SectionType.TRIANGULAR:
            # V-channels need reasonable slopes
            if params.side_slope < 0.5:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    code="tri_steep_slope",
                    message="V-channel with very steep slopes may be unstable",
                    field="side_slope",
                    suggestion="Side slope >= 1.0 recommended for stability"
                ))

        elif params.section_type == SectionType.PIPE:
            # Validate wall thickness for pipe
            if params.lining_thickness <= 0:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    code="pipe_no_wall",
                    message="Pipe requires wall thickness > 0",
                    field="lining_thickness",
                    suggestion="Set wall thickness based on pipe material/SDR"
                ))

            # Check SDR ratio
            if params.lining_thickness > 0:
                sdr = params.bottom_width / (2 * params.lining_thickness)
                if sdr < 9:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        code="pipe_thick_wall",
                        message=f"SDR {sdr:.1f} indicates very thick walls",
                        field="lining_thickness"
                    ))
                elif sdr > 26:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        code="pipe_thin_wall",
                        message=f"SDR {sdr:.1f} indicates thin walls (low pressure)",
                        field="lining_thickness"
                    ))

        return results

    @classmethod
    def _validate_hydraulics(cls, params: "ChannelParams") -> List[ValidationResult]:
        """Validate hydraulic efficiency."""
        results = []

        # Skip for pipes (different hydraulic behavior)
        if params.section_type == SectionType.PIPE:
            return results

        # Check aspect ratio (width/height)
        if params.section_type in (SectionType.TRAPEZOIDAL, SectionType.RECTANGULAR):
            aspect = params.bottom_width / params.height if params.height > 0 else 0

            if aspect < 0.5:
                results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    code="narrow_deep",
                    message=f"Channel is narrow and deep (aspect {aspect:.2f})",
                    suggestion="Wider channels often more efficient hydraulically"
                ))
            elif aspect > 5:
                results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    code="wide_shallow",
                    message=f"Channel is wide and shallow (aspect {aspect:.2f})",
                    suggestion="May have higher friction losses"
                ))

        # Check freeboard ratio
        if params.height > 0:
            fb_ratio = params.freeboard / params.height
            if fb_ratio > 0.5:
                results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    code="high_freeboard",
                    message=f"Freeboard is {fb_ratio*100:.0f}% of height",
                    suggestion="Typical freeboard is 15-30% of design depth"
                ))

        return results

    @classmethod
    def _validate_mesh_settings(cls, params: "ChannelParams") -> List[ValidationResult]:
        """Validate mesh quality settings."""
        results = []

        # Check resolution vs channel size
        min_dimension = min(params.bottom_width, params.height) if params.height > 0 else params.bottom_width

        if params.resolution_m > min_dimension:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                code="coarse_resolution",
                message=f"Resolution ({params.resolution_m}m) > smallest dimension ({min_dimension:.2f}m)",
                field="resolution_m",
                suggestion=f"Resolution should be <= {min_dimension:.2f}m"
            ))

        # Check profile vs axis resolution mismatch
        if hasattr(params, 'profile_resolution') and hasattr(params, 'subdivide_profile'):
            if params.subdivide_profile:
                ratio = params.resolution_m / params.profile_resolution
                if ratio > 3 or ratio < 0.33:
                    results.append(ValidationResult(
                        level=ValidationLevel.INFO,
                        code="resolution_mismatch",
                        message="Axis and profile resolutions differ significantly",
                        suggestion="Match resolutions for uniform quad faces"
                    ))

        return results

    @classmethod
    def is_valid(cls, params: "ChannelParams") -> bool:
        """Quick check if parameters have no errors."""
        results = cls.validate(params)
        return not any(r.is_error for r in results)

    @classmethod
    def get_errors(cls, params: "ChannelParams") -> List[str]:
        """Get list of error messages only."""
        results = cls.validate(params)
        return [r.message for r in results if r.is_error]

    @classmethod
    def get_warnings(cls, params: "ChannelParams") -> List[str]:
        """Get list of warning messages only."""
        results = cls.validate(params)
        return [r.message for r in results if r.is_warning]


# Commercial pipe data (HDPE PE100 SDR series)
# Format: (nominal_diameter_mm, outer_diameter_mm, sdr, wall_thickness_mm)
HDPE_PIPE_DATA = {
    # DN (mm): [(OD, SDR, wall_thickness), ...]
    110: [(110, 11, 10.0), (110, 17, 6.6)],
    160: [(160, 11, 14.6), (160, 17, 9.5)],
    200: [(200, 11, 18.2), (200, 17, 11.9)],
    250: [(250, 11, 22.7), (250, 17, 14.8)],
    315: [(315, 11, 28.6), (315, 17, 18.7)],
    400: [(400, 11, 36.4), (400, 17, 23.7)],
    500: [(500, 11, 45.5), (500, 17, 29.7)],
    630: [(630, 11, 57.3), (630, 17, 37.4)],
    800: [(800, 11, 72.7), (800, 17, 47.4)],
    1000: [(1000, 11, 90.9), (1000, 17, 59.3)],
    1200: [(1200, 11, 109.1), (1200, 17, 71.1)],
}

# PVC pipe data (SCH40 / SCH80)
PVC_PIPE_DATA = {
    # Nominal size (inches): (OD_mm, wall_sch40_mm, wall_sch80_mm)
    2: (60.3, 3.91, 5.54),
    3: (88.9, 5.49, 7.62),
    4: (114.3, 6.02, 8.56),
    6: (168.3, 7.11, 10.97),
    8: (219.1, 8.18, 12.70),
    10: (273.1, 9.27, 15.09),
    12: (323.9, 10.31, 17.48),
    14: (355.6, 11.13, 19.05),
    16: (406.4, 12.70, 21.44),
    18: (457.2, 14.27, 23.83),
    20: (508.0, 15.09, 26.19),
    24: (609.6, 17.48, 30.94),
}

# Concrete pipe data (standard diameters)
CONCRETE_PIPE_DATA = {
    # DN (mm): (inner_diameter_mm, wall_thickness_mm)
    300: (300, 44),
    400: (400, 51),
    500: (500, 57),
    600: (600, 64),
    800: (800, 76),
    1000: (1000, 89),
    1200: (1200, 102),
    1500: (1500, 127),
    1800: (1800, 152),
    2000: (2000, 165),
    2400: (2400, 191),
}


@dataclass
class ChannelParams:
    """Parameters for channel generation."""

    section_type: SectionType = SectionType.TRAPEZOIDAL
    bottom_width: float = 2.0  # meters (or diameter for circular/pipe)
    side_slope: float = 1.5  # horizontal:vertical (Z:1)
    height: float = 2.0  # meters
    freeboard: float = 0.3  # meters
    lining_thickness: float = 0.15  # meters (or wall thickness for pipes)
    resolution_m: float = 1.0  # sampling resolution along axis

    # Profile subdivision for uniform mesh density
    subdivide_profile: bool = True  # Whether to subdivide profile edges
    profile_resolution: float = 1.0  # Max edge length in profile (meters)

    # Pipe-specific parameters
    pipe_material: str = "HDPE"  # HDPE, PVC, CONCRETE
    pipe_sdr: int = 11  # Standard Dimension Ratio (for HDPE)
    pipe_schedule: str = "SCH40"  # SCH40, SCH80 (for PVC)

    @property
    def total_height(self) -> float:
        """Total height including freeboard."""
        if self.section_type in (SectionType.CIRCULAR, SectionType.PIPE):
            return self.bottom_width  # Diameter is the total height
        return self.height + self.freeboard

    @property
    def inner_diameter(self) -> float:
        """Get inner diameter for pipes."""
        if self.section_type == SectionType.PIPE:
            # Outer diameter - 2 * wall thickness
            return self.bottom_width - 2 * self.lining_thickness
        return self.bottom_width

    @property
    def top_width(self) -> float:
        """Calculate top width for trapezoidal section."""
        if self.section_type == SectionType.TRAPEZOIDAL:
            return self.bottom_width + 2 * self.side_slope * self.total_height
        elif self.section_type == SectionType.TRIANGULAR:
            return 2 * self.side_slope * self.total_height
        elif self.section_type == SectionType.RECTANGULAR:
            return self.bottom_width
        else:
            return self.bottom_width  # For circular/pipe, this is diameter

    def hydraulic_area(self, water_depth: float) -> float:
        """Calculate hydraulic area for given water depth."""
        import math

        if self.section_type == SectionType.TRAPEZOIDAL:
            return (self.bottom_width + self.side_slope * water_depth) * water_depth
        elif self.section_type == SectionType.RECTANGULAR:
            return self.bottom_width * water_depth
        elif self.section_type == SectionType.TRIANGULAR:
            # V-channel: A = z * y^2 where z is side slope, y is depth
            return self.side_slope * water_depth * water_depth
        elif self.section_type in (SectionType.CIRCULAR, SectionType.PIPE):
            r = self.inner_diameter / 2 if self.section_type == SectionType.PIPE else self.bottom_width / 2
            if water_depth >= r * 2:
                return math.pi * r * r
            if water_depth <= 0:
                return 0.0
            theta = 2 * math.acos((r - water_depth) / r)
            return r * r * (theta - math.sin(theta)) / 2
        return 0.0

    def wetted_perimeter(self, water_depth: float) -> float:
        """Calculate wetted perimeter for given water depth."""
        import math

        if self.section_type == SectionType.TRAPEZOIDAL:
            return self.bottom_width + 2 * water_depth * math.sqrt(1 + self.side_slope**2)
        elif self.section_type == SectionType.RECTANGULAR:
            return self.bottom_width + 2 * water_depth
        elif self.section_type == SectionType.TRIANGULAR:
            # V-channel: P = 2 * y * sqrt(1 + z^2)
            return 2 * water_depth * math.sqrt(1 + self.side_slope**2)
        elif self.section_type in (SectionType.CIRCULAR, SectionType.PIPE):
            r = self.inner_diameter / 2 if self.section_type == SectionType.PIPE else self.bottom_width / 2
            if water_depth >= r * 2:
                return math.pi * r * 2
            if water_depth <= 0:
                return 0.0
            theta = 2 * math.acos((r - water_depth) / r)
            return r * theta
        return 0.0

    def hydraulic_radius(self, water_depth: float) -> float:
        """Calculate hydraulic radius for given water depth."""
        wp = self.wetted_perimeter(water_depth)
        if wp > 0:
            return self.hydraulic_area(water_depth) / wp
        return 0.0

    def validate(self) -> List[ValidationResult]:
        """
        Validate this parameter set.

        Returns:
            List of ValidationResult objects (empty if valid)
        """
        return ParameterValidator.validate(self)

    def is_valid(self) -> bool:
        """Quick check if parameters have no errors."""
        return ParameterValidator.is_valid(self)

    def get_validation_summary(self) -> Tuple[int, int, int]:
        """
        Get counts of validation issues.

        Returns:
            Tuple of (error_count, warning_count, info_count)
        """
        results = self.validate()
        errors = sum(1 for r in results if r.level == ValidationLevel.ERROR)
        warnings = sum(1 for r in results if r.level == ValidationLevel.WARNING)
        infos = sum(1 for r in results if r.level == ValidationLevel.INFO)
        return errors, warnings, infos


@dataclass
class SectionProfile:
    """Represents a 2D section profile (local coordinates)."""

    points: list  # List of (x, y) tuples representing the section outline
    is_closed: bool = False

    @classmethod
    def from_channel_params(cls, params: ChannelParams, include_lining: bool = False) -> "SectionProfile":
        """Generate section profile from channel parameters."""
        points = []
        h = params.total_height

        if params.section_type == SectionType.TRAPEZOIDAL:
            bw = params.bottom_width
            tw = params.top_width

            # Inner profile (bottom to top, counterclockwise)
            points = [
                (-bw / 2, 0),  # Bottom left
                (bw / 2, 0),  # Bottom right
                (tw / 2, h),  # Top right
                (-tw / 2, h),  # Top left
            ]

        elif params.section_type == SectionType.RECTANGULAR:
            bw = params.bottom_width
            points = [
                (-bw / 2, 0),
                (bw / 2, 0),
                (bw / 2, h),
                (-bw / 2, h),
            ]

        elif params.section_type == SectionType.CIRCULAR:
            import math

            r = params.bottom_width / 2
            segments = 32
            for i in range(segments + 1):
                angle = math.pi + (math.pi * i / segments)  # Bottom half circle
                x = r * math.cos(angle)
                y = r * math.sin(angle) + r
                points.append((x, y))

        return cls(points=points, is_closed=True)
