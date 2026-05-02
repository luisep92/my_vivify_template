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

## Instanciar escenario custom

Pattern: `InstantiatePrefab` a beat 0, prefab con mesh + material propio bundleado en `aline_bundle`. Para una "plataforma" donde Aline pelea sin pelearse con la geometría natural del rip, **el approach que probó funcionar es construir el mesh ad-hoc en Blender** en lugar de ripear de E33.

### Por qué mesh custom en lugar de rip directo

Probado en sesión 2026-05-02:
1. Ripear `SM_Rock_A_CliffEdge` del juego dio una piedra alargada con superficie irregular natural. Resultado: Aline flota sobre las depresiones / queda enterrada en los picos. **Imposible alinear pies con suelo a milímetro porque el "suelo" es función no-constante de XZ.**
2. Iteramos posición/escala/rotación a ojo (~6 iteraciones), llegamos a "casi bien" pero nunca exacto.
3. Switch a custom mesh: óvalo plano construido en Blender con bumps controlados, **pivot exactamente en el TOP-CENTER**. Placement determinístico de UNA pasada. Cero iteraciones a ciegas.

Trade-off: pierdes la "autenticidad" del asset E33, pero la textura sigue siendo del juego (`Albedo_2K_vlzkba1fw.png` de Megascans/Surfaces/Jagged_Rock — la usa el juego en sus rocks). Visualmente lee como "roca de E33". Para Phase 1 con deadline esto es lo correcto.

### Receta del mesh custom (versión consolidada)

Script reutilizable: `scripts/blender/build_rock_platform.py`. Idempotente (limpia cualquier `RockPlatform*` previo, construye, exporta FBX a `Assets/Aline/Scenery/Meshes/`). Para regenerar tras tunear parámetros: pegar el script en blender-mcp `execute_blender_code` o ejecutar como `__main__`.

Estructura del builder:
1. **Cylinder primitive con `end_fill_type='TRIFAN'`** (no NGON). Con NGON el top cap es un solo polígono sin vertices interiores → el corredor central queda sin geometría displaceable y la cara se vuelve no-planar tras displace. TRIFAN da center-vert + triángulos → subdivide propaga al interior.
2. Subdivide global → luego subdivide top-only para concentrar densidad arriba.
3. **Translate vertices `-THICKNESS/2`** para que top quede en `z=0` local (`primitive_cylinder_add(location=...)` setea object location, no mesh-local origin — el mesh siempre se construye centrado).
4. **Silueta perimetral** vía `mathutils.noise.noise(cos(θ), sin(θ))` — la entrada en el círculo hace la función continua sin discontinuidad en θ=±π. Random per-bin produce zigzag tipo "sun spike" (probado y descartado).
5. **Corredor plano** rectángulo con falloff radial. Verts dentro del rectángulo se saltan; verts fuera reciben `displace * blend(distance / FALLOFF)`. FALLOFF amplio (~2m) evita "baches al pie de Aline".
6. UVs: `bpy.ops.uv.smart_project(angle_limit=66)`. NO planar projection (la planar = los rayos radiales del bug original).
7. Smooth shading per-polygon (`p.use_smooth = True`).
8. **Espejo en Y al final** (`v.co.y = -v.co.y` + `bmesh.ops.reverse_faces`). Necesario porque el combo `bake_space_transform=True + axis_forward='-Z'` mapea Blender +Y a Unity -Z (espalda del jugador). Negar Y antes de exportar garantiza que el corredor caiga en Unity +Z (hacia el boss). Ver gotcha "FBX axis flip" abajo.
9. Export FBX: `axis_forward="-Z"`, `axis_up="Y"`, `bake_space_transform=True`, `apply_scale_options="FBX_SCALE_NONE"`.

### Gotcha: FBX axis flip Blender → Unity 2019.4

El combo de export `axis_forward='-Z' + axis_up='Y' + bake_space_transform=True + use_space_transform=True` en Blender 4.2 LTS produce dos comportamientos no-obvios al importarse en Unity 2019.4:
- **Sin `bake_space_transform`**: la mesh aparece como pared vertical (Blender Y → Unity Y, sin axis swap). `Renderer.bounds.extents` muestra `(width, length, depth)` con length en Y (up). Bug visible: el suelo no existe.
- **Con `bake_space_transform=True`**: la mesh queda horizontal correcta (Blender Y → Unity Z), PERO el sentido del eje se invierte (Blender +Y → Unity -Z). Bug visible: lo que querías delante del jugador queda detrás.

