---
name: vivify-animations
description: Use when working on character animations for a Vivify bundle — pipeline `.psa` → Blender → FBX → Unity Animator → Vivify `SetAnimatorProperty`. Trigger when user mentions 'animations', 'animate', 'AnimatorController', 'Idle1', 'SetAnimatorProperty', 'psa', 'rig', 'bone', 'state machine', 'AnimationClip', 'fcurve' or sees errors like 'T-pose', 'giant model', 'preview not animating', 'clips identity', 'rest pose mismatch', 'scale curve'. Covers the canonical pipeline and the gotchas.
---

# Vivify Animations Workflow

Pipeline to animate characters that live in a Vivify bundle, from Unreal dump to BS runtime. This skill is the operational guide: if you follow it step by step, the animations make it into the game.

## Canonical pipeline

```
.psa from FModel  (Unreal animation file, several per character)
    │  scripts/blender/import_all_psa.py  (Blender MCP or Scripting workspace)
    ▼
Blender actions  (one per .psa, in bpy.data.actions)
    │  scripts/blender/synthesize_root_motion.py
    │     - only for clips with displacement (DashIn-Idle1, DashIn-Idle2,
    │       DashOut-Idle1, DashOut-Idle2, DefaultSlot/.001): moves the forward
    │       motion of pose.bones["root"] to the armature object with correct
    │       axis remap, and normalizes frame 0 to (0,0,0) per axis to avoid
    │       cross-clip discontinuities. Idempotent, marks each processed action
    │       with custom property '_root_motion_synthesized'.
    │  scripts/blender/export_anims_fbx.py
    │     - strip scale fcurves (idempotent, .psa files come with scale=1 which adds nothing)
    │     - push each action to its NLA track UNMUTED, strip name = "<armature>|<action>"
    │     - export ARMATURE only, takes via bake_anim_use_nla_strips=True
    ▼
Aline_Anims.fbx  (~185 MB, gitignored, .meta is versioned)
    │  Unity FBX importer + AlineAnimsImporter:
    │     - preserveHierarchy=true  (keeps SK_Curator_Aline as a named GO)
    │     - motionNodeName="SK_Curator_Aline" (motion lives in the top GO's location,
    │       Unity automatically extracts it as the clip's root motion)
    │     - loopTime=true on canonical idles (Inspector bug workaround 2019.4)
    │     - lockRootPositionXZ=false + keepOriginalPositionXZ=false + keepOriginalPositionY=false
    │       on clips with displacement (XzRootMotionSuffixes: DashIn-Idle1/2,
    │       DashOut-Idle1/2, DefaultSlot/.001)
    ▼
26 AnimationClips as sub-assets, paths "SK_Curator_Aline/root/pelvis/..."
    │  Tools > Aline > Build Animator Controller
    ▼
Aline_AC.controller with state machine
   (Any State → X via trigger; non-loop states chain to a contextual destination
    according to ChainOverrides, or to Idle1 default if no override)
    │  Assigned to the PREFAB ROOT's Animator (not the SK_Curator_Aline child)
    ▼
Runtime: Vivify SetAnimatorProperty with id=prefab_id + properties[].id=trigger_name
```

## Once-per-character setup (strict order)

1. **Import `.psa` into Blender** — open `Aline_project.blend`, run `scripts/blender/import_all_psa.py`. Idempotent. The DarklightGames PSK/PSA addon creates actions in `bpy.data.actions` but does NOT auto-link to the armature: the script sets `arm.animation_data.action` manually.

2. **Synthesize root motion in clips with displacement** — run `scripts/blender/synthesize_root_motion.py`. Only applies to `Paintress_DashIn-Idle1`, `Paintress_DashOut-Idle2`, `DefaultSlot`, `DefaultSlot.001`. Moves `pose.bones["root"].location` to the armature object with axis remap (Y bone → Z object negated; see "Root motion for clips with displacement" below for the why). Idempotent: marks each processed action with custom property `_root_motion_synthesized`, detects previous versions of the axis-mapping and un-applies before re-applying. If you add new clips with motion, add their name to `TARGET_ACTIONS`.

3. **Export FBX armature-only with animations** — run `scripts/blender/export_anims_fbx.py`. Output at `VivifyTemplate/Assets/Aline/Animations/Aline_Anims.fbx` (~185 MB, ~150 s export). The script:
   - Strips scale fcurves from the actions (`.psa` files come with constant scale=1 which adds nothing).
   - Creates one NLA track per action in the armature, **strip unmuted**, named `"<ARMATURE_NAME>|<action.name>"`.
   - Exports with `bake_anim_use_nla_strips=True`, `bake_anim_use_all_actions=False`.

