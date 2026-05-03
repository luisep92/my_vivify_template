---
name: vivify-mapping
description: Use when editing Beat Saber map .dat files (Info.dat, [Difficulty]Standard.dat) for the Vivify map. Covers V3 beatmap syntax, lowercase asset paths, CRC sync after Unity rebuilds, the InstantiatePrefab/AnimateTrack/DestroyObject event templates, settings setter starter pack, and the family attack catalog. Trigger also when user mentions 'add an event', 'animate the prefab', or sees errors like 'Could not find UnityEngine.GameObject', 'Checksum not defined', 'Asset bundle could not be loaded', '[Vivify] Track does not exist'.
---

# Vivify Mapping

Editar el mapa Beat Saber con Vivify. Cubre los `.dat`, los eventos Vivify y el catálogo de familias de ataque.

## Formatos

- `*Standard.dat`, `BPMInfo.dat` → V3 beatmap (`"version": "3.x.x"`, claves cortas `b/x/y/c/d/t`, `customData` sin underscore).
- `Info.dat` → schema con underscore (`_version: "2.x.x"`, `_difficultyBeatmapSets`, etc.). BS 1.34.2 espera este; no hay alternativa.

### Schema mínimo V3 requerido en cada `*Standard.dat`

Si falta una entry, BS no parsea el archivo y la dificultad no carga:

```
version, bpmEvents, rotationEvents, colorNotes, bombNotes, obstacles, sliders,
burstSliders, waypoints, basicBeatmapEvents, colorBoostBeatmapEvents,
lightColorEventBoxGroups, lightRotationEventBoxGroups, lightTranslationEventBoxGroups,
basicEventTypesWithKeywords: {d: []}, useNormalEventsAsCompatibleEvents: false,
customData: {}
```

Las que no usemos van como `[]` literal.

### Cheatsheet V2 → V3

Útil cuando copias snippets de `vivify_examples/` (algunos antiguos siguen siendo V2) o de docs antiguos.

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
| `_disableSpawnEffect: true` | `spawnEffect: false` (renombrado e invertido) |
| `_pointDefinitions: [{_name, _points}]` array | `pointDefinitions: {name: points}` dict |
| `_environment[*]._id` | `environment[*].id` |

### Gotcha PowerShell `ConvertTo-Json` con arrays vacíos

PowerShell serializa `@()` como `{}` (objeto), no como `[]` (array). BS rechaza el `.dat` si encuentra `{}` donde espera array. Workaround: usar `,@()` (comma-prefix) para forzar array vacío. Y `[IO.File]::WriteAllText($path, $json, [System.Text.UTF8Encoding]::new($false))` para strip BOM (BS no parsea con BOM).

## Asset paths

**Siempre lowercase** dentro de eventos: `assets/aline/prefabs/aline.prefab`, no `Assets/Aline/...`. Match exacto con `bundleinfo.json`.

Antes de añadir un `InstantiatePrefab`/`SetMaterialProperty`, abrir `bundleinfo.json` y verificar que el path existe — corta el ciclo "edito el evento → abro el juego → falla → vuelvo".

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

**El nombre es `DestroyObject`, no `DestroyPrefab`.** `DestroyPrefab` no existe — BS lo ignora silenciosamente y los prefabs se acumulan. Verificar nombres de eventos contra [`docs/heckdocs-main/docs/vivify/events.md`](../../../docs/heckdocs-main/docs/vivify/events.md).

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

Detalle de animaciones en la skill [`vivify-animations`](../vivify-animations/SKILL.md).

## Conversión lane units ↔ world meters (NoodleExtensions)

NoodleExtensions usa **lane units** en `coordinates`/`definitePosition` (1 lane = 0.6m). Vivify `InstantiatePrefab` usa **world meters**. Conversión calibrada empíricamente:

