if "bpy" in locals():
    import importlib
    for module in sys.modules.values():
        importlib.reload(module)
else:
    from .ct_Importer import *

# give Python access to Blender's functionality
import bpy
import sys 
import os

from bpy_extras.io_utils import ImportHelper

sys.path.append(os.path.abspath("E:\Files\Blender Python\Carmatools"))

bl_info = {
    "name": "Carmatools",
    "author": "Harm Sollie",
    "version": (0, 0, 1),
    "blender": (4, 0, 1),
    "location": "3D Viewport > Sidebar > Carmatools",
    "description": "My custom operator buttons",
    "category": "Development",
}

class ctFileLoader(bpy.types.Operator, ImportHelper):
    """Load a custom file format"""
    bl_idname = "custom.file_loader"
    bl_label = "Load Custom File"

    # Filter the file types
    filter_glob: bpy.props.StringProperty(
        default="*.act;*.dat;*.sdf",
        options={'HIDDEN'},
        maxlen=255,
    ) # type: ignore
    
    def execute(self, context):
        filepath = self.filepath
        # Your loading logic here
        
        matFile = importModel(filepath)
        
        self.report({'INFO'}, "File loaded: {}".format(matFile))
        
        return {'FINISHED'}

class VIEW3D_PT_carmatools_panel(bpy.types.Panel):  # class naming convention ‘CATEGORY_PT_name’

    # where to add the panel in the UI
    bl_space_type = "VIEW_3D"  # 3D Viewport area (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items)
    bl_region_type = "UI"  # Sidebar region (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items)

    bl_category = "Carmatools"  # found in the Sidebar
    bl_label = "Carmatools v0.1.0"  # found at the top of the Panel

    def draw(self, context):
        """define the layout of the panel"""
        row = self.layout.row()
        #row.operator("ctFileLoader.importAct", text="Import")
        row.operator("custom.file_loader", text="Load Custom File")
        
        #row = self.layout.row()
        #row.operator("mesh.primitive_ico_sphere_add", text="Add Ico Sphere")
        #row = self.layout.row()
        #row.operator("object.shade_smooth", text="Shade Smooth")


def register():
    bpy.utils.register_class(VIEW3D_PT_carmatools_panel)
    bpy.utils.register_class(ctFileLoader)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_carmatools_panel)
    bpy.utils.unregister_class(ctFileLoader)

if __name__ == "__main__":
    register()
