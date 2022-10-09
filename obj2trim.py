# requires pillow

import PIL.Image as pil
import sys
import math
import struct
import numpy
import zlib
from tritexgen import *

if len(sys.argv) != 4:
	print("Usage: %s inputtexture.png inputmesh.obj output.trim" % (sys.argv[0]))
	sys.exit()

def chunk_start(file, magic):
	file.write(magic.encode())
	file.write(dword(0))
	return file.tell()

def chunk_end(file, off):
	new_off = file.tell()
	file.seek(off - 4)
	file.write(dword(new_off - off))
	file.seek(new_off)

# Chunk generation routines

def gen_texture_chunk(file, texfile):
	print("Generating texture chunk from %s..." % (texfile))

	chunk_off = chunk_start(file, "tImg")
	file.write(bytes([0] * 64)) # filename, we don't care

	gen_texture(file, texfile, 1)

	chunk_end(file, chunk_off)

def gen_mesh_chunk(file, objfile):
	print("Generating mesh chunk from %s..." % (objfile))

	chunk_off = chunk_start(file, "tMhH")

	obj = open(objfile, "r")
	objlines = obj.read().splitlines()
	obj.close()

	v = []
	vt = []
	vn = []
	f = []

	for lnum in range(len(objlines)):
		line = objlines[lnum]
		
		if line.startswith("#"):
			continue

		entries = line.split(" ")
		
		match entries[0]:
			case "v":
				if len(entries) != 4:
					print("  ERROR: Geometric vertex @ line %d does not have exactly 3 parameters:\n    %s\n" % (lnum + 1, line))
					sys.exit()

				v.append([
					float(entries[1]),
					float(entries[2]),
					float(entries[3])
				])

			case "vt":
				if len(entries) != 3:
					print("  ERROR: Texture coordinate @ line %d does not have exactly 2 parameters:\n    %s\n" % (lnum + 1, line))
					sys.exit()

				# Adjust the values corresponding to the texture scale

				vt.append([
					float(entries[1]),
					(1 - float(entries[2]))
				])

			case "vn":
				if len(entries) != 4:
					print("  ERROR: Vertex normal @ line %d does not have exactly 3 parameters:\n    %s\n" % (lnum + 1, line))
					sys.exit()

				vn.append([
					float(entries[1]),
					float(entries[2]),
					float(entries[3])
				])

			case "f":
				if len(entries) != 4:
					print("  ERROR: Face element @ line %d does not have exactly 3 parameters (i.e. it is not a triangle):\n    %s\n" % (lnum + 1, line))
					sys.exit()

				f1 = entries[1].split("/")
				f2 = entries[2].split("/")
				f3 = entries[3].split("/")

				if len(f1) != 3 or len(f2) != 3 or len(f3) != 3:
					print("  ERROR: One or more points of the face element @ line %d does not have exacly 3 parameters (geometric vertex, texture coordinate, vertex normal):\n    %s\n" % (lnum + 1, line))
					sys.exit()

				for i in range(3):
					f1[i] = int(f1[i])
					f2[i] = int(f2[i])
					f3[i] = int(f3[i])

				f.append([f1, f2, f3])

			case _:
				print("  Warning: Unknown command @ line %d:\n    %s\n" % (lnum + 1, line))

	print("  Mesh import successful:\n    %d geometric vertices\n    %d texture coordinates\n    %d vertex normals\n    %d triangle face elements" % (len(v), len(vt), len(vn), len(f)))

	file.write(bytes([0] * 12)) # name, don't care
	file.write(dword(0b111111111)) # vertFormat (GU_TEXTURE_32BITF|GU_NORMAL_32BITF|GU_VERTEX_32BITF)
	file.write(word(len(f) * 3)) # numVerts
	file.write(word(3)) # flags (zlib compression, GU_TRIANGLES)
	file.write(word(36)) # vertSize (U, V, color, NX, NY, NZ, X, Y, Z)
	file.write(word(0)) # texID

	output = bytes([])

	for face in f:
		for vert in face:
			output += (struct.pack('f', vt[vert[1] - 1][0])) # U
			output += (struct.pack('f', vt[vert[1] - 1][1])) # V
			output += (dword(0xFFFFFFFF)) # Color
			output += (struct.pack('f', vn[vert[2] - 1][0])) # NX
			output += (struct.pack('f', vn[vert[2] - 1][1])) # NY
			output += (struct.pack('f', vn[vert[2] - 1][2])) # NZ
			output += (struct.pack('f', v[vert[0] - 1][0])) # X
			output += (struct.pack('f', v[vert[0] - 1][1])) # Y
			output += (struct.pack('f', v[vert[0] - 1][2])) # Z

	compressed = zlib.compress(output)
	file.write(dword(len(compressed))) # dataSize
	file.write(compressed)

	chunk_end(file, chunk_off)

def gen_model_chunk(file):
	print("Generating model chunk...")

	chunk_off = chunk_start(file, "tMH ")

	# Model info

	file.write(bytes([0] * 12)) # name, don't care
	file.write(word(1)) # numParts
	file.write(word(0)) # flags
	file.write(bytes([0] * 32)) # pos & rot
	
	# Part info

	file.write(bytes([0] * 12)) # name, don't care
	file.write(word(0)) # meshID
	file.write(word(0)) # texID
	file.write(bytes([0] * 32)) # pos & rot

	chunk_end(file, chunk_off)

def gen_eof_chunk(file):
	print("Generating EOF chunk...")

	chunk_off = chunk_start(file, "tEOF")
	chunk_end(file, chunk_off)

# Create output file & write file header

trim = open(sys.argv[3], "wb")

trim.write("triModel".encode()) # magic
trim.write(word(1)) # numMeshes
trim.write(word(1)) # numModels
trim.write(word(1)) # numTexs
trim.write(word(0)) # reserved

# Generate file chunks

gen_texture_chunk(trim, sys.argv[1])
gen_mesh_chunk(trim, sys.argv[2])
gen_model_chunk(trim)
gen_eof_chunk(trim)

trim.close()
print("Done!")
