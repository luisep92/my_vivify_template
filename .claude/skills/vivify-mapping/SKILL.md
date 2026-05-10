---
name: vivify-mapping
description: Use when editing Beat Saber map .dat files (Info.dat, [Difficulty]Standard.dat) for the Vivify map. Covers V3 beatmap syntax, lowercase asset paths, CRC sync after Unity rebuilds, the InstantiatePrefab/AnimateTrack/DestroyObject event templates, settings setter starter pack, and the family attack catalog. Trigger also when user mentions 'add an event', 'animate the prefab', or sees errors like 'Could not find UnityEngine.GameObject', 'Checksum not defined', 'Asset bundle could not be loaded', '[Vivify] Track does not exist'.
---

# Vivify Mapping

Editing the Beat Saber map with Vivify. Covers the `.dat` files, Vivify events, and the attack family catalog.

## Formats

- `*Standard.dat`, `BPMInfo.dat` → V3 beatmap (`"version": "3.x.x"`, short keys `b/x/y/c/d/t`, `customData` without underscore).
- `Info.dat` → schema with underscore (`_version: "2.x.x"`, `_difficultyBeatmapSets`, etc.). BS 1.34.2 expects this; no alternative.

### Minimum V3 schema required in each `*Standard.dat`

If an entry is missing, BS won't parse the file and the difficulty won't load:

```
version, bpmEvents, rotationEvents, colorNotes, bombNotes, obstacles, sliders,
burstSliders, waypoints, basicBeatmapEvents, colorBoostBeatmapEvents,
lightColorEventBoxGroups, lightRotationEventBoxGroups, lightTranslationEventBoxGroups,
basicEventTypesWithKeywords: {d: []}, useNormalEventsAsCompatibleEvents: false,
customData: {}
```

The ones we don't use go as literal `[]`.

### V2 → V3 cheatsheet

Useful when copying snippets from `vivify_examples/` (some old ones are still V2) or from old docs.

| V2 | V3 |
|---|---|
| `_version` | `version` |
| `_notes` | `colorNotes` |
| `_obstacles` | `obstacles` |
| `_events` | `basicBeatmapEvents` |
| `_customData` | `customData` |
| `_time` (note/event) | `b` |
| `_lineIndex` | `x` |
| `_lineLayer` | `y` |
| `_type` (note color) | `c` |
| `_cutDirection` | `d` |
| `_type` (event) | `t` |
| `_data` (event) | `d` |
| `_track` | `track` |
| `_animation` | `animation` |
| `_dissolve` / `_definitePosition` | `dissolve` / `definitePosition` |
| `_disableSpawnEffect: true` | `spawnEffect: false` (renamed and inverted) |
| `_pointDefinitions: [{_name, _points}]` array | `pointDefinitions: {name: points}` dict |
| `_environment[*]._id` | `environment[*].id` |

### Gotcha PowerShell `ConvertTo-Json` with empty arrays

