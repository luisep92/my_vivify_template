---
name: vivify-animations
description: Use when working on character animations for a Vivify bundle — pipeline `.psa` → Blender → FBX → Unity Animator → Vivify `SetAnimatorProperty`. Trigger when user mentions 'animaciones', 'animar', 'AnimatorController', 'Idle1', 'SetAnimatorProperty', 'psa', 'rig', 'bone', 'state machine', 'AnimationClip', 'fcurve' or sees errors like 'T-pose', 'modelo gigante', 'preview no anima', 'clips identity', 'rest pose mismatch', 'scale curve'. Covers el pipeline canónico y los gotchas.
---

# Vivify Animations Workflow

Pipeline para animar personajes que viven en un bundle Vivify, desde dump de Unreal hasta runtime BS. Esta skill es la guía operativa: si la sigues paso a paso, las animaciones llegan al juego.

## Pipeline canónico

```
.psa de FModel  (Unreal animation file, varios por personaje)
    │  scripts/blender/import_all_psa.py  (Blender MCP o Scripting workspace)
    ▼
Blender actions  (una por .psa, en bpy.data.actions)
    │  scripts/blender/export_anims_fbx.py
    │     - strip scale fcurves (idempotente, las .psa traen scale=1 que no aporta)
    │     - push cada action a su NLA track UNMUTED, strip name = "<armature>|<action>"
    │     - export ARMATURE only, takes vía bake_anim_use_nla_strips=True
    ▼
Aline_Anims.fbx  (~185 MB, gitignored, .meta sí versionado)
    │  Unity FBX importer + AlineAnimsImporter:
    │     - preserveHierarchy=true  (mantiene SK_Curator_Aline como GO nombrado)
    │     - loopTime=true en idles canónicos (workaround del Inspector bug 2019.4)
    ▼
26 AnimationClips como sub-assets, paths "SK_Curator_Aline/root/pelvis/..."
    │  Tools > Aline > Build Animator Controller
    ▼
Aline_AC.controller con state machine
   (Any State → X via trigger; estados no-loop chainan a un destino contextual
    según ChainOverrides, o a Idle1 default si no hay override)
    │  Asignado al Animator del PREFAB ROOT (no de SK_Curator_Aline child)
    ▼
Runtime: Vivify SetAnimatorProperty con id=prefab_id + properties[].id=trigger_name
```

## Setup once-per-character (orden estricto)

1. **Importar `.psa` a Blender** — abre `Aline_project.blend`, ejecuta `scripts/blender/import_all_psa.py`. Idempotente. El addon DarklightGames PSK/PSA crea actions en `bpy.data.actions` pero NO auto-linkea al armature: el script setea `arm.animation_data.action` manualmente.

2. **Exportar FBX armature-only con animaciones** — ejecuta `scripts/blender/export_anims_fbx.py`. Salida en `VivifyTemplate/Assets/Aline/Animations/Aline_Anims.fbx` (~185 MB, ~150 s de export). El script:
   - Strippa scale fcurves de las actions (las `.psa` traen scale=1 constante que no aporta).
   - Crea un NLA track por action en el armature, **strip unmuted**, named `"<ARMATURE_NAME>|<action.name>"`.
   - Exporta con `bake_anim_use_nla_strips=True`, `bake_anim_use_all_actions=False`.

3. **Esperar el reimport en Unity** — la primera vez ~2 min (FBX de 185 MB). El `AlineAnimsImporter` (AssetPostprocessor) corre solo:
   - `OnPreprocessModel` → `preserveHierarchy = true` (impide que Unity colapse el nodo `SK_Curator_Aline`).
   - `OnPreprocessAnimation`:
     - Marca `loopTime = true` en los idles canónicos (`LoopingSuffixes`).
     - Para clips con motion horizontal real (`XzRootMotionSuffixes`: `DashIn-Idle1`, `DashOut-Idle2`, `DefaultSlot`, `DefaultSlot (1)`) setea `lockRootPositionXZ = false` y `keepOriginalPositionXZ = false` para que Unity extraiga el delta XZ como root motion. El resto de clips quedan con XZ baked en pose (default conservador para idles y transiciones).

