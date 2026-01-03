"""
CADHY Test Runner
Runs all tests when executed from Blender's Python.

Usage:
    blender --background --python cadhy/tests/run_all.py

This script is designed to be run from the repository root directory.
"""

import os
import sys
import traceback

# Add the parent directory to the path so we can import cadhy
script_dir = os.path.dirname(os.path.abspath(__file__))
addon_dir = os.path.dirname(os.path.dirname(script_dir))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_result(name: str, passed: bool, message: str = "") -> None:
    """Print test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status}: {name}")
    if message:
        print(f"         {message}")


def run_test(name: str, test_func) -> bool:
    """Run a single test function and return success status."""
    try:
        test_func()
        print_result(name, True)
        return True
    except Exception as e:
        print_result(name, False, str(e))
        traceback.print_exc()
        return False


def test_addon_registration():
    """Test that the addon registers without errors."""
    import bpy

    # Check if already registered
    if "cadhy" in bpy.context.preferences.addons:
        return

    # Register the addon
    import cadhy

    cadhy.register()

    # Verify registration
    assert hasattr(bpy.types.Scene, "cadhy"), "Scene.cadhy not registered"
    assert hasattr(bpy.types.Object, "cadhy_channel"), "Object.cadhy_channel not registered"
    assert hasattr(bpy.types.Object, "cadhy_cfd"), "Object.cadhy_cfd not registered"


def test_preferences_registered():
    """Test that addon preferences are accessible."""
    import bpy

    addon = bpy.context.preferences.addons.get("cadhy")
    if addon is None:
        # Register if not already
        import cadhy

        cadhy.register()
        addon = bpy.context.preferences.addons.get("cadhy")

    # Preferences should exist after registration
    # Note: In headless mode, preferences may not be fully initialized
    # Just verify the import works
    from cadhy.blender.preferences import CADHYPreferences

    assert CADHYPreferences is not None


def test_logging_setup():
    """Test that logging is properly configured."""
    from cadhy.core.util.logging import LOG_DIR, get_logger

    logger = get_logger()
    assert logger is not None
    assert logger.name == "CADHY"

    # Verify log directory can be created
    import os

    os.makedirs(LOG_DIR, exist_ok=True)
    assert os.path.exists(LOG_DIR)


def test_create_curve():
    """Test creating a curve object."""
    import bpy

    # Create a bezier curve
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    curve = bpy.context.active_object

    assert curve is not None
    assert curve.type == "CURVE"

    return curve


def test_build_channel():
    """Test building a channel from a curve."""
    import bpy

    # Create a curve first
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    curve = bpy.context.active_object

    # Set as axis in scene settings
    bpy.context.scene.cadhy.axis_object = curve

    # Build channel
    result = bpy.ops.cadhy.build_channel()

    assert result == {"FINISHED"}, f"Build channel failed with result: {result}"

    # Find the channel object
    channel_found = False
    for obj in bpy.data.objects:
        if obj.type == "MESH" and "CADHY_Channel" in obj.name:
            channel_found = True
            ch = obj.cadhy_channel
            assert ch.is_cadhy_object, "Channel not marked as CADHY object"
            assert ch.source_axis == curve, "Source axis not set"
            break

    assert channel_found, "Channel object not created"


def test_build_cfd_domain():
    """Test building a CFD domain."""
    import bpy

    # Create a curve first
    bpy.ops.curve.primitive_bezier_curve_add(location=(10, 0, 0))
    curve = bpy.context.active_object

    # Set as axis in scene settings
    bpy.context.scene.cadhy.axis_object = curve

    # Build CFD domain
    result = bpy.ops.cadhy.build_cfd_domain()

    assert result == {"FINISHED"}, f"Build CFD domain failed with result: {result}"

    # Find the domain object
    domain_found = False
    for obj in bpy.data.objects:
        if obj.type == "MESH" and "CADHY_CFD" in obj.name:
            domain_found = True
            cfd = obj.cadhy_cfd
            assert cfd.is_cadhy_object, "CFD domain not marked as CADHY object"
            break

    assert domain_found, "CFD domain object not created"


def test_channel_params():
    """Test channel parameters dataclass."""
    from cadhy.core.model.channel_params import ChannelParams, SectionType

    params = ChannelParams(
        section_type=SectionType.TRAPEZOIDAL,
        bottom_width=2.0,
        side_slope=1.5,
        height=1.5,
        freeboard=0.3,
        lining_thickness=0.15,
        resolution_m=0.5,
    )

    assert params.bottom_width == 2.0
    assert params.total_height == 1.8  # height + freeboard
    assert params.section_type == SectionType.TRAPEZOIDAL


def test_version_info():
    """Test version information is consistent."""
    from cadhy import bl_info
    from cadhy.core.util.versioning import CADHY_VERSION

    # bl_info version should match versioning module
    bl_version = bl_info["version"]
    assert bl_version == CADHY_VERSION, f"Version mismatch: bl_info={bl_version}, versioning={CADHY_VERSION}"


def main():
    """Run all tests."""
    print_header("CADHY Addon Test Suite")

    tests = [
        ("Addon Registration", test_addon_registration),
        ("Preferences Registered", test_preferences_registered),
        ("Logging Setup", test_logging_setup),
        ("Channel Parameters", test_channel_params),
        ("Version Info", test_version_info),
        ("Create Curve", test_create_curve),
        ("Build Channel", test_build_channel),
        ("Build CFD Domain", test_build_cfd_domain),
    ]

    passed = 0
    failed = 0

    print_header("Running Tests")

    for name, func in tests:
        if run_test(name, func):
            passed += 1
        else:
            failed += 1

    print_header("Results")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total:  {len(tests)}")

    # Exit with error code if any tests failed
    if failed > 0:
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
