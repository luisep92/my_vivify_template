---
name: vivify-environment
description: Use when modifying the visual environment of the Vivify map — skybox, ambient lighting, disabling the BS environment, instantiating custom scenery prefabs, fog, post-processing. Trigger when user mentions 'skybox', 'environment custom', 'ocultar Timbaland', 'ambient', 'fog', 'background', or sees errors like '[Vivify/SetRenderingSettings] Setting [skybox]' that didn't render visually.
---

# Vivify Environment

Setup visual del entorno donde Aline pelea: skybox, environment del mapa, iluminación ambiente, escenario propio. Separado de `vivify-mapping` (que cubre eventos generales del mapa) y de `vivify-materials` (que cubre shaders/materiales del personaje).

## Skybox custom

### Receta

1. **Textura equirect 2:1** (typical: 4096×2048). Si la fuente es 1:1 (algunos packs UE), no es equirect — necesitas approach distinto (backdrop quad o cubemap, no Skybox/Panoramic).
2. **Importer Unity**: `wrapMode = Repeat`, `filterMode = Bilinear`, `anisoLevel = 9`, `mipmapEnabled = true`, `maxTextureSize = 4096`.
3. **Material** con shader `Skybox/Panoramic`:
   - `_MainTex` = la textura
   - `_Mapping` = 1 (Latitude Longitude) + EnableKeyword `_MAPPING_LATITUDE_LONGITUDE_LAYOUT`
   - `_ImageType` = 0 (360 Degrees)
   - `_MirrorOnBack` = 0, `_Layout` = 0
   - `_Tint` = blanco (1,1,1,1) inicial; ajustar para warm/cool
   - `_Exposure` = 1.0 inicial
   - `_Rotation` = 0 inicial; iterar para encarar el "punto interesante" del sky al jugador (player mira +Z)
4. **Bundlear el material** asignando `assetBundleName` igual al del prefab principal (ej: `aline_bundle`). La textura se arrastra como dependencia automáticamente — NO etiquetarla aparte. Verificar tras F5 que el bundle contiene tanto el `.mat` como la textura (`AssetBundle.LoadFromFile(...).GetAllAssetNames()` desde Editor).
5. **Eventos en `.dat`** — DOS, no uno (ver gotcha abajo):

```json
{
  "_time": 0,
  "_type": "SetRenderingSettings",
  "_data": {
    "renderSettings": {
      "skybox": "assets/aline/materials/m_skybox_e33.mat"
    }
  }
},
{
  "_time": 0,
  "_type": "SetCameraProperty",
  "_data": {
    "properties": {
      "clearFlags": "Skybox"
    }
  }
}
```

### Gotcha: SetRenderingSettings.skybox no renderiza solo

`SetRenderingSettings.skybox` solo carga el material en `RenderSettings.skybox` global de Unity. Para que la cámara lo USE para clear, necesita `clearFlags = Skybox`. Las cámaras de BS por defecto hacen clear con `SolidColor` o `Depth` (lo controla cada environment), así que sin `SetCameraProperty.clearFlags=Skybox` el skybox custom queda invisible. El log de Vivify dirá `Setting [skybox]` aún en el caso roto — es positivo confirmando carga, no que se esté renderizando.

### Iteración rápida de rotación/tint/exposure

Si necesitas tunear el material muchas veces:
- **Bake en el material + F5** (lento por F5 cada iteración) — para valores definitivos.
- **`SetMaterialProperty` event en el .dat** (relaunch BS sin F5) — para iteración estética rápida. Apuntar al mismo material y override `_Rotation`/`_Tint`/`_Exposure`.

### Diagnóstico cuando el skybox no se ve

| Síntoma | Causa probable | Fix |
|---|---|---|
| `Setting [skybox]` en log + sigue todo negro | Cámara con `clearFlags ≠ Skybox` | Añadir `SetCameraProperty.clearFlags=Skybox` |
| `Setting [skybox]` en log + skybox blank/magenta | Textura no en bundle (no se serializó como dependencia) | Verificar con `bundle.GetAllAssetNames()` desde Editor; si falta, forzar `AssetDatabase.SaveAssets() + Refresh(ForceSynchronousImport)` antes del F5 |
| Skybox visible pero parte interesante mal orientada | `_Rotation` mal | Iterar en grados (0/90/180/270 primero, luego ajuste fino) |
| Skybox aparece distorsionado/estirado | Textura no es 2:1 equirect (probable 1:1) | Cambiar approach: backdrop quad o conseguir equirect real |
| Skybox visible pero environment de BS por encima | Esperado mientras Timbaland está activo | Sigue al subpaso "Disable BS environment" |

## Disable BS environment — TODO

(Pendiente. Patron: comandos Chroma en `_customData.environment[]` con `active: false`. Se documenta cuando lo implementemos.)

## Ambient lighting — TODO

(Pendiente. Pattern: `SetRenderingSettings` con `ambientLight` / `ambientIntensity` / `ambientMode`. Se documenta cuando lo implementemos.)

## Instanciar escenario custom — TODO

(Pendiente. Pattern: `InstantiatePrefab` a beat 0 sin track, prefab con mesh + materiales propios bundleados. Se documenta cuando lo implementemos.)

## HUD removal

**No hay forma directa en Vivify/Chroma** de ocultar el HUD del jugador (puntuación, combo, multiplicador). Depende de mods que cada jugador tenga instalados (NoHUD, Camera2). Para showcase maps, lo estándar es documentar la recomendación al jugador (ej: "instala NoHUD para máximo impacto visual") en la descripción del mapa.

## Referencias

- Eventos Vivify: [`docs/heckdocs-main/docs/vivify/events.md`](../../../docs/heckdocs-main/docs/vivify/events.md) — secciones `SetRenderingSettings`, `SetCameraProperty`, `Blit`, `CreateCamera`, `InstantiatePrefab`.
- Comandos Chroma del environment: [`docs/heckdocs-main/docs/environment/environment.md`](../../../docs/heckdocs-main/docs/environment/environment.md).
- Skill `vivify-mapping` para edición general de `.dat` y validación de paths.
- Memory `feedback_skybox_clearflags` para el gotcha cross-proyecto.
- Memory `project_sandfall_hunt_pattern` para metodología de localizar el asset E33 correcto.