4. **Configurar avatar manual una vez**:
   - `Aline.fbx` (mesh+rig): Animation Type = `Generic`, Avatar Definition = `Create From This Model`, Root node = `SK_Curator_Aline`. Apply.
   - `Aline_Anims.fbx`: Animation Type = `Generic`, Avatar Definition = `Copy From Other Avatar` → `AlineAvatar` (sub-asset del Aline.fbx). Apply.

5. **Generar el AnimatorController** — menu `Tools > Aline > Build Animator Controller`. Idempotente (borra y recrea). 26 estados + 26 triggers (`Idle1`, `Skill1`, …, sin prefijo `Paintress_`). Default = `Idle1`. Ver "Patrón del AnimatorController" más abajo para los chain-overrides aplicados.

6. **Animator en el prefab** — el component `Animator` vive en el prefab root (`aline.prefab` raíz), NO en el child `SK_Curator_Aline`. Avatar = `AlineAvatar`, Controller = `Aline_AC`. **`Apply Root Motion = ON`** si tienes clips con `XzRootMotionSuffixes` y quieres que Aline se traslade de verdad (paso 3 del importer); si está OFF, los clips de DashIn/DashOut harán "snap-back" al terminar.

   > **Nota (2026-05-01):** la regen del controller borra el `.controller` y crea uno nuevo con GUID nuevo. Eso rompe la referencia del Animator del prefab al controller. Tras cada regen toca re-asignar `Aline_AC` al campo Controller del Animator y guardar el prefab. Pendiente: hacer la regen idempotente preservando GUID.

7. **Verificar runtime** — abre el prefab en escena, dale al play del Animator (Window > Animation > Animator), o samplea programáticamente:

   ```csharp
   // En execute_code del unity-mcp:
   var clip = ...; // Skill1
   clip.SampleAnimation(prefabInstance, clip.length * 0.5f);
   // Los bones de SK_Curator_Aline/root/pelvis/... deben tener localRotation distinta de la rest pose.
   ```

8. **Disparar desde el `.dat`** — añade un evento `SetAnimatorProperty` con `properties[].id` = trigger name (ej. `"Idle1"`, `"Skill1"`).

## Tools del flujo

| File | Qué hace | Cuándo correr |
|---|---|---|
| `scripts/blender/import_all_psa.py` | Batch-importa `.psa` de `Sandfall/.../Animation/` como Blender actions vía la API del addon DarklightGames PSK/PSA. Idempotente. | Una vez al inicio. Si añades `.psa` nuevos. |
| `scripts/blender/export_anims_fbx.py` | Exporta `SK_Curator_Aline` armature-only con todas las actions a `Aline_Anims.fbx` vía NLA strips unmuted. Idempotente (recrea NLA tracks si no existen). | Cada vez que cambien las actions en Blender. |
| `Assets/Aline/Editor/AlineAnimsImporter.cs` | AssetPostprocessor del FBX: setea `preserveHierarchy=true` y `loopTime=true` en idles canónicos. | Auto al reimportar el FBX. |
| `Assets/Aline/Editor/BuildAlineAnimator.cs` | Menu `Tools > Aline > Build Animator Controller`. Lee los clips del FBX, regenera `Aline_AC.controller` (idempotente). 1 estado + 1 trigger por clip; `Any State → X`; auto-return a `Idle1` al exit time para no-loops. | Tras el reimport del FBX. |
| `Assets/Aline/Editor/InspectAlineClips.cs` | Diagnóstico. Menu `Tools > Aline > Inspect Clip Curves (Idle1 / Summary all)`. Vuelca curves de un clip a Console. | Cuando algo va mal y necesitas ver fcurves. |

## Reglas no negociables

1. **NLA strips UNMUTED** en el armature antes del export FBX. El exporter de Blender con `bake_anim_use_nla_strips=True` **salta strips muted silenciosamente** (FBX sale en 0.1s con 0.4 MB y cero AnimCurves en vez de 150s y 185 MB). El script ya lo hace bien — no toques `track.mute` a `True`.

2. **Strip name = `"<ARMATURE_NAME>|<action.name>"`**. Con NLA bake, el nombre del strip se vuelve el take name del FBX. El `.meta` cachea `clipAnimations` con `takeName` que sigue esa convención. Si exportas con strips llamados solo `action.name`, Unity loguea `Split Animation Take Not Found 'SK_Curator_Aline|...'` y descarta los per-clip overrides (loopTime, etc.).

