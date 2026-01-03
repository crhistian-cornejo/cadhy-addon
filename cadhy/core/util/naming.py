"""
Naming Module
Consistent naming conventions for CADHY objects.
"""

# Prefixes for different object types
PREFIX_CHANNEL = "CADHY_Channel"
PREFIX_CFD_DOMAIN = "CADHY_CFD_Domain"
PREFIX_SECTION = "CADHY_Section"
PREFIX_AXIS = "CADHY_Axis"

# Collection names
COLLECTION_CHANNELS = "CADHY_Channels"
COLLECTION_CFD = "CADHY_CFD"
COLLECTION_SECTIONS = "CADHY_Sections"
COLLECTION_AXES = "CADHY_Axes"

# Material prefixes
MAT_PREFIX = "CADHY_Mat"


def get_channel_name(axis_name: str) -> str:
    """
    Generate channel object name from axis name.

    Args:
        axis_name: Name of the axis curve

    Returns:
        Channel object name
    """
    # Remove any existing CADHY prefix
    clean_name = axis_name.replace(PREFIX_AXIS + "_", "")
    return f"{PREFIX_CHANNEL}_{clean_name}"


def get_cfd_domain_name(axis_name: str) -> str:
    """
    Generate CFD domain object name from axis name.

    Args:
        axis_name: Name of the axis curve

    Returns:
        CFD domain object name
    """
    clean_name = axis_name.replace(PREFIX_AXIS + "_", "")
    return f"{PREFIX_CFD_DOMAIN}_{clean_name}"


def get_section_name(axis_name: str, station: float) -> str:
    """
    Generate section object name.

    Args:
        axis_name: Name of the axis curve
        station: Station/chainage in meters

    Returns:
        Section object name
    """
    clean_name = axis_name.replace(PREFIX_AXIS + "_", "")
    return f"{PREFIX_SECTION}_{clean_name}_{station:.1f}m"


def get_material_name(material_type: str) -> str:
    """
    Generate material name.

    Args:
        material_type: Type of material (e.g., 'concrete', 'water')

    Returns:
        Material name
    """
    return f"{MAT_PREFIX}_{material_type}"


def parse_cadhy_name(name: str) -> dict:
    """
    Parse a CADHY object name to extract components.

    Args:
        name: Object name

    Returns:
        Dictionary with parsed components
    """
    result = {"is_cadhy": False, "type": None, "base_name": None, "station": None}

    if not name.startswith("CADHY_"):
        return result

    result["is_cadhy"] = True

    parts = name.split("_")

    if len(parts) >= 2:
        type_part = parts[1]

        if type_part == "Channel":
            result["type"] = "channel"
            result["base_name"] = "_".join(parts[2:])
        elif type_part == "CFD":
            result["type"] = "cfd_domain"
            result["base_name"] = "_".join(parts[3:]) if len(parts) > 3 else ""
        elif type_part == "Section":
            result["type"] = "section"
            if len(parts) >= 3:
                # Try to extract station from last part
                last_part = parts[-1]
                if last_part.endswith("m"):
                    try:
                        result["station"] = float(last_part[:-1])
                        result["base_name"] = "_".join(parts[2:-1])
                    except ValueError:
                        result["base_name"] = "_".join(parts[2:])
                else:
                    result["base_name"] = "_".join(parts[2:])
        elif type_part == "Axis":
            result["type"] = "axis"
            result["base_name"] = "_".join(parts[2:])
        elif type_part == "Mat":
            result["type"] = "material"
            result["base_name"] = "_".join(parts[2:])

    return result


def ensure_collection(collection_name: str) -> "bpy.types.Collection":
    """
    Get or create a collection by name.

    Args:
        collection_name: Name of collection

    Returns:
        Blender collection object
    """
    import bpy

    if collection_name not in bpy.data.collections:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[collection_name]

    return collection


def move_to_collection(obj, collection_name: str) -> None:
    """
    Move object to specified collection.

    Args:
        obj: Blender object
        collection_name: Target collection name
    """

    collection = ensure_collection(collection_name)

    # Remove from all current collections
    for coll in obj.users_collection:
        coll.objects.unlink(obj)

    # Add to target collection
    collection.objects.link(obj)
