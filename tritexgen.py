import PIL.Image as pil
import sys
import math
import numpy
import zlib

def word(num):
	return num.to_bytes(2, "little")

def dword(num):
	return num.to_bytes(4, "little")

def gen_texture(file, texfile, mustbesquare):
	img = pil.open(texfile).convert("P", palette=pil.Palette.ADAPTIVE, colors=256)
	w,h = img.size
	w2 = int(math.pow(2, math.ceil(math.log(w, 2))))

	if mustbesquare:
		if w != w2:
			print("  Error: texture width is not a power of 2!")
			sys.exit()

		if w != h:
			print("  Error: texture is not square!")
			sys.exit()

	print("  Loaded texuture: %dx%d pixels" % (w, h))
	
	if not mustbesquare:
		print("  Width expanded to %d pixels" % (w2))

	file.write("triImage".encode()) # magic
	file.write(dword(1)) # numFrames
	file.write(dword(0)) # reserved
	file.write(word(5)) # texture fmt - GU_PSM_T8
	file.write(word(3)) # palette fmt - GU_PSM_8888
	file.write(word(4)) # zlib compression, no swizzling
	file.write(word(0)) # numFrames
	file.write(word(0)) # delay - only for anims
	file.write(word(0)) # xOffs
	file.write(word(0)) # yOffs
	file.write(word(0)) # reserved

	indata = numpy.array(img.getdata())

	# Write palette

	pal = img.getpalette()

	if len(pal) != 768:
		print("Error! Palette has %d entries, expected 768!" % (len(pal)))
		sys.exit()

	for i in range(256):
		for j in range(3):
			file.write(bytes([pal[i * 3 + j]]))

		file.write(bytes([0xFF])) # Transparency byte

	# Write texture header

	file.write(dword(w)) # width
	file.write(dword(h)) # height
	file.write(dword(w2)) # width aligned to 2^x

	output = bytes([])

	for y in range(h):
		for x in range(w2):
			if x < w:
				output += bytes([indata[x + y * w]])
			else:
				output += bytes([0])

	compressed = zlib.compress(output)
	file.write(dword(len(compressed)))
	file.write(compressed)


if __name__ == "__main__":
	if len(sys.argv) != 3:
		print("Usage: %s inputtexture.png output.tri" % (sys.argv[0]))
		sys.exit()

	tri = open(sys.argv[2], "wb")

	print("Converting %s..." % (sys.argv[2]))
	gen_texture(tri, sys.argv[1], 0)
	tri.close()
	print("\nDone!")
