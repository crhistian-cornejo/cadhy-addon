"""
Geometry Nodes Preview System
Creates non-destructive preview using Geometry Nodes modifiers.
This provides fast visual feedback while editing parameters.
"""


import bpy

# Node group name for CADHY preview
GN_PREVIEW_NAME = "CADHY_ChannelPreview"


def get_or_create_preview_nodegroup() -> bpy.types.NodeTree:
    """
    Get or create the CADHY channel preview node group.

    Returns:
        The node group for channel preview
    """
    # Check if already exists
    if GN_PREVIEW_NAME in bpy.data.node_groups:
        return bpy.data.node_groups[GN_PREVIEW_NAME]

    # Create new node group
    ng = bpy.data.node_groups.new(name=GN_PREVIEW_NAME, type="GeometryNodeTree")

    # Create interface (inputs and outputs)
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    # Parameters as inputs
    ng.interface.new_socket("Bottom Width", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Height", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Side Slope", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Resolution", in_out="INPUT", socket_type="NodeSocketFloat")

    # Set default values
    for item in ng.interface.items_tree:
        if item.name == "Bottom Width":
            item.default_value = 2.0
            item.min_value = 0.1
        elif item.name == "Height":
            item.default_value = 1.5
            item.min_value = 0.1
        elif item.name == "Side Slope":
            item.default_value = 1.5
            item.min_value = 0.0
        elif item.name == "Resolution":
            item.default_value = 1.0
            item.min_value = 0.1

    # Create nodes
    nodes = ng.nodes
    links = ng.links

    # Group Input
    input_node = nodes.new("NodeGroupInput")
    input_node.location = (-600, 0)

    # Group Output
    output_node = nodes.new("NodeGroupOutput")
    output_node.location = (600, 0)

    # Curve to Mesh
    curve_to_mesh = nodes.new("GeometryNodeCurveToMesh")
    curve_to_mesh.location = (200, 0)

    # Create profile curve (trapezoidal)
    profile_curve = nodes.new("GeometryNodeCurvePrimitiveLine")
    profile_curve.location = (-200, -200)
    profile_curve.mode = "POINTS"

    # For now, create a simple rectangular profile
    # A more complete implementation would build the trapezoidal profile
    curve_line = nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    curve_line.location = (-200, -100)
    curve_line.mode = "RECTANGLE"

    # Math nodes to calculate profile dimensions
    # Width = Bottom Width
    # Height = Height parameter

    # Connect basic flow
    links.new(input_node.outputs["Geometry"], curve_to_mesh.inputs["Curve"])
    links.new(curve_line.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])
    links.new(curve_to_mesh.outputs["Mesh"], output_node.inputs["Geometry"])

    # Connect width and height to quadrilateral
    links.new(input_node.outputs["Bottom Width"], curve_line.inputs["Width"])
    links.new(input_node.outputs["Height"], curve_line.inputs["Height"])

    return ng


def create_preview_modifier(curve_obj: bpy.types.Object) -> bpy.types.Modifier:
    """
    Create a Geometry Nodes modifier for channel preview on a curve.

    Args:
        curve_obj: The curve object to add preview to

    Returns:
        The created modifier
    """
    # Get or create the node group
    ng = get_or_create_preview_nodegroup()

    # Check if modifier already exists
    mod_name = "CADHY_Preview"
    if mod_name in curve_obj.modifiers:
        mod = curve_obj.modifiers[mod_name]
    else:
        mod = curve_obj.modifiers.new(name=mod_name, type="NODES")

    mod.node_group = ng

    return mod


def update_preview_parameters(
    curve_obj: bpy.types.Object,
    bottom_width: float = 2.0,
    height: float = 1.5,
    side_slope: float = 1.5,
    resolution: float = 1.0
) -> bool:
    """
    Update the preview modifier parameters.

    Args:
        curve_obj: The curve object with preview modifier
        bottom_width: Channel bottom width
        height: Channel height
        side_slope: Side slope (H:V)
        resolution: Mesh resolution

    Returns:
        True if successful
    """
    mod_name = "CADHY_Preview"
    if mod_name not in curve_obj.modifiers:
        return False

    mod = curve_obj.modifiers[mod_name]

    # Update parameters through modifier interface
    # The parameter names match the socket names in the node group
    try:
        mod["Socket_2"] = bottom_width  # Bottom Width
        mod["Socket_3"] = height         # Height
        mod["Socket_4"] = side_slope     # Side Slope
        mod["Socket_5"] = resolution     # Resolution
        return True
    except Exception as e:
        print(f"[CADHY] Preview parameter update failed: {e}")
        return False


