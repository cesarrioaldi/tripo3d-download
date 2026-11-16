"""Blender-side converter, called as:
  blender.exe -b --python tripo_convert.py -- <src> <dst>
Imports src (glb/gltf/fbx/obj/stl) and exports dst by its extension.
"""
import bpy, sys, pathlib

argv = sys.argv[sys.argv.index("--") + 1:]
src, dst = argv[0], argv[1]
sext = pathlib.Path(src).suffix.lower()
dext = pathlib.Path(dst).suffix.lower()

bpy.ops.wm.read_factory_settings(use_empty=True)

if sext in (".glb", ".gltf"):
    bpy.ops.import_scene.gltf(filepath=src)
elif sext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=src)
elif sext == ".obj":
    bpy.ops.wm.obj_import(filepath=src)
elif sext == ".stl":
    bpy.ops.wm.stl_import(filepath=src)
else:
    raise SystemExit(f"unsupported input {sext}")

if dext in (".glb", ".gltf"):
    bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB")
elif dext == ".fbx":
    bpy.ops.export_scene.fbx(filepath=dst, path_mode="COPY", embed_textures=True)
elif dext == ".obj":
    bpy.ops.wm.obj_export(filepath=dst, export_materials=True, path_mode="COPY")
elif dext == ".stl":
    bpy.ops.wm.stl_export(filepath=dst)
else:
    raise SystemExit(f"unsupported output {dext}")

print("CONVERTED", dst)
