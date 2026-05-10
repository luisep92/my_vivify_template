---
name: vivify-materials
description: Use when creating or modifying materials/shaders for prefabs that ship in a Vivify bundle (characters, props, environments). Trigger when user mentions 'create material', 'assign material', 'Vivify shader', 'texture', 'apply textures', 'magenta in BS', 'missing material', or after importing a model from FModel that needs materials. Covers the unlit cutout recipe, FModel JSON-to-Unity material mapping, and common errors.
---

# Vivify Materials Workflow

How to build materials for prefabs that live inside a Vivify bundle. Unity's default shaders (Standard, URP) don't compile in Vivify bundles (Built-in render pipeline + restrictions). You have to go with a custom shader + project-local materials.

## Default recipe: unlit cutout, double-sided

For a 3D character that shows up in a BS scene (typical case: boss, NPC, animated prop), the recommended default shader is **unlit with cutout and `Cull Off`**. Reasons:

1. **BS doesn't light Vivify bundles by default**. If the shader is lit, the model looks gray/dark or requires lights baked into the prefab — and the directional light always leaves the opposite face dark.
2. **Textures exported from Unreal with FModel** typically have BlendMode=Masked + TwoSided (cutout + double-sided faces). Replicating this in Unity = `Cull Off` + `clip(col.a - cutoff)`.
3. **Unlit is performant** and predictable. No surprises from lighting calculations.

Example: [Assets/Aline/Shaders/AlineStandard.shader](../../../VivifyTemplate/Assets/Aline/Shaders/AlineStandard.shader). Reusable pattern for any character.

```hlsl
Shader "Aline/Standard"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _AlphaCutoff ("Alpha Cutoff", Range(0,1)) = 0
    }
    SubShader
    {
        Tags { "RenderType"="TransparentCutout" "Queue"="AlphaTest" }
        Cull Off
        Pass
        {
            // ... standard vert/frag ...
            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv) * _Color;
                clip(col.a - _AlphaCutoff);
                return col;
            }
        }
    }
}
```

`_MainTex` with default `"white"` + `_Color` lets you reuse the same shader for materials without a texture (e.g., solid black) without needing a separate shader.

## The `Hidden/Vivify/Templates/Standard` template can't be used as-is

[VivifyTemplate/.../Templates/Standard.shader](../../../VivifyTemplate/Assets/VivifyTemplate/Utilities/Shaders/Templates/Standard.shader) is the base recommended by VivifyTemplate, but its name starts with `Hidden/` → it doesn't show up in the Material Inspector dropdown. **You have to duplicate it** to `Assets/<Project>/Shaders/` and rename the shader path to something visible (e.g., `"Aline/Standard"`).

It's also opaque and single-sided by default — when duplicating, add cutout + Cull Off per the recipe above.

## FModel → Unity mapping (textures to FBX material slots)

When you import an FBX exported via FModel→Blender→FBX, the FBX comes with **N material slots named like `MI_<something>` or `M_<something>`**. The source of truth for which texture goes with which slot lives in the original game's `MaterialInstanceConstant` — and as of 2026-05-03 we inspect them via **fmodel-mcp** instead of exporting JSONs and reading them by hand.

### Canonical flow (with fmodel-mcp)

1. **Inventory the FBX slots** — same as before: Unity Inspector → SkinnedMeshRenderer → Materials, or read the `.prefab` (`m_Materials` with guids → map to `.mat.meta`). For meshes not imported yet: the `SkeletalMesh` `.json` gives the order in `SkeletalMaterials`. Example for Aline:
   ```
   mcp__fmodel__fmodel_search ("**/SK_Curator_Aline*")
   mcp__fmodel__fmodel_read   ("Sandfall/Content/.../SK_Curator_Aline")
   ```
   `SkeletalMaterials[i].MaterialSlotName` gives you the order + the default MI path.

2. **Inspect each MaterialInstance** with `mcp__fmodel__fmodel_inspect_material(path)` — returns **only what's actionable**: Textures, Scalars, Vectors, parent material, BlendMode, TwoSided, OpacityMaskClipValue. Much lighter than the raw JSON.

   **Better in parallel** (one message, N tool calls): the inspects are independent and <1s each. For Aline (5 slots) it was a single batch.

