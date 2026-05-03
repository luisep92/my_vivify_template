---
name: unity-rebuild
description: Use after editing prefabs, materials, or shaders in the Unity VivifyTemplate project. Triggers when user mentions 'F5', 'rebuild bundle', 'rebuild', 'Build Configuration Window', or after any change in Unity that needs to take effect in Beat Saber. Also covers updating CRCs in Info.dat post-rebuild and errors like 'BuildAssetBundles error', 'Build failed', 'Unity license', 'Unity version mismatch'.
---

# Unity Rebuild Workflow

After modifying any prefab, material, shader, or asset in the VivifyTemplate Unity project:

## Standard rebuild flow

1. Build (dos opciones equivalentes):
    - **F5** (atajo rápido) — equivale a "Build Working Version Uncompressed". Para iteración.
    - **`Vivify > Build > Build Configuration Window`** — ventana con control sobre plataformas (Windows 2019 / Windows 2021 / Android 2021) y modo Compressed/Uncompressed. **Compressed** obligatorio antes de subir el mapa a producción.
2. Unity exporta `bundleWindows2021.vivify` (y otros variantes según config) + `bundleinfo.json` a la carpeta del mapa.
3. **Sync de CRCs es automático.** El Editor script [`PostBuildSyncCRCs.cs`](../../../VivifyTemplate/Assets/Aline/Editor/PostBuildSyncCRCs.cs) tiene un `FileSystemWatcher` sobre `bundleinfo.json` y lanza `scripts/sync-crcs.ps1` cada vez que Vivify reescribe el archivo. Output del sync se ve en la consola de Unity (`[sync-crcs] ...`). Toggleable desde `Tools/Aline/Auto-sync CRCs after Vivify build`.
4. Reiniciar Beat Saber (o solo relanzar el mapa) — Vivify recarga bundles por launch.

**Manual fallback** (auto-sync desactivado o trabajando sin Unity abierto): `.\scripts\sync-crcs.ps1` (PowerShell). Desde bash: `powershell -ExecutionPolicy Bypass -File ./scripts/sync-crcs.ps1`. Mismo script que invoca el watcher — single source of truth.

## Estructura de los CRCs

`bundleinfo.json` (escrito por Vivify) contiene hasta 3 CRCs según las plataformas que construyas:

```json
{
  "bundleCRCs": {
    "_windows2019": 2604998796,   // PC BS 1.29.1
    "_windows2021": 2051513366,   // PC BS 1.34.2+ (este proyecto)
    "_android2021": 3982829844    // Quest, solo si se construye
  }
}
```

`Info.dat._customData._assetBundle` tiene que matchear exactamente los CRCs de `bundleinfo.json`:

```json
"_customData": {
  ...,
  "_assetBundle": {
    "_windows2021": <CRC_DEL_BUNDLEINFO>
  }
}
```

`sync-crcs.ps1` se encarga de mantener esto sincronizado. **Primera vez**: si la clave `_windows2021` (u otra plataforma) no existe aún en `Info.dat._customData._assetBundle`, hay que añadirla a mano una vez con valor placeholder (e.g. `0`); el script la detecta y la actualiza. En sucesivos rebuilds queda automatizado.

## Plataformas — cuándo construir cada una

| Bundle | Para | Single Pass Mode | Por defecto en este proyecto |
|---|---|---|---|
| `_windows2019` | PC Beat Saber 1.29.1 | Single Pass | No |
| `_windows2021` | PC Beat Saber 1.34.2+ | Single Pass Instanced | **Sí** |
| `_android2021` | Quest | Single Pass Instanced | No |

Cambiar en `Vivify > Build > Build Configuration Window`.

## Cuando los CRCs no matchean

Síntoma: `[Vivify/AssetBundleManager] Checksum not defined` (en `beatsaber-logs/_latest.log`). Siempre significa que los CRCs en `Info.dat` no matchean el archivo bundle. Releer `bundleinfo.json` y resyncar.

## Bypass para iteración

Para iteración rápida sin resyncar CRCs cada vez, lanzar Beat Saber con flag `-aerolunaisthebestmodder`. Esto desactiva la validación de checksum. **Quitar el flag antes del testing final — el mapa publicado debe funcionar sin él.**

## Errores comunes en build

| Síntoma | Causa | Fix |
|---|---|---|
| `BuildAssetBundles error` | Algún asset corrupto en `Assets/` | Revisar la consola de Unity, suele señalar el `.prefab`/`.mat` concreto |
| Build OK pero `Info.dat` sigue rompiendo | CRCs no actualizados tras el rebuild | `.\scripts\sync-crcs.ps1` |
| `Unity version mismatch` al abrir el proyecto | Unity != 2019.4.28f1 | Instalar exactamente esa versión desde Unity Hub |
| Falta una plataforma en el output | Build Configuration no la incluía | `Vivify > Build > Build Configuration Window` y marcar Windows 2019 / 2021 / Android 2021 |
| Mapa publicado se ve mal pero en local va bien | Subiste un build Uncompressed | Re-build en modo Compressed antes de publicar |
| Texto del HUD descolocado en BS 1.29.1 | TextMeshPro de Unity 2019.4.28f1 | Downgrade TMP a `com.unity.textmeshpro@1.4.1` (no aplica a 1.34.2) |
| `Unity license` error al abrir | License caducada o no renovada | Renovar en Unity Hub |

