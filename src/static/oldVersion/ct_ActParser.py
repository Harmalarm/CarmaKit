import bpy
from .ct_BinaryReader import *
import math
from mathutils import Matrix, Euler, Vector


class ActObject:
    rendermode1 = 1
    rendermode2 = 4
    actor_name = ""
    matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0]]
    bbox = [[0, 0, 0], [0, 0, 0]]
    material_name = ""
    model_name = ""
    parent = None
    parentIndex = None


def import_act(actfile):
    act_objects = []
    act_object = ActObject()
    parent = None
    parentIndex = -1

    with open(actfile, 'rb') as f:
        file_size = get_size(f)

        # read header
        first = read_float(f)
        second = read_float(f)
        face = read_float(f)
        two = read_float(f)

        while (f.tell() < file_size):
            identifier = read_int(f)
            block_length = read_int(f)

            # actor start and properties
            if identifier == 35:
                act_object = ActObject()
                
                #apply the parentIndex before incrementing
                act_object.parentIndex = parentIndex
                act_objects.append(act_object)
                
                #increment the parentIndex
                parentIndex = (len(act_objects) - 1)

                act_object.rendermode1 = read_char(f)
                act_object.rendermode2 = read_char(f)
                act_object.actor_name = read_string(f)

            # transformation matrix
            if identifier == 43:
                x1 = read_float(f)
                x2 = read_float(f)
                x3 = read_float(f)
                y1 = read_float(f)
                y2 = read_float(f)
                y3 = read_float(f)
                z1 = read_float(f)
                z2 = read_float(f)
                z3 = read_float(f)
                p1 = read_float(f)
                p2 = read_float(f)
                p3 = read_float(f)
                
                act_matrix = Matrix((
                    (x1, x2, x3, p1),
                    (y1, y2, y3, p2),
                    (z1, z2, z3, p3),
                    (0, 0, 0, 1),
                ))
                
                #extract rotation matrix and re-arrange rotations
                euler = (act_matrix.to_euler('XYZ'))
                rotation_matrix = (Euler([-euler.x,euler.z,-euler.y], 'YZX').to_matrix()).to_4x4()
                #create position matrix
                translation_matrix = Matrix.Translation(Vector((p1,-p3,p2)))
                #extract scale matrix and re-arrange scales
                scale_x = act_matrix.col[0].length
                scale_y = act_matrix.col[1].length
                scale_z = act_matrix.col[2].length
                scale_matrix = Matrix.Diagonal(Vector((scale_x,scale_z,scale_y))).to_4x4()
                
                #create transformation matrix
                transformation_matrix = translation_matrix @ rotation_matrix @ scale_matrix
                
                act_object.matrix = transformation_matrix
                
            # unknown 
            if identifier == 37:
                pass
            
            # bounding box
            if identifier == 50:
                xmin = read_float(f)
                ymin = read_float(f)
                zmin = read_float(f)
                xmax = read_float(f)
                ymax = read_float(f)
                zmax = read_float(f)
                act_object.bbox = [[xmin, ymin, zmin], [xmax, ymax, zmax]]

            # start hierarchy level
            if identifier == 41:  
                pass
            
            # actor materials
            if identifier == 38:
                act_object.material_name = read_string(f)

            # model names
            if identifier == 36:
                act_object.model_name = read_string(f)

            # end hierarchy level
            if identifier == 42:  
                #decrement the parentIndex
                parentIndex = (act_objects[parentIndex]).parentIndex
            
            # EOF
            if identifier == 0:
                
                pass
    return act_objects


def build_actors(act_actors, dat_models, mat_materials):
    built_actors = []
    
    for act_actor in act_actors:
        # define empty actor
        actor = None
        
        # collect parent object
        parent = None
        if act_actor.parentIndex != -1:
            parent = built_actors[act_actor.parentIndex]
            
        # collect model object
        model = None
        for dat_model in dat_models:
            if dat_model.name == act_actor.model_name:
                model = dat_model
                exit

        # build actor with model
        if model != None:
            actor = bpy.data.objects.new(act_actor.actor_name, model.mesh)
            
            # add materials to the actor or use actor materials
            if act_actor.material_name != "":
                mat = bpy.data.materials.get(f'{act_actor.material_name}')
                actor.data.materials.append(mat)
            else:
                mat_count = len(model.mat_names)
               
                for i in range(mat_count):
                    mat_name = model.mat_names[i]
                    for mat in mat_materials:
                        if mat.name == mat_name:
                            actor.data.materials.append(mat)
                    #mat = mat_materials.get(f'{mat_name}')
                    #mat = bpy.data.materials.get(f'{mat_name}')
        else:
            #print('dummy actor')
            actor = bpy.data.objects.new(act_actor.actor_name, None)
            actor.empty_display_size = 0.1
        
        bpy.context.collection.objects.link(actor)
        actor.parent = parent
        #actor.matrix_local = act_actor.matrix
        if parent != None:
            actor.matrix_world = act_actor.matrix @ actor.parent.matrix_world
        else:
            actor.matrix_world = act_actor.matrix
        
        #store the actor in the built actors list
        built_actors.append(actor)
        
