# NEXT_STEPS

## Current state

End-to-end pipeline operational:

- **Beatmap V3** (`*Standard.dat`, `BPMInfo.dat`); Info.dat in its underscore schema. Map versioned in git (commit `ef5bb7d`).
- **Vivify** loads the bundle and instances `aline.prefab` in the scene. CRC sync automatic after F5 (`Editor/PostBuildSyncCRCs.cs` → `scripts/sync-crcs.ps1`).
- **Aline textured** with 5 custom materials: `M_Aline_BlackBody` (fresnel), `M_Aline_Body_1`, `M_Aline_Body_2` (BodyLit with normal+fake-light), `M_Aline_Dress` (EnergyMask translucent), `M_Aline_Face` (radial fade). Detail in [`vivify-materials`](../.claude/skills/vivify-materials/SKILL.md).
- **Aline's hair** rigged with 163 strand bones + sway loop (`HairSway.anim`).
- **Animations**: `.psa` → Blender → FBX → Unity Animator → Vivify pipeline working with canonical root motion for clips with displacement. Detail in [`vivify-animations`](../.claude/skills/vivify-animations/SKILL.md).
- **E33 stage** custom (`RockPlatform.fbx`, 217K polys, 3 submeshes: rock + blue ivy carpet + pink bushes). Vanilla environment disable via Chroma `customData.environment[]`. Custom skybox `M_Skybox_E33`.
- **Difficulties** registered: Easy (locomotion sandbox), Normal (clone of Easy + Skill4 trigger at b=40, no gameplay yet — playground for iterating family A), ExpertPlus (cube test sandbox).
- **Our own MCPs**:
  - `unity-mcp` (local fork at `d:\vivify_repo\unity-mcp/`, bridge stdio:6400). Tools `read_console`, `refresh_unity`, `execute_code`, `manage_animation`, `manage_asset`, `manage_material`, `manage_prefabs`, etc.
  - `fmodel-mcp` (`d:\vivify_repo\fmodel-mcp/`, public repo `luisep92/fmodel-mcp`). Tools `mcp__fmodel__fmodel_*`: `search`, `read`, `inspect_material`, `export_texture`/`mesh`/`raw`, `list_exports`, `status`. Canonical flow to inspect/export E33 assets.

---

## Next steps (in order)

> **Scope:** Phase 1 + cosmetic intro, soft deadline. Detail in [DECISIONES.md → "Scope: Phase 1 + cosmetic intro; soft deadline"](DECISIONES.md). The attack families to prototype are reduced to the ones that appear in Phase 1.

> Previous pivot: with the **showcase map** decision ([DECISIONES.md](DECISIONES.md)), the order changes. The song and narrative state machine depend on having the **attack systems** first, defined as reusable contracts. Composing phases on top of unstable systems is a recipe for a mess.

### 1. Attack family catalog + contracts — **done**

Five families (A/B/D/E/F) + stackable modifier C formalized in [`families.md`](../.claude/skills/vivify-mapping/families.md): inputs, event sequence, parry encoding, tunable parameters, non-conflict. Full Animator→family mapping included. Phase-by-phase vision in [PRODUCTO.md](PRODUCTO.md).

### 2. Locomotion sandbox — done

Implemented in `beatsaber-map/EasyStandard.dat` (Easy difficulty of the Test map, registered in `Info.dat`). Chain of `SetAnimatorProperty` runs through idles, transitions, dashes, and canonical stuns. Validated e2e in BS (2026-05-01): idles, transitions, and dashes chain cleanly without snap-back; DashIn translates the GO ~6m forward, DashOut returns it.

### 2.5. Re-export `Aline_Anims.fbx` with canonical root motion — done

Final operational pipeline:
1. The `.psa` files bake forward motion into `pose.bones["root"].location[1]` (Y bone-local). Verifiable with `scripts/blender/inspect_motion.py`.
2. Unity 2019.4 with `Generic + Copy From Other Avatar` doesn't extract motion from an internal bone as root motion, regardless of what you put in `motionNodeName` of the clip importer or the avatar source. It does extract if the motion lives in `location` of the armature object.
3. Solution: `scripts/blender/synthesize_root_motion.py` moves the motion from the "root" bone to the armature object with axis remap (Y bone → Z object negated) compensating the FBX exporter's transform chain (`axis_up="Y"`) + the 270°X rotation that the armature object picks up in Unity.
4. `AlineAnimsImporter` sets `motionNodeName="SK_Curator_Aline"` + unbakes XZ and Y per clip (`XzRootMotionSuffixes`).
5. The prefab's Animator with Apply Root Motion = ON applies the delta to the prefab root.

