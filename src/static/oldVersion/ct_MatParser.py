import bpy
import os
from .ct_BinaryReader import *


class MatMaterial:
    color = [0, 0, 0]
    ambient_light = 0
    directional_light = 0
    specular_light = 0
    specular_power = 0
    flags = 1
    transformation_matrix = [[0, 0, 0], [0, 0, 0]]
    name = ""
    bitmap_name = ""


def import_mat(matfile):

    mat_materials = []
    mat = MatMaterial()

    with open(matfile, 'rb') as f:
        file_size = get_size(f)
        
        # read header
        h1 = read_int(f) 
        h2 = read_int(f) 
        h3 = read_int(f) 
        h4 = read_int(f)
        if h1 != 18 and h2!=8 and h3!=5 and h4!=2:
            print("file is not a proper c2 mat file")
        
        else:
            f.seek(0,0)
            while (f.tell() < file_size):
                identifier = read_int(f)
                block_length = read_int(f)

                #material entry and properties
                if identifier == 60:
                    mat = MatMaterial()

                    r = read_char(f)
                    g = read_char(f)
                    b = read_char(f)
                    a = read_char(f)
                    mat.color = [r, g, b, a]

                    mat.ambient_light = read_float(f)
                    mat.directional_light = read_float(f)
                    mat.specular_light = read_float(f)
                    mat.specular_power = read_float(f)
                    mat.flags = read_int(f)
                    mat.transformation_matrix = [[read_float(f), read_float(f), read_float(f)], [
                        read_float(f), read_float(f), read_float(f)]]
                    read_int(f)
                    for i in range(13):
                        read_char(f)
                    mat.name = read_string(f)

                # bitmap name
                if identifier == 28:
                    mat.bitmap_name = read_string(f)
                    
                # end of material entry
                if identifier == 0:
                    bmat = build_material(mat, matfile)
                    mat_materials.append(bmat)
    return mat_materials


def build_material(mat, mat_path):
    
    # remove old existing materials
    #bmat = bpy.data.materials.get(mat.name)
    #if bmat:
        #print (f"material {mat.name} already exists. Removing it and making a new one")
    #    bpy.data.materials.remove(bmat)
    
    #create a fresh material
    bmat = bpy.data.materials.new(name=mat.name)
    bmat.use_nodes = True
    tif_path = mat_path.parent / "tiffrgb"
    if mat.bitmap_name != "":
        # add bitmap
        bitmap_path = tif_path / (f"{mat.bitmap_name}.tif")
        if bitmap_path.exists():
            nodes = bmat.node_tree.nodes
            principled_bsdf = nodes.get("Principled BSDF")
            if principled_bsdf is None:
                principled_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
            material_output = nodes.get("Material Output")
            if material_output is None:
                material_output = nodes.new(type="ShaderNodeOutputMaterial")
            links = bmat.node_tree.links
            links.new(principled_bsdf.outputs["BSDF"], material_output.inputs["Surface"])

            # Add an image texture to the material and connect it to the Base Color of the Principled BSDF
            if os.path.exists(bitmap_path):
                image = bpy.data.images.load(str(bitmap_path))
                texture = bpy.data.textures.new(name="Texture", type='IMAGE')
                texture.image = image
                #texture.use_interpolation = False
                #texture.filter_type = 'BOX'
                texture_node = nodes.new(type="ShaderNodeTexImage")
                texture_node.image = image
                texture_node.interpolation = 'Closest' 
                links.new(texture_node.outputs["Color"], principled_bsdf.inputs["Base Color"])
                links.new(texture_node.outputs["Alpha"], principled_bsdf.inputs["Alpha"])        
    return bmat
