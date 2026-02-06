import bpy
from struct import unpack


def get_size(f):
    f.seek(0, 2)  # move the cursor to the end of the file
    size = f.tell()
    f.seek(0, 0)
    return size


def read_char(f):
    le_char = unpack('>B', f.read(1))[0]
    return le_char


def read_short(f):
    le_val = unpack('>H', f.read(2))[0]
    return le_val


def read_int(f):
    le_int = unpack('>L', f.read(4))[0]
    return le_int


def read_float(f):
    le_float = unpack('>f', f.read(4))[0]
    return le_float


def read_string(f):
    string = ""
    while True:
        char = f.read(1)
        if char == b'\x00':
            break
        else:
            string = string + char.decode('windows-1252') #.decode('utf-8').
    return string
