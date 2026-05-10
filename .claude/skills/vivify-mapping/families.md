# Attack family catalog

This file formalizes the **attack contracts** for the boss fight. Described in [PRODUCTO.md](../../../docs/PRODUCTO.md): each of Aline's abilities is a **reusable family** (prefab + animation + `.dat` event sequence + parry encoding). Once a family is defined and validated with a prototype, instantiating it N times in the map with different timings/positions is mechanical work.

If you're adding a new attack, **search this catalog first** for an existing family that fits. Only create a new family (G, H...) if the attack doesn't fit any existing one.

## Trigger identification table

Confirmed mapping from Aline's Animator (`Aline_AC.controller`) to the attack families. The **trigger** name (Animator parameter) doesn't carry the `Paintress_` prefix; the **clip** does carry it in some cases (FBX importer artifact).

| Trigger | Clip | Phase | Family | Notes |
|---|---|---|---|---|
| `Idle1` | `Paintress_Idle1` | 1 | — | Base idle phase 1 (on ground) |
| `Idle2` | `Paintress_Idle2` | 2 | — | Base idle phase 2 (floating) |
| `Idle3` | `Paintress_Idle3` | 3 | — | Defeated idle (on ground) |
| `Idle1_to_idle2_transition` | `Paintress_Idle1_to_idle2_transition` | 1→2 | — | Transition between idles |
| `Idle2_to_idle3_transition` | `Paintress_Idle2_to_Idle3_transition` | 2→3 | — | Falls from floating to ground |
| `Idle2_Stun` | `Paintress_Idle2_Stun` | 2 | — | Hunched forward (stun) |
| `Idle_Countered` | `Paintress_Idle_Countered` | 2 | — | Hit reaction, hunched back |
| `DashIn-Idle1` | `Paintress_DashIn-Idle1` | 1 | **B** | Dash in + melee strike |
| `DashOut-Idle2` | `Paintress_DashOut-Idle2` | 1 | B (post) | Retreat after melee, returns to far position |
| `DefaultSlot` | (no prefix) | 1 | B (alias) | Same clip as `DashIn-Idle1` |
| `DefaultSlot (1)` | (no prefix) | 1 | B (alias) | Same clip as `DashIn-Idle1` |
| `Skill1` | `Paintress_Skill1` | 1 | **E** | Gestures with explosions (multi-hit chain with explosive VFX) |
| `Skill2_Start` | `Paintress_Skill2_Start` | 1 | **F** (intro) | Aline rises, raises arm |
| `Skill2_Loop` | `Paintress_Skill2_Loop` | 1 | **F** (sustain) | Elevated idle, energy ball charging |
| `Skill2_End` | `Paintress_Skill2_End` | 1 | **F** (resolve) | Aline lowers to ground after the explosion |
| `Skill3` | `Paintress_Skill3` | 1 | **A** | "Plays the harp" + 3 giant sequential rocks |
| `Skill4` | `Paintress_Skill4` | 1 | **A** | "Plays the harp" + spin + N small projectiles |
| `Skill5` | `Paintress_Skill5` | 1 | **B + modifier C** | Melee with distortion (gray environment for the player) |
| `Skill6` | `Paintress_Skill6` | 1→2 | — | Narrative transition: jumps, floats, arms herself with a big paintbrush, distortion |
| `Skill7` | `Paintress_Skill7` | 2 | **E** | 5 strikes with dash-back-return, big paintbrush |
| `Skill7_MaelleBurningCanvasVersion` | (variant) | 2 | E (variant) | Visually almost identical to `Skill7` |
| `Skill8` | `Paintress_Skill8` | 2 | **special case** | Giant Aline in background + energy balls + series of strikes (see "Deferred" in NEXT_STEPS) |
| `Skill9` | (does NOT exist in clips) | 2? | — | Suspected: giant Aline attack; extraction pending from FModel |
| `Skill10` | `Paintress_Skill10` | 2 | **E** | Series of strikes in place |
| `Skill11` | (does NOT exist in clips) | — | — | Gap in Animator numbering |
| `Skill12` | `Paintress_Skill12` | 2 | **E** | Long series with jumps |
| `Skill_Aline_P3_Skill1` | (no Paintress_ prefix) | 3 | — | Healing to the player, Aline no longer fights |
| `Skill_Aline_P3_Skill2` | (no Paintress_ prefix) | 3 | — | Healing variant |

