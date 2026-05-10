---
name: vivify-environment
description: Use when modifying the visual environment of the Vivify map — skybox, ambient lighting, disabling the BS environment, instantiating custom scenery prefabs, fog, post-processing. Trigger when user mentions 'skybox', 'custom environment', 'hide Timbaland', 'ambient', 'fog', 'background', or sees errors like '[Vivify/SetRenderingSettings] Setting [skybox]' that didn't render visually.
---

# Vivify Environment

Visual setup of the environment where Aline fights: skybox, map environment, ambient lighting, custom scenery. Separate from `vivify-mapping` (which covers general map events) and from `vivify-materials` (which covers character shaders/materials).

## Custom skybox

### Recipe

1. **Equirect 2:1 texture** (typical: 4096×2048). If the source is 1:1 (some UE packs), it's not equirect — you need a different approach (backdrop quad or cubemap, not Skybox/Panoramic).
2. **Unity importer**: `wrapMode = Repeat`, `filterMode = Bilinear`, `anisoLevel = 9`, `mipmapEnabled = true`, `maxTextureSize = 4096`.
3. **Material** with shader `Skybox/Panoramic`:
   - `_MainTex` = the texture
   - `_Mapping` = 1 (Latitude Longitude) + EnableKeyword `_MAPPING_LATITUDE_LONGITUDE_LAYOUT`
   - `_ImageType` = 0 (360 Degrees)
   - `_MirrorOnBack` = 0, `_Layout` = 0
   - `_Tint` = white (1,1,1,1) initially; adjust for warm/cool
   - `_Exposure` = 1.0 initially
   - `_Rotation` = 0 initially; iterate to face the "interesting spot" of the sky toward the player (player looks +Z)
4. **Bundle the material** by assigning `assetBundleName` equal to the main prefab's (e.g.: `aline_bundle`). The texture is dragged in as a dependency automatically — DO NOT tag it separately. After F5, verify the bundle contains both the `.mat` and the texture (`AssetBundle.LoadFromFile(...).GetAllAssetNames()` from the Editor).
5. **Events in `.dat` (V3)** — TWO, not one (see gotcha below):

```json
{
  "b": 0,
  "t": "SetRenderingSettings",
  "d": {
    "renderSettings": {
      "skybox": "assets/aline/materials/m_skybox_e33.mat"
    }
  }
},
{
  "b": 0,
  "t": "SetCameraProperty",
  "d": {
    "properties": { "clearFlags": "Skybox" }
  }
}
```

### Gotcha: SetRenderingSettings.skybox doesn't render on its own

`SetRenderingSettings.skybox` only loads the material into Unity's global `RenderSettings.skybox`. For the camera to actually USE it for clear, it needs `clearFlags = Skybox`. BS cameras by default clear with `SolidColor` or `Depth` (each environment controls this), so without `SetCameraProperty.clearFlags=Skybox` the custom skybox stays invisible. Vivify's log will say `Setting [skybox]` even in the broken case — that's a positive confirming load, not that it's rendering.

### Fast iteration of rotation/tint/exposure

If you need to tune the material many times:
- **Bake into the material + F5** (slow because of F5 every iteration) — for final values.
- **`SetMaterialProperty` event in the .dat** (relaunch BS without F5) — for fast aesthetic iteration. Point at the same material and override `_Rotation`/`_Tint`/`_Exposure`.

### Diagnosis when the skybox doesn't show

