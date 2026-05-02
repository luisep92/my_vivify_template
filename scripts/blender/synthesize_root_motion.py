"""
Move pose-bone 'root' location keys to armature-object location keys, per
action, in TARGET_ACTIONS, with axis remapping for the Blender->Unity FBX
axis convention.

Why: en los .psa de Aline el desplazamiento del personaje vive en
pose.bones["root"].location[1] (Y bone-local = forward del rig de Unreal).
Unity 2019.4 con Generic + Copy From Other Avatar NO extrae el motion del
bone aunque exista en transformPaths (motionNodeName="root", avatar
rebuild, keepOriginalPositionY=false — todos descartados,
hasGenericRootTransform sigue False). En cambio sí lo extrae si vive
como location del armature object (motionNodeName="SK_Curator_Aline").

Axis remap: bone-local Y (forward, source) → object-local Z (Z up Blender).
Empíricamente: Blender Y object → Unity Z m_LocalPosition que tras la
rotación -90°X del armature object (conversión Z-up→Y-up del FBX exporter)
se convierte en world -Y Unity (down) — Aline cae verticalmente. En cambio
Blender Z object → Unity Y m_LocalPosition que tras la misma rotación queda
en world +Z Unity (forward) — Aline avanza. Por eso movemos la componente
forward del bone (Y bone-local) al axis Z del object Blender.

  bone.location[0] (X = lateral)    -> object.location[0] (X)
  bone.location[1] (Y = forward)    -> object.location[2] (Z, será forward
                                       en Unity tras el axis transform)
  bone.location[2] (Z = up del bone) -> object.location[1] (Y, raramente
                                       tiene motion, pero por consistencia)

Pre-requisito: rest matrix del bone "root" identity y armature object
matrix_world identity (verificado 2026-05-01). Si dejaran de serlo habría
que componer matrices.

Idempotencia: marca cada action procesada con '_root_motion_synthesized'
con valor del axis-mapping mode aplicado. Si la action ya tiene un mode
distinto, des-aplica el viejo antes de re-aplicar el nuevo.

Run desde Blender:
  - Open Aline_project.blend
  - Scripting workspace, Run Script
  - O via MCP execute_blender_code

Después: correr export_anims_fbx.py para regenerar Aline_Anims.fbx.
"""

import bpy

ARMATURE_NAME = "SK_Curator_Aline"
ROOT_BONE = "root"
TARGET_ACTIONS = [
    "Paintress_DashIn-Idle1",
    "Paintress_DashIn-Idle2",
    "Paintress_DashOut-Idle2",
    "DefaultSlot",
    "DefaultSlot.001",
]
MARK_KEY = "_root_motion_synthesized"
# Axis mapping: dst_axis -> (src_axis, sign).
# v4 = "Y bone forward -> Z object negated".
# Bone forward (Y) needs to map to Blender object Z so it ends up on Unity
# m_LocalPosition.y → world +Z forward after the -90°X rotation of the
# armature object. Empirically the sign was inverted (Aline dashing
# backwards on DashIn), so we negate the Y-bone -> Z-object copy. The
# other axes carry no significant motion in DashIn/DashOut, but mirror
# the same convention for consistency.
AXIS_MAP_MODE = "v5-bone-y-to-object-z-negated-normalized"
AXIS_MAP = {0: (0, 1.0), 1: (2, 1.0), 2: (1, -1.0)}  # dst: (src, sign)

SOURCE_PATH = 'pose.bones["{}"].location'.format(ROOT_BONE)
TARGET_PATH = "location"


def _copy_keyframes(src_fc, dst_fc, sign=1.0):
    dst_fc.keyframe_points.add(len(src_fc.keyframe_points))
    for i, kp_src in enumerate(src_fc.keyframe_points):
        kp_dst = dst_fc.keyframe_points[i]
        kp_dst.co = (kp_src.co[0], kp_src.co[1] * sign)
        kp_dst.handle_left = (kp_src.handle_left[0], kp_src.handle_left[1] * sign)
        kp_dst.handle_right = (kp_src.handle_right[0], kp_src.handle_right[1] * sign)
        kp_dst.interpolation = kp_src.interpolation
        kp_dst.handle_left_type = kp_src.handle_left_type
        kp_dst.handle_right_type = kp_src.handle_right_type
    dst_fc.update()


