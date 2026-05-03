"""
Convert a single .pskx/.psk (UE mesh, optionally rigged) to .fbx for Unity import.

Run from Blender CLI:
  blender --background --python scripts\blender\pskx_to_fbx.py -- <input.pskx> [output.fbx]

If output.fbx is omitted, writes alongside input with .fbx extension.

Si el archivo trae armature + skin weights (típico .psk de skeletal mesh, ej. hair
con strand bones), el script lo preserva y exporta el FBX con MESH + ARMATURE
para que Unity instancie SkinnedMeshRenderer. Si solo trae mesh estático, exporta
mesh sin más.

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

    # UE → m: el addon de PSK importa vertices/bones con valores literales de UE
    # (centímetros) pero Blender los trata como metros. Sin scale-down, el FBX
    # sale 100x demasiado grande en Unity.
    #
    # - Static (sólo MESH): set scale 0.01 en el mesh, apply transform.
    # - Rigged (MESH + ARMATURE): NO pre-aplicamos en Blender. Pre-aplicar
    #   doble-bakea (mesh y armature compondrían la deformación). En su lugar,
    #   delegamos el scale al FBX exporter via global_scale=0.01 +
    #   apply_scale_options='FBX_SCALE_ALL' que baja uniformemente bones +
    #   vertices en una sola pasada coherente.
    UE_TO_M = 0.01
    armatures = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    has_armature = len(armatures) > 0

    if not has_armature:
        for obj in meshes:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            obj.scale = (UE_TO_M, UE_TO_M, UE_TO_M)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    object_types = {"MESH", "ARMATURE"} if has_armature else {"MESH"}

    # Export as FBX with Unity conventions: Y-up, Z-forward, no animations.
    # Static: pre-scale ya hecho, global_scale=1.0.
    # Rigged: global_scale=0.01 + apply_scale_options='FBX_SCALE_ALL' baja
    #   bones+mesh juntos uniformemente en el export.
    # use_armature_deform_only=False incluye TODOS los strand bones aunque
    # alguno no tenga weights. armature_nodetype='ROOT' evita el "Armature"
    # dummy node intermedio que añade Blender por defecto.
    global_scale = UE_TO_M if has_armature else 1.0
    apply_scale_options = "FBX_SCALE_ALL" if has_armature else "FBX_SCALE_NONE"

    bpy.ops.export_scene.fbx(
        filepath=out,
        use_selection=False,
        global_scale=global_scale,
        apply_unit_scale=True,
        apply_scale_options=apply_scale_options,
        bake_space_transform=True,
        axis_forward="-Z",
        axis_up="Y",
        object_types=object_types,
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        armature_nodetype="ROOT",
        use_armature_deform_only=False,
        bake_anim=False,
    )

    print(f"OK: {inp} -> {out}")


if __name__ == "__main__":
    main()