| Symptom | Likely cause | Fix |
|---|---|---|
| `Setting [skybox]` in log + still all black | Camera with `clearFlags ≠ Skybox` | Add `SetCameraProperty.clearFlags=Skybox` |
| `Setting [skybox]` in log + skybox blank/magenta | Texture not in bundle (wasn't serialized as a dependency) | Verify with `bundle.GetAllAssetNames()` from the Editor; if missing, force `AssetDatabase.SaveAssets() + Refresh(ForceSynchronousImport)` before F5 |
| Skybox visible but interesting part misoriented | `_Rotation` wrong | Iterate in degrees (0/90/180/270 first, then fine tune) |
| Skybox shows up distorted/stretched | Texture isn't 2:1 equirect (likely 1:1) | Change approach: backdrop quad or get a real equirect |
| Skybox visible but BS environment on top of it | Expected while Timbaland is active | Follow the "Disable BS environment" subsection |

## Disable BS environment

Even if you change `_environmentName` to `DefaultEnvironment` (the one that adds least noise, see `DECISIONES.md`), its geometry and lights still render over your custom scenery. To turn it off, Chroma commands in the `.dat`'s `customData.environment[]`.

### Recipe (DefaultEnvironment, V3)

```json
"customData": {
  "environment": [
    { "id": "Environment|GameCore", "lookupMethod": "Regex", "position": [0, -69420, 0] },
    { "id": "DustPS",      "lookupMethod": "Contains", "active": false },
    { "id": "PlayersPlace", "lookupMethod": "Contains", "active": false }
  ]
}
```

Three commands, not one:
1. **Yeet `Environment|GameCore`** to -69420 — moves all the geometry/lights out of the frustum.
2. **Disable `DustPS`** — particles don't move with `position` (particle system with its own local coordinates), they need `active: false`.
3. **Disable `PlayersPlace`** — the tile under the player's feet. If you want them standing on your own floor, get rid of it.

### Why yeet (-69420) instead of `active: false`

Some environment GameObjects have game scripts that **reactivate** them (`OnEnable` of managers, scene-load callbacks). A yeeted GameObject is invisible to the game: no script checks "I'm far, I'll come back". More robust than `active: false` for the base geometry. The trade is minimal CPU (animators/particles ticking in limbo) — irrelevant for a single song. For particles, using `active: false` is OK (they don't usually reactivate and are cheap to kill).

Pattern derived from `vivify_examples/43a24 (End Times - Chaimzy)` — DefaultEnvironment + Vivify, published and playable map.

### Diagnosis when the environment is still visible

| Symptom | Likely cause | Fix |
|---|---|---|
| Changes to `environment[]` do nothing, no error | The array is outside `customData` or the keys are misspelled | Make sure the path is `customData.environment[]` with `id`/`lookupMethod`/`active` |
| Some GameObjects disappear but others don't | The regex doesn't capture all of them | Broaden the regex; log with `PrintEnvironmentEnhancementDebug: true` in `Chroma.json` |
| Env disappears locally but some players see it weird | They have a global environment override (BillieEnvironment, etc.) | Force it with Settings Setter `_environments._overrideEnvironments: false` |
| Geometry disabled with `active:false` reactivates itself | A game script reactivates it | Yeet with `position: [0,-69420,0]` instead of `active: false` |

## Settings Setter

Covered in the [`vivify-mapping`](../vivify-mapping/SKILL.md) skill, section "Settings Setter". Lives in `Info.dat._difficultyBeatmaps[]._customData` (V2 schema because it's Info.dat). Disables the vanilla HUD, forces Dynamic NJS, etc.

## Ambient lighting

When needed (Phase 2+), `SetRenderingSettings` event with `ambientMode` / `ambientLight` / `ambientSkyColor` / `ambientEquatorColor` / `ambientGroundColor`. For a custom shader inside the Vivify bundle to react to ambient, use `unity_AmbientSky/Equator/Ground` directly, NOT `ShadeSH9` — detail in [`vivify-materials`](../vivify-materials/SKILL.md) section "Ambient in Vivify bundles".

## Instantiating custom scenery

Pattern: `InstantiatePrefab` at beat 0, prefab with mesh + own material bundled into `aline_bundle`. For a "platform" where Aline fights without conflicting with the natural geometry of the rip, **the approach that proved to work is to build the mesh ad-hoc in Blender** instead of ripping from E33.

### Why a custom mesh instead of a direct rip

Tested in the 2026-05-02 session:
1. Ripping `SM_Rock_A_CliffEdge` from the game gave us an elongated stone with naturally irregular surface. Result: Aline floats over the depressions / gets buried in the peaks. **Impossible to align feet to the ground at millimeter precision because the "ground" is a non-constant function of XZ.**
2. We iterated position/scale/rotation by eye (~6 iterations), got to "almost right" but never exact.
3. Switch to custom mesh: flat oval built in Blender with controlled bumps, **pivot exactly at the TOP-CENTER**. Deterministic placement in ONE pass. Zero blind iterations.

Trade-off: you lose the "authenticity" of the E33 asset, but the texture is still from the game (`Albedo_2K_vlzkba1fw.png` from Megascans/Surfaces/Jagged_Rock — the game uses it in its rocks). Visually it reads as "E33 rock". For Phase 1 with a deadline this is the right call.

### Custom mesh recipe (consolidated version)

Reusable script: `scripts/blender/build_rock_platform.py`. Idempotent (cleans up any previous `RockPlatform*`, builds, exports FBX to `Assets/Aline/Scenery/Meshes/`). To regenerate after tuning parameters: paste the script into blender-mcp `execute_blender_code` or run it as `__main__`.

Builder structure:
1. **Cylinder primitive with `end_fill_type='TRIFAN'`** (not NGON). With NGON the top cap is a single polygon with no interior vertices → the central corridor ends up without displaceable geometry and the face becomes non-planar after displace. TRIFAN gives center-vert + triangles → subdivide propagates inward.
2. Global subdivide → then subdivide top-only to concentrate density at the top.
3. **Translate vertices `-THICKNESS/2`** so the top sits at `z=0` local (`primitive_cylinder_add(location=...)` sets object location, not mesh-local origin — the mesh is always built centered).
4. **Perimeter silhouette** via `mathutils.noise.noise(cos(θ), sin(θ))` — the circular input makes the function continuous without discontinuity at θ=±π. Random per-bin produces "sun spike" zigzag (tested and discarded).
5. **Flat corridor** rectangle with radial falloff. Verts inside the rectangle are skipped; verts outside receive `displace * blend(distance / FALLOFF)`. Wide FALLOFF (~2m) avoids "bumps at Aline's feet".
6. UVs: `bpy.ops.uv.smart_project(angle_limit=66)`. NOT planar projection (planar = the radial rays of the original bug).
7. Smooth shading per-polygon (`p.use_smooth = True`).
8. **Mirror on Y at the end** (`v.co.y = -v.co.y` + `bmesh.ops.reverse_faces`). Needed because the combo `bake_space_transform=True + axis_forward='-Z'` maps Blender +Y to Unity -Z (player's back). Negating Y before export guarantees the corridor lands on Unity +Z (toward the boss). See "FBX axis flip" gotcha below.
9. Export FBX: `axis_forward="-Z"`, `axis_up="Y"`, `bake_space_transform=True`, `apply_scale_options="FBX_SCALE_NONE"`.

### Ground decoration (petal/leaf carpet) — prefer pre-built mesh over tile-shader

To cover the ground with vegetation in a "petal carpet" style (see E33 photo: dense leaf coverage on the rock), we evaluated four approaches in order of discovery:

1. **Scatter of N small discrete clusters** (mesh `SM_DeadLeaves_Petals_new` x22 instances). Result: dotty, sparse, doesn't reach "carpet" but rather "sparse dots". Discarded.
2. **Single merged mesh + dense cluster scatter** (~80 clusters). Improves density but still reads as discrete instead of continuous. Discarded.
3. **Duplicate of the rock top + atlas-tile via shader** (`build_petal_carpet` + `_AtlasRegion` cropping). Continuous coverage YES, but the tiling clearly shows the atlas pattern every 25cm — "you can see the whole atlas repeated". Discarded.
4. **Pre-built "scattered carpet" mesh from a marketplace pack** (Real_Ivy_Pack/SM_ivy_floor_plane_dense). 5 rotated instances + scale variation + aggressive Z squash (0.15) to flatten plants into petals. **Works.**

**Consolidated lesson**: for ground decoration in VR/BS, **mesh asset choice > shader gymnastics**. A pre-built asset pack designed for scatter already has the organic distribution baked-in (UVs point to the atlas correctly, no visible tile pattern). Tiling an atlas via shader always shows the pattern at any tiling-rate. Before sinking time into complex shader-tile, scout FModel for `SM_*floor_plane*`, `SM_*ground_*`, `SM_*carpet*` or equivalents.

**Final consolidated architecture (Phase 1):**

`RockPlatform.fbx` with ONE mesh and THREE submeshes/material slots:

1. **Layer 0 — Rock**: procedural platform mesh (`build()`). Material `M_Rock_Cliff` with shader `Aline/Standard` (no LUMINANCE_TINT, opaque).
2. **Layer 1 — Ivy carpet**: scatter of N rotated+Z-squashed copies of the pre-built mesh `SM_ivy_floor_plane_dense_spread_*` (`build_ivy_scatter()`). Material `M_BlueIvy` with `LUMINANCE_TINT` cool blue overbright. Covers the ground with a "continuous petal coverage" look without a visible pattern.
3. **Layer 2 — 3D bush scatter**: deterministic random scatter of N copies of the small mesh `SM_ground_foliage_03_*` (`build_bush_scatter()`). Material `M_PinkBush` with `LUMINANCE_TINT` pink-magenta overbright. Adds contrasting color touches + small 3D protrusions poking out above the ivy. Restricted to `y >= BUSH_Y_MIN` Blender pre-mirror = only in front of the player (BS's fixed camera doesn't justify geometry behind).

Result: 1 mesh upload, 3 draw calls (one per material), ~217K tris total for the entire decorated scenery.

**Final carpet scatter pipeline (technical reference):**
1. Scatter N rotated copies (random yaw) of the template mesh, explicit asymmetric positions (focus on the front of the player, minimum behind — fixed camera doesn't see back)
2. **Decimate the template** (not the copies) BEFORE duplicating — savings multiply by N. Ratio 0.5 visually indistinguishable at BS distance
3. Non-uniform scale `(s, s, s * HEIGHT_SCALE)` with HEIGHT_SCALE ~0.15 — flattens verticality of meshes that are "plants growing" into "petals lying down". Without this the leaves read as vertical grass blades
4. Join into one mesh with `material_index=1`, attached to the rock as a submesh → 1 mesh, 2 submeshes, 2 draw calls (rock opaque + ivy cutout-alpha)

### Material preview in Blender (iterate without the BS round-trip)

By default the slot placeholders have no shading → the Material Preview viewport looks gray. To iterate visually without re-bundling + launching BS for every change: fill the placeholders with real textures + EEVEE nodes that approximate the Aline/Standard shader.

`build_rock_platform.py:_make_preview_material()` reproduces the 3 modes of the shader:
- Plain texture (rock): texture → emission, no tint, no alpha
- Multiply tint (default): texture × tint_color → emission
- Luminance tint (ivy/petals): texture → RGB→BW (luminance) × tint_color → emission, with Mix Shader + Transparent BSDF based on the texture's alpha, `blend_method='CLIP'`

Switch viewport via `space.shading.type = 'MATERIAL'`. Result: rock with its texture + blue ivy with alpha cutout, almost indistinguishable from the final BS look. Good enough to iterate density/placement/size without touching Unity.

### Gotcha: FBX axis flip Blender → Unity 2019.4

The export combo `axis_forward='-Z' + axis_up='Y' + bake_space_transform=True + use_space_transform=True` in Blender 4.2 LTS produces two non-obvious behaviors when imported into Unity 2019.4:
- **Without `bake_space_transform`**: the mesh shows up as a vertical wall (Blender Y → Unity Y, no axis swap). `Renderer.bounds.extents` shows `(width, length, depth)` with length in Y (up). Visible bug: no floor.
- **With `bake_space_transform=True`**: the mesh ends up horizontally correct (Blender Y → Unity Z), BUT the axis sense is inverted (Blender +Y → Unity -Z). Visible bug: what you wanted in front of the player ends up behind.

Solution without touching export options: negate Y of all verts in Blender + `reverse_faces` to keep normals. Encapsulated in `build_rock_platform.py:build()`. Always validate with `Renderer.bounds.center.z` (must be positive if the content goes forward in Unity).

### Pivots — the key factor

**The trick that makes placement deterministic:** mesh top at z=0 local + pivot at (0,0,0) → when instanced at `position.y = Y_target`, the top is exactly at world Y = Y_target.

To align Aline's feet on top of the plate: you need to know where Aline's feet are. Measure it in Unity:
1. `GameObject.Instantiate` Aline.prefab at (0,0,0) with scale 0.01 and identity rotation
2. Read `SkinnedMeshRenderer.bounds.min.y` — that's the distance (negative) from the pivot to the feet in world space
3. The formula: `feet_world_Y = position.y + bounds.min.y`

For Aline (verified): `bounds.min.y = -0.43m` with scale 0.01 → feet at `position.y - 0.43`.

If Aline is at `position.y=1`, her feet are at `world Y = 0.57`. Plate at `position.y = 0.57` → top exactly at `world Y = 0.57` → perfect contact.

**Caveat:** the bbox reading is in T-pose (rest pose). If the animation Aline is running displaces her body (idle hover, raised pose), apparent feet can sit higher. In testing 2026-05-02 we had to add +0.4m to the computed position (from 0.57 → 0.97) for the feet to land visually. It's a fine adjustment over the base formula.

### Operational pipeline (summary)

1. Build the mesh in Blender (ad-hoc script or blender-mcp interactive). Output FBX directly to `VivifyTemplate/Assets/Aline/Scenery/Meshes/`
2. Unity: refresh, create a material with shader `Aline/Standard` + texture. Bundle name `aline_bundle` on mesh + material
3. Create a prefab wrapping the FBX with the material assigned on its renderer. `PrefabUtility.SaveAsPrefabAsset`. Bundle name on the prefab too
4. Vivify > Build > Build Working Version Uncompressed (F5)
5. PostBuildSyncCRCs.cs syncs CRC to Info.dat automatically
6. Add `InstantiatePrefab` event in the `.dat` with deterministic position

Total time with script + MCP: ~30-45 min from "Blender mesh" to seeing it in BS.

## Convert Unreal `.pskx` → `.fbx` (static mesh)

When you rip a static mesh with FModel you get a `.pskx` (Unreal format). For Unity you need FBX. Script: `scripts/blender/pskx_to_fbx.py`. Run:

```
"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" --background --python scripts\blender\pskx_to_fbx.py -- "<input.pskx>"
```

Generates `<input>.fbx` next to the `.pskx`. Requires the `io_scene_psk_psa` addon (Befzz/DarklightGames) — the same one we use for animation `.psa`s.

## HUD removal

**There is a direct way via Heck Settings Setter** — see section above. `_noTextsAndHuds: true` disables the vanilla HUD (combo, score, multiplier, energy, miss text). The player gets a prompt before loading and accepts. For mods that render their own HUD (Counters+, UITweaks) you have to add their specific settings to the same block.

The only thing you CAN'T control from the map are completely external overlay-mod HUDs (Twitch chat overlay, performance counters, etc.) — those are user configuration.

## References

- Vivify events: [`docs/heckdocs-main/docs/vivify/events.md`](../../../docs/heckdocs-main/docs/vivify/events.md) — sections `SetRenderingSettings`, `SetCameraProperty`, `Blit`, `CreateCamera`, `InstantiatePrefab`.
- Chroma environment commands: [`docs/heckdocs-main/docs/environment/environment.md`](../../../docs/heckdocs-main/docs/environment/environment.md).
- [`vivify-mapping`](../vivify-mapping/SKILL.md) skill for general `.dat` editing and path validation.

## Methodology: locate the real E33 asset (vs marketplace pack)

Sandfall bundles many Unreal Marketplace asset packs (`SkyboxPack`, `Real_Ivy_Pack`, `AdvancedLocomotionV4`, `FabricCollection`, etc.) in their build. Finding "a texture that looks good" doesn't mean it's the real one used by the target scene — the devs bought them as libraries. For fidelity, trace from the LEVEL backwards, not from the assets forward.

**Lookup chain with `mcp__fmodel__*`:**

1. **Identify the target level** — `Sandfall/Content/Levels/<Zone>/<SubLevel>/Level_*.json`. Names are sometimes cryptic (`Monolith_Interior_PaintressGrandFinale_Main` = playable fight, `*_PaintressIntro` = preceding cinematic). If in doubt, grep by character/skill names in `GameActions/`.
2. **Grep within the level** by the type of object you're looking for: skybox → `BP_SkyBox`, `SM_Skybox`, `[Ss]kybox`. Environment mesh → `BP_Monolith`, `SM_Floor`, etc.
3. **Find the actor blueprint and the StaticMeshComponent**. The actor (`BP_*_C`) references the component. The component has `OverrideMaterials` with the real `MI_*`.
4. **Read the `MI_*.json`** with `fmodel_inspect_material` — it lives in `Content/Materials/<Folder>/`. Lists `Parent`, `TextureParameterValues` (concrete texture), `ScalarParameterValues`, `VectorParameterValues`.
5. **The texture** lives at `<Folder>/Textures/...`; export with `fmodel_export_texture`.

**Levels vs marketplace packs:**
- Marketplace: `SkyboxPack*`, `*Collection*`, `Advanced*`, `Procedural*` — purchased libraries. The textures may be referenced from the game's real MIs, but the actual MI and the composed shader always live in `Content/Materials/`.
- Sandfall-internal: `Content/Materials/`, `Content/Characters/Enemies/<Boss>/`, `Content/Levels/`, `Content/Effect/`. This is where the MIs and the real decisions live.

**Filesystem gotcha:** FModel sometimes shows folders with different casing (`Skies` and `SKIES` at the same level). Windows collapses case and when exporting both into `Output/` one overwrites the other. If the result seems short, check for case-different siblings that weren't exported.

**Efficient workflow (reduces ping-pong with FModel):**
1. `fmodel_export_raw` on relevant top-level folders — kilobytes, contain metadata without heavy textures.
2. Grep + Read the exported JSON to find the target asset.
3. Only then `fmodel_export_texture`/`fmodel_export_mesh` for the specific binaries.