```
LANE_UNIT_M       = 0.6     # 1 lane unit = 0.6 metros
LANE_X_ZERO_WORLD = -0.9    # lane x=0 corresponde a world x=-0.9
LANE_Y_ZERO_WORLD =  1.0    # lane y=0 corresponde a world y=1.0 (ground level)
```

Fórmula:
```
lane_x = (world_x - LANE_X_ZERO_WORLD) / LANE_UNIT_M
lane_y = (world_y - LANE_Y_ZERO_WORLD) / LANE_UNIT_M
lane_z = world_z / LANE_UNIT_M     # sin offset, player en world z=0
```

La doc Beatwalls sugiere `x=0=center` pero empíricamente necesita el offset. **Usar la calibración, no la doc.**

## Settings Setter (en `Info.dat._difficultyBeatmaps[]._customData`)

Heck implementa un dialog que se muestra al jugador antes de cargar el mapa proponiendo settings. Cancelable. Restaura al salir.

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

- `_requirements`: hard — sin el mod, BS no carga el mapa. Añadir `"Noodle Extensions"` si el `.dat` usa `coordinates`/`definitePosition`/etc.
- `_suggestions`: soft — recomendado pero opcional.
- Heck **salta** silenciosamente settings cuyos mods no están instalados, así que es seguro mandar bloques de Counters+/UITweaks aunque no estés seguro de qué tiene el jugador.

Doc oficial: [`docs/heckdocs-main/docs/settings.md`](../../../docs/heckdocs-main/docs/settings.md).

### Starter pack

Derivado de scan a 10 mapas Vivify del corpus. Los settings con mayor cobertura.

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

| Setting | Cobertura corpus | Por qué |
|---|---|---|
| `_noteJumpDurationTypeSettings: "Dynamic"` | 10/10 | Sin esto, jugadores en modo Static ignoran nuestro NJS. |
| `_environmentEffectsFilterPreset: "AllEffects"` | 6/10 | Algunos juegan en NoEffects por epilepsia/perf — eso rompe el custom env Vivify. |
| `_leftHanded: false` | 8/10 | Si la coreografía asume diestro, fuérzalo. |
| `_environments._overrideEnvironments: false` | 4/10 (crítico) | Si el jugador tiene env override global (BillieEnvironment, etc), nuestro env no carga. |
| `_chroma._disableEnvironmentEnhancements: false` | 10/10 | Fuerza que se apliquen los `customData.environment[]` del `.dat` (los que disable BS env). |
| `_chroma._disableChromaEvents: false` | 5/10 | Análogo para eventos Chroma. |

**Adicionales por necesidad:**

- `_playerOptions._noTextsAndHuds: true` — apaga HUD vanilla (combo, score, multiplier, energy, miss text). Para showcase cinemático SÍ.
- `_countersPlus._mainEnabled: false` — apaga HUD de Counters+ (mod independiente del HUD vanilla). Necesario si pones `_noTextsAndHuds: true`.
- `_uiTweaks._{multiplier,energy,combo,position,progress}Enabled: false` — apaga UITweaks. Misma razón.
- `_graphics._maxShockwaveParticles: 0` — útil si tienes muchos efectos custom.

**Gotcha — `PlayersPlace` no es HUD.** Es GameObject del environment. `_noTextsAndHuds` NO lo quita. Hay que apagarla con `customData.environment[]` en el `.dat`. Receta en [`vivify-environment`](../vivify-environment/SKILL.md) sección "Disable BS environment".

**Ejemplos del corpus:** `vivify_examples/43a26 (luminescent - nasafrasa)` y `43a2e (Ego Death - Sands)` para `_settings`. `43999 (42-flux - Aeroluna)` y `43a24 (End Times - Chaimzy)` para estrategias de `customData.environment[]`.

## Catálogo de familias de ataque

Para añadir un ataque al mapa, **no escribir eventos desde cero**. Cada habilidad de Aline está modelada como una **familia reutilizable** con su contrato (inputs, secuencia de eventos, encoding del parry, parámetros tunables, reglas de no-conflicto). Ver [`families.md`](families.md).

