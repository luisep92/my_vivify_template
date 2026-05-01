"""
Export every action in the .blend as a separate Take inside one FBX.
Output is armature-only — meant to ride on top of the existing Aline.fbx
in Unity via Rig = Generic + Avatar = "Copy From Other Avatar".

Run from Blender:
  - Open Aline_project.blend
  - Open Scripting workspace, run this file (or call export_anims() from console)

Notes:
  - use_selection=True + object_types={'ARMATURE'}: only the rig + actions ship.
  - bake_anim_use_all_actions=True: every action in bpy.data.actions becomes a Take.
  - bake_anim_use_nla_strips=False: takes stay separate, no NLA blending.
  - add_leaf_bones=False: Unity adds its own; including them causes import noise.
  - Scale stays at 1.0 — set Scale Factor in Unity's FBX importer if the rig comes
    in too big (the existing Aline.fbx uses 0.01 per the project notes).
  - Pre-paso: poda de fcurves de scale en TODAS las actions (data_path == "scale"
    o termina en ".scale"). Las .psa traen scale constante 1 en cada bone más
    en el armature object; al llegar a Unity como AnimationClip se traduce en
    curvas m_LocalScale en el path '<root>' que pisan el scale baked del prefab
    (multiplicador 100x al samplear). Se podan in-place — no se pierde info
    porque los valores son constantes 1.
"""

import os
import bpy

ARMATURE_NAME = "SK_Curator_Aline"
OUTPUT_PATH = r"D:\vivify_repo\my_vivify_template\VivifyTemplate\Assets\Aline\Animations\Aline_Anims.fbx"


def strip_scale_fcurves():
    """Remove all scale fcurves from every action. Returns (actions_touched, fcurves_removed)."""
    actions_touched = 0
    total_removed = 0
    for action in bpy.data.actions:
        to_remove = [
            fc for fc in action.fcurves
            if fc.data_path == "scale" or fc.data_path.endswith(".scale")
        ]
        if to_remove:
            actions_touched += 1
            for fc in to_remove:
                action.fcurves.remove(fc)
            total_removed += len(to_remove)
    return actions_touched, total_removed


def push_actions_to_nla(arm):
    """Push every action in bpy.data.actions onto its own NLA track on the armature.
    Idempotent: skips if a track with the expected name already exists.
    bake_anim_use_all_actions in Blender 4.2 doesn't cycle actions reliably from the
    FBX exporter when run via headless/MCP context — NLA strips force per-take baking.

    Strip naming: '{ARMATURE_NAME}|{action.name}'. With bake_anim_use_nla_strips=True,
    the FBX take name equals the strip name. Unity's ModelImporter caches clip overrides
    by takeName under the same convention (e.g. 'SK_Curator_Aline|Paintress_Idle1');
    matching it preserves loopTime and the trigger-naming convention used by
    BuildAlineAnimator and the SetAnimatorProperty events.
    """
    if arm.animation_data is None:
        arm.animation_data_create()

    existing_track_names = {t.name for t in arm.animation_data.nla_tracks}
    pushed = 0
    for action in bpy.data.actions:
        strip_name = f"{ARMATURE_NAME}|{action.name}"
        if strip_name in existing_track_names:
            continue
        track = arm.animation_data.nla_tracks.new()
        track.name = strip_name
        # NOTE: strips MUST stay unmuted. The FBX exporter with
        # bake_anim_use_nla_strips=True silently skips muted tracks (verified
        # 2026-05-01: muted tracks → 0.4 MB FBX in 0.1s; unmuted → 185 MB in
        # 150s). Overlap on the timeline is irrelevant — the exporter bakes
        # each strip as its own Take based on the strip's frame range.
        track.mute = False
        track.strips.new(name=strip_name, start=int(action.frame_range[0]), action=action)
        pushed += 1
    return pushed


def export_anims():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature '{ARMATURE_NAME}' not found in scene.")

    # Stash selection / active state for restore.
    prev_active = bpy.context.view_layer.objects.active
    prev_selected = [o for o in bpy.context.selected_objects]

    try:
        # Set selection without ops (works without a VIEW_3D context).
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm

        # Poda de scale fcurves antes de exportar.
        actions_touched, fcurves_removed = strip_scale_fcurves()
        print(f"[fbx-export] scale fcurves stripped: {fcurves_removed} across {actions_touched} actions")

        # Push actions a NLA tracks para que el exporter pueda bakear cada una como Take.
        pushed = push_actions_to_nla(arm)
        print(f"[fbx-export] {pushed} actions pushed to NLA (others ya estaban)")

        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        action_count = len(bpy.data.actions)
        print(f"[fbx-export] exporting {action_count} actions to {OUTPUT_PATH}")

        bpy.ops.export_scene.fbx(
            filepath=OUTPUT_PATH,
            use_selection=True,
            object_types={"ARMATURE"},
            add_leaf_bones=False,
            armature_nodetype="NULL",
            primary_bone_axis="Y",
            secondary_bone_axis="X",
            use_armature_deform_only=False,
            bake_anim=True,
            bake_anim_use_all_bones=True,
            bake_anim_use_nla_strips=True,   # cada NLA track muted -> 1 Take en FBX
            bake_anim_use_all_actions=False, # con NLA, ya no hace falta iterar acciones
            bake_anim_force_startend_keying=True,
            bake_anim_step=1.0,
            bake_anim_simplify_factor=0.0,
            axis_forward="-Z",
            axis_up="Y",
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_ALL",
            path_mode="AUTO",
        )

        size = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
        print(f"[fbx-export] done. file size: {size:.1f} MB")
    finally:
        # Restore selection without invoking ops that need a 3D-view context
        # (this script runs fine from the Scripting editor or MCP, neither of
        # which guarantees an active VIEW_3D for bpy.ops.object.select_all).
        try:
            for o in bpy.context.view_layer.objects:
                o.select_set(False)
            for o in prev_selected:
                if o.name in bpy.context.view_layer.objects:
                    o.select_set(True)
            if prev_active is not None:
                bpy.context.view_layer.objects.active = prev_active
        except Exception:
            pass


if __name__ == "__main__":
    export_anims()