3. **Export the referenced textures** with `mcp__fmodel__fmodel_export_texture(path)`. Also parallelizable. They come out as PNGs to `D:\vivify_repo\Output\Exports\<package_path>.png`.

4. **Move the PNGs** from `Output/Exports/...` directly to `VivifyTemplate/Assets/Aline/Textures/` (or wherever it fits). Textures don't need a Blender step or a mirror in `Sandfall/`. What does go through `Sandfall/` are the **meshes** (`.pskx` → Blender → `.fbx`).

5. **Mapping decisions** — convert what's in the MI to the Unity material:
   - `BlendMode: BLEND_Masked` + `OpacityMaskClipValue` → cutout, `_AlphaCutoff` = that value.
   - `TwoSided: true` → `Cull Off`.
   - `BlendMode: BLEND_Translucent` → real alpha blending (more expensive), not cutout.
   - Loose textures like `Normal`, `ORM`, `Opacity_Mask`, `Mask_Face` → plug into shader properties. If the current shader doesn't support them, extend (see "Upgrade path" section).

### When NOT to use fmodel-mcp

- **Pure parent material / UMaterial** (not MI): inspect returns nearly empty because the logic lives in the shader's node graph, not in parameters. There, use `fmodel_export_raw` or accept that the parent defines a shader we'll approximate by hand.
- **Inverse reference lookup** ("which materials use this texture?"): not supported in Tier 1. Workaround: `fmodel_search` by name + `fmodel_inspect_material` on each candidate.

### What the SK asks for ≠ what the game renders

The SK's `SkeletalMaterials[]` is the asset's "default" material, but the Blueprints that spawn that SK can override specific slots via `OverrideMaterials[]`. To port the correct game look it's not enough to read the SK — you have to trace **the BP that actually uses it** (cinematic, gameplay, etc.) and look at its overrides.

Canonical Aline case (2026-05-03):
- `SK_Curator_Aline` slot 4 (`Curator_Aline_Hole`) → parent `M_CuratorFace` (pure UMaterial, no accessible params).
- `BP_Cine_Curator_Aline` → `OverrideMaterials[4] = MI_CuratorFace_Aline` (with Aline-specific `Mask_Curator_Aline`).

If you only read the SK, you assume the parent. If you also read the cinematic BP, you discover that the actual render uses the MI with its own mask. Recipe:

1. `fmodel_search "**/BP_*<Character>*"` to list the BPs that may spawn the character.
2. `fmodel_export_raw` of the candidate BP and grep `"OverrideMaterials"` — nulls inherit from the SK, objects are overrides.
3. Decide based on which BP corresponds to your use (cinematic for visual reference, gameplay BP for dynamic spawn, etc.).

### Limitation: pure UMaterial vs MaterialInstanceConstant

`fmodel_inspect_material` extracts `TextureParameterValues / ScalarParameterValues / VectorParameterValues / Parent / BlendMode`. That lives in MIs (`MaterialInstanceConstant`), not in the parent `UMaterial`. For the parent, inspect returns nearly empty (the logic lives in the shader's node graph and in `CachedExpressionData`, which the current tool doesn't extract).

Workaround: `fmodel_export_raw` of the parent gives you `RuntimeEntries[].ParameterInfoSet` (param names) + `ScalarValues / VectorValues / TextureValues` (defaults). Enough to infer what knobs exist and start porting. A future MCP improvement (Tier 1.5) would be extracting that directly from `inspect`.

## Material creation flow

1. Expected folders (create if missing):
   - `Assets/<Project>/Shaders/` — the duplicated/custom .shader
   - `Assets/<Project>/Materials/` — the .mat files
   - `Assets/<Project>/Textures/` — the PNGs (gitignored, .meta versioned)

2. **Create shader**: duplicate `Hidden/Vivify/Templates/Standard.shader`, rename the shader path, add cutout + Cull Off + any extra properties you need.

3. **Import textures**: use `mcp__fmodel__fmodel_export_texture` and move the PNGs from `Output/Exports/.../*.png` to `Assets/<Project>/Textures/`. Unity imports them when you return to the Editor.

