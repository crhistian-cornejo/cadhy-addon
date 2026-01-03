"""
Assign Materials Operator
Operator to assign predefined materials to CADHY objects.
"""

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

from ...core.util.logging import OperationLogger

# Material definitions
MATERIAL_PRESETS = {
    "CONCRETE": {
        "name": "CADHY_Concrete",
        "color": (0.6, 0.6, 0.6, 1.0),
        "roughness": 0.8,
        "metallic": 0.0,
    },
    "EARTH": {
        "name": "CADHY_Earth",
        "color": (0.4, 0.3, 0.2, 1.0),
        "roughness": 0.9,
        "metallic": 0.0,
    },
    "STEEL": {
        "name": "CADHY_Steel",
        "color": (0.5, 0.5, 0.55, 1.0),
        "roughness": 0.3,
        "metallic": 0.9,
    },
    "WATER": {
        "name": "CADHY_Water",
        "color": (0.2, 0.4, 0.8, 0.8),
        "roughness": 0.1,
        "metallic": 0.0,
        "transmission": 0.9,
    },
    "GRASS": {
        "name": "CADHY_Grass",
        "color": (0.2, 0.5, 0.15, 1.0),
        "roughness": 0.9,
        "metallic": 0.0,
    },
}


def get_or_create_material(preset_name: str) -> bpy.types.Material:
    """Get or create a material from preset."""
    preset = MATERIAL_PRESETS.get(preset_name)
    if not preset:
        return None

    mat_name = preset["name"]

    # Check if material exists
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    # Create new material
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True

    # Get principled BSDF node
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = preset["color"]
        bsdf.inputs["Roughness"].default_value = preset.get("roughness", 0.5)
        bsdf.inputs["Metallic"].default_value = preset.get("metallic", 0.0)

        if "transmission" in preset:
            bsdf.inputs["Transmission Weight"].default_value = preset["transmission"]
            mat.blend_method = "BLEND"

    return mat


class CADHY_OT_AssignMaterials(Operator):
    """Assign materials to CADHY objects"""

    bl_idname = "cadhy.assign_materials"
    bl_label = "Assign Material"
    bl_description = "Assign predefined material to selected object"
    bl_options = {"REGISTER", "UNDO"}

    material: EnumProperty(
        name="Material",
        description="Material preset to apply",
        items=[
            ("CONCRETE", "Concrete", "Gray concrete material"),
            ("EARTH", "Earth", "Brown earth/soil material"),
            ("STEEL", "Steel", "Metallic steel material"),
            ("WATER", "Water", "Transparent water material"),
            ("GRASS", "Grass", "Green grass material"),
        ],
        default="CONCRETE",
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        """Execute the operator."""
        obj = context.active_object

        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "No mesh object selected")
            return {"CANCELLED"}

        with OperationLogger("Assign Material", self) as logger:
            # Get or create material
            mat = get_or_create_material(self.material)

            if not mat:
                self.report({"ERROR"}, f"Unknown material preset: {self.material}")
                return {"CANCELLED"}

            # Assign to object
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

            logger.set_success(f"Assigned {mat.name} to {obj.name}")

        return {"FINISHED"}

    def invoke(self, context, event):
        """Show material selection."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw operator options."""
        layout = self.layout
        layout.prop(self, "material")


class CADHY_OT_AssignAllMaterials(Operator):
    """Assign appropriate materials to all CADHY objects"""

    bl_idname = "cadhy.assign_all_materials"
    bl_label = "Assign All Materials"
    bl_description = "Automatically assign materials to all CADHY objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return True

    def execute(self, context):
        """Execute the operator."""
        with OperationLogger("Assign All Materials", self) as logger:
            assigned_count = 0

            for obj in bpy.data.objects:
                if obj.type != "MESH":
                    continue

                mat = None

                # Check if it's a CADHY channel
                if hasattr(obj, "cadhy_channel") and obj.cadhy_channel.is_cadhy_object:
                    mat = get_or_create_material("CONCRETE")

                # Check if it's a CADHY CFD domain
                elif hasattr(obj, "cadhy_cfd") and obj.cadhy_cfd.is_cadhy_object:
                    mat = get_or_create_material("WATER")

                # Check by collection
                else:
                    for coll in obj.users_collection:
                        if "Channel" in coll.name:
                            mat = get_or_create_material("CONCRETE")
                            break
                        elif "CFD" in coll.name:
                            mat = get_or_create_material("WATER")
                            break

                if mat:
                    if obj.data.materials:
                        obj.data.materials[0] = mat
                    else:
                        obj.data.materials.append(mat)
                    assigned_count += 1

            logger.set_success(f"Assigned materials to {assigned_count} objects")

        return {"FINISHED"}