### Composition by phase

- **Phase 1 (ground, `Idle1`):** A (Skill3, Skill4), B (DashIn-Idle1), B+C (Skill5), E (Skill1), F (Skill2 multi-stage). Transitions to phase 2 via `Idle1_to_idle2_transition` + `Skill6`.
- **Phase 2 (floating, `Idle2`):** E (Skill7, Skill10, Skill12), special case (Skill8). Transitions to phase 3 via `Idle2_to_idle3_transition`.
- **Phase 3 (defeated, `Idle3`):** no combat. P3_Skill1 / P3_Skill2 are narrative healings.

---

## Shared contract (valid for all families)

Rules every instance of any family respects. Breaking them == attacks that step on each other, scene leaks, impossible debugging.

### Track namespacing

Each **instance** of an attack generates a **unique track ID**. Convention:

```
atk_<family>_<NNN>
```

Where `<family>` ∈ `{a, b, d, e, f, ...}` and `<NNN>` is a 3-digit counter per family (`atk_a_001`, `atk_a_002`, ..., `atk_e_017`). If an instance generates multiple objects (e.g. family A with N projectiles), add suffix `_iN`: `atk_a_001_i0`, `atk_a_001_i1`, etc.

**Why:** `AssignTrackParent` and `DestroyPrefab` need to locate the track unambiguously. Without structured namespacing, tracks from different attacks collide and cleaning up one wipes another.