Operational detail and gotchas in the [`vivify-animations`](../.claude/skills/vivify-animations/SKILL.md) skill, "Root motion for clips with displacement" + "Closed paths" sections. Consolidated decision in [`DECISIONES.md`](DECISIONES.md).

### 3. Custom environment + Aline materials — **done except cosmetic intro**

The default BS environment (TimbalandEnvironment) visually eats Aline: the `BlackPart`/`BlackPart1`/`CuratorFace` black materials disappear on a dark background. Any fresnel/face shader work on Aline isn't judgeable until we have a correct visual context. That's why environment goes before materials in this step. Vivify capabilities validated in `docs/heckdocs-main/docs/vivify/events.md` + `environment/environment.md`.

Substeps in order:

1. **Custom skybox** — **done 2026-05-02**. `M_Skybox_E33` material with `Skybox/Panoramic` shader, `T_Skybox_6_HybrydNoiseVT` texture (4096×2048 equirect, ripped from Sandfall via FModel), white tint, exposure 1.0, 180° rotation. Bundled under `aline_bundle`. `SetRenderingSettings` + `SetCameraProperty.clearFlags=Skybox` events (both needed — the first alone doesn't render). Canonical source identified but unused: `M_Flowmap_Nebula_9_Inst_2` → `T_Skybox_12_HybridNoiseVT` in `Monolith_Interior_PaintressGrandFinale`. Skybox_6 (nighttime blue-grey) chosen over _12 (cosmic-red) for its fit with the misty/blue look of the original fight. Rip methodology + skybox recipe in the [`vivify-environment`](../.claude/skills/vivify-environment/SKILL.md) skill.

2. **Switch to DefaultEnvironment + disable + Settings Setter** — **done 2026-05-02**. `Info.dat._environmentName` changed to `DefaultEnvironment`. Env disable via `customData.environment[]` with three commands: yeet `Environment|GameCore` (regex, position -69420), `active: false` for `DustPS` and `PlayersPlace`. Settings Setter in `Info.dat._customData._settings` per difficulty: starter pack + HUD off. Validated in BS. Recipe consolidated in [`vivify-environment`](../.claude/skills/vivify-environment/SKILL.md) and [`vivify-mapping`](../.claude/skills/vivify-mapping/SKILL.md).

3. **Ambient lighting** — **deferred to Phase 2** (tried and reverted 2026-05-03, commits `2fd1d7a`/`163a2f9` and reverts `b68ab0f`/`cf1fe45`).

   Architectural implementation (`AlineLighting.cginc` with modulative `AlineShade` + additive `AlineRimTint`, refactor of 4 shaders, `_AmbientFloor=0` so that lights-out is really lights-out) got to end-to-end working via `unity_AmbientSky/Equator/Ground` (gotcha of `ShadeSH9=0` in Vivify bundles: see [`vivify-materials → Ambient in Vivify bundles`](../.claude/skills/vivify-materials/SKILL.md)).

   **Why the revert:** with a single skybox and zero lighting changes in Phase 1, the system added constant tuning with no narrative value. Each skybox×ambientMode×ambientValues combination required visual iteration. Timing lesson in [`DECISIONES.md → Build low-layer systems when there's a use case`](DECISIONES.md).

   **When to revisit (Phase 2):** when there are lighting changes with narrative purpose (phase change, fade outs, particles with real light, skybox recolor as FX). Cherry-pickable commits as a starting point.

   Current state: each material has its own hardcoded `_LightDir/_LightStrength/_Ambient` (BodyLit) or no lighting (Hair/Fresnel/EnergyMask/Face). Aline reads well on the blue-grey skybox without reacting to the environment. Enough for Phase 1.

4. **E33 stage mesh** — **done 2026-05-02 with custom mesh, iterated to a rocky version**. We tried direct rip first (`SM_Rock_A_CliffEdge` + texture `Albedo_2K_vlzkba1fw` from Megascans/Jagged_Rock that the game uses) — natural irregular geometry made it impossible to align Aline's feet to the millimeter. Switched to custom mesh in Blender via blender-mcp.

   **v1 (2026-05-02 midday):** flat oval 6m × 10m × 0.5m, subtle dips (max 8cm), `position: [0, 0.97, 4]`. Functional but the NGON cap left the top as a single polygon and the texture showed radial rays (planar UV from above).

   **v2 (2026-05-02 afternoon):** rocky mountaintop-style version. Reusable builder in `scripts/blender/build_rock_platform.py`. 12×18m oval with a flat 5×11m central corridor (player at `z=0` center, Aline at `z=8` at the edge of the long axis), irregular perimeter silhouette via noise(cos θ, sin θ), relief on the flanks up to +50cm/-18cm with 2m falloff toward the corridor, smart UVs (no rays), smooth shading. `position: [0, 0.97, 0]` (centered on the player). Pipeline: Blender → FBX → Unity import → `Vivify/Build/Build Working Version Uncompressed` → PostBuildSyncCRCs auto-sync. Iterations to tune relief amplitude and push bumps away from the corridor. Pattern consolidated in the `vivify-environment` skill (sections "Custom mesh recipe" and "Gotcha: FBX axis flip").

   **Stage decoration — blue petals (done 2026-05-03):** scatter merged into the same `RockPlatform.fbx` as a second material slot/submesh. Mesh source: `Sandfall/Content/EnviroPacks/Real_Ivy_Pack/Meshes/foliage/ivy/SM_ivy_floor_plane_dense_spread_01_leaves.pskx` (stock Unreal Marketplace asset that Sandfall reused). 5 asymmetric rotated patches, aline-side focus + flanks, minimum behind the player (fixed camera doesn't see it). Pipeline:
   - `scripts/blender/build_rock_platform.py:build_ivy_scatter()` — imports the template FBX, applies Decimate ratio 0.5 (300K → 150K tris), duplicates N copies at explicit `IVY_PATCHES` positions, non-uniform scale `(s, s, s*IVY_HEIGHT_SCALE=0.15)` to squash the native ivy's vertical leaves to a "fallen petals" look, merged into rock_obj
   - Material `M_BlueIvy` with `Aline/Standard` shader + `LUMINANCE_TINT` keyword (see below) → real saturated blue recolor
   - Blender preview: the script now creates placeholder materials with real textures + EEVEE nodes that reproduce the luminance-tint (`_make_preview_material()`) — viewport in Material Preview shows an almost-final result without round-trip to BS
   - Key decision: we tried 4 approaches (discrete cluster scatter, dense cluster scatter, rock-top duplicate + atlas-tile shader, ivy floor_plane scatter) → only the last worked. Lesson: for ground decoration in BS Vivify, **mesh asset choice > shader gymnastics** — a pre-built "scattered carpet" asset pack always beats tiling an atlas via shader.

   **Stage decoration — 3D pink bushes (done 2026-05-03):** third submesh of `RockPlatform.fbx`, deterministic random scatter (seed=23, BUSH_COUNT=14) of mesh `Sandfall/Content/EnviroPacks/Environment_Set/Environment/Foliage/Models/SM_ground_foliage_03_*.pskx` (~64 native tris per JSON, ~4.4K after pskx import; 62K total after 14 instances). Restricted to `y >= 0.5` Blender pre-mirror = only in front of the player (fixed camera doesn't see behind). Material `M_PinkBush` with overbright pink-magenta luminance tint `(1.5, 0.4, 0.8)`. Adds contrasting color touches to the blue ivy carpet + small 3D protrusions. Recipe consolidated in `vivify-environment` skill, "Layer 3 — 3D bushes scatter" section.

   **Phase 1 stage state**: complete. Total ~217K polys, 1 mesh, 3 submeshes (rock 9.8K + ivy 145K + bush 62K), 3 draw calls. Plenty for BS PC, OK for Quest if needed.

4.5. **Dash Y-jump bug — closed 2026-05-02** with a fix in three layers:
   - **Blender / synthesize_root_motion v5**: normalize frame 0 to origin per axis. The `.psa` curves carry absolute baselines from the Unreal rig and don't match cross-clip (DashOut-Idle2 started at Z=604.49 while DashIn-Idle1 at Z=0); v5 subtracts the frame 0 value from all keyframes so that all clips start at `(0,0,0)` object space. Idempotent with a custom property marker.
   - **Blender / import_all_psa**: detect generic seq names ("DefaultSlot" in `_Montage.psa`) and rename using the file's basename. `Paintress_DashOut-Idle1_Montage.psa` was silenced by collision with DashIn-Idle1_Montage (alphabetically first, both with seq "DefaultSlot"); the rename frees the collision and recovers the missing action.
   - **Unity AnimatorController**: pose-mismatch between clips is absorbed with blend > 0 on the transitions. DashOut-Idle1 (new state, exit to grounded Idle1) uses `exitTime=0.7 + duration=0.3` so the blend overlaps with the last 30% of the clip — the landing happens during the dash's motion instead of "Aline reaches destination floating and then drops". 0.3s entry blend to cushion takeoff from grounded. DashOut-Idle2 (floating→floating) keeps no blend.

   Key finding: `Paintress_DashOut-Idle1_Montage.psa` and `Paintress_DashOut-Idle2.psa` contain identical skeletal animation on Aline (verified: 2604 fcurves, zero difference). The "grounded vs floating" semantics from the original game lived in UE blueprints/Montage metadata that don't travel to `.psa`. We replicate the landing via Animator blend (technique equivalent to UE's Montage "Blend Out duration"). Pattern consolidated in the `vivify-animations` skill.

5. **Aline's hair** — **done 2026-05-03 (Phases 1 + 2)**.

   Asset in `Sandfall/Content/Characters/Hair/Mirror_Family/Aline/` (NOT in `Bun_Hairstyle/`). PSK + 4 textures + Skeleton + AnimBlueprint + 3 MaterialInstances. **Zero `.psa` for the hair** — Sandfall simulated it at runtime with AnimBlueprint (UE graph with physical constraints over the strand bones), not portable to Vivify.

   **Final operational pipeline:**
   - PSK + textures exported via `mcp__fmodel__*`.
   - PSK → **rigged** FBX via `scripts/blender/pskx_to_fbx.py` (preserves armature + skin weights). Output to `Sandfall/.../Aline/Aline_curator_hair_skl.fbx` + manual copy to `VivifyTemplate/Assets/Aline/Hair/`.
   - The FBX includes 163 bones (`Root` → 19 top-level `Strand_X_1` → chains down to `Strand_X_Y_Z`), 32K verts, SkinnedMeshRenderer.
   - `Aline/Hair` shader (unlit cutout cards: `_MainTex` Color + separate `_AlphaMap` mask + `_Brightness` + very low `_AlphaCutoff=0.08` to preserve fine strands).
   - `M_Aline_Hair` material with `T_Hair_Aline_Color` + `T_Hair_Aline_Mask`, brightness 1.0.
   - Instanced as a child of the prefab's `head` bone. Path: `SK_Curator_Aline/root/pelvis/spine_*/.../neck_02/head/Aline_curator_hair_skl`.
   - **Critical scale fix:** `localScale = (100, 100, 100)` to compensate for the 0.01 chain scale of Aline's rig.
   - Final pose: `localPosition=(0,0,0) localRotation=identity` — the natural bind pose of Sandfall's rig positions the hair "wind-blown / ethereal" upwards+backwards, fitting the character's E33 look without touching anything.
   - Dedicated Animator on the top GameObject with `HairSway.anim`: 19 top-level bones × 4 quaternion curves (`m_LocalRotation.x/y/z/w`) composed around each bone's bind pose. Sway `±6° X / ±4° Z` with phase shift `i × 2π/19` so the strands don't move in sync. 2.5s loop at 30fps. Sub-bones follow by hierarchy → natural motion without animating them.

   **Why bones (original rig) and NOT DynamicBone:** Vivify bundles do script stripping → custom MonoBehaviour doesn't execute in BS. DynamicBone/SpringBones/Magica Cloth would simulate in Unity Editor but stay inert in BS. Animating bones via pre-baked AnimationClip is the only viable route. Detail in [`vivify-materials → Custom MonoBehaviour does NOT survive stripping`](../.claude/skills/vivify-materials/SKILL.md).

   **Performance:** 32K verts skinned + 163 bones + 19×4 curve evals per frame. Plenty in BS PC; ~0.3-0.5ms extra for Aline in Quest. Wide margin.

   **Gotchas resolved along the way:**
   - If you scale armature + mesh separately in Blender and apply, the deformation compounds with the bind pose and ends up 100× smaller. Solution: **delegate the scale to the FBX exporter** via `global_scale=0.01 + apply_scale_options='FBX_SCALE_ALL'` when there's an armature. Pre-scale in Blender only for static mesh. Detail in the docstring of [`scripts/blender/pskx_to_fbx.py`](../scripts/blender/pskx_to_fbx.py).
   - Re-importing the FBX resets the SMR's material to the default `MI_Hair_NPCs_Aline_Curator/Standard`. Reassign `M_Aline_Hair` post-import.
   - `localScale=100` is preserved after re-import; pose `(0,0,0)` too.
   - The hair's bind pose comes rotated +X 270° from the Blender→Unity FBX axis flip, but it's absorbed in the intermediate child `Aline_curator_hair_skl/Aline_curator_hair_skl`. Don't touch.

6. **Aline materials (BlackPart fresnel + CuratorFace)** — **done 2026-05-03**. Five slots audited against `SK_Curator_Aline.uasset` + override in `BP_Cine_Curator_Aline`:
   - Slot 0 `Curator_Black_Body` → `M_Aline_BlackBody` with new `Aline/Fresnel` shader (cutout fresnel; `Curator_Black_Body_Normal` normal map; BlackPart1 MI params: Alpha 0.35, Fresnel 0.5, FresnelR 2). Tuned to `_Alpha=1.0, _FresnelExponent=3.0, _RimBoost=1.5, _AlphaCutoff=0.5` so the rim only appears in silhouette (the "burnt skin" patches integrate without looking like an overlay).
   - Slot 1/2 `Curator_Body_001 / Curator_Body` → `M_Aline_Body_2 / M_Aline_Body_1` with new `Aline/BodyLit` shader (BaseColor + Normal + AO + fake-light direction). Tuned to `_LightStrength=0.45, _Ambient=0.55, _BumpScale=1.5, _OcclusionStrength=0`. **Finding:** the "ORM" (`OcclusionRoughnessMetallic`) that FModel ripped is **NOT a standard packed ORM** — it's a multichannel pseudocolor texture (orange/green/magenta) that probably encodes paint masks or other effects, not AO/Roughness/Metallic. AO disabled. Normal map does provide relief on the cracks.
   - Slot 3 `Curator_Dress` → `M_Aline_Dress` with new `Aline/EnergyMask` shader (translucent blend, no clip — smooth alpha gradient; uses `Curator_Dress_Normal` + `Curator_Dress_Opacity`). Tuned to `_Alpha=0.85, _FresnelExponent=1.5, _RimBoost=1.0` for an "energy dress / wispy" look. `Cull Off` may cause overdraw; consider `Cull Back` if it bothers.
   - Slot 4 `Curator_Aline_Hole` → `M_Aline_Face` with new `Aline/Face` shader (translucent + radial fade approximating UE's M_CuratorFace). Also implements UV transform (`_UVScale`, `_UVOffset`, `_UVAngleDeg`) to support `Mask_Curator_Aline` mask-driven, but the current version uses **radial only** (`_Radius=0.40, _Hardness=0.2`) for simplicity and control. The mask stays as opt-in for future iterations (more faithful but less predictable).

   **Important finding:** the SK directly references the parent `M_CuratorFace` (raw UMaterial), not the `MI_CuratorFace_Aline` MI. The correct override lives in `BP_Cine_Curator_Aline.OverrideMaterials[4]`. Recipe for "tracing SK + BP that uses it" consolidated in the `vivify-materials` skill.

   **New workflow confirmed:** iterate shaders/materials via Scene view screenshot instead of Vivify Build + relaunch BS. Saves ~1min per iteration. Recipe + gotcha for the Toggle keyword not syncing via API in [`unity-rebuild → Iterating materials/shaders without round-trip to BS`](../.claude/skills/unity-rebuild/SKILL.md).

7. **Cosmetic intro** — pending. Aline flying in + getting in position + light fade-in. Cosmetic non-playable, provides narrative context and hides technical setup (instancing, skybox fade, etc.). Implementation: AnimateTrack on the prefab's track + Animator trigger (`Hover` or equivalent from the catalog).

**Deferred to post-Phase-1:**
- **Palettes (`palette.pskx`, `palette1.pskx`)** that Aline holds. Validate first whether BS's fixed camera even sees them before investing in the rip.

When done, move this block and the equivalent "Deferred post-tournament" entry below.

### 4. Prototype of each family in sandbox

A working instance of each family in a sandbox map/difficulty before touching the real map. Success criterion per prototype: animation + VFX + parry + cleanup, instanceable twice without residual state. Snapshot per prototype (`-Label "proto-fam-X"`).

**Suggested order:**
1. **A with `Skill4`** (small projectiles after spin, phase 1) — **core mechanic validated 2026-05-04, in polish phase**. `NormalStandard.dat` has the implementation: trigger `Skill4` at b=4, 7 spheres in a semicircle `(0, 3, 8)` radius 3m with staggered spawns (b=10.67→18.67), 7 native BS cubes with `definitePosition` (sphere → player), spawn animation with scale-pop + 1 CW shape turn easeOutQuad, dissolve trick to hide the "first trip". Parameterizable recipe in [`.claude/skills/vivify-mapping/family-a-recipe.md`](../.claude/skills/vivify-mapping/family-a-recipe.md): implementing each new family A attack is just "fill in inputs" (trigger, beats, positions) and apply templates.

   **Polish — concrete order and plan:**

   **a) Cube visual swap via `AssignObjectPrefab`** — **done 2026-05-04**.

   - Mesh: `Default Base.fbx` from [legoandmars/CustomNotesUnityProject](https://github.com/legoandmars/CustomNotesUnityProject) → copied as `Assets/Aline/Prefabs/projectiles/NoteCube.fbx` (1536v / 3068t, no UVs, normals + tangents OK, bounds 0.011 → compensated with `localScale=45` on the prefab).
   - [`Aline/Outline`](../VivifyTemplate/Assets/Aline/Shaders/AlineOutline.shader) shader — inverted-hull adapted from Ronja (CC-BY 4.0), 2 opaque passes, outline offset in world space, GPU instancing on pass 2 so Vivify can pass `_Color` per-instance (saber color: red if `c=0`, blue if `c=1`). SPI macros in both passes. No `_MainTex` (the mesh has no UVs). Recipe consolidated in [`vivify-materials`](../.claude/skills/vivify-materials/SKILL.md) skill, "Outline shader (inverted-hull with per-instance saber color)" section.
   - `M_NoteOutline` material with `_BodyColor=(0.005, 0.005, 0.025, 1)` (very deep almost-black blue), `_OutlineIntensity=2.0` (HDR so BS's bloom punches), `_OutlineThickness=0.02` (2cm world). GPU instancing enabled.
   - `NoteCube.prefab` with root + MeshRenderer on the same GO. `localScale=(45, 45, 45)`. Assigned to `aline_bundle`.
   - `AssignObjectPrefab` event in `NormalStandard.dat` (`b=0`, `loadMode=Single`, the 7 skill4 tracks, `anyDirectionAsset` because the notes are `d=8`).

   **Major gotcha discovered along the way (Heck per-note animation timing):** the Heck doc says that `customData.animation` per-note is relative to the object's **individual lifetime**, where `t=0` = post-landing (NJS jump-in ends), `t=0.5` = hit time, `t=1` = despawn. **During the NJS jump-in, objects strictly use the first point of each curve.** That means:
   - `scale` curve original `[[0.1,0.1,0.1, 0.5], [1,1,1, 0.515], [1,1,1, 1]]` with first point `(0.1, 0.1, 0.1)` kept the notes visible as **small dots** during the whole NJS travel from far Z.
   - Change to `[[0,0,0,0], [0,0,0,0.499], [1,1,1,0.515], [1,1,1,1]]` leaves the first point at `(0,0,0)` → cubes invisible during the jump-in. The pop at `t=0.5` still matches sphere spawn (`b=hit_beat`) and rotation (`t=0.5..0.52`), everything synced.
   - The `dissolve` curve in Heck convention (`0=transparent, 1=opaque`) Vivify maps internally to `_Cutout` per-instance, but **the `_Cutout` that Vivify passes seems to be driven by player proximity, not by the dissolve curve**: if the shader reads it with `clip(cutout - 0.5)`, it hides the notes right as they fire at the player. That's why the shader **declares `_Cutout` per-instance but does NOT use it for active discard** (kept as a hook for parry / debris fade).

   **Resolved along the way:** `dissolveArrow` desync (the `DisappearingArrowControllerBase` limitation documented in family-a-recipe). The custom cube has no vanilla arrow geometry → the vanilla controller has nothing to touch → no race condition.

   **Dot indicator added to the prefab:** child GameObject with the `Dot` mesh from CustomNotes' `Default Arrows.fbx` (`NoteArrows.fbx` in the repo) and [`Aline/DotOverlay`](../VivifyTemplate/Assets/Aline/Shaders/AlineDotOverlay.shader) shader (solid HDR color + `ZTest Always` + `ZWrite Off`). Positioned at `localPosition=(0,0,0)` (cube center) with `localRotation=Euler(90,0,0)` to align the mesh's XY plane with the visible face. ZTest Always makes the dot pass through body+outline and always appear centered to the silhouette from any face-to-player rotation.

   **Directional (future):** infrastructure already in place — `NoteArrows.fbx` also brings the `Arrow` mesh. For `d=0..7` create an analogous `NoteCubeDir.prefab` with an Arrow child pointing local +Y (BS rotates the prefab according to `d`); apply via `AssignObjectPrefab.colorNotes.asset` (instead of `anyDirectionAsset`) on the directional tracks. Probably the same `Euler(90,0,0)` rotation for the child.

   Operational detail + new event template in the [`vivify-mapping/family-a-recipe.md`](../.claude/skills/vivify-mapping/family-a-recipe.md) skill. DotOverlay shader pattern in [`vivify-materials → Dot/Arrow indicator overlay shader`](../.claude/skills/vivify-materials/SKILL.md). Consolidated decision in [DECISIONES.md → "Cube swap via AssignObjectPrefab + inverted-hull outline shader"](DECISIONES.md).

   **b) Particles for sphere telegraph + cube smoke envelope/trail** — **done 2026-05-05** (b1 + b2 unified; the original plan had a separate Trail Renderer but in the end a child ParticleSystem solved both roles + the "telegraph" one better).

   **Final design (3 coordinated ParticleSystems, all `Aline/ParticleSmoke` shader):**

   - **`SphereBurst.prefab`** (1 ParticleSystem, World sim): instanced at `spawn_beat[i]` of each sphere. Visually replaces the warning telegraph spheres — dark smoke burst (14 puffs, lifetime 1.5-2.2s, auto-destroy via `stopAction=Destroy`). `M_Smoke` material with `_CoreOpacity=0.45` (diffuse/subtle smoke, doesn't dominate the scene). The .dat telegraph spheres (`InstantiatePrefab` + `DestroyObject` for `skill4_sphere_*`) were REMOVED — the burst is now the entire visual telegraph.
   - **`NoteCube.prefab → SmokeEnvelope` child** (Local sim): contained envelope stuck to the cube for its whole lifetime. `simulationSpace=Local` → particles attached to cube transform; `scalingMode=Hierarchy` + `localScale=(1/45, 1/45, 1/45)` → inherits the `lossyScale=0` from the cube root during NJS jump-in → automatically invisible until the `scale-pop`. Rate 15/s, lifetime 0.6-1.0s, startSize 0.8-1.2, alpha peak 0.95.
   - **`NoteCube.prefab → SmokeTrailWorld` child** (World sim): tail left behind when the cube fires. Same scaling technique for invisibility during jump-in. Rate 30/s (high density so the tail reads continuous at high speeds, not as "pellets"), lifetime 0.7-1.0s, alpha peak 0.85 from t=0 (no fade-in, avoids a visible gap between cube and tail).

   **New recipes / shaders consolidated in skills:**
   - [`vivify-materials → Particle shaders in Vivify bundles`](../.claude/skills/vivify-materials/SKILL.md): required vertex inputs (POSITION + COLOR + TEXCOORD0; POSITION-only shaders for static mesh do NOT work for billboard particles), additive HDR vs alpha-blend, simulationSpace=Local vs World, scalingMode=Hierarchy+localScale=1/parent_scale trick, alpha curves without fade-in for trails.
   - [`vivify-mapping/family-a-recipe.md → Conceptual model + Cube swap`](../.claude/skills/vivify-mapping/family-a-recipe.md): "telegraph + cube" architecture updated to the 3 ParticleSystems model; event templates (`InstantiatePrefab(SphereBurst)` replaces sphere+destroy).

   **Pending validation (non-blocking):**
   - VR test (the feel of contained smoke + tail in headset may read differently than on flatscreen).
   - Higher cube speed (`travel_beats` < 2): hypothesis is that the 30/s trail rate already covers it, but confirm empirically when we get to polish (d).
   - "Blur / haze" at spawn beat (a one-shot large additive quad) deferred to iteration 2 if the telegraph feels weak without it.

   **c) Hit particle** — visual finetune when the saber cuts the cube. Deferred until (a) and (b) are validated.

   **d) Tune `travel_beats`** — currently 2 beats (1.2s). Probably drop to 1-1.5 for more intensity when combat is real.

   **e) Remove `uninteractable: true`** and configure `c` (color, alternating 0/1 per flow) and `d` (cut direction, per approach angle of each cube) for scorable parry.

   **Pending cleanup**: `d:/vivify_repo/ShaderTutorials/` was left as an empty dir with corrupted `.git` after a failed clone (zombie process holding a lock). The shader we need is already downloaded in `_outline-shader-ref/`. Delete manually when the process releases the lock (reboot fixes).
2. **A with `Skill3`** (3 giant rocks, phase 1) — variant of Skill4 (same hold-then-launch pattern, N=3, lower NJS, big scale).
3. **B with `DashIn-Idle1`** (standard melee, phase 1) — validates the three-beat choreography (DashIn + hit + DashOut). Separate case (Aline moves, no projectile).
4. **F with `Skill2_Start/Loop/End`** (charge + explosion, phase 1) — validates multi-stage trigger sequence and long timing.
5. **E with `Skill1`** (multi-hit chain, phase 1) — validates a chain of N parries synced with N hits embedded in the clip.
6. **D standalone** (shrinking indicator, no source anim) — validates that the Unity-built indicator conveys the E33 feel.
7. **B + modifier C with `Skill5`** — validates family + modifier composition (Blit + SetMaterialProperty).

**Once 2-3 families are implemented:** consolidate the pattern into a helper function that parameterizes (N, positions, NJS, scale, prefab) — avoid copy-paste per family.

### 5. Definitive song

Once the 4 contracts are proven. Decide a concrete piece from the E33 OST with the criteria: enough duration for 5 phases, atmosphere coherent with the showcase. Import the `.ogg` into `beatsaber-map/`, adjust BPM and duration. Note in `DECISIONES.md`.

### 6. Narrative wiring of the state machine

Depends on the family catalog (step 1) and trigger identification (step 2). Define which family (and which `Skill_X` from the Animator) fires each phase of the boss fight. Compose the map's timeline by instancing skill templates, not writing events by hand each time. Snapshot the map before a big block of events.

### 7. ReMapper setup

Bring up Deno + first script in `ReMapper-master/`. Likely but not mandatory: if the composition benefits from scripting family instancing, ReMapper is the place. Output target: directly to `beatsaber-map/ExpertPlusStandard.dat` or intermediate staging. Fill in the `remapper-scripting` skill during this step.

### 8. Narrative design and polish

Translate the phase structure of [PRODUCTO.md](PRODUCTO.md) into a concrete attack sequence. Readability iteration with external feedback (VR + third-party eyes).

---

## Side-projects

### Minimal port of unity-mcp to Unity 2019.4 — DONE

Working fork in `d:\vivify_repo\unity-mcp/` (`luisep92/unity_vivify_mcp`), wired to the Aline project. Pending: once it has a few sessions under its belt, evaluate a PR to upstream `CoplayDev/unity-mcp`. The commits are organized with one conceptual change each and English messages, intended for clean cherry-pick. Detail in [unity-mcp/README.md](../../unity-mcp/README.md).

---

## Open design decisions

Narrative beats identified but pending decision, before wiring the state machine (step 5):

- **Phase 2 climax — `Skill8` with giant Aline.** The user identifies it as "the attack that would be really impressive to land". The animation as-is depends on a second Aline (giant, in the background) shooting energy balls, plus a series of her own hits. Three options to evaluate: (a) **FModel rip** of the giant Aline model + second prefab + separate animator — big scope; (b) **trim `Skill8`** down to just the hit series and accept that phase 2's spectacle comes from elsewhere; (c) **replace the context** with something different that sustains the moment without the giant. Dedicated conversation before prototyping phase 2.
- **`Skill9` absent.** Trigger declared in the Animator but **with no imported clip**. User suspicion: it was the giant Aline's attack in E33. If the climax (previous decision) goes with option (a), `Skill9` is a candidate to extract from the dump (`Sandfall/`) via FModel and bring into the FBX. If it goes with (b)/(c), `Skill9` is dropped.
- **`Skill11` absent.** Gap in Animator numbering, no clue what it was. Not a priority.

## Deferred post-tournament

Cleanup for once the map is shipped:

- **Rename `my_vivify_template/` → `aline-boss-fight/`**. Procedure: close VSCode, `cd d:\vivify_repo && ren my_vivify_template aline-boss-fight`, reopen VSCode. Junctions and `.git` travel with the folder.
- **Translate docs/skills to English** if at some point the repo gets published to the Vivify community (international).
- **Change `origin/main`** from the upstream template (`Swifter1243/VivifyTemplate`) to our own remote when set up on GitHub.
- **Upgrade unlit → lit/PBR for Aline**. Normal/ORM/Emissive already described in `MI_Curator_Aline_*.json` from the dump. Implies copying additional PNGs, extending `Aline/Standard` (or creating `Aline/Lit`), deciding on a lighting model. (The black slots and palettes are bumped up to step 3 of the active order.)
