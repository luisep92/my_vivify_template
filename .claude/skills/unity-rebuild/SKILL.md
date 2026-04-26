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
3. **Sincronizar CRCs**: `.\scripts\sync-crcs.ps1` (PowerShell). Lee `bundleCRCs` de `bundleinfo.json` y patcha surgically los CRCs en `Info.dat._customData._assetBundle`, preservando el formato exacto del .dat. Idempotente: no escribe si los CRCs ya matchean. Si bash: `powershell -ExecutionPolicy Bypass -File ./scripts/sync-crcs.ps1`.
4. Reiniciar Beat Saber (o solo relanzar el mapa) — Vivify recarga bundles por launch.

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
