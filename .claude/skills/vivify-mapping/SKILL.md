---
name: vivify-mapping
description: Use when editing Beat Saber map .dat files (Info.dat, [Difficulty]Standard.dat) for the Vivify map. Covers V2 format syntax, lowercase asset paths in events, CRC sync after Unity rebuilds, and the InstantiatePrefab/AnimateTrack/DestroyPrefab event templates. Trigger also when user mentions 'add an event', 'animate the prefab', or sees errors like 'Could not find UnityEngine.GameObject', 'Checksum not defined', 'Asset bundle could not be loaded', '[Vivify] Track does not exist', or '[Vivify/InstantiatePrefab] Enabled'.
---

# Vivify Mapping

Working on a Beat Saber map using Vivify mod for custom 3D content.

## Format
- This map uses V2 format (`_customEvents`, `_time`, `_type`, `_data` with underscores)
- Asset paths in events MUST be lowercase: `assets/aline/prefabs/aline.prefab`
- Nunca uses guión bajo en `asset`, `id`, `track`, `position`, etc. dentro de `_data`
  (esos van sin underscore)

## Standard event template
```json
{
  "_time": 0,
  "_type": "InstantiatePrefab",
  "_data": {
    "asset": "assets/aline/prefabs/aline.prefab",
    "id": "alineMain",
    "track": "alineTrack",
    "position": [0, 0, 5],
    "rotation": [0, 180, 0],
    "scale": [0.01, 0.01, 0.01]
  }
}
```

## Important
- After every Unity rebuild, update `_assetBundle` CRCs in Info.dat from bundleinfo.json
- Common Vivify events: InstantiatePrefab, DestroyPrefab, AnimateTrack, AssignTrackParent, SetMaterialProperty, Blit
- See docs/vivify-events.md for full reference

## Validar paths antes de usarlos

`bundleinfo.json` (en `beatsaber-map/`) lista los assets reales del bundle:

```json
{
  "materials": {
    "alineBody": { "path": "assets/aline/materials/aline_body.mat", ... }
  },
  "prefabs": {
    "alineMain": "assets/aline/prefabs/aline.prefab"
  }
}
```

Antes de añadir un evento `InstantiatePrefab` o `SetMaterialProperty`, abrir
`bundleinfo.json` y verificar que el `asset` que vas a referenciar aparece
exactamente (lowercase). Esto corta el ciclo "edito el evento → abro el juego
→ falla → vuelvo".

## Errores comunes y diagnóstico

| Síntoma en log de BS | Causa probable | Fix |
|---|---|---|
| `[Vivify/InstantiatePrefab] Enabled` | (positivo) confirma que el evento se procesa | — |
| `Could not find UnityEngine.GameObject [path]` | Path mal escrito o en mayúsculas | Lowercase + match exacto con `bundleinfo.json` |
| `[Vivify/AssetBundleManager] Checksum not defined` | CRCs en `Info.dat` no matchean bundle | Resync desde `bundleinfo.json` (ver skill `unity-rebuild`) |
| `Asset bundle could not be loaded` | Bundle corrupto o ausente, o falta el archivo .vivify | Rebuild en Unity |
| `[Vivify] Track does not exist` en AnimateTrack | Track no creado por un `InstantiatePrefab` previo | Comprobar orden temporal: el `InstantiatePrefab` debe ir antes del `AnimateTrack` que lo referencia |
| Prefab carga pero invisible | Escala mala (UE5 cm → Unity m) o fuera de cámara | Scale 0.01 + revisar position |
| Prefab carga pero negro/oscuro | Sin Directional Light dentro del prefab | Añadir luz al prefab; las luces vanilla NO afectan a Vivify |
| Evento ignorado silenciosamente | Falta `_` en V2 (`type` vs `_type`) | V2: TODO con underscore en root, sin underscore dentro de `_data` |
| Cambios en `.dat` no se reflejan en BS | Beat Saber está cacheando | Salir al menú principal y reentrar al mapa (no hace falta reiniciar BS) |

## Debugging checklist cuando un prefab no aparece

1. Buscar `[Vivify/InstantiatePrefab] Enabled` en el log — si no está, el evento es malformado
2. Buscar `Checksum not defined` — CRCs desactualizados, copiar de `bundleinfo.json`
3. Buscar `Could not find UnityEngine.GameObject [path]` — path mal escrito o no expuesto en bundle (verificar contra `bundleinfo.json`)
4. Si todo el log sale limpio pero no se ve: revisar `position`/`scale` (UE5 cm → Unity m, scale 0.01) y que la cámara lo enfoque
5. Si se ve pero está negro: añadir Directional Light hijo del prefab en Unity y rebuild