**What does NOT use this namespace:**
- Aline animations → always track `alineTrack` (defined in Aline's original `InstantiatePrefab` when the map loads).
- Post-process filters (modifier C) → separate `postFx_<NNN>` track, not `atk_*`.

### Separation between Aline tracks vs attack tracks

**Aline animations** (`SetAnimatorProperty` with triggers `Skill1`, `Skill5`, etc.) **always** go on `alineTrack`. Aline's prefab is instantiated once at the start of the map and lives for the whole song.

**Attack prefabs** (projectiles, indicators, slashes) go on `atk_*` tracks and are destroyed at the end of the attack. **Never** parent an attack prefab to `alineTrack` unless the attack visually follows Aline during her movement (rare case; document it in the instance).

### Mandatory cleanup

Every family ends its sequence with a `DestroyPrefab` for each `atk_*` track it opened. No exceptions. Instantiated prefab `id`s are also explicitly destroyed. Verify when prototyping: instantiating the attack twice in a row must leave no residue in scene.

### NJS and reaction time

Parry notes are placed in the `.dat`'s `_notes` array with their `_time` computed **backwards**: `_time = T_impact - (jumpDuration / 2)`. For showcase with low NJS (~10) the jump duration is generous, but **telegraph readability wins**: if the attack doesn't read in time, lower NJS or move the telegraph's `_time` earlier.

---

## Family A — Ranged Sequence

**Mechanic:** Aline launches N projectiles that appear above/beside her and fall sequentially toward the player. Each projectile = one parry.

**Pattern validated in Skill4 (2026-05-04).** Semi-transparent sphere (Vivify `InstantiatePrefab` of the telegraph) + native BS cube with `definitePosition` that keeps it anchored to the sphere's position during the indicator window, and at `launch_beat` sweeps it to the player. Sphere despawns on the same `launch_beat`. **Full parameterizable recipe** in [`family-a-recipe.md`](family-a-recipe.md) (calibrated constants, world↔lane conversion, static-face-player rotation calculation, dissolve trick, JSON templates, step-by-step algorithm). For a new family A attack you only need the "Inputs" block of the recipe.

### Required inputs

| Input | Value | Notes |
|---|---|---|
| Animator trigger | `Skill3` (3 giant rocks, phase 1) or `Skill4` (N small projectiles after spin, phase 1) | Both variants fit A; VFX and N change |
| Indicator prefab (sphere) | `assets/aline/prefabs/projectiles/telegraphsphere.prefab` | Reusable semi-transparent sphere. Will be replaced by a custom mesh in polish (see recipe section "dissolveArrow limitation") |
| Projectile prefab | Native BS cube (no Vivify prefab needed) | The cube is the note — `c=0/1, d=0..8`, with `definitePosition` pointing to the sphere |

### `.dat` event sequence

Validated with Skill4. The full structure with templates is in [`family-a-recipe.md`](family-a-recipe.md). Summary of times relative to `launch_beat` (= when the cube is fired, sphere despawns):

```
trigger_beat       : SetAnimatorProperty (animator trigger) → alineMain  (== Aline animation starts)
launch_beat - 10b  : InstantiatePrefab sphere_i + AssignPathAnimation cube_i (b=0)
                     ColorNote of cube i with b=spawn_beat (== sphere appears)
launch_beat        : DestroyObject sphere_i
                     Cube i starts moving toward the player (path keyframe fire_time)
launch_beat + 2b   : Cube reaches the player (path keyframe arrival_time)
```

> Concrete offsets per instance come from the recipe (`fire_time`, `arrival_time` are computed from `spawn_beat`/`launch_beat`/`travel_beats`).

### Parry encoding

- Type: `_notes` with `_cutDirection` encoding **the projectile's quadrant of origin**.
- Typical distribution: projectiles fall in a frontal arc → notes on mid/upper rows.
- Each note is separated from the next by `delta` (60/BPM × beats).
- Color (`_type` 0/1) can alternate to force parries with both hands.

### Tunable parameters (per instance)

| Parameter | Typical range | Notes |
|---|---|---|
| `T_impact_0` | any `_time` | attack start |
| `N` | 3 (Skill3) or 5-7 (Skill4) | dictated by the animation |
| `delta` | 0.3s-0.8s | low = more intense, less readable |
| Note directions | 8 BS values | one per projectile |

### NOT tunable

- Event structure (order and relative deltas of the telegraph).
- That each projectile has its own `_iX` track.
- N must match the launch visible in the animation.

### No-conflict rules

- Tracks used: `atk_a_NNN`, `atk_a_NNN_i0..iN-1`.
- Don't overlap two family A in `T_impact_0 ± 2s`: confuses readability.
- Compatible with simultaneous B/D/E/F if they're in another zone of the grid.

---

## Family B — Melee Directional Slash

**Mechanic:** Aline executes a melee strike after closing in on the player. Telegraph = approach (DashIn) + line/streak in the slash's direction. Parry = a single note in the **opposite** direction (real parry).

> **Operational root motion (2026-05-01).** DashIn/DashOut translate the GO via root motion synthesized in Blender (`scripts/blender/synthesize_root_motion.py`) + `motionNodeName="SK_Curator_Aline"` in the FBX importer + Apply Root Motion = ON in the prefab's Animator. Validated e2e in `EasyStandard.dat`: Aline advances ~6m forward in DashIn, returns in DashOut, no snap-back. Operational details and discarded paths in the [`vivify-animations`](../vivify-animations/SKILL.md) skill, section "Root motion for clips with displacement" + "Closed paths".

### Required inputs

| Input | Value | Notes |
|---|---|---|
| Approach animator trigger | `DashIn-Idle1` (ends in Idle1 pose, returns to default) or `DashIn-Idle2` (ends in Idle2 pose, chains directly to Idle2) | Both carry forward motion (~6m world Z) extracted as root motion. The choice depends on which pose you want post-dash: Idle1 if the attack is one-off, Idle2 if Aline chains more combat in alert pose |
| Strike animator trigger | `Skill1` (standard strike) or `Skill5` (strike with distortion — combines with modifier C) | Clips with minor motion (256/75 cm in Y bone-local) that end in a neutral pose — root motion not synthesized (no snap-back because they don't end displaced). |
| Retreat trigger | `DashOut-Idle2` | Returns Aline to far position, chains to Idle2 |
| Streak prefab | `assets/aline/prefabs/slash_streak.prefab` (TBD — pending creation) | Line/trail drawing the slash axis |
| Streak material | unlit emissive with alpha; reusable for all B instances | — |

### Choreography (part of the contract)

The attack consumes three beats: **approach → strike → retreat**. Approximate timings:

- `T_impact - 1.5s` : `DashIn-Idle1` trigger (Aline starts approaching)
- `T_impact - 0.6s` : streak appears, Aline already close
- `T_impact + 0.0s` : strike + note
- `T_impact + 0.5s` : `DashOut-Idle2` trigger (retreat)

If the phase already has Aline close by previous context, you can skip `DashIn-Idle1` and enter from `Idle1` directly to impact, but then the attack is **not canonical Family B** — document it as an atypical instance.

### `.dat` event sequence

```
T_impact - 1.5s : SetAnimatorProperty (DashIn-Idle1 or Skill5) → alineTrack
T_impact - 0.6s : InstantiatePrefab (slash_streak) → atk_b_NNN
T_impact - 0.6s : AnimateTrack (streak scaling/extension) over atk_b_NNN for 0.6s
T_impact + 0.0s : parry note reaches the player
T_impact + 0.2s : DestroyPrefab atk_b_NNN
T_impact + 0.5s : SetAnimatorProperty (DashOut-Idle2) → alineTrack
```

### Parry encoding

- **A single note.** Direction = **opposite to the streak's axis** (If the streak goes left→right, the note is horizontal left).
- Typical position: center of screen — a slash is a single strike.
- Color: whatever fits the flow.

### Tunable parameters

| Parameter | Range | Notes |
|---|---|---|
| `T_impact` | any `_time` | — |
| Slash axis | 8 directions | the streak VFX must match |
| Anim trigger | `DashIn-Idle1` or `Skill5` | Skill5 implies modifier C active |
| Skip DashIn | bool | if the phase already has Aline close |

### NOT tunable

- That the note is **a single one**.
- That its direction is **opposite** to the streak.
- Telegraph→impact window (~0.6s).

### No-conflict rules

- Track used: `atk_b_NNN`.
- Compatible with any other simultaneous family as long as they don't use the same visual quadrant.

---

## Family D — Shrinking Indicator

**Mechanic:** indicator (square with corners + concentric ring, E33 style) appears around a point and shrinks. Parry = single note at the exact moment of closure.

> Visual reference: the marker E33 uses when an enemy telegraphs precision attacks. Adaptation, not replica — the feel is: square with marked corners + outer ring that contracts until it touches the corners.

> **No source animation in Aline's Animator.** This family is **our invention**, not a direct translation of an existing clip. Used wherever we want to force a precision parry, typically as an overlay on the key moment of another family (last projectile of A, explosion of F) or as a standalone attack at the climax.

### Required inputs

| Input | Value | Notes |
|---|---|---|
| Animator trigger | flexible — the indicator is independent of Aline's animation | If combined with another family, the animator trigger is dictated by that family, not D |
| Indicator prefab | `assets/aline/prefabs/indicator_ring.prefab` (TBD — **pending creation**) | Square + concentric ring, animatable by scale |
| Material | unlit emissive white/gold to match E33 aesthetic | reusable |

### `.dat` event sequence

```
T_impact - 1.0s : InstantiatePrefab (indicator_ring) → atk_d_NNN, scale [s_max, s_max, s_max]
T_impact - 1.0s : AnimateTrack (scale s_max → s_min) over atk_d_NNN for 1.0s, easing easeIn
T_impact + 0.0s : parry note reaches the player (ring touching the square's corners)
T_impact + 0.1s : DestroyPrefab atk_d_NNN
```

### Parry encoding

- **A single note** positioned **exactly where the indicator is**: if the indicator is at `[x=2, y=1]` of the note grid, the note goes at `_lineIndex=2, _lineLayer=1`.
- The note's direction can be anything; what defines the attack is the **timing** (ring closure).

### Tunable parameters

| Parameter | Range | Notes |
|---|---|---|
| `T_impact` | any `_time` | — |
| Indicator position | BS 4×3 grid | dictates the note's position |
| `s_max` | 1.5-3.0 (world scale) | initial ring size |
| `s_min` | 0.3-0.5 | final size = the block inside the ring |
| Closure duration | 0.6s-1.5s | short = precision parry; long = contemplative parry |

### NOT tunable

- That the ring closure is **monotonic** (doesn't expand again before impact).
- That the note arrives **at the exact instant of closure**, not earlier.

### No-conflict rules

- Track used: `atk_d_NNN`.
- Multiple simultaneous family D are **OK** (several indicators on different grid cells = precision combo).
- Combinable as an overlay on A (last projectile), F (explosion moment), or E (last hit of the chain).

---

## Family E — Multi-hit Chain

**Mechanic:** chain of N parries in rapid succession during a single Aline animation that has N embedded hits. Different from A in that the attack is melee (not projectiles). Different from B in that it's N hits, not 1.

### Required inputs

| Input | Value | Notes |
|---|---|---|
| Animator trigger | `Skill1` (phase 1, gestural magic with explosions) / `Skill7` or `Skill7_MaelleBurningCanvasVersion` (phase 2, big paintbrush, dash-back-return × 5) / `Skill10` (phase 2, in place) / `Skill12` (phase 2, long with jumps) | Each has N hits embedded in the clip |
| Per-hit VFX | depends on trigger: explosion (Skill1), paintbrush trace (Skill7-12) | parameterizable per instance |
| VFX prefab/material | TBD per skill | extract from FModel or create custom |

### `.dat` event sequence

Times relative to the **first hit** (`T_first_hit`). Assumes `delta` = separation between consecutive hits, dictated by the animation.

```
T_first_hit - 1.0s : SetAnimatorProperty (trigger) → alineTrack
T_first_hit + 0.0s : InstantiatePrefab (vfx_hit_0) → atk_e_NNN_h0
T_first_hit + 0.0s : parry note #0
T_first_hit + 0.3s : DestroyPrefab atk_e_NNN_h0
T_first_hit + delta : (repeat InstantiatePrefab/note/destroy for h1..hN-1)
```

> `delta` and N are **dictated by the clip** — tune it with the actual animation (Skill7 ≈ 5 hits, Skill10 ≈ several in place, Skill12 ≈ the longest with jumps, Skill1 ≈ gestures in series).

### Parry encoding

- Chain of N notes with separation `delta` (typically 0.4-0.7s).
- Directions can be varied if the anim suggests movement (Skill12 with jumps), or more uniform if the anim is static (Skill10).
- Skill7 with dash-back-return: each hit comes "from afar" — direction can encode Aline's approach angle.

### Tunable parameters

| Parameter | Range | Notes |
|---|---|---|
| `T_first_hit` | any `_time` | — |
| Trigger | `Skill1` / `Skill7` / `Skill7_Maelle...` / `Skill10` / `Skill12` | each with its canonical N and delta |
| Note directions | 8 values | one per hit |
| Per-hit VFX | prefab path | varies per visual instance |

### NOT tunable

- N must match the number of hits embedded in the animation. You can't ask for 3 hits if the clip has 5 — the anim will continue to the end and the hits without notes will hit "in the void".
- The first hit can't arrive before the animation kicks in.

### No-conflict rules

- Tracks: `atk_e_NNN`, `atk_e_NNN_hX` (X = 0..N-1).
- Don't overlap two simultaneous family E — the chain of notes becomes unreadable.
- E + modifier C works well for a key hit within the chain (not the whole chain).

---

## Family F — Charging AoE Ball

**Mechanic:** Aline rises, charges a visible energy ball that grows, explodes. Single parry at the moment of explosion. Very long telegraph (~3-4s) distinguishes it from B.

### Required inputs

| Input | Value | Notes |
|---|---|---|
| Animator trigger Start | `Skill2_Start` | Aline rises raising arm |
| Animator trigger Loop | `Skill2_Loop` | Sustained while the ball grows |
| Animator trigger End | `Skill2_End` | Aline lowers to ground after the explosion |
| Ball prefab | `assets/aline/prefabs/energy_ball.prefab` (TBD — pending creation or extraction from FModel) | Energy ball, scalable, emissive |
| Ball material | unlit emissive with bloom (if doable inside the current Vivify pipeline) | reusable |

### `.dat` event sequence

```
T_explosion - 4.0s : SetAnimatorProperty (Skill2_Start) → alineTrack
T_explosion - 3.0s : InstantiatePrefab (energy_ball, scale s_min) → atk_f_NNN
T_explosion - 3.0s : SetAnimatorProperty (Skill2_Loop) → alineTrack
T_explosion - 3.0s : AnimateTrack (scale s_min → s_max) over atk_f_NNN for 3.0s
T_explosion + 0.0s : parry note reaches the player
T_explosion + 0.0s : DestroyPrefab atk_f_NNN (accompany with optional explosion VFX)
T_explosion + 0.3s : SetAnimatorProperty (Skill2_End) → alineTrack
```

### Parry encoding

- **A single note** in central position (the ball is in front of the player).
- Direction: whatever the flow asks for.
- Tip: combinable with D (shrinking indicator) over the note to reinforce the "precision parry" at the exact moment of explosion.

### Tunable parameters

| Parameter | Range | Notes |
|---|---|---|
| `T_explosion` | any `_time` | — |
| Charge duration | 2.0s-4.0s | `Skill2_Loop` can be sustained arbitrarily |
| `s_min` / `s_max` | 0.3 / 1.5-3.0 (world scale) | initial / final ball size |

### NOT tunable

- The animator trigger structure `Skill2_Start` → `Skill2_Loop` → `Skill2_End`. Skipping Loop = Aline ends up badly positioned.
- That the parry is a single note (it's F's signature).

### No-conflict rules

- Track: `atk_f_NNN`.
- Only one F active simultaneously. Two growing balls confuse the telegraph.
- F + modifier C combines very well for phase 1 climax.

---

## Modifier C — Distortion Overlay

**Not a family.** It's a **visual transformation** stackable on A/B/D/E/F in a concrete instance of the attack, that applies a post-process filter to the player (desaturation / grayscale) during a specific window of the telegraph or parry. Replicates E33's "distortion" mechanic (`Skill5`, possibly others in the future).

### Required inputs

| Input | Value | Notes |
|---|---|---|
| Blit material | `assets/aline/materials/m_distortion.mat` (TBD — **pending creation**) | Shader that applies desaturation + optional vignette |
| Animatable property | `_Saturation` (float, 0.0 grayscale → 1.0 normal) | Exposed on the material's shader |

### Events to inject (snippet)

Composes with the base family's sequence adding these events. Typically the window opens before the impact and closes right after.

```
T_window_start - 0.5s : Blit (m_distortion) → postFx_NNN
T_window_start - 0.5s : SetMaterialProperty (_Saturation 1.0 → 0.0) over m_distortion for 0.5s
T_window_end + 0.0s  : SetMaterialProperty (_Saturation 0.0 → 1.0) over m_distortion for 0.3s
T_window_end + 0.3s  : Blit clear postFx_NNN
```

### Composability

- **B + C** → melee with distortion (canonical case, vanilla `Skill5`).
- **A + C** → projectile cascade with distortion on the final descent.
- **E + C** → multi-hit chain with distortion during 1-2 key hits.
- **F + C** → ball charging with distortion at the moment of explosion.
- **D + C** → precision indicator with distortion (climax).

### NOT tunable

- That the Blit shader is **reusable**: a single instance of `m_distortion` for the whole map, don't clone it per instance.
- That **only one C is active simultaneously** in the map. Two distortions step on each other visually.

### Restrictions

- Post-fx track: `postFx_NNN` (separate from the `atk_*` namespace).
- If the base family already visually saturates the screen, C may be redundant or unreadable — verify when prototyping.

---

## Slot for future families

If a pattern surfaces that doesn't fit in A/B/D/E/F, add it here following the same schema (Inputs / Sequence / Encoding / Tunables / NOT tunable / No-conflict). Candidates identified but not needed yet:

- **G — AoE telegraphed area:** a grid zone gets marked as "don't be here when the timer closes". Changes the mechanic: instead of hitting, the player **avoids**. Possible if we find how to fit "don't hit" into BS (walls? bombs? saber-clear?).
- **Special case Skill8 (phase 2 climax):** giant Aline in background + energy balls + series of strikes. Not a reusable family — it's a unique narrative beat. See "Deferred" in NEXT_STEPS.md, requires a dedicated design conversation (the "impressive" attack identified by the user).