def _normalize_to_origin(fc):
    """Resta el valor de frame 0 a todas las keyframes para que la action arranque en 0.

    Por qué: las curvas vienen del .psa con coordenadas absolutas en el rig de Unreal.
    Cada action tiene su propio baseline absoluto y NO coinciden cross-clip
    (ej. DashIn-Idle1 termina en y=600cm, DashOut-Idle2 empieza en y=604.49cm). Al
    transitar entre clips Unity teleporta la mesh los 4.49cm de discontinuidad =
    el saltito de ~5cm visible. Normalizando a origen, MotionT extrae deltas
    puros y todos los clips arrancan en el mismo punto (0).
    """
    if not fc.keyframe_points:
        return 0.0
    offset = fc.keyframe_points[0].co[1]
    if offset == 0.0:
        return 0.0
    for kp in fc.keyframe_points:
        kp.co = (kp.co[0], kp.co[1] - offset)
        kp.handle_left = (kp.handle_left[0], kp.handle_left[1] - offset)
        kp.handle_right = (kp.handle_right[0], kp.handle_right[1] - offset)
    fc.update()
    return offset


# Inverse mappings per mode: object_axis -> (bone_axis, sign).
# The sign is what was applied during synthesis; we apply it again on the way
# back (sign * sign == 1) so the original bone curve is restored exactly.
INVERSE_MAPS = {
    "v3-bone-y-to-object-z": {0: (0, 1.0), 1: (2, 1.0), 2: (1, 1.0)},
    "v4-bone-y-to-object-z-negated": {0: (0, 1.0), 1: (2, 1.0), 2: (1, -1.0)},
    "v5-bone-y-to-object-z-negated-normalized": {0: (0, 1.0), 1: (2, 1.0), 2: (1, -1.0)},
    True: {0: (0, 1.0), 1: (1, 1.0), 2: (2, 1.0)},  # legacy v1 (boolean flag)
}


def _undo_synthesis(action, prev_mode):
    """Move object location curves back to bone location, undoing prior synthesis."""
    inverse = INVERSE_MAPS.get(prev_mode, INVERSE_MAPS[True])

    obj_curves = {}
    for fc in list(action.fcurves):
        if fc.data_path == TARGET_PATH:
            obj_curves[fc.array_index] = fc

    moved_back = 0
    for obj_axis, (bone_axis, sign) in inverse.items():
        src = obj_curves.get(obj_axis)
        if src is None:
            continue
        dst = action.fcurves.new(data_path=SOURCE_PATH, index=bone_axis)
        _copy_keyframes(src, dst, sign=sign)
        moved_back += 1

    for fc in list(action.fcurves):
        if fc.data_path == TARGET_PATH:
            action.fcurves.remove(fc)

    if MARK_KEY in action:
        del action[MARK_KEY]
    print("[synth] undone {} axes from mode '{}'".format(moved_back, prev_mode))


def synthesize(action_name):
    action = bpy.data.actions.get(action_name)
    if action is None:
        print("[synth] action not found: {}".format(action_name))
        return False

    prev_mode = action.get(MARK_KEY)
    if prev_mode == AXIS_MAP_MODE:
        print("[synth] {} already in mode '{}', skipping".format(action_name, AXIS_MAP_MODE))
        return False
    if prev_mode:
        print("[synth] {}: previous mode '{}' detected, reverting first".format(action_name, prev_mode))
        _undo_synthesis(action, prev_mode)

    src_curves = {}
    for fc in list(action.fcurves):
        if fc.data_path == SOURCE_PATH:
            src_curves[fc.array_index] = fc

    if not src_curves:
        print("[synth] {} has no '{}' curves, skipping".format(action_name, SOURCE_PATH))
        return False

    # Remove any pre-existing object-level location curves (clean slate)
    for fc in list(action.fcurves):
        if fc.data_path == TARGET_PATH:
            action.fcurves.remove(fc)

    keys_per_axis = len(next(iter(src_curves.values())).keyframe_points)

    moved = 0
    offsets = {}
    for dst_axis, (src_axis, sign) in AXIS_MAP.items():
        src = src_curves.get(src_axis)
        if src is None:
            continue
        dst = action.fcurves.new(data_path=TARGET_PATH, index=dst_axis)
        _copy_keyframes(src, dst, sign=sign)
        offsets[dst_axis] = _normalize_to_origin(dst)
        moved += 1

    for src in list(src_curves.values()):
        action.fcurves.remove(src)

    action[MARK_KEY] = AXIS_MAP_MODE
    print("[synth] {}: moved {} axes (mode '{}'), {} keys per axis, offsets removed: {}".format(
        action_name, moved, AXIS_MAP_MODE, keys_per_axis, offsets))
    return True


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None:
        raise RuntimeError("Armature '{}' not in scene".format(ARMATURE_NAME))
    if arm.animation_data is None:
        arm.animation_data_create()

    processed = 0
    for name in TARGET_ACTIONS:
        if synthesize(name):
            processed += 1
    print("[synth] done: {} action(s) processed".format(processed))


if __name__ == "__main__":
    main()