def remove_preview_modifier(curve_obj: bpy.types.Object) -> bool:
    """
    Remove the preview modifier from a curve.

    Args:
        curve_obj: The curve object

    Returns:
        True if removed
    """
    mod_name = "CADHY_Preview"
    if mod_name in curve_obj.modifiers:
        curve_obj.modifiers.remove(curve_obj.modifiers[mod_name])
        return True
    return False


def has_preview_modifier(curve_obj: bpy.types.Object) -> bool:
    """Check if curve has preview modifier."""
    return "CADHY_Preview" in curve_obj.modifiers


def toggle_preview(curve_obj: bpy.types.Object, enable: bool = True) -> bool:
    """
    Toggle preview visibility.

    Args:
        curve_obj: The curve object
        enable: Whether to enable or disable preview

    Returns:
        True if successful
    """
    mod_name = "CADHY_Preview"
    if mod_name in curve_obj.modifiers:
        curve_obj.modifiers[mod_name].show_viewport = enable
        curve_obj.modifiers[mod_name].show_render = False  # Never render preview
        return True
    return False


# =============================================================================
# ADVANCED PROFILE GENERATION (Trapezoidal, etc.)
# =============================================================================


def create_trapezoidal_profile_group() -> bpy.types.NodeTree:
    """
    Create a more sophisticated trapezoidal profile generator.
    Uses math nodes to compute profile points.
    """
    group_name = "CADHY_TrapezoidalProfile"

    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    ng = bpy.data.node_groups.new(name=group_name, type="GeometryNodeTree")

    # Interface
    ng.interface.new_socket("Curve", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Bottom Width", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Height", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Side Slope", in_out="INPUT", socket_type="NodeSocketFloat")

    nodes = ng.nodes
    links = ng.links

    # Group I/O
    input_node = nodes.new("NodeGroupInput")
    input_node.location = (-800, 0)

    output_node = nodes.new("NodeGroupOutput")
    output_node.location = (400, 0)

    # Calculate top width: top_width = bottom_width + 2 * side_slope * height
    # Using math nodes

    # Multiply: side_slope * height
    mult1 = nodes.new("ShaderNodeMath")
    mult1.operation = "MULTIPLY"
    mult1.location = (-600, -100)
    links.new(input_node.outputs["Side Slope"], mult1.inputs[0])
    links.new(input_node.outputs["Height"], mult1.inputs[1])

    # Multiply by 2
    mult2 = nodes.new("ShaderNodeMath")
    mult2.operation = "MULTIPLY"
    mult2.inputs[1].default_value = 2.0
    mult2.location = (-400, -100)
    links.new(mult1.outputs[0], mult2.inputs[0])

    # Add to bottom width
    add1 = nodes.new("ShaderNodeMath")
    add1.operation = "ADD"
    add1.location = (-200, -100)
    links.new(input_node.outputs["Bottom Width"], add1.inputs[0])
    links.new(mult2.outputs[0], add1.inputs[1])

    # Create trapezoid using Quadrilateral in TRAPEZOID mode
    trapezoid = nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    trapezoid.mode = "TRAPEZOID"
    trapezoid.location = (0, 0)

    links.new(input_node.outputs["Bottom Width"], trapezoid.inputs["Bottom Width"])
    links.new(add1.outputs[0], trapezoid.inputs["Top Width"])
    links.new(input_node.outputs["Height"], trapezoid.inputs["Height"])

    # Output
    links.new(trapezoid.outputs["Curve"], output_node.inputs["Curve"])

    return ng


def cleanup_preview_resources():
    """Remove all CADHY preview node groups (for cleanup)."""
    groups_to_remove = [
        GN_PREVIEW_NAME,
        "CADHY_TrapezoidalProfile",
    ]

    for name in groups_to_remove:
        if name in bpy.data.node_groups:
            ng = bpy.data.node_groups[name]
            if ng.users == 0:
                bpy.data.node_groups.remove(ng)
