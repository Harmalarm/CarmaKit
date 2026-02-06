import bpy
import os

from bpy_extras import object_utils
from pathlib import Path
from . import ct_DatParser, ct_ActParser, ct_MatParser

def importModel(fileName):
    
    filePath = Path(fileName)
    fileDir = filePath.parent
    fileType = filePath.suffix
    shortFileName = filePath.stem
    
    sdfFile = fileDir / (shortFileName + '.sdf')
    actFile = fileDir / (shortFileName + '.act')
    datFile = fileDir / (shortFileName + '.dat')
    matFile = fileDir / (shortFileName + '.mat')

    # sdf file, here we try to find the act, dat and mat file
    if matFile.exists():
        mat_materials = ct_MatParser.import_mat(matFile)
    
    if datFile.exists():
        dat_models = ct_DatParser.import_dat(datFile)
    
    if actFile.exists():
        act_actors = ct_ActParser.import_act(actFile)
        
    actors = ct_ActParser.build_actors(act_actors, dat_models, mat_materials)
    
    return fileName

#fileName = "D:\Files\Python\CT_Importer\Data\CARS\eagle3\EAGLE3.sdf"
#matFile = importModel(fileName)

#print(matFile)

