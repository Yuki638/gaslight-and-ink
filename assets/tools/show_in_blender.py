# Imports approved FBX assets into the user's open Blender, one collection per kit, laid out in a row.
# Edit KIT/NAMES below, then: python tools/blender_gui.py tools/show_in_blender.py
import bpy

EXPORT = r"D:\claude\roblox1\assets\export"
KIT = "Facade Kit"
NAMES = ["SashWindow", "Door", "ChimneyStack"]
Y_OFFSET = 16.0

col = bpy.data.collections.get(KIT) or bpy.data.collections.new(KIT)
if col.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(col)
for o in list(col.objects):
    bpy.data.objects.remove(o, do_unlink=True)

x = 0.0
placed = []
for name in NAMES:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=f"{EXPORT}\\{name}.fbx")
    new = [o for o in bpy.data.objects if o not in before]
    width = max((o.dimensions.x for o in new), default=2.0)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        o.location.x += x + width / 2
        o.location.y += Y_OFFSET
    placed.append(name)
    x += width + 2.0
result = {"collection": KIT, "placed": placed}
print(result)