4. **Wait for the reimport in Unity** — first time ~2 min (185 MB FBX). `AlineAnimsImporter` (AssetPostprocessor) runs on its own:
   - `OnPreprocessModel` → `preserveHierarchy = true` (prevents Unity from collapsing the `SK_Curator_Aline` node).
   - `OnPreprocessAnimation`:
     - Sets `motionNodeName = "SK_Curator_Aline"` so Unity treats the top GO's motion as root motion (without this, `averageSpeed=0`).
     - Marks `loopTime = true` on canonical idles (`LoopingSuffixes`).
     - For clips with real horizontal motion (`XzRootMotionSuffixes`: `DashIn-Idle1`, `DashOut-Idle2`, `DefaultSlot`, `DefaultSlot (1)`) sets `lockRootPositionXZ=false`, `keepOriginalPositionXZ=false` and `keepOriginalPositionY=false` so Unity unbakes XZ and Y and extracts the delta as root motion. The rest of the clips stay with motion baked in pose (conservative default for idles and transitions, where there's no displacement).

5. **Configure avatar manually once**:
   - `Aline.fbx` (mesh+rig): Animation Type = `Generic`, Avatar Definition = `Create From This Model`, Root node = `SK_Curator_Aline`. Apply.
   - `Aline_Anims.fbx`: Animation Type = `Generic`, Avatar Definition = `Copy From Other Avatar` → `AlineAvatar` (sub-asset of Aline.fbx). Apply.

6. **Generate the AnimatorController** — menu `Tools > Aline > Build Animator Controller`. Idempotent (deletes and recreates). 26 states + 26 triggers (`Idle1`, `Skill1`, …, no `Paintress_` prefix). Default = `Idle1`. See "AnimatorController pattern" below for the applied chain-overrides.

7. **Animator on the prefab** — the `Animator` component lives on the prefab root (`aline.prefab` root), NOT on the `SK_Curator_Aline` child. Avatar = `AlineAvatar`, Controller = `Aline_AC`. **`Apply Root Motion = ON`** so that clips with `XzRootMotionSuffixes` actually translate the GO. If it's OFF, DashIn/DashOut clips "snap-back" when they finish.

   > **Note (2026-05-01):** controller regen deletes the `.controller` and creates a new one with a new GUID. That breaks the prefab Animator's reference to the controller. After every regen you have to re-assign `Aline_AC` to the Animator's Controller field and save the prefab. TODO: make regen idempotent by preserving the GUID.

8. **Verify runtime** — open the prefab in the scene, hit play on the Animator (Window > Animation > Animator), or sample programmatically:

   ```csharp
   // In unity-mcp's execute_code:
   var clip = ...; // Skill1
   clip.SampleAnimation(prefabInstance, clip.length * 0.5f);
   // Bones in SK_Curator_Aline/root/pelvis/... should have localRotation different from the rest pose.
   ```

9. **Trigger from the `.dat`** — add a `SetAnimatorProperty` event with `properties[].id` = trigger name (e.g. `"Idle1"`, `"Skill1"`).

## Pipeline tools

| File | What it does | When to run |
|---|---|---|
| `scripts/blender/import_all_psa.py` | Batch-imports `.psa` files from `Sandfall/.../Animation/` as Blender actions via the DarklightGames PSK/PSA addon API. Idempotent. | Once at the start. When you add new `.psa` files. |
| `scripts/blender/synthesize_root_motion.py` | Moves motion from the `root` bone to the armature object with axis remap (Y bone → Z object negated) in clips with displacement. Normalizes frame 0 to origin per axis so all clips start at `(0,0,0)` and there's no cross-clip discontinuity. Idempotent, marks each processed action with a custom property and the axis-mapping mode; detects old versions and un-applies before re-applying. | After importing new `.psa` files that have motion in the root bone. If you tweak the axis remap. |
| `scripts/blender/inspect_motion.py` | Read-only diagnostic. Reports location and rotation_quaternion per bone (root, pelvis, spine_01) and the top global movers by max-min excursion. Useful for seeing where the motion lives in an action. | When a new clip doesn't translate in BS. |
| `scripts/blender/export_anims_fbx.py` | Exports `SK_Curator_Aline` armature-only with all actions to `Aline_Anims.fbx` via unmuted NLA strips. Idempotent (recreates NLA tracks if they don't exist). | Whenever the actions change in Blender (including after `synthesize_root_motion.py`). |
| `Assets/Aline/Editor/AlineAnimsImporter.cs` | FBX AssetPostprocessor: sets `preserveHierarchy=true`, `motionNodeName="SK_Curator_Aline"`, `loopTime=true` on canonical idles and unbakes XZ+Y on clips with motion. | Auto on FBX reimport. |
| `Assets/Aline/Editor/BuildAlineAnimator.cs` | Menu `Tools > Aline > Build Animator Controller`. Reads the FBX clips, regenerates `Aline_AC.controller` (idempotent). 1 state + 1 trigger per clip; `Any State → X`; auto-return to `Idle1` on exit time for non-loops. | After FBX reimport. |
| `Assets/Aline/Editor/InspectAlineClips.cs` | Unity-side diagnostic. Menu `Tools > Aline > Inspect Clip Curves (Idle1 / Summary all)`. Dumps a clip's curves to Console. | When something goes wrong and you need to see the imported clip's fcurves. |

## Non-negotiable rules

1. **NLA strips UNMUTED** on the armature before FBX export. Blender's exporter with `bake_anim_use_nla_strips=True` **silently skips muted strips** (FBX comes out in 0.1s at 0.4 MB with zero AnimCurves instead of 150s and 185 MB). The script already does this right — don't set `track.mute` to `True`.

2. **Strip name = `"<ARMATURE_NAME>|<action.name>"`**. With NLA bake, the strip name becomes the FBX take name. The `.meta` caches `clipAnimations` with `takeName` following that convention. If you export with strips named only `action.name`, Unity logs `Split Animation Take Not Found 'SK_Curator_Aline|...'` and discards per-clip overrides (loopTime, etc.).

3. **`preserveHierarchy = true`** on `Aline_Anims.fbx`'s FBX importer. Blender's export collapses the armature object into the FBX root when it's armature-only (no mesh child). Unity also collapses single-child top-level transform nodes by default. Without this flag, `SK_Curator_Aline` disappears from the hierarchy → clip paths come out as `root/...` without prefix → FBX inspector preview breaks (T-pose) when it uses `Aline.fbx` as the model. `AlineAnimsImporter.OnPreprocessModel` applies it.

4. **Animator on the PREFAB ROOT, not on the `SK_Curator_Aline` child**. With `preserveHierarchy=true` the clip paths start with `SK_Curator_Aline/...` and match the prefab hierarchy from the root. The scale curves that the FBX exporter inserts by default go to path `SK_Curator_Aline` (not path `<root>`), applied to the GO `SK_Curator_Aline` (scale=1) → no-op. The prefab root keeps its baked `localScale: 0.01`.

5. **`Aline.fbx` (mesh)**: Rig = Generic, Avatar = `Create From This Model`, Root node = `SK_Curator_Aline`.

6. **`Aline_Anims.fbx` (animations)**: Rig = Generic, Avatar = `Copy From Other Avatar` → `AlineAvatar` from `Aline.fbx`. Without this, the clips don't hang correctly off the rig at runtime.

7. **Trigger naming**: clip name minus the `Paintress_` prefix. E.g.: clip `SK_Curator_Aline|Paintress_Idle1` → trigger `Idle1`. That goes in the `properties[].id` of the `SetAnimatorProperty` event.

8. **`Aline_Anims.fbx` is gitignored**. Only the `.meta` is versioned. Re-export from Blender is the way to regenerate it — don't expect to recover it from git.

## Vivify event to trigger animations (V3)

```json
{
  "b": 16,
  "t": "SetAnimatorProperty",
  "d": {
    "id": "alineMain",
    "properties": [
      { "id": "Skill1", "type": "Trigger", "value": true }
    ]
  }
}
```

`id` = the id of the `InstantiatePrefab` that brought Aline into the scene. `properties[].id` = the name of the Animator's trigger. Vivify looks at all Animator components inside the prefab with that id and applies.

See [`docs/heckdocs-main/docs/vivify/events.md`](../../../docs/heckdocs-main/docs/vivify/events.md) for Bool/Float/Integer.

**Operational rule:** **don't fire a trigger for Aline's current state.** The AnyState transition has `canTransitionToSelf = false`, so the trigger doesn't consume — it stays queued. When Aline moves to ANOTHER state via a later trigger, the queued one fires too and aborts the just-entered clip after 4-5 frames. Symptom: "the anim moves a bit and goes back to idle". Default state already covers starting in Idle1 — no need to re-trigger. Don't re-trigger Idle2 if it's already floating via DashOut chain-override. Etc.

## AnimatorController pattern

Generated by [`Assets/Aline/Editor/BuildAlineAnimator.cs`](../../../VivifyTemplate/Assets/Aline/Editor/BuildAlineAnimator.cs). Three rules that dictate how each state chains:

1. **`Any State → state` per trigger** (all 26 triggers). Blend `duration = 0.1f`, `hasExitTime = false`, `canTransitionToSelf = false`. The 0.1s blend smooths pose mismatches between unrelated clips; hard cut (0) leaves visible jumps, longer blend introduces weird sprints.

2. **Chain-override at exit time (95%) for non-loops**, via the `ChainOverrides` dict:
   - `Paintress_Idle1_to_idle2_transition` → `Paintress_Idle2`
   - `Paintress_Idle2_to_idle3_transition` → `Paintress_Idle3`
   - `Paintress_DashOut-Idle2` → `Paintress_Idle2`
   - `Paintress_DashIn-Idle1` → `Paintress_Idle1` (returns to default after the dash, neutral pose)
   - The rest of the non-loops without override fall back to `defaultState` (Idle1) with `duration = 0.15f`.

3. **`NoFallback`** (HashSet). States that stay on their last frame and DON'T chain to anything. Empty by default. Useful if some day a clip ends in a pose that should NOT return to idle (e.g. an impact final pose that stays held until the next trigger).

If you add a clip whose canonical destination is not Idle1 (e.g. a phase-2 skill that should return to Idle2 floating), edit `ChainOverrides` in `BuildAlineAnimator.cs` adding `{ "Paintress_NewSkill", "Paintress_Idle2" }`. Regenerate via `Tools > Aline > Build Animator Controller`.

## Locomotion sandbox

`beatsaber-map/EasyStandard.dat` is the map's Easy difficulty, dedicated to testing isolated animations (no VFX, no notes, no significant audio). Its `_customEvents` has an `InstantiatePrefab` of Aline + a chain of `SetAnimatorProperty` that walks through the canonical idles and transitions at 100 BPM. The `Info.dat` registers it alongside `ExpertPlusStandard.dat`.

When to use it:
- Validate a change in `BuildAlineAnimator.cs` (regenerate controller + see if transitions chain in BS).
- Validate a change in `AlineAnimsImporter.cs` (re-import FBX + see if the clips behave differently).
- Test a new trigger in isolation before putting it in a family prototype.

How to use it: `Ctrl+R` in BS reloads the `.dat` files (not the bundle — for a bundle change you have to F5 from Unity). Launch the Test map, select Easy difficulty. With no VFX or notes, the only thing happening is Aline running through the chain.

Edit `EasyStandard.dat` directly to add/remove test triggers. **Don't commit test changes to the `.dat`** — it lives under the junction and isn't versioned, which is good for sandbox but also means that if you want to preserve a specific test setup, you have to copy the `.dat` to `docs/map-snapshots/`.

## Root motion for clips with displacement

Some clips (DashIn-Idle1, DashOut-Idle2 and aliases) carry horizontal motion: Aline approaches the player, hits, falls back. For the prefab's GameObject to actually translate (not just the mesh), the motion has to reach the Animator as **root motion** and `Apply Root Motion = ON` on the component.

### The concrete issue

The original `.psa` files bake forward motion in `pose.bones["root"].location[1]` (bone-local Y of the "root" bone, forward in the Unreal rig). Blender's FBX export correctly exposes it as `m_LocalPosition.y` of path `SK_Curator_Aline/root` in Unity. **But Unity 2019.4 with `Generic + Copy From Other Avatar` doesn't extract motion from the "root" bone as root motion**, not with `motionNodeName="root"`, not by rebuilding the avatar, not by unbaking `keepOriginalPositionY`. `hasGenericRootTransform` stays `False` and `averageSpeed = (0,0,0)` always. It's a limitation of the Generic+CFOA flow, not a punctual bug: see "Closed paths" below for the exhausted attempts.

### The fix

Pre-process the action in Blender (`scripts/blender/synthesize_root_motion.py`) to move the motion from the "root" bone to the **armature object** (top GO of the rig). When the motion lives in the armature object's `location`, Unity does extract it automatically as root motion with `motionNodeName="SK_Curator_Aline"` (applied by `AlineAnimsImporter.OnPreprocessAnimation`).

The script applies a deliberate axis remap:

```
bone.location[0] (X bone-local, lateral)   → object.location[0] (X)            sign +1
bone.location[1] (Y bone-local, forward)   → object.location[2] (Z up Blender) sign -1
bone.location[2] (Z bone-local, vertical)  → object.location[1] (Y)            sign +1
```

The "swap Y↔Z + sign-flip on axis 2" is not aesthetic — it's the exact composition needed for the motion to land at `+Z world` Unity (forward) after two chained transforms:

1. **FBX exporter Blender→Unity** (`axis_up="Y"`, `axis_forward="-Z"`) swaps Blender Y↔Z when crossing formats. What's location.z in Blender object shows up in Unity as `m_LocalPosition.y`; what was location.y shows up as `m_LocalPosition.z`.

2. **The armature object ends up with rotation `(270°, 0, 0)` in Unity** (Z-up→Y-up requires rotating -90° on X). That permutes the GO's local axes: SK_Curator_Aline's local Y in Unity points to `+Z world`, local Z points to `-Y world`.

Without axis remap (1:1 copy Y bone→Y object) the motion ends up at `-Y world` (Aline falls vertically). With remap to Z object but without negating, it ends up at `-Z world` (Aline moves backwards). With the final remap (`Z object negated`), it ends up at `+Z world` (forward). Empirical variables until validated — chained axis transforms are not intuitive.

### Operational pipeline

1. **Blender**: with the actions imported via `import_all_psa.py`, run `synthesize_root_motion.py`. Idempotent: marks each processed action with custom property `_root_motion_synthesized` with the applied mode (`v5-bone-y-to-object-z-negated-normalized`); detects previous versions and un-applies before re-applying.
2. **Blender**: re-export with `export_anims_fbx.py`.
3. **Unity**: the FBX reimport triggers `AlineAnimsImporter`, which sets `motionNodeName = "SK_Curator_Aline"` and, per clip in `XzRootMotionSuffixes`, `lockRootPositionXZ=false + keepOriginalPositionXZ=false + keepOriginalPositionY=false`.
4. **Verify**: `clip.averageSpeed` should be different from `(0,0,0)` for the 4 clips with motion. For `DashIn-Idle1` you get something close to `(0, 0, ~+173)` (≈ 600 cm forward / 3.46 s). DashOut opposite sign.
5. **Animator**: `Apply Root Motion = ON` is already on the prefab. The extracted root motion is applied to the root transform `aline.prefab`, not to the child `SK_Curator_Aline`.

### How to check if a clip has extractable root motion

- In Unity: `clip.averageSpeed` via API (the FBX inspector's Animation tab preview also shows it as "Average Velocity").
- If all axes are `0` despite visible motion in preview, no extraction is happening. Investigate where the motion lives in Blender before pulling on Unity-side configs: `scripts/blender/inspect_motion.py` reports motion per bone and per-axis (checks object-level and bone-local on location and rotation_quaternion).

## Cross-clip pose mismatch: blend in Animator, don't edit data

If a clip A ends in a pose different from where clip B starts (typical: floating ↔ grounded between dashes and idles), a transition with `duration = 0` shows a visible teleport. Replicate UE Montage "Blend Out duration" pattern in Unity's AnimatorController:

1. **Exit transition with `duration > 0`**: N-second blend toward the target. Unity interpolates the poses during that time. For transitions "the clip ends in floating, target is grounded", start at `duration = 0.2-0.3s`.

2. **`exitTime < 1.0`** if the clip has a static "tail" after completing the motion: the blend starts earlier (e.g. `exitTime = 0.7` → at 70% of the clip), overlapping with the last frames of the movement. Visual result: the landing happens DURING the dash, not after Aline arrives standing at the destination. Without this the blend looks like a pose change in place.

3. **Entry blend (AnyState transition with `duration > 0`)** to cushion the snap when ENTERING the state from a mismatched pose (e.g. trigger `DashOut-Idle1` from Idle1 grounded — the dash starts floating). Same concept, opposite direction.

Validated 2026-05-02 with DashOut-Idle1 (new state, exit to Idle1 grounded): `exitTime=0.7, duration=0.3` on exit + `duration=0.3` on AnyState entry dissolves a ~5cm UP/DOWN teleport observable to the eye. The clip data isn't touched.

**When you DON'T need this:** when the transition's target and source have compatible poses. DashOut-Idle2 (floating→floating) stays with `duration = 0` default — nothing to blend.

**When you do need it:** transitions `Idle1 (grounded) → Idle1_to_idle2_transition (starts grounded?)` also show snap if the transition clip doesn't start exactly where Idle1 leaves off. Applied `duration=0.2` on its AnyState entry.

## Gotcha: `_Montage.psa` with generic seq name "DefaultSlot"

Some `.psa` files exported from UE have "DefaultSlot" as the internal sequence name (the montage slot), not the montage name. If two different `.psa` files share that seq name, `import_all_psa.py` with `SKIP_EXISTING=True` imports the first alphabetically and silently discards the rest — you lose animations without a visible warning.

Real case (2026-05-02): `Paintress_DashIn-Idle1_Montage.psa` and `Paintress_DashOut-Idle1_Montage.psa` both with seq "DefaultSlot". Only the first one (DashIn) was imported → DashOut-Idle1 absent from the FBX and the AnimatorController for months without anyone noticing.

**Systemic fix:** `import_all_psa.py` detects seq names in `GENERIC_SEQ_NAMES` (set with "DefaultSlot") and renames them using the `.psa` basename (without the `_Montage` suffix). If the rename would conflict with an existing action, leaves the original with a warning. Applies before the `SKIP_EXISTING` check, so guarantees uniqueness without touching the `.psa` source.

**When to add a name to `GENERIC_SEQ_NAMES`:** if you find `.psa` files with seq names that DON'T match their filename and you suspect a silent collision. Symptom: `summary.imported < count(.psa)` without clear warnings.

Additional caveat: UE Montage `.psa` files sometimes bring bones from OTHER characters (shared multi-character asset). The addon warns "missing N bones" — expected, ignore if the names are from another entity (e.g. "Aberration_*" on Aline). Aline's animation imports correctly via subset-matching.

## Finding: Montage `.psa` vs non-Montage can be identical in skeletal data

`Paintress_DashOut-Idle1_Montage.psa` and `Paintress_DashOut-Idle2.psa` show up as different assets in FModel but contain identical skeletal animation for Aline (verified: 2604 fcurves, zero difference). The `.psa` only carries the skeletal track; UE Montages additionally wrap metadata (notifies, sections, blend rules, root motion mode) that does NOT travel to the `.psa`.

Implication: the grounded vs floating differentiation, landing blend, foot IK, etc. that the original game does at runtime with those clips lived in UE blueprints, not in the animation. Replicating them in Unity requires reconstructing those behaviors (typically via blends in the AnimatorController, see previous section). Don't expect duplicating a Montage rip to give a visually distinct animation from the base clip.

## Closed paths (don't waste time here)

Things that seem reasonable but have been ruled out with debugging cost — documented so the next person doesn't repeat them.

### Do NOT use `AnimateTrack` with `_offsetPosition` on Vivify-prefab tracks

Tested: the event is processed silently (doesn't error, doesn't log) and **doesn't affect the position** of the instantiated prefab. Possibly Heck-AnimateTrack in V2 expects note tracks, and the `_offsetPosition` property doesn't apply to the parent track Vivify creates for the prefab. **The behavior documented in heckdocs `properties.md` applies to notes, not to Vivify-prefabs.**

### Do NOT use `AnimateTrack` with `_position` to manage Aline's position cross-clip

Tested: `_position` DOES affect the Vivify-prefab track (the elevation test confirmed it), but the units don't match those of `InstantiatePrefab`'s `position`. World [0,1,8] of InstantiatePrefab doesn't equal `_position` [0,1,8] or [0, 1.667, 13.333] (lane equivalent). Any value tested introduces teleports at the start or end of each AnimateTrack. On top of that, managing position clip-to-clip via compensation becomes unsustainable when you add intermediate clips — each new clip adds another level of coordination, the compensations are cumulative. **The right path is root motion (FBX importer + Apply Root Motion ON), not AnimateTrack compensation.**

### Do NOT expect `Apply Root Motion = ON` to solve snap-back on its own

Tested: ticking the toggle on the prefab Animator produces no delta if the clips have motion baked in pose (Unity's default for Generic). You have to FIRST configure the FBX importer to extract (`lockRootPositionXZ=false`, `keepOriginalPositionXZ=false`, `keepOriginalPositionY=false`) AND have the motion live in the armature object's location, not in the internal bone (that's what `synthesize_root_motion.py` takes care of).

### Do NOT try to make Unity extract root motion from the "root" bone in Generic + Copy From Other Avatar

Aline's `.psa` files bake forward motion in `pose.bones["root"].location[1]`. The FBX exporter DOES expose it as `m_LocalPosition.y` of path `SK_Curator_Aline/root` in Unity (verifiable with `AnimationUtility.GetCurveBindings`). But Unity 2019.4 with `animationType=Generic + avatarSetup=CopyFromOtherAvatar` doesn't extract motion from an internal bone as root motion, **no matter what you put in `motionNodeName`**.

Tested and discarded:
- `motionNodeName="root"` pointing to the bone (clip importer and avatar source).
- `motionNodeName="SK_Curator_Aline/root"` with full path.
- Avatar rebuild (avatarSetup → NoAvatar → CreateFromThisModel).
- `keepOriginalPositionY=false` per clip without prior axis remap.

In every case `clip.hasGenericRootTransform` stays `False` and `averageSpeed=(0,0,0)`. Extraction only works when the motion lives in the armature object's (top GO of the rig) `location` and `motionNodeName="SK_Curator_Aline"`. That's why `synthesize_root_motion.py` moves the motion from the bone to the object before FBX export.

### Do NOT regenerate the `.controller` without re-assigning the controller to the prefab

`AssetDatabase.DeleteAsset` + `CreateAnimatorControllerAtPath` deletes the `.meta` and creates a new GUID. The prefab's reference to `Aline_AC` is left broken. Symptom: after regen, Aline appears in T-pose in BS because the Animator has no controller. **Temporary solution:** after each regen, open `aline.prefab`, drag `Aline_AC` to the Controller field, save. **Pending solution:** make `BuildAlineAnimator.cs` idempotent preserving GUID (clean contents instead of deleting the asset).

### Do NOT fire redundant triggers from the `.dat`

If Aline is already in Idle1 (default state) and you fire the `Idle1` trigger, she doesn't transition (`canTransitionToSelf = false`). The trigger stays queued and fires when Aline changes to another state, aborting that state after 4-5 frames. Same with any other redundant trigger. **Default state covers the startup, chain-overrides cover the canonical destinations** — only fire triggers that represent real transitions.

## Known gotchas

### Blender's FBX exporter skips muted NLA strips

Symptom: export finishes in 0.1s and FBX comes out at 0.4 MB with no AnimCurves. `Aline_Anims.fbx` Inspector → Animation tab → "No animation data available in this model" or a list of takes but all empty.

**Cause**: `bake_anim_use_nla_strips=True` silently ignores tracks with `mute=True`. The assumption "muted = no blend at runtime, still exportable" is false.

**Fix**: the `export_anims_fbx.py` script creates strips with `track.mute = False`. If you manually add NLA tracks, leave them unmuted. Timeline overlapping doesn't matter — the exporter bakes each strip by its frame range.

### The PSK/PSA addon doesn't auto-link the action to the armature

After `import_psa(...)` the action is created in `bpy.data.actions` but `arm.animation_data.action` stays `None`. You have to set it manually:

```python
arm.animation_data.action = bpy.data.actions["Paintress_Idle1"]
```

The batch import does it for all of them. If you do it manually, don't forget this step.

### Unity 2019.4 collapses top-level nodes with a single child

Symptom: `Aline_Anims.fbx` Inspector shows clips, but the preview animates the model in T-pose. SampleAnimation directly on the rig works; preview doesn't.

**Cause**: the FBX Blender exports in armature-only mode doesn't preserve the `SK_Curator_Aline` node (the armature object collapses with its single child `root`, the pose root bone). On top of that Unity, with `preserveHierarchy=false` (default), also collapses single-child top-level nodes. Result: clip paths start with `root/...` (no `SK_Curator_Aline` prefix), but the FBX inspector preview uses `Aline.fbx` as the model (via avatar source), whose hierarchy is `<top>/SK_Curator_Aline/root/...` → mismatch → T-pose.

**Fix**: `preserveHierarchy = true` on `Aline_Anims.fbx` importer. `AlineAnimsImporter.OnPreprocessModel` applies it automatically on import.

### Unity 2019.4 does NOT have `AnimationUtility.SetEditorCurves` (plural)

If you're going to transform clip curves in an AssetPostprocessor (path rewrite, binding strip, etc.), **don't iterate** `AnimationUtility.SetEditorCurve(clip, b, ...)` per binding: each call makes the clip dirty + revalidates and for 4480 bindings × 26 clips you get ~10 min of Unity-wide hang, no progress bar.

The plural API `SetEditorCurves` only shows up in Unity 2020+. In 2019.4 the options are:

- **Do the transformation in Blender** before export (preferred — the exporter already has a fast pipeline).
- **`AnimationClip.ClearCurves()` + reconstruction**: only viable if you don't need to preserve the original curves.
- **Modify the ModelImporter** (e.g. `preserveHierarchy`, `clipAnimations[].loopTime`) in `OnPreprocess*` — this is the cheap one.

If you open Unity and the FBX says "A default asset was created because the asset importer crashed on it last time", you probably put a per-curve loop in the postprocessor. Force-close Unity, revert the postprocessor, reimport.

### New takes from the FBX don't show up in the AnimatorController after adding actions in Blender

Symptom: you add a new action in Blender (via import_all_psa or manually), re-export FBX, reimport in Unity — but `BuildAlineAnimator` doesn't generate a state or trigger for that clip, and it doesn't show up as a listable sub-asset.

**Cause**: `ModelImporter.clipAnimations` is a snapshot serialized in the `.meta`. When an AssetPostprocessor manipulates it and saves it, it gets frozen with those N takes. If you add take N+1 to the FBX, `defaultClipAnimations` (live read of the FBX) includes it, but `clipAnimations` (persisted snapshot) doesn't — the new take never imports.

**Fix**: `AlineAnimsImporter.cs` ALWAYS starts from `importer.defaultClipAnimations` (not from `clipAnimations`). The per-clip settings are deterministic by suffix, so reset+re-apply every import is safe and guarantees that new takes enter the pipeline automatically. If you want to add your own manual overrides in the inspector, they won't be respected — put their logic in `AlineAnimsImporter` by suffix.

Known case: `Paintress_DashIn-Idle2` was discovered hidden on 2026-05-01 — existed in Blender + FBX defaults, but neither in the AnimatorController nor as an imported AnimationClip. After the fix, all 26 takes stay synchronized.

### Unity 2019.4's Inspector discards per-clip toggles when changing clip without Apply

Symptom: you tick Loop Time on Idle1, go to Idle2, come back to Idle1 and it's unticked.

**Fix**: `AlineAnimsImporter.cs` sets `loopTime` programmatically on import using an explicit HashSet of clips that should loop. Don't touch the toggle by hand — if you do, the next reimport overwrites it.

### Changing the Rig type in `Aline.fbx` resets the Avatar Definition

If you change `Aline.fbx` Rig Animation Type between None / Generic / Humanoid in the Inspector, the Avatar Definition resets to "No Avatar". The prefab's Animator is left with `m_Avatar` pointing to a sub-asset that no longer exists.

**Fix**: Avatar Definition = "Create From This Model", Root node = `SK_Curator_Aline`, Apply. The regenerated avatar has the same fileID (9000000) and GUID (the FBX's), so the broken reference restores itself.

### Rest pose mismatch between `Aline.fbx` and `Aline_Anims.fbx`

Symptom: clips look right in their native FBX preview, but when applied to `aline.prefab` (whose mesh comes from `Aline.fbx`) the mesh distorts — bones moved to impossible positions, fragments scattered.

**Cause**: Generic avatars in Unity do NOT retarget — they use the rig's hierarchy and rest pose directly. If Aline_Anims (where the clips were authored) and Aline.fbx (where the mesh is) have slightly different rest poses, the clips write transforms from the "foreign" rig over the mesh's rig.

**Fix**: both FBX files must come from the same `.blend` exported with the same settings (axis, scale, addleafbones). Using `Copy From Other Avatar` Aline_Anims → Aline.fbx forces bone names to match.

### Aline_Anims.fbx takes a long time to import (~2 min)

Size 185 MB with 26 takes × 4480 curves × up to 480 frames each. It is what it is. If you add an AssetPostprocessor that iterates all the curves (per-binding), multiply by 5-10x the import time → hangs. Avoid per-curve manipulation in post-process; prefer fixing in the FBX export from Blender or in `ModelImporter` settings (preprocess).

## Current pipeline state (2026-05-02)

[x] Import .psa → Blender (27 actions after DashOut-Idle1_Montage recovery; "DefaultSlot" seq name rename to avoid silent collision)
[x] Synthesize root motion for clips with displacement (Y bone → Z object negated, normalized to frame 0 = origin)
[x] Export Blender → FBX (NLA strips unmuted, named with armature prefix, ~190 MB in ~160 s)
[x] Import FBX → Unity (`preserveHierarchy=true`, `motionNodeName="SK_Curator_Aline"`, avatar copy, loopTime auto, keepOriginalPositionY=false on motion clips)
[x] AnimatorController generation (27 states + triggers + chain-overrides for contextual destinations)
[x] Animator on prefab root, scale curves no-op (no 100x bug)
[x] Aline visible in BS at correct size, animations playing back
[x] FBX inspector preview animating with Aline.fbx mesh
[x] Locomotion sandbox (`EasyStandard.dat`) validated in BS: idles, transitions, dashes, stuns chain cleanly. DashIn translates the GO forward (~6m world Z), DashOut returns it. No snap-back. Apply Root Motion = ON active on the prefab Animator.
[x] Cross-clip pose mismatch absorbed via blend in transitions (DashOut-Idle1: `exitTime=0.7, duration=0.3` exit + `duration=0.3` entry); the ~5cm Y hop when transitioning grounded↔floating eliminated (2026-05-02).
