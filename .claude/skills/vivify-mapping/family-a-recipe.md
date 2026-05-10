# Recipe — Family A (Indicator + Projectile Sequence)

Reusable implementation of a family A attack. Validated with Skill4 in `NormalStandard.dat` on 2026-05-04.

> **When to apply this recipe:** an attack where Aline runs an animation that launches N sequential projectiles at the player (Skill3, Skill4, future variants). The player parries each one with a native BS cube.
>
> **When NOT to apply:** melee attacks (B), single-parry AoE (F), multi-hit chains where Aline spawns the VFX from her own hand (E). Different families, different recipes.

## Conceptual model

Each projectile is a **telegraph (smoke) + cube** pair:

- **Telegraph** = `InstantiatePrefab` of [`SphereBurst.prefab`](../../../VivifyTemplate/Assets/Aline/VFX/SphereBurst.prefab) at the fixed "above Aline" position at `spawn_beat`. It's a **dark smoke burst** (1 ParticleSystem child, simulationSpace=World, lifetime ~1.5-2.2s, auto-destroy via `stopAction=Destroy`). Replaces what used to be "semi-transparent placeholder spheres" — the smoke ONLY occupies the indicator spot. It doesn't persist until `launch_beat`; the cube becoming visible at hit_beat works as the subsequent telegraph.
- **Cube** = native BS note (`AssignObjectPrefab` → `NoteCube.prefab` swap) with `definitePosition` that keeps it "anchored" at the telegraph position throughout the indicator window, and at `launch_beat` moves to the player over `~2 beats`. The cube has **2 ParticleSystem children** (`SmokeEnvelope` Local-sim for contained wrap + `SmokeTrailWorld` World-sim for trail on launch). Detail in the "Cube swap" section below.

The cube **is** the parry system — cuttable, scoreable. The telegraph (initial burst + envelope) is just cosmetic.

**Particle architecture (3 coordinated ParticleSystems):**

| Particle | Visual lifetime | Lives in | When it appears |
|---|---|---|---|
| `SphereBurst.Smoke` | 1.5-2.2s, 14 puffs in burst | World, fixed sphere position | `spawn_beat` (initial telegraph) |
| `NoteCube.SmokeEnvelope` | Continuous during cube life, rate 15/s, lifetime 0.6-1.0s | Local to the cube transform | Appears automatically at the cube's `scale-pop` (see "scalingMode=Hierarchy" gotcha in [`vivify-materials → Particle shaders`](../vivify-materials/SKILL.md)) |
| `NoteCube.SmokeTrailWorld` | Continuous during cube life, rate 30/s, lifetime 0.7-1.0s | World | Same as envelope; during hover the particles emit near the cube; during launch the previously emitted particles stay in world → continuous trail behind. |

All three use the `Aline/ParticleSmoke` shader (dark alpha-blend, procedural circular mask). M_Smoke (CoreOpacity 0.45 — soft burst) and M_SmokeTrail (CoreOpacity 0.85 — visible envelope/trail) are separate materials to tune opacity without affecting the rest.

## Inputs (per-instance parameters of the attack)

| Parameter | Type | Notes |
|---|---|---|
| `trigger_id` | string | Animator Trigger (`Skill4`, `Skill3`, …) |
| `trigger_beat` | float | Beat at which `SetAnimatorProperty` is sent (== when Aline starts the animation) |
| `N` | int | Number of projectiles (5-7 typical, dictated by the animation) |
| `spheres[]` | array of objects | Per projectile i: `{world_pos: [x,y,z], spawn_beat, launch_beat}` |
| `travel_beats` | float | How many beats the cube takes to reach the player from its `launch_beat` (default 2 = 1.2s @ BPM 100) |
| `sphere_scale` | float | Scale of the indicator prefab (default 1.5) |
| `attack_id` | string | `atk_a_NNN` for track namespacing (see families.md "Track namespacing") |

