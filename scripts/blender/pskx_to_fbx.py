"""
Convert a single .pskx (UE static mesh) to .fbx for Unity import.

Run from Blender CLI:
  blender --background --python scripts\blender\pskx_to_fbx.py -- <input.pskx> [output.fbx]

If output.fbx is omitted, writes alongside input with .fbx extension.

Requires the io_scene_psk_psa addon (Befzz / DarklightGames). Same one used
by import_all_psa.py for animations.
"""

import os
import sys
import bpy


def _resolve_addon():
    candidates = [
        "bl_ext.user_default.io_scene_psk_psa",
        "io_scene_psk_psa",
    ]
    for name in candidates:
        try:
            mod = __import__(name, fromlist=["psk"])
            return mod
        except ImportError:
            continue
    raise RuntimeError("io_scene_psk_psa addon not found. Enable in Preferences > Extensions.")


def _parse_args():
    if "--" not in sys.argv:
        raise RuntimeError("Pass args after `--` separator")
    args = sys.argv[sys.argv.index("--") + 1:]
    if not args:
        raise RuntimeError("Usage: blender --background --python pskx_to_fbx.py -- <input.pskx> [output.fbx]")
    inp = os.path.abspath(args[0])
    out = os.path.abspath(args[1]) if len(args) > 1 else os.path.splitext(inp)[0] + ".fbx"
    return inp, out


def main():
    inp, out = _parse_args()
    if not os.path.isfile(inp):
        raise RuntimeError(f"Input not found: {inp}")

    addon = _resolve_addon()

    # Clear default scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Import .pskx via the addon. The operator id matches the addon's PSK importer.
    psk_import_op = bpy.ops.import_scene.psk
    psk_import_op(filepath=inp)

    # Apply the imported mesh's transforms — clean for Unity.
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Export as FBX with Unity conventions: Y-up, Z-forward, no animations
    bpy.ops.export_scene.fbx(
        filepath=out,
        use_selection=False,
        global_scale=1.0,
        apply_unit_scale=True,
        bake_space_transform=True,
        axis_forward="-Z",
        axis_up="Y",
        object_types={"MESH"},
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        bake_anim=False,
    )

    print(f"OK: {inp} -> {out}")


if __name__ == "__main__":
    main()