3. **`preserveHierarchy = true`** en el FBX importer de `Aline_Anims.fbx`. El export de Blender colapsa el armature object en la raíz del FBX cuando es armature-only (sin mesh hijo). Unity, además, colapsa nodos transform de un solo hijo en la raíz por defecto. Sin este flag, `SK_Curator_Aline` desaparece de la jerarquía → clip paths salen como `root/...` sin prefijo → preview del FBX inspector rompe (T-pose) cuando usa `Aline.fbx` como modelo. Lo aplica `AlineAnimsImporter.OnPreprocessModel`.

4. **Animator en el PREFAB ROOT, no en `SK_Curator_Aline` child**. Con `preserveHierarchy=true` las clip paths empiezan por `SK_Curator_Aline/...` y matchean la jerarquía del prefab desde la raíz. Las scale curves que el FBX exporter mete por defecto van a path `SK_Curator_Aline` (no a path `<root>`), aplicadas al GO `SK_Curator_Aline` (scale=1) → no-op. El root del prefab conserva su `localScale: 0.01` baked.

5. **`Aline.fbx` (mesh)**: Rig = Generic, Avatar = `Create From This Model`, Root node = `SK_Curator_Aline`.

6. **`Aline_Anims.fbx` (animaciones)**: Rig = Generic, Avatar = `Copy From Other Avatar` → `AlineAvatar` del `Aline.fbx`. Sin esto, los clips no cuelgan correctamente del rig en runtime.

7. **Naming de triggers**: nombre del clip menos prefijo `Paintress_`. Ej: clip `SK_Curator_Aline|Paintress_Idle1` → trigger `Idle1`. Eso va en el `properties[].id` del evento `SetAnimatorProperty`.

8. **`Aline_Anims.fbx` está gitignored**. Solo se versiona el `.meta`. Re-export desde Blender es la forma de regenerarlo — no esperes recuperarlo desde git.

## Evento Vivify para disparar animaciones

```json
{
  "_time": 16,
  "_type": "SetAnimatorProperty",
  "_data": {
    "id": "alineMain",
    "properties": [
      { "id": "Skill1", "type": "Trigger", "value": true }
    ]
  }
}
```

`id` = el id del `InstantiatePrefab` que metió a Aline en escena. `properties[].id` = el nombre del trigger del Animator. Vivify busca todos los Animator components dentro del prefab con ese id y aplica.

Ver [`docs/heckdocs-main/docs/vivify/events.md`](../../../docs/heckdocs-main/docs/vivify/events.md) para Bool/Float/Integer.

**Regla operativa:** **no dispares un trigger del estado actual de Aline.** El AnyState transition tiene `canTransitionToSelf = false`, así que el trigger no consume — queda queued. Cuando Aline pasa a OTRO estado por un trigger posterior, el queued se dispara también y aborta el clip recién entrado tras 4-5 frames. Síntoma: "la anim se mueve un poco y vuelve a idle". La default state ya cubre el inicio en Idle1 — no necesita re-disparo. No re-dispares Idle2 si ya está flotando por chain-override de DashOut. Etc.

## Patrón del AnimatorController

Generado por [`Assets/Aline/Editor/BuildAlineAnimator.cs`](../../../VivifyTemplate/Assets/Aline/Editor/BuildAlineAnimator.cs). Tres reglas que dictan cómo encadena cada estado:

1. **`Any State → estado` por trigger** (todos los 26 triggers). Blend `duration = 0.1f`, `hasExitTime = false`, `canTransitionToSelf = false`. El blend de 0.1s suaviza mismatches de pose entre clips no relacionados; hard cut (0) deja saltos visibles, blend más largo introduce sprints raros.

2. **Chain-override al exit time (95%) para no-loops**, vía la dict `ChainOverrides`:
   - `Paintress_Idle1_to_idle2_transition` → `Paintress_Idle2`
   - `Paintress_Idle2_to_idle3_transition` → `Paintress_Idle3`
   - `Paintress_DashOut-Idle2` → `Paintress_Idle2`
   - `Paintress_DashIn-Idle1` → `Paintress_Idle1` (vuelve a default tras el dash, pose neutra)
   - El resto de no-loops sin override caen al `defaultState` (Idle1) con `duration = 0.15f`.

3. **`NoFallback`** (HashSet). Estados que se quedan en su última frame y NO chainan a nada. Vacío por defecto. Útil si algún día un clip termina en pose que NO debería volver a idle (p.ej. una pose final de impacto que se queda colgada hasta el siguiente trigger).