PowerShell serializes `@()` as `{}` (object), not as `[]` (array). BS rejects the `.dat` if it finds `{}` where it expects an array. Workaround: use `,@()` (comma-prefix) to force an empty array. And `[IO.File]::WriteAllText($path, $json, [System.Text.UTF8Encoding]::new($false))` to strip the BOM (BS doesn't parse with BOM).

## Asset paths

**Always lowercase** inside events: `assets/aline/prefabs/aline.prefab`, not `Assets/Aline/...`. Exact match with `bundleinfo.json`.

Before adding an `InstantiatePrefab`/`SetMaterialProperty`, open `bundleinfo.json` and verify the path exists — cuts the "edit the event → open the game → fail → come back" cycle.

## Standard event templates

### InstantiatePrefab

```json
{
  "b": 0,
  "t": "InstantiatePrefab",
  "d": {
    "asset": "assets/aline/prefabs/aline.prefab",
    "id": "alineMain",
    "track": "alineTrack",
    "position": [0, 0, 5],
    "rotation": [0, 180, 0],
    "scale": [0.01, 0.01, 0.01]
  }
}
```

### DestroyObject

```json
{ "b": 16, "t": "DestroyObject", "d": { "id": "alineMain" } }
```

**The name is `DestroyObject`, not `DestroyPrefab`.** `DestroyPrefab` doesn't exist — BS silently ignores it and prefabs pile up. Verify event names against [`docs/heckdocs-main/docs/vivify/events.md`](../../../docs/heckdocs-main/docs/vivify/events.md).

### SetAnimatorProperty (Trigger / Bool / Float / Integer)

```json
{
  "b": 8,
  "t": "SetAnimatorProperty",
  "d": {
    "id": "alineMain",
    "properties": [{ "id": "Skill4", "type": "Trigger", "value": true }]
  }
}
```

Animation detail in the [`vivify-animations`](../vivify-animations/SKILL.md) skill.

## Lane units ↔ world meters conversion (NoodleExtensions)

NoodleExtensions uses **lane units** in `coordinates`/`definitePosition` (1 lane = 0.6m). Vivify `InstantiatePrefab` uses **world meters**. Empirically calibrated conversion:

```
LANE_UNIT_M       = 0.6     # 1 lane unit = 0.6 meters
LANE_X_ZERO_WORLD = -0.9    # lane x=0 maps to world x=-0.9
LANE_Y_ZERO_WORLD =  1.0    # lane y=0 maps to world y=1.0 (ground level)
```

Formula:
```
lane_x = (world_x - LANE_X_ZERO_WORLD) / LANE_UNIT_M
lane_y = (world_y - LANE_Y_ZERO_WORLD) / LANE_UNIT_M
lane_z = world_z / LANE_UNIT_M     # no offset, player at world z=0
```

The Beatwalls docs suggest `x=0=center` but empirically it needs the offset. **Use the calibration, not the docs.**

## Settings Setter (in `Info.dat._difficultyBeatmaps[]._customData`)

Heck implements a dialog shown to the player before loading the map proposing settings. Cancelable. Restored on exit.

### Schema

```json
{
  "_requirements": ["Vivify", "Chroma"],
  "_suggestions": [],
  "_settings": {
    "_playerOptions": { ... },
    "_chroma": { ... },
    "_environments": { ... },
    "_modifiers": { ... },
    "_graphics": { ... },
    "_countersPlus": { ... },
    "_uiTweaks": { ... }
  }
}
```

- `_requirements`: hard — without the mod, BS won't load the map. Add `"Noodle Extensions"` if the `.dat` uses `coordinates`/`definitePosition`/etc.
- `_suggestions`: soft — recommended but optional.
- Heck silently **skips** settings whose mods are not installed, so it's safe to ship Counters+/UITweaks blocks even if you're not sure what the player has.

Official doc: [`docs/heckdocs-main/docs/settings.md`](../../../docs/heckdocs-main/docs/settings.md).

### Starter pack

Derived from scanning 10 Vivify maps from the corpus. The settings with the most coverage.

```json
"_settings": {
  "_playerOptions": {
    "_noteJumpDurationTypeSettings": "Dynamic",
    "_environmentEffectsFilterDefaultPreset": "AllEffects",
    "_environmentEffectsFilterExpertPlusPreset": "AllEffects",
    "_leftHanded": false
  },
  "_environments": { "_overrideEnvironments": false },
  "_chroma": {
    "_disableEnvironmentEnhancements": false,
    "_disableChromaEvents": false
  }
}
```

| Setting | Corpus coverage | Why |
|---|---|---|
| `_noteJumpDurationTypeSettings: "Dynamic"` | 10/10 | Without this, players in Static mode ignore our NJS. |
| `_environmentEffectsFilterPreset: "AllEffects"` | 6/10 | Some play on NoEffects for epilepsy/perf — that breaks the custom Vivify env. |
| `_leftHanded: false` | 8/10 | If choreography assumes right-handed, force it. |
| `_environments._overrideEnvironments: false` | 4/10 (critical) | If the player has a global env override (BillieEnvironment, etc), our env doesn't load. |
| `_chroma._disableEnvironmentEnhancements: false` | 10/10 | Forces `customData.environment[]` from the `.dat` to apply (those that disable BS env). |
| `_chroma._disableChromaEvents: false` | 5/10 | Same idea for Chroma events. |

**Add as needed:**

- `_playerOptions._noTextsAndHuds: true` — turns off vanilla HUD (combo, score, multiplier, energy, miss text). For cinematic showcase, YES.
- `_countersPlus._mainEnabled: false` — turns off Counters+ HUD (mod independent of the vanilla HUD). Required if you set `_noTextsAndHuds: true`.
- `_uiTweaks._{multiplier,energy,combo,position,progress}Enabled: false` — turns off UITweaks. Same reason.
- `_graphics._maxShockwaveParticles: 0` — useful if you have lots of custom effects.

**Gotcha — `PlayersPlace` is not HUD.** It's an environment GameObject. `_noTextsAndHuds` does NOT remove it. You have to turn it off with `customData.environment[]` in the `.dat`. Recipe in [`vivify-environment`](../vivify-environment/SKILL.md) section "Disable BS environment".

**Corpus examples:** `vivify_examples/43a26 (luminescent - nasafrasa)` and `43a2e (Ego Death - Sands)` for `_settings`. `43999 (42-flux - Aeroluna)` and `43a24 (End Times - Chaimzy)` for `customData.environment[]` strategies.

## Attack family catalog

To add an attack to the map, **don't write events from scratch**. Each of Aline's abilities is modeled as a **reusable family** with its contract (inputs, event sequence, parry encoding, tunable parameters, no-conflict rules). See [`families.md`](families.md).

Current families:
- **A — Ranged Sequence** (sequential projectiles) — validated and instantiable recipe in [`family-a-recipe.md`](family-a-recipe.md)
- **B — Melee Directional Slash**
- **C — Distortion Window** (post-process grayscale, stackable modifier)
- **D — Shrinking Indicator** (precision parry, E33 style)
- **E — Multi-hit Chain**
- **F — Charging AoE Ball**

Status per family and prototyping order in [docs/NEXT_STEPS.md section 4](../../../docs/NEXT_STEPS.md).

## Validate paths before using them

`bundleinfo.json` lists the actual assets in the bundle:

```json
{
  "materials": {
    "alineBody": { "path": "assets/aline/materials/aline_body.mat", ... }
  },
  "prefabs": { "alineMain": "assets/aline/prefabs/aline.prefab" }
}
```

Before an `InstantiatePrefab`/`SetMaterialProperty`, verify that the `asset` appears exactly (lowercase). It's the `.mat`/`.prefab` path in the bundle, not the Unity Asset path.

## Common errors and diagnosis

| Symptom in BS log | Cause | Fix |
|---|---|---|
| `[Vivify/InstantiatePrefab] Enabled` | (positive) confirms the event is being processed | — |
| `Could not find UnityEngine.GameObject [path]` | Path misspelled or in uppercase | Lowercase + exact match with `bundleinfo.json` |
| `[Vivify/AssetBundleManager] Checksum not defined` | CRCs in `Info.dat` don't match bundle | Resync from `bundleinfo.json` (`unity-rebuild` skill) |
| `Asset bundle could not be loaded` | Bundle corrupt/missing, `.vivify` not present | Rebuild in Unity (F5) |
| `[Vivify] Track does not exist` on AnimateTrack | Track not created by a previous `InstantiatePrefab` | Check temporal order |
| Prefab loads but invisible | Bad scale (UE5 cm → Unity m) or out of camera view | `scale: [0.01, 0.01, 0.01]` + check position |
| Prefab loads but black/dark | No Directional Light inside the prefab | Add a light to the prefab; vanilla lights do NOT affect Vivify |
| Event silently ignored | `t` misspelled or nonexistent event (e.g. `DestroyPrefab`) | Verify name against `docs/heckdocs-main/docs/vivify/events.md` |
| Changes in `.dat` not reflected in BS | BS is caching | Exit to main menu and re-enter |
| Vivify prefabs replaced by custom models or `dissolve` doesn't work | Player has CustomNotes mod active → it intercepts note rendering | The player has to disable CustomNotes; document it in `Info.dat._customData._warnings` per difficulty. No force-disable from the map. |

## Where the log is

`beatsaber-logs/_latest.log` (junction to the BS log directory). For previous sessions there are `*.log.gz` in the same folder (decompress with `gzip -dc` or `Expand-Archive`).

## Debugging checklist when a prefab doesn't show up

1. Look for `[Vivify/InstantiatePrefab] Enabled` in `_latest.log` — if it's not there, the event is malformed.
2. Look for `Checksum not defined` — CRCs outdated, copy from `bundleinfo.json`.
3. Look for `Could not find UnityEngine.GameObject [path]` — path misspelled or not exposed in the bundle.
4. If the log comes out clean but nothing shows: check `position`/`scale` (UE5 cm → Unity m, scale 0.01) and that the camera frames it.
5. If it shows but it's black: add a Directional Light as a child of the prefab in Unity and rebuild. For shaders sensitive to ambient without GI baking, see [`vivify-materials`](../vivify-materials/SKILL.md).
