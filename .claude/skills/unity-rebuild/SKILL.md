---
name: unity-rebuild
description: Use after editing prefabs, materials, or shaders in the Unity VivifyTemplate project. Triggers when user mentions 'F5', 'rebuild bundle', 'rebuild', 'Build Configuration Window', or after any change in Unity that needs to take effect in Beat Saber. Also covers updating CRCs in Info.dat post-rebuild and errors like 'BuildAssetBundles error', 'Build failed', 'Unity license', 'Unity version mismatch'.
---

# Unity Rebuild Workflow

After modifying any prefab, material, shader, or asset in the VivifyTemplate Unity project:

## Standard rebuild flow

1. Build (two equivalent options):
    - **F5** (quick shortcut) — equivalent to "Build Working Version Uncompressed". For iteration.
    - **`Vivify > Build > Build Configuration Window`** — window with control over platforms (Windows 2019 / Windows 2021 / Android 2021) and Compressed/Uncompressed mode. **Compressed** is mandatory before uploading the map to production.
2. Unity exports `bundleWindows2021.vivify` (and other variants per config) + `bundleinfo.json` to the map folder.
3. **CRC sync is automatic.** The Editor script [`PostBuildSyncCRCs.cs`](../../../VivifyTemplate/Assets/Aline/Editor/PostBuildSyncCRCs.cs) has a `FileSystemWatcher` on `bundleinfo.json` and launches `scripts/sync-crcs.ps1` every time Vivify rewrites the file. Sync output shows in the Unity console (`[sync-crcs] ...`). Toggleable from `Tools/Aline/Auto-sync CRCs after Vivify build`.
4. Restart Beat Saber (or just relaunch the map) — Vivify reloads bundles on launch.

**Manual fallback** (auto-sync off or working without Unity open): `.\scripts\sync-crcs.ps1` (PowerShell). From bash: `powershell -ExecutionPolicy Bypass -File ./scripts/sync-crcs.ps1`. Same script the watcher invokes — single source of truth.

## CRC structure

`bundleinfo.json` (written by Vivify) contains up to 3 CRCs depending on the platforms you build:

```json
{
  "bundleCRCs": {
    "_windows2019": 2604998796,   // PC BS 1.29.1
    "_windows2021": 2051513366,   // PC BS 1.34.2+ (this project)
    "_android2021": 3982829844    // Quest, only if built
  }
}
```

`Info.dat._customData._assetBundle` has to exactly match the CRCs in `bundleinfo.json`:

```json
"_customData": {
  ...,
  "_assetBundle": {
    "_windows2021": <CRC_FROM_BUNDLEINFO>
  }
}
```

`sync-crcs.ps1` is in charge of keeping this synced. **First time**: if the `_windows2021` (or other platform) key doesn't yet exist in `Info.dat._customData._assetBundle`, you have to add it by hand once with a placeholder value (e.g. `0`); the script detects it and updates it. On subsequent rebuilds it stays automated.

## Platforms — when to build each one

| Bundle | For | Single Pass Mode | Default in this project |
|---|---|---|---|
| `_windows2019` | PC Beat Saber 1.29.1 | Single Pass | No |
| `_windows2021` | PC Beat Saber 1.34.2+ | Single Pass Instanced | **Yes** |
| `_android2021` | Quest | Single Pass Instanced | No |

Change in `Vivify > Build > Build Configuration Window`.

## When CRCs don't match

Symptom: `[Vivify/AssetBundleManager] Checksum not defined` (in `beatsaber-logs/_latest.log`). Always means the CRCs in `Info.dat` don't match the bundle file. Reread `bundleinfo.json` and resync.

## Bypass for iteration

For fast iteration without resyncing CRCs every time, launch Beat Saber with the flag `-aerolunaisthebestmodder`. This disables checksum validation. **Remove the flag before final testing — the published map has to work without it.**

## Common build errors