## Qué NO necesita rebuild

- Editar los `.dat` del mapa (notas, eventos, custom events). BS los lee directamente, no involucran al bundle.
- Editar `Info.dat`. Igual.
- Añadir luces con ChroMapper. Igual.

Qué SÍ necesita rebuild: cualquier cambio en `VivifyTemplate/Assets/`. Prefabs, materiales, shaders, texturas, scripts.

## Iterar materiales/shaders sin round-trip a BS

Para iterar shaders y propiedades de material en `aline.prefab`, **NO ir directo a "Vivify > Build → relaunch BS → screenshot"**. Capturar el resultado en Unity Scene view via `mcp__unity-mcp__manage_camera screenshot capture_source=scene_view`. ~5s vs ~1min por iteración.

**Receta:**

1. Confirmar que la prefab está en escena: `mcp__unity-mcp__manage_scene get_hierarchy max_depth=2`. Si no está, instanciar.
2. Posicionar Scene View con `mcp__unity-mcp__execute_code`:
   ```csharp
   var sv = UnityEditor.SceneView.lastActiveSceneView;
   sv.Focus();
   sv.pivot = new Vector3(0, 1.6f, 0);                       // y = head height
   sv.rotation = Quaternion.LookRotation(new Vector3(0, 0, -1)); // mirar cara desde +Z
   sv.size = 0.15f;                                           // close-up
   sv.Repaint();
   ```
   `size`: ~0.15 portrait, ~0.6 body. Si el prefab tiene `transform.forward = +Z` puede mostrarse "al revés" — probar `LookRotation((0,0,1))` y `((0,0,-1))`.
3. Screenshot: `mcp__unity-mcp__manage_camera screenshot capture_source=scene_view include_image=true max_resolution=600`. PNG inline.
4. Iterar shader/props sin tocar BS hasta que el resultado sea bueno.
5. Solo entonces F5 + screenshot BS para confirmar que el bundle stripping/keyword rewriting de Vivify no rompió nada.

**Cuándo SÍ hace falta el round-trip BS:** validar el render final con environment + cámara fija + skybox + post-procesado. Esos son detalles de phase final, no de iteración rápida.

**Caveat:** Scene view usa el render path del Editor. Pueden divergir del bundle: iluminación de escena (hay sun/sky por defecto en editor; en bundle solo lo que Vivify mande), shader keyword stripping del bundle build, post-procesado del editor.

### Gotcha crítico: `manage_material set_material_shader_property` no sincroniza keywords

`set_material_shader_property` setea el FLOAT del Toggle property pero **NO enable/disable el shader keyword asociado**. La sincronización float ↔ keyword del `[Toggle(NAME)]` attribute solo ocurre cuando el toggle se cambia desde el inspector de Unity, no via API. Workaround:

```csharp
mat.EnableKeyword("USE_RADIAL_FADE");
// o
mat.DisableKeyword("USE_RADIAL_FADE");
UnityEditor.EditorUtility.SetDirty(mat);
UnityEditor.AssetDatabase.SaveAssets();
```

Vía `mcp__unity-mcp__execute_code`. Si el shader tiene `#ifdef USE_RADIAL_FADE`, sin EnableKeyword el código ifdef nunca se ejecuta aunque el float esté a 1 — bug muy difícil de detectar porque el material parece configurado correcto en Inspector.

## Diagnóstico: menu item missing + Console limpia = compile silenciosa rota

Si un menu item de Unity (`Window > X`) no aparece tras instalar un package y la Console está completamente limpia (0 errors, 0 warnings relevantes), NO confíes en que la asamblea compiló. Comprobar: existe `<proyecto>/Library/ScriptAssemblies/` y contiene los DLLs esperados (`<package-name>.Editor.dll`, `Assembly-CSharp.dll`)? Si la carpeta no existe o está vacía, **la compilación falló silenciosamente** y los `[MenuItem]` no se registraron porque la asamblea entera no se cargó.

**Causas típicas en orden de probabilidad:**
1. **Duplicate DLL** solapando plataformas (caso canónico: package vendoriza `Newtonsoft.Json.dll` y el proyecto ya trae uno). Fix: dejar solo uno (preferir el que viva en `Plugins/` del proyecto host, no vendorizado en el package). El asmdef del package con `precompiledReferences: ["Newtonsoft.Json.dll"]` y `overrideReferences: false` recoge el que esté disponible.
2. asmdef con `precompiledReferences` apuntando a un DLL inexistente.
3. asmdef con `references` a otro asmdef que no existe.
4. Paquete con APIs no soportadas en 2019.4 (puede silenciar el error a Editor.log también).

`Editor.log` a veces sí tiene los `error CS`, pero a veces solo dice `[ScriptCompilation] Recompiling all scripts ... CompileScripts: 2130ms` sin más detalle. Es señal débil — usar la presencia/ausencia de DLLs en `Library/ScriptAssemblies/` como autoritativa.