4. **Create .mat**: Right-click → Create → Material in `Materials/`. Inspector → Shader dropdown → your new shader. Assign `_MainTex`, `_Color`, `_AlphaCutoff`.

5. **Assign to prefab**: open the `.prefab`, select the Renderer, drag your .mat files to Element 0..N (in the order you discovered in the "Mapping" step).

6. **Verify in scene**: the model shows up textured in Unity's Scene view, with no "missing material" warnings in console.

7. **Build**: F5. CRC sync is automatic via the Editor watcher (see `unity-rebuild` skill).

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| Aline/character magenta in BS | Shader doesn't compile in the bundle | Check that the shader follows the recipe (Built-in pipeline, not URP/HDRP). Look at Unity console when building. |
| Aline magenta but only from one angle | Missing `Cull Off` | Add `Cull Off` to the SubShader. |
| Face/back dark in BS | Shader is lit and BS doesn't send lights | Migrate to unlit (the default recipe). |
| Hard edges on hair/clothing where alpha cutout should be | `_AlphaCutoff` = 0 or missing `clip()` | `_AlphaCutoff` = 0.333 (or the value from the Unreal JSON's `OpacityMaskClipValue`). |
| Slot mis-assigned (body part with wrong texture) | Element 0..N order doesn't match what you assumed | Verify Material names in the Inspector. Reassign accordingly. |
| `Material has no _MainTex` warning | Material assigned to a shader that doesn't have that property | Switch to the correct shader, or use default `"white"` in the property declaration. |
| Changes to .mat don't show in BS | F5 not done, or CRCs not synced | F5 (auto-sync via Editor watcher handles the rest). If auto-sync is off, run `.\scripts\sync-crcs.ps1`. |

## Upgrade path: unlit → lit/PBR

If at some point you want full PBR (normals, roughness, metallic, emissive):

1. Import the additional textures already in the dump (Normal, ORM, Emissive). The `.json` files already describe which go with each material slot.
2. Build a new shader that samples those textures (typical: `_NormalMap`, `_ORM`, `_Emissive`).
3. Decide the lighting model: simple lambert, full PBR (BRDF), or stylized (cel-shaded, matcap).
4. If there will be lights in the bundle: include them as children of the prefab and design them to light reasonably from multiple angles (not a single directional). Or enable ambient in Unity and configure it so the bundle respects it.

### Practical recipe: "unlit with fake-light + normal" (what we use in Aline body)

Since BS doesn't send lights to Vivify bundles, a "real" lit shader looks flat. Canonical pattern (see [`AlineBodyLit.shader`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineBodyLit.shader)):

```hlsl
// Base sample with cutout (same as AlineStandard)
fixed4 base = tex2D(_MainTex, uv) * _Color;
clip(base.a - _AlphaCutoff);

// Reconstruct normal in world-space from tangent + normal map
float3 worldN = normalize(nTan.x*T + nTan.y*B + nTan.z*N);

// Fake fixed world-space key light (no Light needed in scene)
float3 L = normalize(_LightDir.xyz);
float ndotl = saturate(dot(worldN, L));
float lambert = lerp(_Ambient, 1.0, ndotl);  // _Ambient avoids pure black on shadow side
float shading = lerp(1.0, lambert, _LightStrength);  // _LightStrength=0 → unlit

return fixed4(base.rgb * shading, base.a);
```

**Tunables (reasonable defaults):** `_LightDir=(0.3, 0.7, -0.6)` (key from above-front), `_LightStrength=0.45` (visible but not cartoonish), `_Ambient=0.55` (shadow side ~half intensity), `_BumpScale=1.5` (matches UE Normal/Bump Multiplier).

### Ambient in Vivify bundles — use `unity_AmbientSky/Equator/Ground`, NOT `ShadeSH9`

When a custom shader inside a Vivify bundle wants to react to the ambient state set by `SetRenderingSettings.ambient*`, **do NOT use `ShadeSH9(unity_SHAr/g/b)`**. SH coefficients are 0 in standalone Vivify bundles because they require a precomputed environment probe (`Lighting → Generate Lighting` in Unity Editor) and bundles don't carry that precompute.

**Valid route — direct uniforms:**
```hlsl
float3 sky     = unity_AmbientSky.rgb;       // Sky color (always populated)
float3 equator = unity_AmbientEquator.rgb;   // Only Trilight; in Flat = 0
float3 ground  = unity_AmbientGround.rgb;    // Only Trilight; in Flat = 0
```

Unity populates them per-frame from `RenderSettings.ambientMode/ambientLight/ambientSkyColor/ambientEquatorColor/ambientGroundColor` automatically, without GI baking.

**Pattern for the three modes (Skybox, Trilight, Flat) in a single function:**
```hlsl
float3 SampleAmbient(float3 worldN) {
    float upWeight    = saturate(worldN.y);
    float downWeight  = saturate(-worldN.y);
    float horizWeight = 1.0 - upWeight - downWeight;

    float3 sky     = unity_AmbientSky.rgb;
    float3 equator = unity_AmbientEquator.rgb;
    float3 ground  = unity_AmbientGround.rgb;

    // Flat mode: Equator + Ground come in as 0; reuse Sky to avoid darkening
    // the model's sides/bottom to black.
    float trilightActive = step(0.001, dot(equator + ground, float3(1,1,1)));
    equator = lerp(sky, equator, trilightActive);
    ground  = lerp(sky, ground,  trilightActive);

    return sky*upWeight + equator*horizWeight + ground*downWeight;
}
```

`RenderSettings.ambientIntensity` also affects this — it multiplies the uniforms automatically. No need to multiply it in shader.

**What's NOT in Vivify bundles** (don't waste time):
- `ShadeSH9` / `unity_SHAr/g/b` (env probe SH, requires GI baking).
- `_LightColor0` / `_WorldSpaceLightPos0` (forward base directional light, requires `LightMode="ForwardBase"` and a real light in scene that BS doesn't send).
- `unity_SpecCube0` (skybox reflection probe — maybe works, untested).

### Custom MonoBehaviour does NOT survive bundle stripping

DynamicBone, FinalIK, Magica Cloth, JiggleBones, SpringBones — any paid/free asset that depends on **runtime scripts** is inert in a Vivify bundle. Vivify does aggressive whitelisting: **what survives** is Materials, Shaders (with keyword rewriter), AnimationClips, AnimatorControllers, Meshes, Textures, Prefab hierarchies, Transform animations, MeshRenderer/SkinnedMeshRenderer; **what doesn't survive** is custom scripts (MonoBehaviour), paid assets with runtime code, shaders with compute/tessellation, native plugins, editor scripts.

For physics-on-bones effects (sway, jiggle, secondary motion), the only viable route is a **pre-baked AnimationClip** that moves bones via `m_LocalRotation`/`m_LocalPosition` curves, looped via Animator. That works in a bundle. For deformations that need to react to real-time inputs (collision, wind direction): not feasible in Vivify, defer to "post-Phase-2" or accept as a limitation.

### Outline shader (inverted-hull with per-instance saber color)

To replace the note cube visual via `AssignObjectPrefab` in family A attacks. Adapted from Ronja's "020 Inverted Hull Unlit" tutorial (CC-BY 4.0, attribution in header).

Canonical source: [`Assets/Aline/Shaders/AlineOutline.shader`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineOutline.shader). Validated with `NoteCube.prefab` on 2026-05-04.

**Look shape:** near-black bluish body + neon outline in the saber color (red if the note is `c=0`, blue if `c=1`). The outline appears automatically because Vivify passes `_Color` per-instance to the prefab's shader when `colorNotes.{asset, anyDirectionAsset, debrisAsset}` is used in `AssignObjectPrefab` (heckdocs Vivify events doc).

**Key pattern:**

1. **2 opaque passes.** Pass 1: body (`Cull Back`, solid color `_BodyColor`). Pass 2: outline (`Cull Front`, vertices extruded along the normal, solid color `_Color × _OutlineIntensity`). Both `ZWrite On`.

2. **Outline offset in world space, not object space.** `worldPos += worldNormal * _OutlineThickness` before clip projection. Reason: the typical prefab has `localScale=45` (compensates for the fact that CustomNotes' `Default Base.fbx` mesh comes in at 0.011 raw). In object space, `_OutlineThickness=0.02` becomes ~1m world (absurd). In world space it's in meters directly, predictable slider.

3. **GPU instancing in pass 2 for per-instance `_Color`.** Without this, Vivify can't pass the saber color per note:
   ```hlsl
   #pragma multi_compile_instancing

   UNITY_INSTANCING_BUFFER_START(Props)
       UNITY_DEFINE_INSTANCED_PROP(fixed4, _Color)
   UNITY_INSTANCING_BUFFER_END(Props)

   // In vert: UNITY_TRANSFER_INSTANCE_ID(v, o);
   // In frag: UNITY_SETUP_INSTANCE_ID(i);
   //         fixed4 c = UNITY_ACCESS_INSTANCED_PROP(Props, _Color);
   ```
   And `mat.enableInstancing = true` on the material. Without the flag, Unity doesn't compile the correct variant.

4. **SPI macros in both passes** (BS 1.34.2 = Single Pass Instanced VR). Repo standard: `UNITY_VERTEX_INPUT_INSTANCE_ID` in `appdata`, `UNITY_VERTEX_OUTPUT_STEREO` in `v2f`, `UNITY_SETUP_INSTANCE_ID + UNITY_INITIALIZE_OUTPUT + UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO` in vert.

5. **No `_MainTex`.** CustomNotes' `Default Base.fbx` mesh has no UVs. Body and outline are solid colors, no samplers. Saves complexity and zero texturing cost.

6. **`[HDR] _Color` with `_OutlineIntensity` multiplier.** Default `_OutlineIntensity=2.0`. BS applies internal bloom to rendering — HDR values > 1 make the outline glow instead of looking flat. Drop to 1.5 if it looks washed out, bump to 2.5+ for more punch.

**Mesh source:** `Default Base.fbx` from [legoandmars/CustomNotesUnityProject](https://github.com/legoandmars/CustomNotesUnityProject). The entire project stays out of the repo at `d:/vivify_repo/CustomNotesUnityProject/`. We only use the mesh; we do **NOT** copy `NoteDescriptor` (a CustomNotes mod component that Vivify doesn't consume). The mesh's soft bevel gives the "comic" look, without arrow geometry → solves the `dissolveArrow desync` documented in `family-a-recipe.md`.

**Convert to prefab:** Empty root with `MeshFilter + MeshRenderer` pointing to the FBX's internal `Cube` mesh, material `M_NoteOutline` assigned, `localScale=45` (compensates the 0.011 raw → world ~0.5m, equivalent to the default BS note). Assign to `aline_bundle`.

**Gotcha — Vivify passes `_Cutout` by proximity, not by `animation.dissolve`:**

The heckdocs doc says `AssignObjectPrefab` sets `_Color`, `_Cutout`, `_CutoutTexOffset` per-instance. Vivify template shaders (`CustomBomb`, `CustomNoteArrow`, `CustomNoteBase`) read `_Cutout` with the convention `0=visible, 1=dissolved`.

**But the observed behavior in BS 1.34.2 with Vivify (validated 2026-05-04):** per-instance `_Cutout` does NOT follow the `customData.animation.dissolve` curve. It seems to be driven by note proximity to the player (probably to prepare the cut animation post-hit). Result: if the shader implements `clip(cutout - 0.5)`, notes get hidden **right when they're fired at the player** — undesired behavior for family A attacks where we want to see them during the whole launch.

**Workaround:** declare `_Cutout` per-instance in the instancing buffer (leave it as a hook for future parry / debris fade) but **don't use it for active clip**. The "dissolve trick" of hiding notes during NJS jump-in is done via `customData.animation.scale` with a first point of `(0,0,0)` (Heck uses the first point during jump-in and objects become effectively invisible). Details in `family-a-recipe.md`.

**Not tested in this project** but plausible for future iterations: if we wanted a real dissolve (e.g. fade post-cut), it would be more reliable to control via `AnimateTrack` setting a custom material property per-track, instead of relying on Vivify's automatic `_Cutout`.

### Dot/Arrow indicator overlay shader (`Aline/DotOverlay`)

For flat indicators (dot, arrow) that live on top of the cube face and must be **always visible** over the body+outline, without fighting the z-buffer. Source: [`Assets/Aline/Shaders/AlineDotOverlay.shader`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineDotOverlay.shader).

**Pattern:** solid HDR color + `ZTest Always` + `ZWrite Off` + `Cull Off` + `Queue=Geometry+10`. No clip, no sampler. Standard SPI macros.

```hlsl
Tags { "RenderType"="Opaque" "Queue"="Geometry+10" }
Cull Off
ZTest Always
ZWrite Off
```

`ZTest Always` makes the indicator always pass the depth test → visible even if it's behind the body or at the same depth as the outline (typical case when the indicator child GameObject is near the cube's face). `ZWrite Off` prevents the indicator from polluting the depth buffer for later frames. `Cull Off` lets it be seen from both sides (defensive in case the child rotation ends up flipped).

**Why not `Aline/Standard` for this:** Standard has `Cull Off` and a normal queue (`AlphaTest`), but respects ZTest LEqual which fights the body's outline pass. The indicator ends up at the same depth as the inflated outline geometry (in NoteCube's case, outline thickness 0.02m world covers exactly the distance from the cube face to where the indicator is). The z-fight hides the indicator some frames and not others — constant visual bug.

**Indicator child positioning** (Dot/Arrow):
- `localPosition=(0,0,0)` — center of the cube. ZTest Always makes the indicator appear projected onto the center of the cube's silhouette from any angle, regardless of the cube's face-to-player rotation.
- `localRotation=Euler(90, 0, 0)` — rotates the XY plane of the `Dot`/`Arrow` mesh (both flat in XY) to align with the visible face of the cube. Without this rotation, the plane stays parallel to the player's view direction and looks "edge-on" (thin line).
- Material in `aline_bundle`. HDR overbright color `(3, 3, 3, 1)` for visible neon white.

Validated 2026-05-04 with `NoteCube.prefab` + child `Dot` (mesh `Dot` from CustomNotes' `Default Arrows.fbx`).

### Particle shaders in Vivify bundles

For `ParticleSystem` (built-in Unity) rendering inside a Vivify bundle. Validated 2026-05-05 with `SphereBurst.prefab` + cube child smoke (E33-style envelope + world trail). ParticleSystem **does** survive bundle stripping (it's a Unity core component, not a custom MonoBehaviour — see "Custom MonoBehaviour does NOT survive stripping" above).

**Gotcha 1 — static mesh (POSITION-only) shaders do NOT work for billboard particles.**

`Aline/DotOverlay` and similar declare `appdata { float4 vertex : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID }`. That works for `MeshRenderer` with a static vertex buffer. `ParticleSystemRenderer` in `Billboard` mode generates quads with `POSITION + COLOR + TEXCOORD0` per particle (color is the per-particle modulation, UV the quad quadrant for masking). If the shader doesn't declare `COLOR/TEXCOORD0`, particles emit fine but come out invisible (default color 0 + no mask = nothing).

Empirical diagnosis: the `[Vivify/InstantiatePrefab] Enabled [...prefab]` log confirms instantiation + correct bundle, so visual silence = incompatible shader, not stripping.

**Compatible shader pattern (see [`AlineParticleSmoke.shader`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineParticleSmoke.shader) and [`AlineParticle.shader`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineParticle.shader)):**

```hlsl
struct appdata {
    float4 vertex : POSITION;
    float4 color  : COLOR;       // per-particle modulation (gradient + startColor)
    float2 uv     : TEXCOORD0;   // 0..1 across quad, for procedural mask
    UNITY_VERTEX_INPUT_INSTANCE_ID
};

struct v2f {
    float4 position : SV_POSITION;
    float4 color    : COLOR;
    float2 uv       : TEXCOORD0;
    UNITY_VERTEX_OUTPUT_STEREO
};

// vert: o.position = UnityObjectToClipPos(v.vertex); o.color = v.color; o.uv = v.uv;
// frag: procedural mask from uv * tint * v.color
```

SPI macros identical to the rest of the shaders in the repo (BS 1.34.2 SinglePassInstanced VR).

**Gotcha 2 — additive HDR for "energy", alpha-blend for "dark smoke".**

Additive (`Blend SrcAlpha One`) over a bright background (whitish skybox) **shows no blacks** because it sums. Dark smoke requires alpha-blend (`Blend SrcAlpha OneMinusSrcAlpha`).

| Case | Shader | Blend | Tint |
|---|---|---|---|
| Sparks / energy / glow | `Aline/Particle` | `SrcAlpha One` (additive) | HDR overbright `(3,3,3,1)` or higher |
| Smoke / dust / dark wisps | `Aline/ParticleSmoke` | `SrcAlpha OneMinusSrcAlpha` (alpha) | LDR dark `(0.04,0.04,0.06,1)` |

`Cull Off`, `ZWrite Off` for both. `ZTest LEqual` (default — smoke respects z-buffer; goes behind the cube body if it's behind).

**Gotcha 3 — `simulationSpace=Local` vs `World` defines whether the effect follows the parent or stays in world.**

| simulationSpace | Behavior | When to use |
|---|---|---|
| `Local` | Particles attached to the parent's transform. Move/rotate parent → particles move with it. | Contained envelope that travels with the projectile (smoke envelope). |
| `World` | Particles emitted in world coords. Move parent → previously emitted particles stay where they were. | Trail / wake that's left behind when the parent moves. Smoke burst at a fixed position. |

Combine both in the same prefab for a rich effect: a Local emitter (envelope) + another World (trail). Example in [`NoteCube.prefab`](../../../VivifyTemplate/Assets/Aline/Prefabs/projectiles/NoteCube.prefab) with `SmokeEnvelope` + `SmokeTrailWorld` siblings.

**Gotcha 4 — Making particles invisible during NJS jump-in via `scalingMode=Hierarchy` + `localScale=1/parent_scale`.**

When a ParticleSystem is a child of a BS note prefab (e.g., `NoteCube.prefab` with `localScale=45` and customData.animation.scale curve `[0,0,0]` during jump-in), we want particles to also be invisible during jump-in and appear at the `scale-pop`. But by default Unity scales particles "Local" — it only respects the PS GO's own `localScale`, not the parent's lossyScale.

**Solution:**
- `MainModule.scalingMode = Hierarchy` — now the system uses lossyScale (parent × child).
- `child.localScale = (1/parent_scale, 1/parent_scale, 1/parent_scale)` — neutralizes the parent's 45 factor. Result: effective lossyScale = 1 when parent.lossyScale=45 (post scale-pop), and = 0 when parent.lossyScale=0 (during jump-in and before the pop).

Without this, you fall back to `MainModule.startDelay` approximating NJS jump-in duration in seconds — fragile because it depends on NJS+BPM and when the ParticleSystem awakes.

**Gotcha 5 — alpha fade-in on trails creates a visible "gap" between cube and tail.**

If the `colorOverLifetime` curve starts at alpha=0 ("fade in"), freshly emitted particles are invisible for ~0.2-0.3s. During that time the cube moves several meters → the visible tail starts far from the cube, not attached.

**Solution:** alpha curve for trails starts at the peak (`0.85` or whatever fits) and only does fade-out at the end. The "soft start" comes from the shader's procedural mask (soft at the quad edge), not from the lifetime curve. For envelope (Local sim, attached to the cube) you can use fade-in without visible gap — because the particle moves with the cube and "appears progressively" in place.

### Gotcha: Sandfall's "ORM" is NOT a standard ORM

Confirmed 2026-05-03 with `Curator_Body_OcclusionRoughnessMetallic.png`: although the name follows the UE convention (Occlusion R, Roughness G, Metallic B packed grayscale), the visual content is **multichannel pseudocolor** (saturated orange+green+magenta, not grayscale). The R channel has values ~0.5-1.0 mostly — multiplied as AO it gives practically identity, darkens nothing.

Likely: Sandfall uses these PNGs to encode paint masks / channel-packed effects for their specific UE pipeline, not for standard PBR. **Real AO is baked into BaseColor.**

Practical implication: **`_OcclusionStrength=0` for Aline body materials** (and probably for any E33 character). The Normal map is standard and plugs in normally.

If you want to validate before writing off an ORM, open the PNG with the Read tool and look at the channels: if the R channel looks grayscale-like, it's a real ORM; if it looks colored, it's the other thing.