Solución sin tocar opciones de export: negar Y de todos los verts en Blender + `reverse_faces` para mantener normales. Encapsulado en `build_rock_platform.py:build()`. Validar siempre con `Renderer.bounds.center.z` (debe ser positivo si el contenido va hacia adelante en Unity).

### Pivots — el factor clave

**El truco que hace deterministico el placement:** mesh top en z=0 local + pivot en (0,0,0) → al instanciar a `position.y = Y_objetivo`, el top está exactamente en world Y = Y_objetivo.

Para alinear pies de Aline sobre el plate: necesitas saber dónde están los pies de Aline. Mídelo en Unity:
1. `GameObject.Instantiate` Aline.prefab en (0,0,0) con scale 0.01 y rotación identity
2. Lee `SkinnedMeshRenderer.bounds.min.y` — esa es la distancia (negativa) del pivot a los pies en world
3. La fórmula: `pies_world_Y = position.y + bounds.min.y`

Para Aline (verificado): `bounds.min.y = -0.43m` con scale 0.01 → pies a `position.y - 0.43`.

Si Aline está a `position.y=1`, sus pies están a `world Y = 0.57`. Plate a `position.y = 0.57` → top exactamente en `world Y = 0.57` → contacto perfecto.

**Caveat:** la lectura del bbox es en T-pose (rest pose). Si la animación que Aline está corriendo desplaza su cuerpo (idle hover, pose levantada), los pies aparentes pueden estar más altos. En testing 2026-05-02 hubo que sumar +0.4m a la posición computada (de 0.57 → 0.97) para que pies apoyaran visualmente. Es ajuste fino sobre la fórmula base.

### Pipeline operativo (resumen)

1. Construir mesh en Blender (script ad-hoc o blender-mcp interactivo). Output FBX directamente a `VivifyTemplate/Assets/Aline/Scenery/Meshes/`
2. Unity: refresh, crea material con shader `Aline/Standard` + textura. Bundle name `aline_bundle` en mesh + material
3. Crear prefab que envuelva el FBX con material asignado en su renderer. `PrefabUtility.SaveAsPrefabAsset`. Bundle name en prefab también
4. Vivify > Build > Build Working Version Uncompressed (F5)
5. PostBuildSyncCRCs.cs sincroniza CRC a Info.dat automáticamente
6. Add evento `InstantiatePrefab` en `.dat` con position determinística

Tiempo total con script + MCP: ~30-45 min de "Blender mesh" hasta verlo en BS.

## Convertir Unreal `.pskx` → `.fbx` (mesh estático)

Cuando ripeas un mesh estático con FModel obtienes `.pskx` (formato Unreal). Para Unity necesitas FBX. Script: `scripts/blender/pskx_to_fbx.py`. Ejecutar:

```
"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" --background --python scripts\blender\pskx_to_fbx.py -- "<input.pskx>"
```

Genera `<input>.fbx` al lado del `.pskx`. Requiere addon `io_scene_psk_psa` (Befzz/DarklightGames) — el mismo que usamos para `.psa` de animaciones.

## HUD removal

**Sí hay forma directa via Heck Settings Setter** — ver sección arriba. `_noTextsAndHuds: true` apaga el HUD vanilla (combo, score, multiplier, energy, miss text). El jugador ve un prompt antes de cargar y acepta. Para mods que renderizan su propio HUD (Counters+, UITweaks) hay que añadir sus settings específicos al mismo bloque.

Lo único que NO controlas desde el mapa son HUDs de mods de overlay completamente externos (Twitch chat overlay, performance counters, etc.) — esos son configuración del usuario.

## Referencias

- Eventos Vivify: [`docs/heckdocs-main/docs/vivify/events.md`](../../../docs/heckdocs-main/docs/vivify/events.md) — secciones `SetRenderingSettings`, `SetCameraProperty`, `Blit`, `CreateCamera`, `InstantiatePrefab`.
- Comandos Chroma del environment: [`docs/heckdocs-main/docs/environment/environment.md`](../../../docs/heckdocs-main/docs/environment/environment.md).
- Skill `vivify-mapping` para edición general de `.dat` y validación de paths.
- Memory `feedback_skybox_clearflags` para el gotcha cross-proyecto.
- Memory `project_sandfall_hunt_pattern` para metodología de localizar el asset E33 correcto.