Global attack constants (don't vary per instance unless explicitly experimenting):

| Constant | Value | Why |
|---|---|---|
| `NJS` | 16 | Standard BS Normal-difficulty |
| `noteJumpStartBeatOffset` | 13 | Gives HJD ≈ 14 beats. Enough for the cube to live from its sphere_spawn_beat to player_arrival without clipping |
| `player_world_pos` | `[0, 1, 0]` | Player's chest center. In lane: `(1.5, 0, 0)` |
| `pop_scale_duration` | `0.015` (of lifetime) | Pop animation duration (~0.34s @ HJD=14, BPM=100) |
| `pop_rotation_duration` | `0.020` (of lifetime) | One CW turn; scale ends at 75% of the spin |

## Calibrated constants (lane ↔ world)

Validated empirically with `scripts/build-calibration.ps1` (see script docs). **Don't re-tune without re-calibrating.**

```
LANE_UNIT_M       = 0.6   # 1 lane = 0.6 m
LANE_X_ZERO_WORLD = -0.9  # x=0 lane → x=-0.9 world
LANE_Y_ZERO_WORLD =  1.0  # y=0 lane → y=+1.0 world
```

### World → lane conversion

```
lane_x = (world_x - LANE_X_ZERO_WORLD) / LANE_UNIT_M = (world_x + 0.9) / 0.6
lane_y = (world_y - LANE_Y_ZERO_WORLD) / LANE_UNIT_M = (world_y - 1.0) / 0.6
lane_z =  world_z                       / LANE_UNIT_M =  world_z       / 0.6
```

The inverse (lane → world) is rarely needed — inputs go in world, outputs in lane.

## Normalized path calculation (definitePosition)

The cube has `b = sphere_spawn_beat` (absolute), HJD = 14 beats. Its normalized time goes `[0, 1]` from `b - HJD` to `b + HJD`. Time `0.5` = `b` = the moment the sphere appears (jump-in ends here).

For each cube i:

```
gap_i        = launch_beat[i] - spawn_beat[i]   # typically 10-12 beats, varies per cube
fire_time_i  = 0.5 + gap_i / (2 * HJD) = 0.5 + gap_i / 28
arrival_time_i = fire_time_i + travel_beats / (2 * HJD)   # must be ≤ 1.0
```

> **Key constraint:** `arrival_time_i ≤ 1.0`. If it fails, raise `noteJumpStartBeatOffset`. For `gap_max + travel_beats <= 14` (with HJD=14) it's OK. If an instance has gaps > 12 beats, rethink timing or raise HJD.

`pointDefinition` per cube:

```json
"<attack_id>_cube_<i>_path": [
  [sphere_lane_x, sphere_lane_y, sphere_lane_z, 0],
  [sphere_lane_x, sphere_lane_y, sphere_lane_z, fire_time_i],
  [player_lane_x, player_lane_y, player_lane_z, arrival_time_i],
  [player_lane_x, player_lane_y, player_lane_z, 1]
]
```

Hold on sphere from `time=0` to `fire_time` (during jump-in it stays at the first keyframe anyway — Heck doesn't animate during jump-in, see "Dissolve trick" below). On `[fire_time, arrival_time]` sweep to player. Afterwards stays at player until despawn.

## Static-face-player rotation calculation

BS puts the cube's "dot/arrow" on its **-Z local** face. For the dot to face the player, the cube's +Z points **AWAY from the player**.

```
direction_away = sphere_world - player_world
direction_normalized = direction_away / |direction_away|

pitch (X) = -asin(direction_normalized.y)       # Unity ZXY extrinsic, positive X = look down
yaw   (Y) = atan2(direction_normalized.x, direction_normalized.z)
roll  (Z) = 0  (animated for the pop spin, see below)
```

Check: the central cube (sphere directly above the player) comes out with `yaw=0`. Lateral ones come out with symmetric positive/negative yaw.

## Pop spin animation (localRotation Z)

The cube appears at `time=0.5` and rotates one clockwise turn while scaling. **Important:** Heck/Unity use quaternion slerp between keyframes — a 0→-360 rotation with 2 keyframes is interpreted as "same orientation" → no visible rotation. **You have to split the path into ≤ 90° steps** to force the long path.

### easeOut curve (progressive deceleration)

Heck supports `easing` per-keyframe (5th element), but since each easing applies only to the segment ending at that keyframe, getting a **global** easeOut across the whole rotation with multi-keyframe is fiddly.

Clean approach: **keep linear interpolation between keyframes but distribute timestamps following the easeOutQuad shape** (`f(t) = 1 - (1-t)²`). Each segment is still 90° linear, but segments get progressively longer in time → effective speed decreases. Visually "fast start, slow end".

For 4 segments of 90° over the `time=0.5 → 0.520` window:

| Accumulated rotation | Norm progress | t in window | Absolute timestamp |
|---|---|---|---|
| 0° | 0% | 0 | 0.5000 |
| -90° | 25% | 0.134 | 0.5027 |
| -180° | 50% | 0.293 | 0.5059 |
| -270° | 75% | 0.500 | 0.5100 |
| -360° | 100% | 1.000 | 0.5200 |

```json
"localRotation": [
  [pitch, yaw,    0, 0],
  [pitch, yaw,    0, 0.5],     // jump-in uses first kf — irrelevant because cube invisible here
  [pitch, yaw,  -90, 0.5027],  // 13.4% of time, first 25% of rotation (fast)
  [pitch, yaw, -180, 0.5059],
  [pitch, yaw, -270, 0.510],
  [pitch, yaw, -360, 0.520],   // last 25% takes half the time (slow)
  [pitch, yaw, -360, 1]        // final hold
]
```

X (pitch) and Y (yaw) constant across all keyframes (= static-face-player rotation). Only Z changes (spin).

For 2 turns: extend with 4 more keyframes (-450 → -540 → -630 → -720) using the same timestamps scaled to twice the duration. Or use more keyframes (8 steps of 90°) if you want the easeOut shape over the full length.

To smooth the deceleration (remove visual stutters between segments): bump to 8 keyframes (45° each) with timestamps following the same easeOutQuad shape. Segments get shorter but the curve gets smoother.

## Dissolve trick (hiding the "first trip")

Without this, the cubes are visible during the whole NJS jump-in from far Z (they look like "tiny dots travelling" because the scale curve keeps them at `scale=0.1` or similar). That breaks the "they materialize in the sphere" effect.

**Canonical fix (validated 2026-05-04 with cube swap):** first point of `scale` curve at `(0, 0, 0)`. Heck doc: during jump-in objects "strictly use the first point in the point definition" → cubes effectively invisible because `scale=0` collapses vertices to origin.

```json
"scale": [[0, 0, 0, 0], [0, 0, 0, 0.499], [1, 1, 1, 0.515], [1, 1, 1, 1]]
```

- NJS jump-in: uses first point `(0, 0, 0)` → invisible.
- `t=0..0.499`: scale=0 → invisible.
- `t=0.499..0.515`: pop scale 0→1 (sync with sphere spawn `t=0.5` and rotation curve `t=0.5..0.52`).
- `t=0.515..1`: scale=1 → visible the whole sphere hold + launch + despawn phase.

**Why not use `dissolve` curve:** Vivify does pass `_Cutout` per-instance to the prefab's shader, but the value is driven by proximity to the player (not by the `dissolve` curve). If the shader implements `clip(cutout)` with any semantics, the cubes hide right when they're fired at the player — opposite of what we want. Gotcha detail in the [`vivify-materials`](../vivify-materials/SKILL.md) skill, "Outline shader" section. `dissolve` and `dissolveArrow` curves remain in the current Skill4 `.dat` but **don't contribute to the effect** and are removable if cleanup is preferred.

## Cube swap via `AssignObjectPrefab` (part of the default recipe)

The default BS note has its own geometry with arrow/dot indicator that suffers `dissolveArrow` desync (`DisappearingArrowControllerBase` race condition documented in the NoodleExtensions source: the vanilla controller clobbers the value NE writes, because NE doesn't patch its LateUpdate).

**Permanent fix:** swap the cube visual for a custom prefab without vanilla arrow geometry. Canonical prefab [`NoteCube.prefab`](../../../VivifyTemplate/Assets/Aline/Prefabs/projectiles/NoteCube.prefab):

- **Body**: mesh `Default Base.fbx` from [legoandmars/CustomNotesUnityProject](https://github.com/legoandmars/CustomNotesUnityProject) with shader [`Aline/Outline`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineOutline.shader) (inverted-hull + SPI + GPU instancing to know color per-instance). Shader recipe in the [`vivify-materials → Outline shader`](../vivify-materials/SKILL.md) skill. `localScale=45` to compensate for the raw mesh's 0.011 bounds.
- **Indicator**: child GameObject `Dot` with the `Dot` mesh from `Default Arrows.fbx` (`NoteArrows.fbx` in the repo), shader [`Aline/DotOverlay`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineDotOverlay.shader) (solid HDR color + `ZTest Always` + `ZWrite Off` so the dot punches through body+outline regardless of depth). `localPosition=(0,0,0)` (cube center), `localRotation=Euler(90, 0, 0)` (aligns the mesh's XY plane with the cube face facing the player). Without that rotation the plane ends up parallel to the view direction and looks "edge-on". Material `M_NoteDot` in `aline_bundle` with `_Color=(3, 3, 3, 1)` HDR.
- **Smoke envelope**: child GameObject `SmokeEnvelope` with `ParticleSystem` configured `simulationSpace=Local`, `scalingMode=Hierarchy`, `localScale=(1/45, 1/45, 1/45)` (neutralizes the root's `localScale=45`). Shader `Aline/ParticleSmoke`, material `M_SmokeTrail`. Rate 15/s, lifetime 0.6-1.0s, startSize 0.8-1.2, alpha peak 0.95 with soft fade-in (envelope visually "breathes" around the cube). Inherits the root's `scale=0` during NJS jump-in → automatically invisible until the `scale-pop`. scalingMode trick detail in [`vivify-materials → Particle shaders → Gotcha 4`](../vivify-materials/SKILL.md).
- **Smoke trail (world)**: child GameObject `SmokeTrailWorld` with `ParticleSystem` `simulationSpace=World`, same `scalingMode=Hierarchy` + `localScale=(1/45, 1/45, 1/45)` so it also inherits invisibility during jump-in. Material `M_SmokeTrail`. Rate 30/s (high density so the trail reads continuous at high speeds, not as "floating pellets"), lifetime 0.7-1.0s, startSize 0.4-0.8, alpha peak 0.85 from t=0 (no fade-in, avoids gap between cube and trail — see [`vivify-materials → Gotcha 5`](../vivify-materials/SKILL.md)). During cube hover particles emit beside the cube; during launch previous particles remain in world → trail.

Apply via `AssignObjectPrefab` with `anyDirectionAsset` (the notes are `d=8` = dot/any direction). For future directional support (notes with `d=0..7`), use `asset` instead of `anyDirectionAsset` and replace the `Dot` child with the `Arrow` mesh from the same `NoteArrows.fbx` (pointing local +Y; BS automatically rotates the prefab based on the `d` value). Same rotation pattern (90X probably) to align the Arrow's XY plane with the visible face.

Sources of the original bug verified: [Aeroluna/Heck — ObjectInitializer.cs](https://github.com/Aeroluna/Heck/blob/master/NoodleExtensions/HeckImplementation/ObjectInitializer.cs), [CutoutManager.cs](https://github.com/Aeroluna/Heck/blob/master/NoodleExtensions/Managers/CutoutManager.cs), [CutoutEffectPatches.cs](https://github.com/Aeroluna/Heck/blob/master/NoodleExtensions/HarmonyPatches/SmallFixes/CutoutEffectPatches.cs).

## Event templates

### 1. Animator trigger (1 event per attack)

```json
{"b": <trigger_beat>, "t": "SetAnimatorProperty", "d": {
  "id": "alineMain",
  "properties": [{"id": "<trigger_id>", "type": "Trigger", "value": true}]
}}
```

### 2. AssignPathAnimation per cube (N events, at `b=0`)

```json
{"b": 0, "t": "AssignPathAnimation", "d": {
  "track": "<attack_id>_cube_<i>",
  "duration": 0,
  "definitePosition": "<attack_id>_cube_<i>_path"
}}
```

### 3. Telegraph burst (N SphereBurst InstantiatePrefab, at `spawn_beat`)

```json
{"b": <spawn_beat[i]>, "t": "InstantiatePrefab", "d": {
  "asset": "assets/aline/vfx/sphereburst.prefab",
  "position": [<sphere_world[i]>]
}}
```

No `id`: the prefab auto-destroys via `stopAction=Destroy` when the ParticleSystem ends (no `DestroyObject` needed). No `rotation`/`scale`: defaults are fine for the burst (it's an omnidirectional puff).

> **Historical note:** the previous version used a "semi-transparent sphere" prefab that lasted the whole indicator window (`spawn_beat → launch_beat`) with a `DestroyObject` at the end. It was replaced (2026-05-05) by the smoke burst, which substitutes the entire sphere. The cube covers the telegraph's visual presence from its `scale-pop` onwards (wrapped in `SmokeEnvelope`).

### 5. Native BS cube (N colorNotes, at `b = spawn_beat`)

```json
{
  "b": <spawn_beat[i]>,
  "x": 0, "y": 0, "c": 0, "d": 8,
  "customData": {
    "track": "<attack_id>_cube_<i>",
    "noteJumpMovementSpeed": 16,
    "noteJumpStartBeatOffset": 13,
    "disableNoteGravity": true,
    "disableNoteLook": true,
    "spawnEffect": false,
    "animation": {
      "dissolve":      [[0,0],[0,0.499],[1,0.5],[1,1]],
      "dissolveArrow": [[0,0],[0,0.499],[1,0.5],[1,1]],
      "scale":         [[0.1,0.1,0.1,0.5], [1,1,1,0.515], [1,1,1,1]],
      "localRotation": [[<pitch_i>,<yaw_i>,0,0],
                        [<pitch_i>,<yaw_i>,0,0.5],
                        [<pitch_i>,<yaw_i>,-90,0.5027],
                        [<pitch_i>,<yaw_i>,-180,0.5059],
                        [<pitch_i>,<yaw_i>,-270,0.510],
                        [<pitch_i>,<yaw_i>,-360,0.520],
                        [<pitch_i>,<yaw_i>,-360,1]]
    }
  }
}
```

### 6. pointDefinition per cube (N entries in `customData.pointDefinitions`)

```json
"<attack_id>_cube_<i>_path": [
  [<sphere_lane_i_x>, <sphere_lane_i_y>, <sphere_lane_i_z>, 0],
  [<sphere_lane_i_x>, <sphere_lane_i_y>, <sphere_lane_i_z>, <fire_time_i>],
  [1.5, 0, 0, <arrival_time_i>],
  [1.5, 0, 0, 1]
]
```

> `c` (color) and `d` (cut direction) currently at `0, 8` (red, dot/any-direction). When we do real parry, **alternate** `c` between 0/1 for flow and pick `d` based on the cube's approach angle (8 ≠ directional but more permissive; 0-7 force a specific cut).

## Step-by-step algorithm

1. **Collect inputs**: `trigger_id`, `trigger_beat`, `N`, `spheres[]` (with world_pos, spawn_beat, launch_beat per one), `attack_id`.
2. **Check HJD constraint**: for all i, `(launch_beat[i] - spawn_beat[i]) + travel_beats <= 14`. If it fails, raise `noteJumpStartBeatOffset`.
3. **For each cube i**:
   - Convert `sphere_world[i]` → `sphere_lane[i]` with the calibrated formula.
   - Compute `pitch_i, yaw_i` with the static-face-player formula (direction AWAY from the player).
   - Compute `fire_time_i = 0.5 + (launch_beat[i] - spawn_beat[i]) / 28`.
   - Compute `arrival_time_i = fire_time_i + travel_beats / 28`.
4. **Generate JSON**:
   - Animator trigger (template 1)
   - 7× AssignPathAnimation (template 2)
   - 7× sphere InstantiatePrefab (template 3)
   - 7× sphere DestroyObject (template 4)
   - 7× cube colorNote with full localRotation/scale/dissolve (template 5)
   - 7× pointDefinition (template 6)
5. **Apply to the `.dat`**: edit directly or via PowerShell with UTF-8 without BOM (watch the `ConvertTo-Json` gotcha with empty arrays — see SKILL.md).
6. **Verify**: `ConvertFrom-Json` round-trip + event count audit.
7. **Launch BS** on the corresponding difficulty, with CustomNotes disabled.

## Full example (current Skill4)

See `beatsaber-map/NormalStandard.dat`. Concrete inputs:

- `trigger_id` = `Skill4`, `trigger_beat` = 4
- `N` = 7
- `spheres[]`:
  - i=0: world `(-3, 3, 8)`, spawn_beat 10.67, launch_beat 20.67
  - i=1: world `(-2.598, 4.5, 8)`, spawn_beat 12, launch_beat 22.34
  - i=2: world `(-1.5, 5.598, 8)`, spawn_beat 13.33, launch_beat 24
  - i=3: world `(0, 6, 8)`, spawn_beat 14.67, launch_beat 25.67
  - i=4: world `(1.5, 5.598, 8)`, spawn_beat 16, launch_beat 27.34
  - i=5: world `(2.598, 4.5, 8)`, spawn_beat 17.33, launch_beat 29
  - i=6: world `(3, 3, 8)`, spawn_beat 18.67, launch_beat 30.67
- `travel_beats` = 2
- `sphere_scale` = 1.5
- `attack_id` = `skill4` (single instance — no `_NNN` yet because there's only one)

The positions form a semicircle centered on `(0, 3, 8)` with a 3m radius, angles 180°→0° (left → right from the player's POV). Timings respect a 1.333 beat step between spawns and 1.667 between launches.

## Variables to tune vs not touch

**Tunable per instance:**
- `trigger_beat`, `spawn_beat[]`, `launch_beat[]`, `travel_beats`
- `sphere_world[]` (arc geometry)
- `N`
- `sphere_scale`
- `attack_id`

**Don't touch without justification:**
- `NJS = 16` (standard)
- `offset = 13` (HJD ≈ 14, minimum for max gap)
- `disableNoteGravity = true`, `disableNoteLook = true`, `spawnEffect = false`
- `dissolve` / `dissolveArrow` paths (the dissolve trick recipe)
- `scale` pop keyframes (0.1 → 1 at time 0.5 → 0.515)
- `localRotation` Z spin keyframes (0 → -360 in 90° steps with easeOutQuad-shaped timestamps — see "easeOut curve" section)
- Convention: `c=0, d=8` in uninteractable mode. When `uninteractable` is removed, alternate `c` by flow and pick `d` by direction.

**Remove when polishing:**
- (future) `uninteractable: true` is implicit (we'll remove it in the last iteration so the notes affect score, but the cube is out of saber-reach during the indicator window, doesn't count as miss). Verify when enabling real parry.
- (future) `AssignObjectPrefab` for visual swap to eliminate the arrow inconsistency.

## Pending polish (not in the recipe, noted)

- Validation with lower `travel_beats` (faster cubes): the SmokeTrailWorld probably needs re-tuning of rate/lifetime so the trail keeps reading continuous. Hypothesis: rate is already prepared for high speeds (30/s), but confirm empirically.
- VR validation (head moving): the "smoke contained around the cube" feeling + trail on fire might read differently from a headset than in flatscreen mode.
- Remove `uninteractable` and configure `c`/`d` for real scoreable parry.
- Separate bug: the cube outline on spawn appears white before changing to red (probable: the Aline/Outline shader's instanced `_Color` starts at default white before Vivify pushes the saber color on the first visible frame). Not blocking but noted.
- (Optional) Point "haze / smudge" on spawn beat — a large additive quad with short life to emphasize the telegraph's "visual explosion". Deferred if the burst alone feels enough.