Si añades un clip cuyo destino canónico no es Idle1 (p.ej. una skill de fase 2 que debería volver a Idle2 flotando), edita `ChainOverrides` en `BuildAlineAnimator.cs` añadiendo `{ "Paintress_NewSkill", "Paintress_Idle2" }`. Regenera vía `Tools > Aline > Build Animator Controller`.

## Locomotion sandbox

`beatsaber-map/EasyStandard.dat` es la difficulty Easy del mapa, dedicada a probar animaciones aisladas (sin VFX, sin notas, sin audio significativo). Su `_customEvents` tiene un `InstantiatePrefab` de Aline + una cadena de `SetAnimatorProperty` que recorre los idles y transiciones canónicos a 100 BPM. El `Info.dat` la registra junto a `ExpertPlusStandard.dat`.

Cuándo usarla:
- Validar un cambio en `BuildAlineAnimator.cs` (regenerar controller + ver si las transiciones encadenan en BS).
- Validar un cambio en `AlineAnimsImporter.cs` (re-importar FBX + ver si los clips se comportan distinto).
- Probar un trigger nuevo aislado antes de meterlo en un prototipo de familia.

Cómo usarla: `Ctrl+R` en BS recarga los `.dat` (no el bundle — para un cambio de bundle hay que F5 desde Unity). Lanza el mapa Test, selecciona difficulty Easy. Sin VFX ni notas, lo único que pasa es Aline ejecutando la cadena.

Editar `EasyStandard.dat` directamente para añadir/quitar triggers de prueba. **No commitear cambios de prueba al `.dat`** — vive bajo la junction y no se versiona, lo cual es bueno para sandbox pero también significa que si quieres preservar un setup de test específico, hay que copiar el `.dat` a `docs/map-snapshots/`.

## Root motion para clips con desplazamiento

Algunos clips (DashIn-Idle1, DashOut-Idle2 y aliases) llevan motion horizontal: Aline se aproxima al jugador, golpea, retrocede. Si el motion vive como **root delta** en el FBX, Unity puede extraerlo y trasladar el GameObject de verdad. Si vive **baked en bones internos** (pelvis/spine sin que el root bone tenga curve de posición), la mesh se ve moverse pero el GO no — y al terminar el clip, los bones vuelven a neutral y la mesh "salta" de vuelta al GO.

**Estado actual (2026-05-01):** el `AlineAnimsImporter` está configurado para extraer XZ root motion en los 4 clips con motion (`XzRootMotionSuffixes`), y el flujo asume `Apply Root Motion = ON` en el Animator. Pero los `.psa` actuales tienen el motion baked en bones internos, no en root, así que la extracción no produce delta y Aline sigue snapping. **Pendiente:** re-export desde Blender con root motion canónico en el bone raíz. Ver paso 2.5 de `NEXT_STEPS.md`.

Cómo verificar si un clip tiene root motion extraíble:
- Selecciona `Aline_Anims.fbx` en Project. Inspector → tab Animation → click en el clip.
- En el panel inferior busca el indicador de "Average Velocity". Si > 0 en X o Z, hay root motion en ese eje.
- 0 en todos los ejes pese a motion visible = motion baked en bones internos, no extraíble.

## Caminos cerrados (no perder tiempo aquí)

Cosas que parecen razonables pero ya descartadas con coste de debugging — documentadas para que el siguiente no las repita.

### NO usar `AnimateTrack` con `_offsetPosition` sobre tracks Vivify-prefab

Probado: el evento se procesa silenciosamente (no errora, no logea) y **no afecta a la posición** del prefab instanciado. Posiblemente Heck-AnimateTrack en V2 espera tracks de notas, y la propiedad `_offsetPosition` no se aplica al track parent que crea Vivify para el prefab. **Comportamiento documentado en heckdocs `properties.md` aplica a notas, no a Vivify-prefabs.**

### NO usar `AnimateTrack` con `_position` para gestionar la posición de Aline cross-clip

