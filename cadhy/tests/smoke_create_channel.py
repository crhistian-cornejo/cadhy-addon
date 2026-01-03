"""
Smoke Test: Create Channel
Basic smoke test to verify channel creation works.

Run in Blender's Python console or as a script:
    exec(open('/path/to/smoke_create_channel.py').read())
"""

import sys

import bpy


def cleanup_scene():
    """Remove all objects from scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Remove CADHY collections
    for name in ["CADHY_Channels", "CADHY_CFD", "CADHY_Sections"]:
        if name in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections[name])


def create_test_curve():
    """Create a simple bezier curve for testing."""
    # Create curve data
    curve_data = bpy.data.curves.new("TestAxis", type="CURVE")
    curve_data.dimensions = "3D"

    # Create spline
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(3)  # 4 points total

    # Set control points (simple S-curve)
    points = [
        (0, 0, 0),
        (10, 5, 0),
        (20, -5, 1),
        (30, 0, 2),
    ]

    for i, (x, y, z) in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = (x, y, z)
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"

    # Create object
    curve_obj = bpy.data.objects.new("TestAxis", curve_data)
    bpy.context.scene.collection.objects.link(curve_obj)

    return curve_obj


def test_build_channel():
    """Test channel building."""
    print("\n=== Testing Channel Build ===")

    # Get scene settings
    settings = bpy.context.scene.cadhy

    # Configure parameters
    settings.section_type = "TRAP"
    settings.bottom_width = 2.0
    settings.side_slope = 1.5
    settings.height = 2.0
    settings.freeboard = 0.3
    settings.resolution_m = 1.0

    # Build channel
    result = bpy.ops.cadhy.build_channel()

    if result == {"FINISHED"}:
        print("✓ Channel build successful")

        # Verify channel exists
        channel_name = f"CADHY_Channel_{settings.axis_object.name}"
        if channel_name in bpy.data.objects:
            obj = bpy.data.objects[channel_name]
            print(f"  - Vertices: {len(obj.data.vertices)}")
            print(f"  - Faces: {len(obj.data.polygons)}")
            return True

    print("✗ Channel build failed")
    return False


def test_build_cfd_domain():
    """Test CFD domain building."""
    print("\n=== Testing CFD Domain Build ===")

    settings = bpy.context.scene.cadhy

    # Configure CFD parameters
    settings.cfd_enabled = True
    settings.cfd_water_level = 1.5
    settings.cfd_inlet_extension = 2.0
    settings.cfd_outlet_extension = 5.0

    # Build CFD domain
    result = bpy.ops.cadhy.build_cfd_domain()

    if result == {"FINISHED"}:
        print("✓ CFD domain build successful")

        # Verify domain exists
        domain_name = f"CADHY_CFD_Domain_{settings.axis_object.name}"
        if domain_name in bpy.data.objects:
            obj = bpy.data.objects[domain_name]
            print(f"  - Vertices: {len(obj.data.vertices)}")
            print(f"  - Faces: {len(obj.data.polygons)}")

            # Check validation
            if hasattr(obj, "cadhy_cfd"):
                cfd = obj.cadhy_cfd
                print(f"  - Watertight: {cfd.is_watertight}")
                print(f"  - Volume: {cfd.volume:.3f} m³")

            return True

    print("✗ CFD domain build failed")
    return False


def test_generate_sections():
    """Test section generation."""
    print("\n=== Testing Section Generation ===")

    settings = bpy.context.scene.cadhy

    # Configure sections
    settings.sections_start = 0.0
    settings.sections_end = 0.0  # Auto
    settings.sections_step = 5.0

    # Generate sections
    result = bpy.ops.cadhy.generate_sections(create_meshes=False)

    if result == {"FINISHED"}:
        print("✓ Section generation successful")

        # Count sections
        if "CADHY_Sections" in bpy.data.collections:
            count = len(bpy.data.collections["CADHY_Sections"].objects)
            print(f"  - Generated {count} sections")
            return True

    print("✗ Section generation failed")
    return False


def test_validate_mesh():
    """Test mesh validation."""
    print("\n=== Testing Mesh Validation ===")

    # Select CFD domain
    settings = bpy.context.scene.cadhy
    domain_name = f"CADHY_CFD_Domain_{settings.axis_object.name}"

    if domain_name in bpy.data.objects:
        obj = bpy.data.objects[domain_name]
        bpy.context.view_layer.objects.active = obj

        result = bpy.ops.cadhy.validate_mesh()

        if result == {"FINISHED"}:
            print("✓ Mesh validation completed")
            return True

    print("✗ Mesh validation failed")
    return False


def run_smoke_tests():
    """Run all smoke tests."""
    print("\n" + "=" * 50)
    print("CADHY SMOKE TESTS")
    print("=" * 50)

    # Cleanup
    cleanup_scene()

    # Create test curve
    curve = create_test_curve()
    print(f"\nCreated test curve: {curve.name}")

    # Set as axis
    settings = bpy.context.scene.cadhy
    settings.axis_object = curve

    # Run tests
    results = []

    results.append(("Build Channel", test_build_channel()))
    results.append(("Build CFD Domain", test_build_cfd_domain()))
    results.append(("Generate Sections", test_generate_sections()))
    results.append(("Validate Mesh", test_validate_mesh()))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 50)

    return passed == total


if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