| Symptom | Cause | Fix |
|---|---|---|
| `BuildAssetBundles error` | Some corrupt asset in `Assets/` | Check the Unity console, it usually points to the specific `.prefab`/`.mat` |
| Build OK but `Info.dat` still breaks | CRCs not updated after the rebuild | `.\scripts\sync-crcs.ps1` |
| `Unity version mismatch` when opening the project | Unity != 2019.4.28f1 | Install exactly that version from Unity Hub |
| A platform is missing in the output | Build Configuration didn't include it | `Vivify > Build > Build Configuration Window` and check Windows 2019 / 2021 / Android 2021 |
| Published map looks bad but it's fine locally | You uploaded an Uncompressed build | Re-build in Compressed mode before publishing |
| HUD text misaligned in BS 1.29.1 | TextMeshPro of Unity 2019.4.28f1 | Downgrade TMP to `com.unity.textmeshpro@1.4.1` (doesn't apply to 1.34.2) |
| `Unity license` error when opening | License expired or not renewed | Renew in Unity Hub |

## What does NOT need a rebuild

- Editing the map's `.dat`s (notes, events, custom events). BS reads them directly, doesn't involve the bundle.
- Editing `Info.dat`. Same.
- Adding lights with ChroMapper. Same.

What DOES need a rebuild: any change in `VivifyTemplate/Assets/`. Prefabs, materials, shaders, textures, scripts.

## Iterating materials/shaders without a round-trip to BS

To iterate shaders and material properties on `aline.prefab`, **DON'T go straight to "Vivify > Build → relaunch BS → screenshot"**. Capture the result in the Unity Scene view via `mcp__unity-mcp__manage_camera screenshot capture_source=scene_view`. ~5s vs ~1min per iteration.

**Recipe:**

1. Confirm the prefab is in the scene: `mcp__unity-mcp__manage_scene get_hierarchy max_depth=2`. If not, instantiate it.
2. Position the Scene View with `mcp__unity-mcp__execute_code`:
   ```csharp
   var sv = UnityEditor.SceneView.lastActiveSceneView;
   sv.Focus();
   sv.pivot = new Vector3(0, 1.6f, 0);                       // y = head height
   sv.rotation = Quaternion.LookRotation(new Vector3(0, 0, -1)); // look at face from +Z
   sv.size = 0.15f;                                           // close-up
   sv.Repaint();
   ```
   `size`: ~0.15 portrait, ~0.6 body. If the prefab has `transform.forward = +Z` it can show up "backwards" — try `LookRotation((0,0,1))` and `((0,0,-1))`.
3. Screenshot: `mcp__unity-mcp__manage_camera screenshot capture_source=scene_view include_image=true max_resolution=600`. PNG inline.
4. Iterate shader/props without touching BS until the result is good.
5. Only then F5 + BS screenshot to confirm that Vivify's bundle stripping/keyword rewriting didn't break anything.

**When you DO need the BS round-trip:** validate the final render with environment + fixed camera + skybox + post-processing. Those are final-phase details, not fast iteration.

**Caveat:** Scene view uses the Editor render path. It can diverge from the bundle: scene lighting (there's a default sun/sky in editor; in the bundle only what Vivify sends), bundle build shader keyword stripping, editor post-processing.

### Critical gotcha: `manage_material set_material_shader_property` doesn't sync keywords

`set_material_shader_property` sets the FLOAT of the Toggle property but **does NOT enable/disable the associated shader keyword**. The float ↔ keyword sync of the `[Toggle(NAME)]` attribute only happens when the toggle is changed from the Unity inspector, not via API. Workaround:

```csharp
mat.EnableKeyword("USE_RADIAL_FADE");
// or
mat.DisableKeyword("USE_RADIAL_FADE");
UnityEditor.EditorUtility.SetDirty(mat);
UnityEditor.AssetDatabase.SaveAssets();
```

Via `mcp__unity-mcp__execute_code`. If the shader has `#ifdef USE_RADIAL_FADE`, without EnableKeyword the ifdef code never runs even though the float is at 1 — a bug that's very hard to detect because the material looks correctly configured in the Inspector.

## Diagnosis: missing menu item + clean Console = silent broken compile

If a Unity menu item (`Window > X`) doesn't appear after installing a package and the Console is completely clean (0 errors, 0 relevant warnings), DON'T trust that the assembly compiled. Check: does `<project>/Library/ScriptAssemblies/` exist and contain the expected DLLs (`<package-name>.Editor.dll`, `Assembly-CSharp.dll`)? If the folder doesn't exist or is empty, **compilation failed silently** and the `[MenuItem]`s didn't register because the whole assembly didn't load.

**Typical causes in order of probability:**
1. **Duplicate DLL** overlapping platforms (canonical case: package vendors `Newtonsoft.Json.dll` and the project already ships one). Fix: keep only one (prefer the one living in the host project's `Plugins/`, not vendored in the package). The package's asmdef with `precompiledReferences: ["Newtonsoft.Json.dll"]` and `overrideReferences: false` picks up whichever is available.
2. asmdef with `precompiledReferences` pointing to a non-existent DLL.
3. asmdef with `references` to another asmdef that doesn't exist.
4. Package with APIs unsupported in 2019.4 (may silence the error to Editor.log too).

`Editor.log` sometimes does have the `error CS`s, but sometimes just says `[ScriptCompilation] Recompiling all scripts ... CompileScripts: 2130ms` with no further detail. It's a weak signal — use the presence/absence of DLLs in `Library/ScriptAssemblies/` as authoritative.