Probado: `_position` SÍ afecta al track Vivify-prefab (test de elevación lo confirmó), pero las unidades no matchean las del `position` de `InstantiatePrefab`. World [0,1,8] del InstantiatePrefab no equivale a `_position` [0,1,8] ni a [0, 1.667, 13.333] (lane equivalent). Cualquier valor probado introduce teleports al inicio o al final de cada AnimateTrack. Encima, gestionar la posición clip-a-clip por compensación se vuelve insostenible al añadir clips intermedios — cada nuevo clip suma un nivel más de coordinación, las compensaciones son cumulativas. **El camino correcto es root motion (FBX importer + Apply Root Motion ON), no compensación AnimateTrack.**

### NO esperar que `Apply Root Motion = ON` resuelva el snap-back por sí solo

Probado: marcar el toggle en el Animator del prefab no produce delta si los clips tienen el motion baked en pose (default Unity para Generic). Hay que ANTES configurar el FBX importer para extraer (`lockRootPositionXZ = false` + `keepOriginalPositionXZ = false`). Y aún así, depende de que el FBX TENGA el motion en el root bone — si el `.psa` lo distribuyó en pelvis/spine, no hay nada que extraer.

### NO regenerar el `.controller` sin re-asignar el controller al prefab

`AssetDatabase.DeleteAsset` + `CreateAnimatorControllerAtPath` borra el `.meta` y crea GUID nuevo. La referencia del prefab al `Aline_AC` queda rota. Síntoma: tras regen, Aline aparece en T-pose en BS porque el Animator no tiene controller. **Solución temporal:** tras cada regen, abrir `aline.prefab`, arrastrar `Aline_AC` al campo Controller, guardar. **Solución pendiente:** hacer `BuildAlineAnimator.cs` idempotente preservando GUID (limpia el contenido en lugar de borrar el asset).

### NO disparar triggers redundantes desde el `.dat`

Si Aline ya está en Idle1 (default state) y disparas el trigger `Idle1`, no transiciona (`canTransitionToSelf = false`). El trigger queda queued y se dispara cuando Aline cambia a otro estado, abortando ese estado tras 4-5 frames. Mismo con cualquier otro trigger redundante. **Default state cubre el arranque, chain-overrides cubren los destinos canónicos** — solo dispara triggers que representan transiciones de verdad.

## Gotchas conocidos

### El FBX exporter de Blender salta NLA strips muted

Síntoma: export termina en 0.1s y FBX sale de 0.4 MB sin AnimCurves. `Aline_Anims.fbx` Inspector → tab Animation → "No animation data available in this model" o lista de takes pero todos vacíos.

**Causa**: `bake_anim_use_nla_strips=True` ignora silenciosamente los tracks con `mute=True`. La asunción "muted = no blend en runtime, sí exportable" es falsa.

**Fix**: el script `export_anims_fbx.py` crea los strips con `track.mute = False`. Si manualmente añades NLA tracks, déjalos unmuted. Overlapping en la timeline da igual — el exporter bakea cada strip por su frame range.

### El addon PSK/PSA no auto-linkea la action al armature

Tras `import_psa(...)` la action se crea en `bpy.data.actions` pero `arm.animation_data.action` queda en `None`. Hay que setear manualmente:

```python
arm.animation_data.action = bpy.data.actions["Paintress_Idle1"]
```

El batch import lo hace por todas. Si lo haces manual, no olvides este paso.

### Unity 2019.4 colapsa nodos top-level con un solo hijo

Síntoma: `Aline_Anims.fbx` Inspector muestra clips, pero la preview anima al modelo en T-pose. SampleAnimation directamente sobre el rig funciona; preview no.

**Causa**: el FBX que exporta Blender en modo armature-only no preserva el nodo `SK_Curator_Aline` (el armature object colapsa con su único hijo `root`, la pose root bone). Encima Unity, con `preserveHierarchy=false` (default), colapsa también nodos top-level con un solo hijo. Resultado: clip paths empiezan por `root/...` (sin prefijo `SK_Curator_Aline`), pero el preview del FBX inspector usa `Aline.fbx` como modelo (vía avatar source), cuya jerarquía es `<top>/SK_Curator_Aline/root/...` → mismatch → T-pose.

**Fix**: `preserveHierarchy = true` en `Aline_Anims.fbx` importer. Lo aplica `AlineAnimsImporter.OnPreprocessModel` automáticamente al importar.

### Unity 2019.4 NO tiene `AnimationUtility.SetEditorCurves` (plural)

