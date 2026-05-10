# ARCHITECTURE — Technical pipeline

## Bootstrap from cold clone

Steps to bring the project up on a fresh machine, strict order.

1. **Install Beat Saber 1.34.2** + Aeroluna's mod chain (Vivify, Heck, CustomJSONData, Chroma, NoodleExtensions). Exact versions in [BS_Dependencies.txt](../BS_Dependencies.txt). **Do not use Mod Assistant** — install by hand from [github.com/Aeroluna/Heck/releases](https://github.com/Aeroluna/Heck/releases) and [github.com/Aeroluna/Vivify/releases](https://github.com/Aeroluna/Vivify/releases). Mod Assistant sometimes serves outdated versions that break the inter-dependencies.

2. **Install Unity 2019.4.28f1** (exact version) from Unity Hub. Different version = bundle incompatible with BS.

3. **Install Blender 4.2 LTS** + `io_scene_psk_psa` addon (Befzz/DarklightGames) enabled in Preferences > Extensions. Needed to process `.psa` (animations) and `.pskx` (meshes) from FModel.

4. **Clone the repo**:
   ```
   git clone <url> d:\vivify_repo\my_vivify_template
   ```

5. **Create the junctions** (cmd, not PowerShell — `mklink` is a cmd builtin):
   ```cmd
   cd d:\vivify_repo\my_vivify_template
   mklink /J beatsaber-map  "C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Beat Saber_Data\CustomWIPLevels\Test"
   mklink /J beatsaber-logs "C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Logs"
   ```
   Create the `CustomWIPLevels\Test\` directory beforehand if it doesn't exist. After this, the versioned `.dat` files (`Info.dat`, `*Standard.dat`, `BPMInfo.dat`, `bundleinfo.json`) are already accessible at `beatsaber-map/` (via junction to the game's directory).

6. **Get the non-versioned binaries**. What's missing after the clone:
   - **Map audio** (`beatsaber-map/La-mandanga.ogg`, ~2.3 MB) — gitignored. Get separately. Without it the map can't load audio and BS may reject it.
   - **Sandfall dump** (`d:\vivify_repo\Sandfall/`, ~40 GB) — re-rip the game with FModel. Setup: `%APPDATA%\FModel\AppSettings.json` with game dir = `D:\SteamLibrary\steamapps\common\Expedition 33`, UE version = 5.4, mappings = `Expedition33Mappings-1.5.4.usmap` (also in `d:\vivify_repo\fmodel-mcp\mappings\`). Expected output dir: `D:\vivify_repo\Output\Exports\`.
   - **Aline_project.blend** (`Sandfall/Content/Characters/Enemies/HumanEnnemies/Aline/Aline_project.blend`) — gitignored. Rebuild with `scripts/blender/import_all_psa.py` (27 actions from `.psa`) + `scripts/blender/synthesize_root_motion.py` (root motion axis remap). The scripts are the deterministic backup — versioned in git.
   - **Textures, FBXes, PSAs** under `VivifyTemplate/Assets/Aline/` — gitignored by extension. Recoverable via re-rip pipeline (see "Recovery").

7. **Tools outside the repo**. If they're not in `d:\vivify_repo/`:
   ```
   cd d:\vivify_repo
   git clone https://github.com/luisep92/unity_vivify_mcp.git unity-mcp
   git clone https://github.com/luisep92/fmodel-mcp.git fmodel-mcp
   git clone --depth 1 https://github.com/legoandmars/CustomNotesUnityProject.git
   mkdir _outline-shader-ref
   curl -L -o _outline-shader-ref/UnlitOutlines.shader https://raw.githubusercontent.com/ronja-tutorials/ShaderTutorials/master/Assets/020_Inverted_Hull/UnlitOutlines.shader
   curl -L -o _outline-shader-ref/SurfaceOutlines.shader https://raw.githubusercontent.com/ronja-tutorials/ShaderTutorials/master/Assets/020_Inverted_Hull/SurfaceOutlines.shader
   ```
   Wiring and startup details in [unity-mcp/README.md](../../unity-mcp/README.md) and [fmodel-mcp/README.md](../../fmodel-mcp/README.md). The Aline project already references `unity-mcp` via `VivifyTemplate/Packages/manifest.json` (local path). `CustomNotesUnityProject` and `_outline-shader-ref` are **reference material** for the cube visual polish (see NEXT_STEPS sub-step 4.1) — not modified, fragments are copied into the Aline project.

8. **Open the Unity project**: `VivifyTemplate/` from Unity Hub. First import takes ~5 min (regenerates `Library/`). If any binary (FBX, PSA, PNG) is missing, "missing reference" warnings will show — recover per the "Recovery" procedure below.

9. **First build**: F5 (or `Vivify > Build > Build Configuration Window`). Generates `bundleWindows2021.vivify` + `bundleinfo.json` in `beatsaber-map/`. PostBuildSyncCRCs syncs the CRC into `Info.dat` automatically.

10. **Launch BS**, go to `Custom WIP Levels`, map `Test`. Easy/Normal/ExpertPlus difficulties should show up.

## Recovery — what happens if you delete X

Table of "if you delete X, is it recoverable and how?". Versioned = in git, recoverable with `git checkout`. Regenerable = rebuilt with a local command. Lost = no backup, has to be re-acquired from outside.

| If you delete... | Status | Recovery |
|---|---|---|
| Any `.md`, `.cs`, `.shader`, `.mat`, `.prefab`, `.meta` | Versioned | `git checkout <path>` |
| `beatsaber-map/*.dat`, `bundleinfo.json` | Versioned | `git checkout beatsaber-map/<file>` |
| `beatsaber-map/bundleWindows2021.vivify` (~128 MB) | Regenerable | F5 in Unity (regenerates bundle + bundleinfo.json + sync CRC) |
| `beatsaber-map/La-mandanga.ogg` (~2.3 MB) | **Lost (no backup, not versioned)** | Accepted. The `.ogg` stays ignored — the map audio isn't a repo asset, it has to be obtained separately. |
| `VivifyTemplate/Library/`, `Temp/`, `Logs/` | Regenerable | Open Unity, regenerates on its own (~5 min first startup) |
| `VivifyTemplate/Assets/Aline/Textures/*.png` | Regenerable | Re-rip from `Sandfall/` with `mcp__fmodel__fmodel_export_texture` and move the PNG from `Output/Exports/.../*.png` to the folder. Recipe in [`vivify-materials`](../.claude/skills/vivify-materials/SKILL.md) section "FModel → Unity mapping". |
| `VivifyTemplate/Assets/Aline/Animations/Aline_Anims.fbx` (~185 MB) | Regenerable | Re-export from Blender: `scripts/blender/export_anims_fbx.py` (requires `Aline_project.blend` with the 27 actions imported). |
| `VivifyTemplate/Assets/Aline/Hair/*.fbx` | Regenerable | Re-run `scripts/blender/pskx_to_fbx.py` over the `.psk` from `Sandfall/Content/Characters/Hair/Mirror_Family/Aline/`. |
| `VivifyTemplate/Assets/Aline/Scenery/Meshes/RockPlatform.fbx` | Regenerable | Re-run `scripts/blender/build_rock_platform.py` (idempotent, builds + exports FBX). |
| `VivifyTemplate/Assets/Aline/Prefabs/projectiles/NoteCube.fbx` | Regenerable | Copy `Default Base.fbx` from [legoandmars/CustomNotesUnityProject](https://github.com/legoandmars/CustomNotesUnityProject) (`Assets/Meshes/Examples/Default Base.fbx`) → `VivifyTemplate/Assets/Aline/Prefabs/projectiles/NoteCube.fbx`. The versioned `.meta` preserves the GUID; the `NoteCube.prefab` (versioned) references the FBX's internal `Cube` mesh. |
| `VivifyTemplate/Assets/Aline/Prefabs/projectiles/NoteArrows.fbx` | Regenerable | Copy `Default Arrows.fbx` from the same CustomNotesUnityProject repo (`Assets/Meshes/Examples/Default Arrows.fbx`) → `VivifyTemplate/Assets/Aline/Prefabs/projectiles/NoteArrows.fbx`. The FBX contains two meshes (`Dot` for `d=8`, `Arrow` for directionals); the `NoteCube.prefab` references the `Dot` mesh as child indicator. |
| `Sandfall/` (~40 GB) | Regenerable | Re-rip the game with FModel (see Bootstrap step 6). Selective: only what `VivifyTemplate/` references. |
| `Aline_project.blend` (in `Sandfall/`) | Regenerable via scripts (not versioned) | Rebuild: `scripts/blender/import_all_psa.py` (imports the 27 `.psa` as actions from `Sandfall/.../Animation/`) + `scripts/blender/synthesize_root_motion.py` (root motion axis remap for clips with displacement). Both scripts are versioned in git, idempotent, and self-contained — they are the deterministic backup of the `.blend`. The `.blend` itself stays gitignored. |
| `unity-mcp/` or `fmodel-mcp/` (outside the repo) | Regenerable | `git clone` the public repos (URLs in CLAUDE.md). |
| `ReMapper-master/`, `FModel.exe` (outside the repo) | Regenerable | Re-download from their respective sources. No active use yet. |

## Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│ SOURCE: Expedition 33 (Unreal Engine 5)                              │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  fmodel-mcp (.NET CLI over CUE4Parse + Python MCP server)
                                 GUI fallback: FModel.exe for visual browsing
┌──────────────────────────────────────────────────────────────────────┐
│ D:\vivify_repo\Output\Exports\Sandfall\Content\...                   │
│   PNGs, .pskx, .psa, .json (selective, not full dump)                │
│   Scratch: what's confirmed gets moved to its destination            │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  Textures: straight to Unity. Meshes: via Sandfall/ + Blender
                              │
                              ▼  Blender 4.2 LTS + Blender MCP server
┌──────────────────────────────────────────────────────────────────────┐
│ .blend (rig + N actions imported from .psa)                          │
│ scripts/blender/import_all_psa.py    (batch import .psa → actions)   │
│ scripts/blender/export_anims_fbx.py  (export armature + actions)     │
│ → Aline.fbx       (mesh + rig)                                       │
│ → Aline_Anims.fbx (rig only + animation takes)                       │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  Unity 2019.4.28f1 + VivifyTemplate
┌──────────────────────────────────────────────────────────────────────┐
│ VivifyTemplate/Assets/Aline/                                         │
│   Prefabs/aline.prefab          (Animator on the PREFAB ROOT)        │
│   Textures/                      (PNGs from FModel)                  │
│   Materials/                     (M_Aline_Body_1/2, M_Aline_Black)   │
│   Shaders/Aline/Standard.shader  (unlit + alpha cutout + Cull Off)   │
│   Animations/Aline_AC.controller (state machine, 26 states)          │
│   Editor/PostBuildSyncCRCs.cs    (auto CRC sync)                     │
│   Editor/AlineAnimsImporter.cs   (preserveHierarchy=true + loopTime) │
│   Editor/BuildAlineAnimator.cs   (Tools menu: regenerates AC)        │
│   Editor/InspectAlineClips.cs    (Tools menu: dump fcurves)          │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  F5 / Vivify > Build > Build Configuration Window
┌──────────────────────────────────────────────────────────────────────┐
│ beatsaber-map/  (junction to CustomWIPLevels/Test/)                  │
│   bundleWindows2021.vivify   (asset bundle, ~MB)                     │
│   bundleWindows2019.vivify   (optional)                              │
│   bundleinfo.json            (CRCs + asset paths)                    │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  Auto CRC sync (Editor watcher)
┌──────────────────────────────────────────────────────────────────────┐
│ beatsaber-map/Info.dat                                               │
│   _customData._assetBundle._windows2021 = <CRC>                      │
│ beatsaber-map/ExpertPlusStandard.dat                                 │
│   _customEvents → InstantiatePrefab, AnimateTrack, DestroyPrefab,    │
│                   SetAnimatorProperty (Bool/Float/Int/Trigger)       │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  Beat Saber 1.34.2 + Vivify mod
┌──────────────────────────────────────────────────────────────────────┐
│ Runtime: Vivify loads the bundle, instantiates the prefab, animates  │
│ tracks                                                               │
└──────────────────────────────────────────────────────────────────────┘
```

## Stack — exact versions

| Layer | Tool | Version | Why this exact one |
|---|---|---|---|
| Game | Beat Saber | **1.34.2** (build 7115288407) | Last one compatible with Aeroluna's mod chain. |
| Mod core | Vivify | **1.0.7+1.34.2** | Stable on 1.34.2. |
| Mod core | Heck | **1.8.1+1.34.2** | Required by Vivify. |
| Mod core | CustomJSONData | **2.6.8+1.34.2** | Required by Heck. |
| Mod | Chroma | **2.9.22+1.34.2** | Custom lighting. |
| Mod | NoodleExtensions | **1.7.20+1.34.2** | Custom note motion. |
| Editor | Unity | **2019.4.28f1** | Version mandated by VivifyTemplate (Single Pass Instanced for Windows 2021). |
| 3D | Blender | **4.2 LTS** | Import `.psa` (DarklightGames PSK/PSA addon), export FBX for Unity. |
| 3D — automation | Blender MCP | `uvx blender-mcp` (ahujasid/blender-mcp) | Lets Claude Code run Python in Blender (rig inspection, batch imports, FBX export). |
| Asset explorer (GUI) | FModel | (latest) | Visual browsing of UE5 assets. For non-GUI automation we use fmodel-mcp. |
| Asset explorer (programmatic) | fmodel-mcp | in-house (CUE4Parse 1.2.2 + .NET 9) | CLI + MCP server. Repo at `d:\vivify_repo\fmodel-mcp/`. `mcp__fmodel__*` tools in Claude. |
| Map editor | ChroMapper | (latest) | Visual map editor. |
| Scripting | ReMapper | (master) | Programmatic generation of notes/events. **Not used yet.** |
| Unity automation | unity-mcp (local fork) | port to 2019.4 | Minimal fork at `d:\vivify_repo\unity-mcp/` hooked in via `Packages/manifest.json`. Stdio bridge on port 6400. See [unity-mcp/README.md](../../unity-mcp/README.md). |

## Which file lives where and why

### Inside the repo

| Path | What | Versioned |
|---|---|---|
| `CLAUDE.md`, `docs/*.md`, `BS_Dependencies.txt` | Documentation | Yes |
| `.gitignore` | Versioning rules | Yes |
| `.claude/skills/*/SKILL.md` | Instructions for Claude Code | Yes |
| `scripts/snapshot-map.ps1` | Local tool for manual snapshots | Yes |
| `scripts/sync-crcs.ps1` | Post-build CRC sync (invoked by Editor watcher) | Yes |
| `scripts/blender/import_all_psa.py` | Batch import `.psa` → Blender actions | Yes |
| `scripts/blender/export_anims_fbx.py` | Export armature + actions to FBX for Unity | Yes |
| `docs/map-snapshots/.gitkeep` | Folder marker | Yes |
| `docs/map-snapshots/*/` | Snapshots of the `.dat` files before big changes | **No** (folder-ignored) |
| `beatsaber-map/*.dat`, `bundleinfo.json` | Map: V3 difficulties, V2 manifest, BPM, bundle info | **Yes** (since 2026-05-04, commit `ef5bb7d`) |
| `beatsaber-map/*.vivify`, `*.ogg`, `*.bak`, `*.v2bak` | Compiled bundles, audio, manual backups | **No** |
| `VivifyTemplate/Assets/**` (no binaries) | Prefabs, scripts, materials (`.mat`), shaders, `.meta` | Yes |
| `VivifyTemplate/Assets/**/*.png/.fbx/.psa/...` | Textures, 3D models, binary animations | **No** |
| `VivifyTemplate/Library/`, `Temp/`, `Logs/`, `UserSettings/` | Unity cache | **No** (covered by `VivifyTemplate/.gitignore`) |
| `VivifyTemplate/Packages/`, `ProjectSettings/` | Package manifest and settings | Yes |

### Outside the repo (in `d:\vivify_repo\`)

| Path | What | Why outside |
|---|---|---|
| `Sandfall/` | UE5 dump of Expedition 33 | ~40 GB. Extraction tool, not part of the product. |
| `ReMapper-master/` | Deno/TS scripting tool | Has its own `.git`. Better kept alongside the repo. |
| `FModel.exe` | ~47 MB .exe tool | Binary, better outside. GUI fallback. |
| `fmodel-mcp/` | Canonical programmatic wrapper over CUE4Parse (.NET 9 CLI + Python MCP server) | Its own repo (`luisep92/fmodel-mcp`). MCP stdio bridge. See [fmodel-mcp/README.md](../../fmodel-mcp/README.md). |
| `Output/Exports/` | Scratch dir where FModel GUI and `mcp__fmodel__fmodel_export_*` write | Variable size. What's confirmed gets moved to `my_vivify_template/Sandfall/` (meshes) or `VivifyTemplate/Assets/<area>/Textures/` (PNGs). |
| `CustomNotesUnityProject/` | Canonical repo from [legoandmars/CustomNotesUnityProject](https://github.com/legoandmars/CustomNotesUnityProject) — Unity project of reference for custom notes (meshes, materials, shaders, prefab structure) | Reference for building our projectile prefabs via `AssignObjectPrefab`. **We don't use `NoteDescriptor`** (CustomNotes mod component); we only copy geometry/material. Unity 2018.x, open in 2019.4.28f1. |
| `_outline-shader-ref/` | Ad-hoc folder with [Ronja's UnlitOutlines.shader / SurfaceOutlines.shader](https://github.com/ronja-tutorials/ShaderTutorials/tree/master/Assets/020_Inverted_Hull) downloaded directly | Base inverted-hull shader for the custom cube outline. CC-BY 4.0 — credit Ronja in the shader header when adapting it to the Vivify project. |

### Junctions to the Beat Saber install

Two Windows junctions (`mklink /J`) — the **link itself** is not versioned (each machine creates it), but the **map content** is (the `.dat` files and `bundleinfo.json` are the versioned source of truth in git since commit `ef5bb7d`, 2026-05-04). Logs are not versioned.

#### `beatsaber-map/` → `CustomWIPLevels\Test\`

```cmd
mklink /J beatsaber-map "C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Beat Saber_Data\CustomWIPLevels\Test"
```

Lets you read `Info.dat`, `*Standard.dat`, `BPMInfo.dat`, `bundleinfo.json` and `bundle*.vivify` with a relative path from the repo. After creating the junction on a fresh machine, the versioned `.dat` files are already in git — only the heavy binaries are missing (`*.vivify` are generated with F5/Build, `*.ogg` is copied manually once).

#### `beatsaber-logs/` → `Beat Saber\Logs\`

```cmd
mklink /J beatsaber-logs "C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Logs"
```

Lets you read IPA + Vivify logs from the repo. Structure:

- **`_latest.log`** — current session uncompressed. This is the one we normally read.
- **`<timestamp>.log`** — current session uncompressed (same content as `_latest.log`).
- **`<timestamp>.log.gz`** — previous sessions compressed with gzip. To read a specific one: `gzip -dc <file>` (Git Bash) or `Expand-Archive` from PowerShell.

Useful for diagnosing:

- `[Vivify/InstantiatePrefab] Enabled` (positive: the event is being processed).
- `Could not find UnityEngine.GameObject` (wrong path in the event).
- `[Vivify/AssetBundleManager] Checksum not defined` (CRCs out of date).
- `Asset bundle could not be loaded` (bundle missing or corrupt).
- `[Vivify] Track does not exist` (event temporal ordering broken).

(`cmd` command, not PowerShell — `mklink` is a cmd builtin.)

## Rebuild flow

Two equivalent options:

- **F5** — shortcut. Equivalent to "Build Working Version Uncompressed". For iteration.
- **`Vivify > Build > Build Configuration Window`** — window with control over platforms (Windows 2019 / Windows 2021 / Android 2021) and compression mode.

Output: bundles + `bundleinfo.json` in `beatsaber-map/`.

### Uncompressed vs Compressed

| Mode | When | Notes |
|---|---|---|
| **Uncompressed** | Iteration, testing changes | F5 default. Larger bundle, build almost instant. **Don't distribute.** |
| **Compressed** | Before publishing the map | Much slower build. Mandatory for release. |

### Platforms

| Bundle | For | Single Pass Mode |
|---|---|---|
| `_windows2019` | PC Beat Saber 1.29.1 | Single Pass |
| `_windows2021` | PC Beat Saber 1.34.2+ (this project) | Single Pass Instanced |
| `_android2021` | Quest | Single Pass Instanced |

By default we only build `_windows2021`. If at some point we want to ship a Quest version, also tick `_android2021` in the Build Configuration and sync its CRC.

## Animation pipeline

Sub-flow independent of the prefab/material one. Runs once to generate the AnimationClips, afterwards they're only invoked via `SetAnimatorProperty` event.

```
.psa from FModel
   │  scripts/blender/import_all_psa.py  (via Blender MCP or Scripting workspace)
   ▼
