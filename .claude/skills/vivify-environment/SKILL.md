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

## Disable BS environment

Aunque cambies `_environmentName` a `DefaultEnvironment` (el que menos ruido mete, ver `DECISIONES.md`), su geometría y luces siguen renderizando por encima de tu escenario custom. Para apagarla, comandos Chroma en `_customData._environment[]` del `.dat` (V2) o `customData.environment[]` (V3) — ver gotcha V2/V3 abajo.

### Receta (DefaultEnvironment, V2)

```json
"_customData": {
  "_environment": [
    { "_id": "Environment|GameCore", "_lookupMethod": "Regex", "_position": [0, -69420, 0] },
    { "_id": "DustPS",      "_lookupMethod": "Contains", "_active": false },
    { "_id": "PlayersPlace", "_lookupMethod": "Contains", "_active": false }
  ]
}
```

Tres comandos, no uno:
1. **Yeet `Environment|GameCore`** al -69420 — mueve toda la geometría/luces fuera del frustum.
2. **Apagar `DustPS`** — partículas no se mueven con `_position` (sistema de partículas con coordenadas locales propias), van con `_active: false`.
3. **Apagar `PlayersPlace`** — la baldosa bajo los pies del jugador. Si quieres que pise tu propio suelo, fuera.

### Por qué yeet (-69420) en vez de `_active: false`

Algunos GameObjects del environment tienen scripts del juego que los **reactivan** (`OnEnable` de managers, scene-load callbacks). Un GameObject yeeteado es invisible al juego: ningún script chequea "estoy lejos, vuelvo". Más robusto que `_active: false` para la geometría base. El trade es CPU mínimo (animators/particles tickeando en el limbo) — irrelevante para una sola canción. Para partículas usar `_active: false` es OK (no suelen reactivarse y son baratas de matar).

Pattern derivado de `vivify_examples/43a24 (End Times - Chaimzy)` — DefaultEnvironment + Vivify, mapa publicado y jugable.

### Gotcha V2/V3: el array name también lleva underscore en V2

Heckdocs documenta SOLO V3. El array se llama `customData.environment` (sin underscore) con keys `id`/`lookupMethod`/`active` (sin underscore).

En V2 **TODO lleva underscore**, incluido el nombre del array y todas las keys: `_customData._environment[]` con `_id`/`_lookupMethod`/`_active`/`_position`. Mezclar (array sin underscore, keys con underscore) hace que Chroma lo ignore **silenciosamente** — sin warning en consola, el env sigue visible y pierdes una iteración debugueando lo que no es. Confirmado 2026-05-02.

Ver memoria `feedback_v2_v3_syntax` para mapeo completo.

### Diagnóstico cuando el environment sigue visible

| Síntoma | Causa probable | Fix |
|---|---|---|
| Cambios a `_environment[]` no hacen nada, sin error | Sintaxis V2/V3 mezclada | Asegurar `_environment` (no `environment`) + claves con underscore |
| Algunos GameObjects desaparecen pero otros no | El regex no captura todos | Ampliar regex; loguear con `PrintEnvironmentEnhancementDebug: true` en `Chroma.json` |
| Env desaparece en local pero algunos jugadores lo ven raro | Tienen un environment override global (BillieEnvironment, etc.) | Forzar con Settings Setter `_environments._overrideEnvironments: false` |
| Geometría apagada con `_active:false` se reactiva sola | Script del juego la reactiva | Yeetear con `_position: [0,-69420,0]` en lugar de `_active: false` |

## Settings Setter (HUD off, mod requirements, prompt al jugador)

Heck implementa el "Settings Setter": al cargar el mapa, BS muestra un dialog al jugador con los settings que el mapa recomienda aplicar. Si acepta, los cambia para esa sesión y los restaura al salir. Vive en `Info.dat._difficultyBeatmaps[]._customData`.

### Starter pack para mapa Vivify (V2, derivado de scan a 10 mapas del corpus)

```json
"_customData": {
  "_requirements": ["Vivify", "Chroma"],
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
}
```

Justificación por línea: ver memoria `reference_settings_setter`.

**Settings adicionales por necesidad:**
- `_playerOptions._noTextsAndHuds: true` — apaga HUD vanilla (combo, score, multiplier, energy, miss text). Para mapa cinemático tipo showcase, SÍ. Confirmado funciona.
- `_countersPlus._mainEnabled: false` — apaga el HUD del mod Counters+ (HUD independiente del vanilla). Necesario si pones `_noTextsAndHuds: true` y quieres consistencia.
- `_uiTweaks._{multiplier,energy,combo,position,progress}Enabled: false` — apaga el HUD del mod UITweaks. Misma razón. Heck salta silenciosamente si el mod no está instalado, así que es seguro mandar bloque aunque no estés seguro.

**Requirements vs Suggestions:**
- `_requirements`: hard — sin el mod, BS no carga el mapa.
- `_suggestions`: soft — recomendado pero opcional.

### Gotcha: la plataforma del jugador NO es HUD

`PlayersPlace` (la baldosa bajo los pies) es GameObject del environment, no HUD. `_noTextsAndHuds` NO la quita — hay que apagarla con `_environment[]` (ver receta arriba).

## Ambient lighting — TODO

(Pendiente. Pattern: `SetRenderingSettings` con `ambientLight` / `ambientIntensity` / `ambientMode`. Se documenta cuando lo implementemos.)

## Instanciar escenario custom — TODO

(Pendiente. Pattern: `InstantiatePrefab` a beat 0 sin track, prefab con mesh + materiales propios bundleados. Se documenta cuando lo implementemos.)

## HUD removal

**Sí hay forma directa via Heck Settings Setter** — ver sección arriba. `_noTextsAndHuds: true` apaga el HUD vanilla (combo, score, multiplier, energy, miss text). El jugador ve un prompt antes de cargar y acepta. Para mods que renderizan su propio HUD (Counters+, UITweaks) hay que añadir sus settings específicos al mismo bloque.

Lo único que NO controlas desde el mapa son HUDs de mods de overlay completamente externos (Twitch chat overlay, performance counters, etc.) — esos son configuración del usuario.

## Referencias

- Eventos Vivify: [`docs/heckdocs-main/docs/vivify/events.md`](../../../docs/heckdocs-main/docs/vivify/events.md) — secciones `SetRenderingSettings`, `SetCameraProperty`, `Blit`, `CreateCamera`, `InstantiatePrefab`.
- Comandos Chroma del environment: [`docs/heckdocs-main/docs/environment/environment.md`](../../../docs/heckdocs-main/docs/environment/environment.md).
- Skill `vivify-mapping` para edición general de `.dat` y validación de paths.
- Memory `feedback_skybox_clearflags` para el gotcha cross-proyecto.
- Memory `project_sandfall_hunt_pattern` para metodología de localizar el asset E33 correcto.