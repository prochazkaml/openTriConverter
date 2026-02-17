# Moved over to [Codeberg](https://codeberg.org/prochazkaml/openTriConverter).

---

# openTriConverter
A texture & 3D model converter for the openTri PSP 3D game engine.

The texture converter (`tritexgen.py`) is quite simple: you pass it an image file (.PNG, preferrably), and it spits out a .tri image file.

The model converter (`obj2trim.py`) is a bit more involved, you need to pass it an .OBJ file
(which must consist only of triangles and must contain geometric vertices, texture coordinates and vector normals)
and a texture image file, which must be square and its width & height must be a power of 2.
It outputs a .trim file, which contains both the mesh as well as the texture.

Requires Python 3.10 or newer (as it uses the match/case syntax) with the `numpy` and `Pillow` libraries installed.

## TODO

- transparent textures
- more than 8-bit textures
- more supported file formats
- support for more parts, models & textures in a single model file
- a simple working code example