Blender actions in bpy.data.actions (372 bones matched, scale fcurves stripped)
   │  scripts/blender/export_anims_fbx.py
   │     - push actions to NLA tracks UNMUTED, strip name = "<armature>|<action>"
   │     - export armature only, takes via bake_anim_use_nla_strips=True
   ▼
Aline_Anims.fbx (~185 MB, gitignored, .meta is versioned)
   │  Unity 2019.4 FBX importer + Editor/AlineAnimsImporter:
   │     - preserveHierarchy=true (keeps SK_Curator_Aline as GO)
   │     - loopTime=true on canonical idles
   ▼
26 AnimationClips as sub-assets, paths "SK_Curator_Aline/root/pelvis/..."
   │  Tools > Aline > Build Animator Controller (Editor/BuildAlineAnimator)
   ▼
Aline_AC.controller with 26 states, 26 triggers (Any State → X), auto-return to Idle1
   │  Assigned to the Animator component on the PREFAB ROOT (not on the SK_Curator_Aline child)
   ▼
Runtime: Vivify SetAnimatorProperty with prefab id + trigger name
```

### Why the Animator lives on the prefab root + `preserveHierarchy=true`

Blender's armature-only export collapses the armature object as the FBX root node. Unity, on top of that, collapses top-level nodes with a single child by default. Without a countermeasure, the clip paths come out as `root/pelvis/...` with no `SK_Curator_Aline` prefix. The FBX inspector preview uses `Aline.fbx` as the model (via avatar source), whose hierarchy does preserve `SK_Curator_Aline` → mismatch → T-pose.

`preserveHierarchy=true` (set by `AlineAnimsImporter.OnPreprocessModel`) makes Unity not collapse — `SK_Curator_Aline` stays as a GO in the imported FBX and all clip paths are prefixed with `SK_Curator_Aline/...`. With those paths, the Animator can live on the prefab root and the paths match directly.

The scale curves that the FBX exporter puts by default on the armature object (path `""` originally → `"SK_Curator_Aline"` with preserveHierarchy) land on the `SK_Curator_Aline` GO (scale 1) → no-op. The prefab root keeps its `localScale: 0.01` baked without the clips stepping on it. Decision documented at [DECISIONES.md#2026-05-01](DECISIONES.md).

### Trigger naming convention

Triggers in the AnimatorController are named after the clip minus the `Paintress_` prefix:

| Clip name | Trigger name |
|---|---|
| `SK_Curator_Aline\|Paintress_Idle1` | `Idle1` |
| `SK_Curator_Aline\|Paintress_Skill3` | `Skill3` |
| `SK_Curator_Aline\|Paintress_Idle1_to_idle2_transition` | `Idle1_to_idle2_transition` |
| `SK_Curator_Aline\|Skill_Aline_P3_Skill1` | `Skill_Aline_P3_Skill1` |

That's what goes into `properties[].id` of the `SetAnimatorProperty` event in the `.dat`.

### `vivify-animations` skill

Operational guide for the pipeline: step-by-step once-per-character setup + tool table + non-negotiable rules + 6 documented gotchas (NLA strips muted, addon PSA action linking, preserveHierarchy, no plural SetEditorCurves in 2019.4, Inspector loopTime bug, rest pose mismatch). Check it before touching anything in the flow.

---

## `bundleinfo.json` as source of truth

After each rebuild, `bundleinfo.json` ends up looking like this:

```json
{
  "materials": {
    "alineBody": {
      "path": "assets/aline/materials/aline_body.mat",
      "properties": { "_Color": { "type": { "Color": null }, "value": [...] } }
    }
  },
  "prefabs": {
    "alineMain": "assets/aline/prefabs/aline.prefab"
  },
  "bundleFiles": [
    "C:/.../bundleWindows2021.vivify"
  ],
  "bundleCRCs": {
    "_windows2021": 2051513366
  },
  "isCompressed": false
}
```

Two uses:

1. **Validate paths before referencing them**: `prefabs.{name}` and `materials.{name}.path` list the actual bundle assets. Before adding an `InstantiatePrefab` or a `SetMaterialProperty` to the `.dat`, check here that the path exists (lowercase, exact).
2. **CRC sync**: copy `bundleCRCs._windows2021` (and `_windows2019`/`_android2021` if you build those platforms) into `Info.dat._customData._assetBundle`.

## CRC sync — format in `Info.dat`

```json
"_customData": {
  "...": "...",
  "_assetBundle": {
    "_windows2021": <CRC_FROM_BUNDLEINFO>
  }
}
```

If the CRCs don't match: `[Vivify/AssetBundleManager] Checksum not defined` error in the BS log and the map won't load assets.

Iteration bypass: launch BS with the flag `-aerolunaisthebestmodder` (disables validation). **Remove before publishing.**

## Mods — manual install

Mod Assistant sometimes installs outdated versions of CustomJSONData/Heck/Chroma/NoodleExtensions that break dependencies between each other. For this project, Aeroluna's mods are installed by hand from GitHub:

- https://github.com/Aeroluna/Heck/releases
- https://github.com/Aeroluna/Vivify/releases

Exact versions in [BS_Dependencies.txt](../BS_Dependencies.txt).