Si vas a transformar curves de clips en un AssetPostprocessor (rewrite de paths, strip de bindings, etc.), **no itereres** `AnimationUtility.SetEditorCurve(clip, b, ...)` por cada binding: cada llamada hace dirty + revalidate del clip y para 4480 bindings × 26 clips son ~10 min de hang Unity entero, sin progress bar.

La API plural `SetEditorCurves` solo aparece en Unity 2020+. En 2019.4 las opciones son:

- **Hacer la transformación en Blender** antes del export (preferido — el exporter ya tiene el pipeline rápido).
- **`AnimationClip.ClearCurves()` + reconstrucción**: solo viable si no necesitas preservar curves originales.
- **Modificar el ModelImporter** (ej. `preserveHierarchy`, `clipAnimations[].loopTime`) en `OnPreprocess*` — esto es lo barato.

Si abres Unity y el FBX dice "A default asset was created because the asset importer crashed on it last time", probablemente metiste un per-curve loop en el postprocessor. Force-close Unity, revierte el postprocessor, reimporta.

### Inspector de Unity 2019.4 descarta toggles per-clip al cambiar de clip sin Apply

Síntoma: marcas Loop Time en Idle1, vas a Idle2, vuelves a Idle1 y se ha desmarcado.

**Fix**: el `AlineAnimsImporter.cs` setea `loopTime` programáticamente al importar usando una HashSet explícita de clips que deben loopear. No tocar el toggle a mano — si lo haces, el siguiente reimport te lo sobreescribe.

### Cambiar el Rig type en `Aline.fbx` resetea el Avatar Definition

Si en el Inspector cambias `Aline.fbx` Rig Animation Type entre None / Generic / Humanoid, el Avatar Definition se resetea a "No Avatar". El Animator del prefab queda con `m_Avatar` apuntando a un sub-asset que ya no existe.

**Fix**: Avatar Definition = "Create From This Model", Root node = `SK_Curator_Aline`, Apply. El avatar regenerado tiene el mismo fileID (9000000) y GUID (el del FBX), así que la referencia rota se restaura sola.

### Mismatch de rest pose entre `Aline.fbx` y `Aline_Anims.fbx`

Síntoma: clips se ven bien en preview de su FBX nativo, pero al aplicar a `aline.prefab` (cuya mesh viene de `Aline.fbx`) la mesh se distorsiona — bones moved a posiciones imposibles, fragmentos esparcidos.

**Causa**: Generic avatars en Unity NO retargetean — usan la jerarquía y rest pose del rig directamente. Si Aline_Anims (donde se autoraron los clips) y Aline.fbx (donde está la mesh) tienen rest poses ligeramente distintas, los clips escriben transforms del rig "ajeno" sobre el rig de la mesh.

**Fix**: ambos FBX deben venir del mismo `.blend` exportado con los mismos settings (axis, scale, addleafbones). Usar `Copy From Other Avatar` de Aline_Anims → Aline.fbx fuerza que los nombres de bones coincidan.

### Aline_Anims.fbx tarda mucho en importar (~2 min)

Tamaño 185 MB con 26 takes × 4480 curves × hasta 480 frames cada una. Es lo que es. Si añades un AssetPostprocessor que itere todas las curves (per-binding), multiplica por 5-10x el tiempo de import → cuelgues. Evitar manipulación per-curve en post-process; preferir fix en el FBX export desde Blender o en `ModelImporter` settings (preprocess).

## Estado actual del pipeline (2026-05-01)

✅ Import .psa → Blender (26 actions, addon manual fix)
✅ Export Blender → FBX (NLA strips unmuted, named con armature prefix, ~185 MB en ~150 s)
✅ Import FBX → Unity (`preserveHierarchy=true`, avatar copy, loopTime auto)
✅ Generación AnimatorController (26 estados + triggers + chain-overrides para destinos contextuales)
✅ Animator en prefab root, scale curves no-op (no hay 100x bug)
✅ Aline visible en BS a tamaño correcto, animaciones reproduciéndose
✅ Preview del FBX inspector animando con la mesh de Aline.fbx
✅ Locomotion sandbox (`EasyStandard.dat`) validado en BS: idles, transiciones, dashes, stuns encadenan limpio modulo el snap-back de DashIn/DashOut.
🟡 Root motion para clips con desplazamiento: importer configurado (`XzRootMotionSuffixes`), pero `.psa` actuales no exponen delta extraíble en root bone. Pendiente re-export Blender con root motion canónico para que DashIn/DashOut trasladen el GO.
