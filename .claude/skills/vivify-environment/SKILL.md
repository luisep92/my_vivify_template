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
5. **Eventos en `.dat` (V3)** — DOS, no uno (ver gotcha abajo):

```json
{
  "b": 0,
  "t": "SetRenderingSettings",
  "d": {
    "renderSettings": {
      "skybox": "assets/aline/materials/m_skybox_e33.mat"
    }
  }
},
{
  "b": 0,
  "t": "SetCameraProperty",
  "d": {
    "properties": { "clearFlags": "Skybox" }
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

Aunque cambies `_environmentName` a `DefaultEnvironment` (el que menos ruido mete, ver `DECISIONES.md`), su geometría y luces siguen renderizando por encima de tu escenario custom. Para apagarla, comandos Chroma en `customData.environment[]` del `.dat`.

### Receta (DefaultEnvironment, V3)

```json
"customData": {
  "environment": [
    { "id": "Environment|GameCore", "lookupMethod": "Regex", "position": [0, -69420, 0] },
    { "id": "DustPS",      "lookupMethod": "Contains", "active": false },
    { "id": "PlayersPlace", "lookupMethod": "Contains", "active": false }
  ]
}
```

Tres comandos, no uno:
1. **Yeet `Environment|GameCore`** al -69420 — mueve toda la geometría/luces fuera del frustum.
2. **Apagar `DustPS`** — partículas no se mueven con `position` (sistema de partículas con coordenadas locales propias), van con `active: false`.
3. **Apagar `PlayersPlace`** — la baldosa bajo los pies del jugador. Si quieres que pise tu propio suelo, fuera.

### Por qué yeet (-69420) en vez de `active: false`

Algunos GameObjects del environment tienen scripts del juego que los **reactivan** (`OnEnable` de managers, scene-load callbacks). Un GameObject yeeteado es invisible al juego: ningún script chequea "estoy lejos, vuelvo". Más robusto que `active: false` para la geometría base. El trade es CPU mínimo (animators/particles tickeando en el limbo) — irrelevante para una sola canción. Para partículas usar `active: false` es OK (no suelen reactivarse y son baratas de matar).

Pattern derivado de `vivify_examples/43a24 (End Times - Chaimzy)` — DefaultEnvironment + Vivify, mapa publicado y jugable.

### Diagnóstico cuando el environment sigue visible

| Síntoma | Causa probable | Fix |
|---|---|---|
| Cambios a `environment[]` no hacen nada, sin error | El array está fuera de `customData` o claves mal escritas | Asegurar path `customData.environment[]` con `id`/`lookupMethod`/`active` |
| Algunos GameObjects desaparecen pero otros no | El regex no captura todos | Ampliar regex; loguear con `PrintEnvironmentEnhancementDebug: true` en `Chroma.json` |
| Env desaparece en local pero algunos jugadores lo ven raro | Tienen un environment override global (BillieEnvironment, etc.) | Forzar con Settings Setter `_environments._overrideEnvironments: false` |
| Geometría apagada con `active:false` se reactiva sola | Script del juego la reactiva | Yeetear con `position: [0,-69420,0]` en lugar de `active: false` |

## Settings Setter

Cubierto en la skill [`vivify-mapping`](../vivify-mapping/SKILL.md) sección "Settings Setter". Vive en `Info.dat._difficultyBeatmaps[]._customData` (V2 schema porque es Info.dat). Apaga HUD vanilla, fuerza Dynamic NJS, etc.

## Ambient lighting

Cuando se necesite (Phase 2+), evento `SetRenderingSettings` con `ambientMode` / `ambientLight` / `ambientSkyColor` / `ambientEquatorColor` / `ambientGroundColor`. Para que un shader custom dentro del bundle Vivify reaccione al ambient, usar `unity_AmbientSky/Equator/Ground` directamente, NO `ShadeSH9` — detalle en [`vivify-materials`](../vivify-materials/SKILL.md) sección "Ambient en bundles Vivify".

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

### Decoración de ground (carpet de pétalos / hojas) — preferir mesh pre-built sobre tile-shader

Para cubrir el suelo con vegetación tipo "alfombra de pétalos" (ver foto E33: dense leaf coverage en el rock), evaluamos cuatro approaches en orden de discovery:

1. **Scatter de N clusters discretos pequeños** (mesh `SM_DeadLeaves_Petals_new` x22 instancias). Resultado: dotty, sparse, no llega a "carpet" sino a "puntitos esparcidos". Descartado.
2. **Mesh único merged + clusters scatter denso** (~80 clusters). Mejora densidad pero sigue leyéndose discreto en lugar de continuo. Descartado.
3. **Duplicate del top del rock + atlas-tile vía shader** (`build_petal_carpet` + `_AtlasRegion` cropping). Continuous coverage SI, pero el tiling muestra el patrón del atlas claramente cada 25cm — "se ve el atlas entero repetido". Descartado.
4. **Mesh pre-built de "scattered carpet" del marketplace** (Real_Ivy_Pack/SM_ivy_floor_plane_dense). 5 instancias rotadas + scale variation + Z squash agresivo (0.15) para flatten plantas a petals. **Funciona.**

**Lección consolidada**: para ground decoration en VR/BS, **mesh asset choice > shader gymnastics**. Un asset pack pre-built diseñado para scatter ya tiene la organic distribution baked-in (UVs apuntan al atlas correctamente, no hay tile pattern visible). Tilear un atlas vía shader siempre muestra el patrón a cualquier tiling-rate. Antes de invertir tiempo en shader-tile complejo, scoutear FModel para `SM_*floor_plane*`, `SM_*ground_*`, `SM_*carpet*` o equivalentes.

**Arquitectura final consolidada (Phase 1):**

`RockPlatform.fbx` con UNA mesh y TRES submeshes/material slots:

1. **Capa 0 — Rock**: mesh procedural del platform (`build()`). Material `M_Rock_Cliff` con shader `Aline/Standard` (sin LUMINANCE_TINT, opaque).
2. **Capa 1 — Ivy carpet**: scatter de N copias rotadas+scale-Z-aplastadas del mesh pre-built `SM_ivy_floor_plane_dense_spread_*` (`build_ivy_scatter()`). Material `M_BlueIvy` con `LUMINANCE_TINT` cool blue overbright. Cubre el suelo con look "petals continuous coverage" sin patrón visible.
3. **Capa 2 — Bushes 3D scatter**: scatter aleatorio determinista de N copias del mesh pequeño `SM_ground_foliage_03_*` (`build_bush_scatter()`). Material `M_PinkBush` con `LUMINANCE_TINT` pink-magenta overbright. Aporta toques de color contrastante + pequeñas protrusiones 3D que asoman sobre el ivy. Restringido a `y >= BUSH_Y_MIN` Blender pre-mirror = solo en frente del jugador (cámara fija de BS no justifica geometría detrás).

Resultado: 1 mesh upload, 3 draw calls (uno por material), ~217K tris totales para todo el escenario decorado.

**Pipeline final del scatter de carpet (referencia técnica):**
1. Scatter N copias rotadas (yaw aleatorio) del template mesh, posiciones explícitas asimétricas (foco frente del jugador, mínimo detrás — la cámara fija no ve atrás)
2. **Decimate al template** (no a las copias) ANTES de duplicar — savings se multiplican por N. Ratio 0.5 indistinguible visualmente a distancia BS
3. Scale no-uniforme `(s, s, s * HEIGHT_SCALE)` con HEIGHT_SCALE ~0.15 — aplasta verticalidad de meshes que son "plantas creciendo" a "petalos tirados". Sin esto los leaves se leen como grass blades verticales
4. Join en una mesh con `material_index=1`, attached al rock como submesh → 1 mesh, 2 submeshes, 2 draw calls (rock opaque + ivy cutout-alpha)

### Preview de materiales en Blender (iteración sin BS round-trip)

Por defecto los placeholders de los slots no tienen shading → el viewport Material Preview se ve gris. Para iterar visualmente sin re-bundle + lanzar BS por cada cambio: rellenar los placeholders con texturas reales + EEVEE nodes que aproximan el shader Aline/Standard.

`build_rock_platform.py:_make_preview_material()` reproduce los 3 modos del shader:
- Plain texture (rock): texture → emission, sin tint, sin alpha
- Multiply tint (default): texture × tint_color → emission
- Luminance tint (ivy/petals): texture → RGB→BW (luminance) × tint_color → emission, con Mix Shader + Transparent BSDF basado en alpha del texture, `blend_method='CLIP'`

Switch viewport vía `space.shading.type = 'MATERIAL'`. Result: rock con su textura + ivy azul con alpha cutout, casi indistinguible del look final BS. Sirve para iterar density/placement/size sin tocar Unity.

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
- Skill [`vivify-mapping`](../vivify-mapping/SKILL.md) para edición general de `.dat` y validación de paths.

## Metodología: localizar el asset E33 real (vs marketplace pack)

Sandfall agrupa muchos Unreal Marketplace asset packs (`SkyboxPack`, `Real_Ivy_Pack`, `AdvancedLocomotionV4`, `FabricCollection`, etc.) en su build. Encontrar "una textura que se vea bien" no significa que sea la real usada por la escena objetivo — los devs los compraron como librerías. Para fidelidad, rastrear desde el LEVEL hacia atrás, no desde los assets hacia adelante.

**Cadena de lookups con `mcp__fmodel__*`:**

1. **Identificar el level objetivo** — `Sandfall/Content/Levels/<Zone>/<SubLevel>/Level_*.json`. Nombres a veces crípticos (`Monolith_Interior_PaintressGrandFinale_Main` = pelea jugable, `*_PaintressIntro` = cinemática previa). Si dudas, grep por nombres de personaje/skill en `GameActions/`.
2. **Grep en el level** por el tipo de objeto buscado: skybox → `BP_SkyBox`, `SM_Skybox`, `[Ss]kybox`. Environment mesh → `BP_Monolith`, `SM_Floor`, etc.
3. **Encontrar el actor blueprint y el StaticMeshComponent**. El actor (`BP_*_C`) referencia el componente. El componente tiene `OverrideMaterials` con la `MI_*` real.
4. **Leer el `MI_*.json`** con `fmodel_inspect_material` — vive en `Content/Materials/<Folder>/`. Lista `Parent`, `TextureParameterValues` (textura concreta), `ScalarParameterValues`, `VectorParameterValues`.
5. **La textura** vive en `<Folder>/Textures/...`; export con `fmodel_export_texture`.

**Levels vs marketplace packs:**
- Marketplace: `SkyboxPack*`, `*Collection*`, `Advanced*`, `Procedural*` — librerías compradas. Las texturas pueden ser referenciadas desde MIs reales del juego, pero el MI propio y el shader compuesto siempre viven en `Content/Materials/`.
- Sandfall-internas: `Content/Materials/`, `Content/Characters/Enemies/<Boss>/`, `Content/Levels/`, `Content/Effect/`. Aquí están los MIs y las decisiones reales.

**Filesystem gotcha:** FModel a veces muestra carpetas con casing distinto (`Skies` y `SKIES` en el mismo nivel). Windows colapsa case y al exportar las dos a `Output/` una sobreescribe la otra. Si el resultado parece corto, comprobar hermanas case-distinta no exportadas.

**Workflow eficiente (reduce ping-pong con FModel):**
1. `fmodel_export_raw` sobre carpetas top-level relevantes — kilobytes, contienen metadata sin texturas pesadas.
2. Grep + Read los JSON exportados para encontrar el asset objetivo.
3. Solo entonces `fmodel_export_texture`/`fmodel_export_mesh` de los binarios específicos.