"""
Read-only diagnostic for root-motion location keys in Aline actions.

Para cada action en TARGET_ACTIONS reporta, para los bones de interés y los
top movers globales, las curvas de location y el rango de cada axis. La
métrica "max excursion" mide la diferencia max-min dentro de la action
(no end-to-end), porque algunos clips arrancan y terminan en el mismo
sitio aunque tengan motion durante el clip.

Importante: Blender almacena pose.bones[X].location en espacio LOCAL del
bone (eje Y local del bone = "forward" del bone). El bone "root" del rig
de Aline tiene Y local apuntando hacia adelante del personaje, así que
el motion del dash vive en `root.location[1]`, no en [0] o [2]. Cualquier
métrica que asuma "X mundo + Z mundo" pierde el motion real — por eso
el script reporta los 3 axes por separado.

Run desde Blender:
  - Abrir Aline_project.blend (las actions de los .psa deben existir)
  - Scripting workspace, Run Script
  - Alternativa: vía MCP execute_blender_code (capturar stdout con
    contextlib.redirect_stdout porque el MCP no devuelve prints).
"""

import re
import bpy

ARMATURE_NAME = "SK_Curator_Aline"
TARGET_ACTIONS = [
    "Paintress_DashIn-Idle1",
    "Paintress_DashOut-Idle2",
    "Paintress_Idle1",
    "DefaultSlot",
]
BONES_OF_INTEREST = ("root", "pelvis", "spine_01")
TOP_N = 5
EPSILON = 0.5  # Blender units, ~0.5cm en el rig de Aline (export en cm)

PATH_RE = re.compile(r'pose\.bones\["([^"]+)"\]\.(\w+)$')


def _max_excursion(fc):
    if fc is None or len(fc.keyframe_points) < 2:
        return 0.0, 0.0, 0.0
    vals = [kp.co[1] for kp in fc.keyframe_points]
    return vals[0], vals[-1], max(vals) - min(vals)


def _split_curves(action):
    bone_props = {}      # bone -> { property_name -> {axis: fc} }
    obj_props = {}       # property_name -> {axis: fc}
    for fc in action.fcurves:
        dp = fc.data_path
        m = PATH_RE.match(dp)
        if m:
            bone, prop = m.group(1), m.group(2)
            bone_props.setdefault(bone, {}).setdefault(prop, {})[fc.array_index] = fc
        elif "." not in dp and "[" not in dp:
            obj_props.setdefault(dp, {})[fc.array_index] = fc
    return bone_props, obj_props


def inspect_action(action_name):
    a = bpy.data.actions.get(action_name)
    if a is None:
        print("[miss] action '{}' not found".format(action_name))
        return
    print("=== {} (frames {} -> {}) ===".format(action_name, int(a.frame_range[0]), int(a.frame_range[1])))
    bone_props, obj_props = _split_curves(a)

    if obj_props:
        print("  OBJECT-level keys:", list(obj_props.keys()))

    # Bones of interest: dump location y rotation_quaternion summary
    for bone in BONES_OF_INTEREST:
        props = bone_props.get(bone)
        if not props:
            print("  {}: NO CURVES".format(bone))
            continue
        loc = props.get("location", {})
        for ax in (0, 1, 2):
            v0, vN, exc = _max_excursion(loc.get(ax))
            print("    {}.location[{}] start={:>10.4f} end={:>10.4f} exc={:>10.4f}".format(bone, "XYZ"[ax], v0, vN, exc))
        rot = props.get("rotation_quaternion", {})
        rot_max = 0.0
        for ax in (0, 1, 2, 3):
            _, _, exc = _max_excursion(rot.get(ax))
            if exc > rot_max:
                rot_max = exc
        print("    {}.rotation_quaternion max excursion: {:.4f}".format(bone, rot_max))

    # Top movers globally by total location excursion (sum of 3 axes)
    cands = []
    for bone, props in bone_props.items():
        loc = props.get("location", {})
        ex_x = _max_excursion(loc.get(0))[2] if 0 in loc else 0.0
        ex_y = _max_excursion(loc.get(1))[2] if 1 in loc else 0.0
        ex_z = _max_excursion(loc.get(2))[2] if 2 in loc else 0.0
        total = ex_x + ex_y + ex_z
        cands.append((total, bone, ex_x, ex_y, ex_z))
    cands.sort(reverse=True)
    print("  Top {} bones by total location excursion (intra-frame max-min):".format(TOP_N))
    print("    {:<24} {:>10} {:>10} {:>10}".format("bone", "excX", "excY", "excZ"))
    for total, bone, ex, ey, ez in cands[:TOP_N]:
        print("    {:<24} {:>10.4f} {:>10.4f} {:>10.4f}".format(bone, ex, ey, ez))

    # Verdict
    root_loc = bone_props.get("root", {}).get("location", {})
    root_motion = max(
        _max_excursion(root_loc.get(0))[2] if 0 in root_loc else 0.0,
        _max_excursion(root_loc.get(1))[2] if 1 in root_loc else 0.0,
        _max_excursion(root_loc.get(2))[2] if 2 in root_loc else 0.0,
    )
    if root_motion > EPSILON:
        print("  >> 'root' bone HAS location motion (max axis excursion: {:.2f}). FBX should expose this as root motion.".format(root_motion))
    else:
        if cands and cands[0][0] > EPSILON:
            print("  >> 'root' bone is flat. Top mover '{}' (excursion total {:.2f}). Motion baked in non-root bone.".format(cands[0][1], cands[0][0]))
        else:
            print("  >> No location motion in any bone. Action is purely rotational or static.")


def main():
    print("[inspect] file: {}".format(bpy.data.filepath))
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None:
        print("[inspect] WARNING armature '{}' not in scene".format(ARMATURE_NAME))
    else:
        roots = [b.name for b in arm.data.bones if b.parent is None]
        print("[inspect] armature has {} bones; root-level: {}".format(len(arm.data.bones), roots))

    for action_name in TARGET_ACTIONS:
        inspect_action(action_name)
        print()


if __name__ == "__main__":
    main()