Familias actuales:
- **A — Ranged Sequence** (proyectiles secuenciales)
- **B — Melee Directional Slash**
- **C — Distortion Window** (post-process grayscale, modificador apilable)
- **D — Shrinking Indicator** (parry de precisión, estilo E33)
- **E — Multi-hit Chain**
- **F — Charging AoE Ball**

Status por familia y orden de prototipado en [docs/NEXT_STEPS.md sección 4](../../../docs/NEXT_STEPS.md).

## Validar paths antes de usarlos

`bundleinfo.json` lista los assets reales del bundle:

```json
{
  "materials": {
    "alineBody": { "path": "assets/aline/materials/aline_body.mat", ... }
  },
  "prefabs": { "alineMain": "assets/aline/prefabs/aline.prefab" }
}
```

Antes de un `InstantiatePrefab`/`SetMaterialProperty`, verificar que el `asset` aparece exactamente (lowercase). Es el path del `.mat`/`.prefab` en el bundle, no el path del Asset path Unity.

## Errores comunes y diagnóstico

| Síntoma en log de BS | Causa | Fix |
|---|---|---|
| `[Vivify/InstantiatePrefab] Enabled` | (positivo) confirma que el evento se procesa | — |
| `Could not find UnityEngine.GameObject [path]` | Path mal escrito o en mayúsculas | Lowercase + match exacto con `bundleinfo.json` |
| `[Vivify/AssetBundleManager] Checksum not defined` | CRCs en `Info.dat` no matchean bundle | Resync desde `bundleinfo.json` (skill `unity-rebuild`) |
| `Asset bundle could not be loaded` | Bundle corrupto/ausente, falta el `.vivify` | Rebuild en Unity (F5) |
| `[Vivify] Track does not exist` en AnimateTrack | Track no creado por un `InstantiatePrefab` previo | Comprobar orden temporal |
| Prefab carga pero invisible | Escala mala (UE5 cm → Unity m) o fuera de cámara | `scale: [0.01, 0.01, 0.01]` + revisar position |
| Prefab carga pero negro/oscuro | Sin Directional Light dentro del prefab | Añadir luz al prefab; las luces vanilla NO afectan a Vivify |
| Evento ignorado silenciosamente | `t` mal escrito o evento inexistente (e.g. `DestroyPrefab`) | Verificar nombre contra `docs/heckdocs-main/docs/vivify/events.md` |
| Cambios en `.dat` no se reflejan en BS | BS está cacheando | Salir al menú principal y reentrar |
| Prefabs Vivify se sustituyen por modelos custom o `dissolve` no funciona | Mod CustomNotes activo del jugador → intercepta el rendering de notas | El jugador debe desactivar CustomNotes; documentar en `Info.dat._customData._warnings` por dificultad. No hay force-disable desde el mapa. |

## Dónde está el log

`beatsaber-logs/_latest.log` (junction al directorio de logs de BS). Para sesiones anteriores hay `*.log.gz` en la misma carpeta (descomprimir con `gzip -dc` o `Expand-Archive`).

## Debugging checklist cuando un prefab no aparece

1. Buscar `[Vivify/InstantiatePrefab] Enabled` en `_latest.log` — si no está, el evento es malformado.
2. Buscar `Checksum not defined` — CRCs desactualizados, copiar de `bundleinfo.json`.
3. Buscar `Could not find UnityEngine.GameObject [path]` — path mal escrito o no expuesto en bundle.
4. Si todo el log sale limpio pero no se ve: revisar `position`/`scale` (UE5 cm → Unity m, scale 0.01) y que la cámara lo enfoque.
5. Si se ve pero está negro: añadir Directional Light hijo del prefab en Unity y rebuild. Para shaders sensibles al ambient sin GI baking, ver [`vivify-materials`](../vivify-materials/SKILL.md).
