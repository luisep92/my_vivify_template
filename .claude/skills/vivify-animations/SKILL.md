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
    │  scripts/blender/synthesize_root_motion.py
    │     - solo para clips con desplazamiento (DashIn-Idle1, DashIn-Idle2,
    │       DashOut-Idle1, DashOut-Idle2, DefaultSlot/.001): mueve el motion
    │       forward de pose.bones["root"] al armature object con axis remap
    │       correcto, y normaliza frame 0 a (0,0,0) por axis para evitar
    │       discontinuidades cross-clip. Idempotente, marca cada action procesada
    │       con custom property '_root_motion_synthesized'.
    │  scripts/blender/export_anims_fbx.py
    │     - strip scale fcurves (idempotente, las .psa traen scale=1 que no aporta)
    │     - push cada action a su NLA track UNMUTED, strip name = "<armature>|<action>"
    │     - export ARMATURE only, takes vía bake_anim_use_nla_strips=True
    ▼
Aline_Anims.fbx  (~185 MB, gitignored, .meta sí versionado)
    │  Unity FBX importer + AlineAnimsImporter:
    │     - preserveHierarchy=true  (mantiene SK_Curator_Aline como GO nombrado)
    │     - motionNodeName="SK_Curator_Aline" (motion live en location del top GO,
    │       Unity lo extrae automáticamente como root motion del clip)
    │     - loopTime=true en idles canónicos (workaround del Inspector bug 2019.4)
    │     - lockRootPositionXZ=false + keepOriginalPositionXZ=false + keepOriginalPositionY=false
    │       en clips con desplazamiento (XzRootMotionSuffixes: DashIn-Idle1/2,
    │       DashOut-Idle1/2, DefaultSlot/.001)
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

2. **Sintetizar root motion en clips con desplazamiento** — ejecuta `scripts/blender/synthesize_root_motion.py`. Solo aplica a `Paintress_DashIn-Idle1`, `Paintress_DashOut-Idle2`, `DefaultSlot`, `DefaultSlot.001`. Mueve `pose.bones["root"].location` al armature object con axis remap (Y bone → Z object negated; ver "Root motion para clips con desplazamiento" más abajo para el porqué). Idempotente: marca cada action procesada con custom property `_root_motion_synthesized`, detecta versiones anteriores del axis-mapping y des-aplica antes de re-aplicar. Si añades nuevos clips con motion, agrega su nombre a `TARGET_ACTIONS`.

3. **Exportar FBX armature-only con animaciones** — ejecuta `scripts/blender/export_anims_fbx.py`. Salida en `VivifyTemplate/Assets/Aline/Animations/Aline_Anims.fbx` (~185 MB, ~150 s de export). El script:
   - Strippa scale fcurves de las actions (las `.psa` traen scale=1 constante que no aporta).
   - Crea un NLA track por action en el armature, **strip unmuted**, named `"<ARMATURE_NAME>|<action.name>"`.
   - Exporta con `bake_anim_use_nla_strips=True`, `bake_anim_use_all_actions=False`.

4. **Esperar el reimport en Unity** — la primera vez ~2 min (FBX de 185 MB). El `AlineAnimsImporter` (AssetPostprocessor) corre solo:
   - `OnPreprocessModel` → `preserveHierarchy = true` (impide que Unity colapse el nodo `SK_Curator_Aline`).
   - `OnPreprocessAnimation`:
     - Setea `motionNodeName = "SK_Curator_Aline"` para que Unity trate el motion del top GO como root motion (sin esto `averageSpeed=0`).
     - Marca `loopTime = true` en los idles canónicos (`LoopingSuffixes`).
     - Para clips con motion horizontal real (`XzRootMotionSuffixes`: `DashIn-Idle1`, `DashOut-Idle2`, `DefaultSlot`, `DefaultSlot (1)`) setea `lockRootPositionXZ=false`, `keepOriginalPositionXZ=false` y `keepOriginalPositionY=false` para que Unity desbakeie XZ e Y y extraiga el delta como root motion. El resto de clips quedan con motion baked en pose (default conservador para idles y transiciones, donde no hay desplazamiento).

5. **Configurar avatar manual una vez**:
   - `Aline.fbx` (mesh+rig): Animation Type = `Generic`, Avatar Definition = `Create From This Model`, Root node = `SK_Curator_Aline`. Apply.
   - `Aline_Anims.fbx`: Animation Type = `Generic`, Avatar Definition = `Copy From Other Avatar` → `AlineAvatar` (sub-asset del Aline.fbx). Apply.

6. **Generar el AnimatorController** — menu `Tools > Aline > Build Animator Controller`. Idempotente (borra y recrea). 26 estados + 26 triggers (`Idle1`, `Skill1`, …, sin prefijo `Paintress_`). Default = `Idle1`. Ver "Patrón del AnimatorController" más abajo para los chain-overrides aplicados.

7. **Animator en el prefab** — el component `Animator` vive en el prefab root (`aline.prefab` raíz), NO en el child `SK_Curator_Aline`. Avatar = `AlineAvatar`, Controller = `Aline_AC`. **`Apply Root Motion = ON`** para que los clips con `XzRootMotionSuffixes` trasladen el GO de verdad. Si está OFF, los clips de DashIn/DashOut harán "snap-back" al terminar.

   > **Nota (2026-05-01):** la regen del controller borra el `.controller` y crea uno nuevo con GUID nuevo. Eso rompe la referencia del Animator del prefab al controller. Tras cada regen toca re-asignar `Aline_AC` al campo Controller del Animator y guardar el prefab. Pendiente: hacer la regen idempotente preservando GUID.

8. **Verificar runtime** — abre el prefab en escena, dale al play del Animator (Window > Animation > Animator), o samplea programáticamente:

   ```csharp
   // En execute_code del unity-mcp:
   var clip = ...; // Skill1
   clip.SampleAnimation(prefabInstance, clip.length * 0.5f);
   // Los bones de SK_Curator_Aline/root/pelvis/... deben tener localRotation distinta de la rest pose.
   ```

9. **Disparar desde el `.dat`** — añade un evento `SetAnimatorProperty` con `properties[].id` = trigger name (ej. `"Idle1"`, `"Skill1"`).

## Tools del flujo

| File | Qué hace | Cuándo correr |
|---|---|---|
| `scripts/blender/import_all_psa.py` | Batch-importa `.psa` de `Sandfall/.../Animation/` como Blender actions vía la API del addon DarklightGames PSK/PSA. Idempotente. | Una vez al inicio. Si añades `.psa` nuevos. |
| `scripts/blender/synthesize_root_motion.py` | Mueve motion del bone `root` al armature object con axis remap (Y bone → Z object negated) en clips con desplazamiento. Normaliza frame 0 a origen por axis para que todos los clips arranquen en `(0,0,0)` y no haya discontinuidad cross-clip. Idempotente, marca cada action procesada con custom property y modo del axis-mapping; detecta versiones antiguas y des-aplica antes de re-aplicar. | Tras importar `.psa` nuevas que tengan motion en el bone root. Si retocas el axis remap. |
| `scripts/blender/inspect_motion.py` | Diagnóstico read-only. Reporta location y rotation_quaternion por bone (root, pelvis, spine_01) y los top movers globales por excursión max-min. Útil para ver dónde vive el motion en una action. | Cuando un clip nuevo no se traslada en BS. |
| `scripts/blender/export_anims_fbx.py` | Exporta `SK_Curator_Aline` armature-only con todas las actions a `Aline_Anims.fbx` vía NLA strips unmuted. Idempotente (recrea NLA tracks si no existen). | Cada vez que cambien las actions en Blender (incluido tras `synthesize_root_motion.py`). |
| `Assets/Aline/Editor/AlineAnimsImporter.cs` | AssetPostprocessor del FBX: setea `preserveHierarchy=true`, `motionNodeName="SK_Curator_Aline"`, `loopTime=true` en idles canónicos y desbakea XZ+Y en clips con motion. | Auto al reimportar el FBX. |
| `Assets/Aline/Editor/BuildAlineAnimator.cs` | Menu `Tools > Aline > Build Animator Controller`. Lee los clips del FBX, regenera `Aline_AC.controller` (idempotente). 1 estado + 1 trigger por clip; `Any State → X`; auto-return a `Idle1` al exit time para no-loops. | Tras el reimport del FBX. |
| `Assets/Aline/Editor/InspectAlineClips.cs` | Diagnóstico Unity-side. Menu `Tools > Aline > Inspect Clip Curves (Idle1 / Summary all)`. Vuelca curves de un clip a Console. | Cuando algo va mal y necesitas ver fcurves del clip ya importado. |

## Reglas no negociables

1. **NLA strips UNMUTED** en el armature antes del export FBX. El exporter de Blender con `bake_anim_use_nla_strips=True` **salta strips muted silenciosamente** (FBX sale en 0.1s con 0.4 MB y cero AnimCurves en vez de 150s y 185 MB). El script ya lo hace bien — no toques `track.mute` a `True`.

2. **Strip name = `"<ARMATURE_NAME>|<action.name>"`**. Con NLA bake, el nombre del strip se vuelve el take name del FBX. El `.meta` cachea `clipAnimations` con `takeName` que sigue esa convención. Si exportas con strips llamados solo `action.name`, Unity loguea `Split Animation Take Not Found 'SK_Curator_Aline|...'` y descarta los per-clip overrides (loopTime, etc.).

3. **`preserveHierarchy = true`** en el FBX importer de `Aline_Anims.fbx`. El export de Blender colapsa el armature object en la raíz del FBX cuando es armature-only (sin mesh hijo). Unity, además, colapsa nodos transform de un solo hijo en la raíz por defecto. Sin este flag, `SK_Curator_Aline` desaparece de la jerarquía → clip paths salen como `root/...` sin prefijo → preview del FBX inspector rompe (T-pose) cuando usa `Aline.fbx` como modelo. Lo aplica `AlineAnimsImporter.OnPreprocessModel`.

4. **Animator en el PREFAB ROOT, no en `SK_Curator_Aline` child**. Con `preserveHierarchy=true` las clip paths empiezan por `SK_Curator_Aline/...` y matchean la jerarquía del prefab desde la raíz. Las scale curves que el FBX exporter mete por defecto van a path `SK_Curator_Aline` (no a path `<root>`), aplicadas al GO `SK_Curator_Aline` (scale=1) → no-op. El root del prefab conserva su `localScale: 0.01` baked.

5. **`Aline.fbx` (mesh)**: Rig = Generic, Avatar = `Create From This Model`, Root node = `SK_Curator_Aline`.

6. **`Aline_Anims.fbx` (animaciones)**: Rig = Generic, Avatar = `Copy From Other Avatar` → `AlineAvatar` del `Aline.fbx`. Sin esto, los clips no cuelgan correctamente del rig en runtime.

7. **Naming de triggers**: nombre del clip menos prefijo `Paintress_`. Ej: clip `SK_Curator_Aline|Paintress_Idle1` → trigger `Idle1`. Eso va en el `properties[].id` del evento `SetAnimatorProperty`.

8. **`Aline_Anims.fbx` está gitignored**. Solo se versiona el `.meta`. Re-export desde Blender es la forma de regenerarlo — no esperes recuperarlo desde git.

## Evento Vivify para disparar animaciones (V3)

```json
{
  "b": 16,
  "t": "SetAnimatorProperty",
  "d": {
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

Algunos clips (DashIn-Idle1, DashOut-Idle2 y aliases) llevan motion horizontal: Aline se aproxima al jugador, golpea, retrocede. Para que el GameObject del prefab se traslade de verdad (no solo la mesh), el motion debe llegar al Animator como **root motion** y `Apply Root Motion = ON` en el componente.

### El issue concreto

Los `.psa` originales bakean el motion forward en `pose.bones["root"].location[1]` (Y bone-local del bone "root", forward del rig de Unreal). El FBX export de Blender lo expone correctamente como `m_LocalPosition.y` del path `SK_Curator_Aline/root` en Unity. **Pero Unity 2019.4 con `Generic + Copy From Other Avatar` no extrae el motion del bone "root" como root motion**, ni con `motionNodeName="root"`, ni reconstruyendo el avatar, ni desbakeando `keepOriginalPositionY`. `hasGenericRootTransform` se queda en `False` y `averageSpeed = (0,0,0)` siempre. Es una limitación del flujo Generic+CFOA, no un bug puntual: ver "Caminos cerrados" más abajo para los intentos exhaustos.

### El fix

Pre-procesar la action en Blender (`scripts/blender/synthesize_root_motion.py`) para mover el motion del bone "root" al **armature object** (top GO del rig). Cuando el motion vive en `location` del armature object, Unity sí lo extrae automáticamente como root motion con `motionNodeName="SK_Curator_Aline"` (lo aplica `AlineAnimsImporter.OnPreprocessAnimation`).

El script aplica un axis remap deliberado:

```
bone.location[0] (X bone-local, lateral)   → object.location[0] (X)            sign +1
bone.location[1] (Y bone-local, forward)   → object.location[2] (Z up Blender) sign -1
bone.location[2] (Z bone-local, vertical)  → object.location[1] (Y)            sign +1
```

El "swap Y↔Z + signo invertido en el axis 2" no es estético — es la composición exacta para que el motion termine en `+Z world` Unity (forward) tras dos transformaciones encadenadas:

1. **FBX exporter Blender→Unity** (`axis_up="Y"`, `axis_forward="-Z"`) intercambia Blender Y↔Z al cruzar formato. Lo que en Blender object es location.z aparece en Unity como `m_LocalPosition.y`; lo que era location.y aparece como `m_LocalPosition.z`.

2. **El armature object queda con rotation `(270°, 0, 0)` en Unity** (Z-up→Y-up requiere rotar -90° en X). Eso permuta los axes locales del GO: la Y local del SK_Curator_Aline en Unity apunta a `+Z world`, la Z local apunta a `-Y world`.

Sin axis remap (copia 1:1 Y bone→Y object) el motion termina en `-Y world` (Aline cae verticalmente). Con remap a Z object pero sin negar, termina en `-Z world` (Aline avanza en sentido contrario). Con el remap final (`Z object negated`), termina en `+Z world` (forward). Variables empíricas hasta validar — el axis transform encadenado no es intuitivo.

### Pipeline operativo

1. **Blender**: con las actions importadas vía `import_all_psa.py`, correr `synthesize_root_motion.py`. Idempotente: marca cada action procesada con custom property `_root_motion_synthesized` con el modo aplicado (`v5-bone-y-to-object-z-negated-normalized`); detecta versiones anteriores y des-aplica antes de re-aplicar.
2. **Blender**: re-export con `export_anims_fbx.py`.
3. **Unity**: el reimport del FBX dispara `AlineAnimsImporter`, que setea `motionNodeName = "SK_Curator_Aline"` y, por clip en `XzRootMotionSuffixes`, `lockRootPositionXZ=false + keepOriginalPositionXZ=false + keepOriginalPositionY=false`.
4. **Verificar**: `clip.averageSpeed` debería ser distinto de `(0,0,0)` para los 4 clips con motion. Para `DashIn-Idle1` da algo cercano a `(0, 0, ~+173)` (≈ 600 cm forward / 3.46 s). DashOut signo opuesto.
5. **Animator**: `Apply Root Motion = ON` ya está en el prefab. El root motion extraído se aplica al transform raíz `aline.prefab`, no al child `SK_Curator_Aline`.

### Cómo verificar si un clip tiene root motion extraíble

- En Unity: `clip.averageSpeed` por API (preview del FBX inspector tab Animation también lo muestra como "Average Velocity").
- Si todos los axes son `0` pese a motion visible en preview, no hay extracción. Investigar dónde vive el motion en Blender antes de tirar de configs Unity-side: `scripts/blender/inspect_motion.py` reporta motion por bone y per-axis (chequea object-level y bone-local en location y rotation_quaternion).

## Pose mismatch cross-clip: blend en Animator, no editar data

Si un clip A termina en pose distinta de la que el clip B inicia (típico: floating ↔ grounded entre dashes y idles), una transition con `duration = 0` muestra un teleport visible. Replicar el pattern de UE Montage "Blend Out duration" en el AnimatorController de Unity:

1. **Exit transition con `duration > 0`**: blend de N segundos hacia el target. Unity interpola las poses durante ese tiempo. Para transiciones "el clip termina en floating, target es grounded", arrancar en `duration = 0.2-0.3s`.

2. **`exitTime < 1.0`** si el clip tiene "tail" estático tras completar el motion: el blend arranca antes (ej. `exitTime = 0.7` → al 70% del clip), solapándose con los últimos frames del movimiento. Resultado visual: el aterrizaje ocurre DURANTE el dash, no después de que Aline llegue parada al destino. Sin esto el blend queda visible como un cambio de pose en el sitio.

3. **Entry blend (AnyState transition con `duration > 0`)** para amortiguar el snap al ENTRAR al state desde una pose mismatch (ej. trigger `DashOut-Idle1` desde Idle1 grounded — el dash arranca floating). Mismo concepto, otra dirección.

Validado 2026-05-02 con DashOut-Idle1 (state nuevo, exit a Idle1 grounded): `exitTime=0.7, duration=0.3` en exit + `duration=0.3` en AnyState entry disuelve un teleport de ~5cm UP/DOWN observable a ojo. La data del clip no se toca.

**Cuándo NO necesitas esto:** cuando target y source de la transición tienen pose compatible. DashOut-Idle2 (floating→floating) sigue con `duration = 0` default — no hay nada que blendear.

**Cuándo sí lo necesitas:** transiciones `Idle1 (grounded) → Idle1_to_idle2_transition (arranca grounded?)` también muestran snap si el clip de transition no arranca exacto donde Idle1 lo deja. Aplicado `duration=0.2` en su AnyState entry.

## Gotcha: `_Montage.psa` con seq name genérica "DefaultSlot"

Algunos `.psa` exportados de UE tienen como nombre interno de sequence "DefaultSlot" (el slot del montage), no el nombre del montage. Si dos `.psa` distintos comparten esa seq name, `import_all_psa.py` con `SKIP_EXISTING=True` importa el primero alfabéticamente y descarta el resto silenciosamente — pierdes animaciones sin warning visible.

Caso real (2026-05-02): `Paintress_DashIn-Idle1_Montage.psa` y `Paintress_DashOut-Idle1_Montage.psa` ambos con seq "DefaultSlot". Solo se importó el primero (DashIn) → DashOut-Idle1 ausente del FBX y del AnimatorController durante meses sin que se notara.

**Fix sistémico:** `import_all_psa.py` detecta seq names en `GENERIC_SEQ_NAMES` (set con "DefaultSlot") y las renombra usando el basename del `.psa` (sin `_Montage` suffix). Si el rename produciría conflicto con una action existente, deja el original con warning. Aplica antes del `SKIP_EXISTING` check, así garantiza unicidad sin tocar el `.psa` source.

**Cuándo añadir un nombre a `GENERIC_SEQ_NAMES`:** si encuentras `.psa` con seq name que NO matchea su nombre de archivo y sospechas colisión silenciosa. Síntoma: `summary.imported < count(.psa)` sin warnings claros.

Cuidado adicional: los `.psa` de UE Montages a veces traen bones de OTROS personajes (asset compartido multi-character). El addon avisa "missing N bones" — esperable, ignora si los nombres son de otra entidad (ej. "Aberration_*" en Aline). La animación de Aline se importa correctamente subset-matching.

## Hallazgo: `.psa` Montage vs no-Montage pueden ser idénticos en skeletal data

`Paintress_DashOut-Idle1_Montage.psa` y `Paintress_DashOut-Idle2.psa` aparecen como assets distintos en FModel pero contienen skeletal animation idéntica para Aline (verificado: 2604 fcurves, zero diferencia). El `.psa` solo lleva la pista skeletal; los Montage de UE wrappean además metadata (notifies, sections, blend rules, root motion mode) que NO viaja al `.psa`.

Implicación: la diferenciación grounded vs floating, blend de aterrizaje, IK de pies, etc. que el juego original hace en runtime con esos clips vivían en blueprints de UE, no en la animación. Replicarlos en Unity requiere reconstruir esos behaviors (típicamente vía blends en el AnimatorController, ver sección anterior). No esperar que duplicar el rip de un Montage dé una animación visualmente distinta del clip base.

## Caminos cerrados (no perder tiempo aquí)

Cosas que parecen razonables pero ya descartadas con coste de debugging — documentadas para que el siguiente no las repita.

### NO usar `AnimateTrack` con `_offsetPosition` sobre tracks Vivify-prefab

Probado: el evento se procesa silenciosamente (no errora, no logea) y **no afecta a la posición** del prefab instanciado. Posiblemente Heck-AnimateTrack en V2 espera tracks de notas, y la propiedad `_offsetPosition` no se aplica al track parent que crea Vivify para el prefab. **Comportamiento documentado en heckdocs `properties.md` aplica a notas, no a Vivify-prefabs.**

### NO usar `AnimateTrack` con `_position` para gestionar la posición de Aline cross-clip

Probado: `_position` SÍ afecta al track Vivify-prefab (test de elevación lo confirmó), pero las unidades no matchean las del `position` de `InstantiatePrefab`. World [0,1,8] del InstantiatePrefab no equivale a `_position` [0,1,8] ni a [0, 1.667, 13.333] (lane equivalent). Cualquier valor probado introduce teleports al inicio o al final de cada AnimateTrack. Encima, gestionar la posición clip-a-clip por compensación se vuelve insostenible al añadir clips intermedios — cada nuevo clip suma un nivel más de coordinación, las compensaciones son cumulativas. **El camino correcto es root motion (FBX importer + Apply Root Motion ON), no compensación AnimateTrack.**

### NO esperar que `Apply Root Motion = ON` resuelva el snap-back por sí solo

Probado: marcar el toggle en el Animator del prefab no produce delta si los clips tienen el motion baked en pose (default Unity para Generic). Hay que ANTES configurar el FBX importer para extraer (`lockRootPositionXZ=false`, `keepOriginalPositionXZ=false`, `keepOriginalPositionY=false`) Y que el motion live en location del armature object, no del bone interno (de eso se encarga `synthesize_root_motion.py`).

### NO intentar que Unity extraiga root motion del bone "root" en Generic + Copy From Other Avatar

Los `.psa` de Aline bakean el motion forward en `pose.bones["root"].location[1]`. El FBX exporter SÍ lo expone como `m_LocalPosition.y` del path `SK_Curator_Aline/root` en Unity (verificable con `AnimationUtility.GetCurveBindings`). Pero Unity 2019.4 con `animationType=Generic + avatarSetup=CopyFromOtherAvatar` no extrae motion de un bone interno como root motion, **da igual lo que metas en `motionNodeName`**.

Probado y descartado:
- `motionNodeName="root"` apuntando al bone (clip importer y avatar source).
- `motionNodeName="SK_Curator_Aline/root"` con path completo.
- Rebuild del avatar (avatarSetup → NoAvatar → CreateFromThisModel).
- `keepOriginalPositionY=false` por clip sin previo axis remap.

En todos los casos `clip.hasGenericRootTransform` se queda en `False` y `averageSpeed=(0,0,0)`. La extracción solo funciona cuando el motion vive en `location` del armature object (top GO del rig) y `motionNodeName="SK_Curator_Aline"`. Por eso `synthesize_root_motion.py` mueve el motion del bone al object antes del export FBX.

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

### Takes nuevos del FBX no aparecen en el AnimatorController tras añadir actions en Blender

Síntoma: añades una action nueva en Blender (vía import_all_psa o manual), re-exportas FBX, reimportas en Unity — pero el `BuildAlineAnimator` no genera state ni trigger para ese clip, y no aparece como sub-asset listable.

**Causa**: el `ModelImporter.clipAnimations` es un snapshot serializado en el `.meta`. Cuando un AssetPostprocessor lo manipula y lo guarda, queda congelado con esos N takes. Si añades take N+1 en el FBX, `defaultClipAnimations` (lectura viva del FBX) lo incluye, pero `clipAnimations` (snapshot persistido) no — el take nuevo nunca se importa.

**Fix**: el `AlineAnimsImporter.cs` arranca SIEMPRE desde `importer.defaultClipAnimations` (no desde `clipAnimations`). Los settings per-clip son deterministas según suffix, así que reset+re-aplicar cada import es seguro y garantiza que takes nuevos entren al pipeline automáticamente. Si quieres añadir tus propios overrides manuales en el inspector, no se respetarán — meter su lógica en el `AlineAnimsImporter` por suffix.

Caso conocido: `Paintress_DashIn-Idle2` se descubrió 2026-05-01 escondido — existía en Blender + FBX defaults, pero ni en el AnimatorController ni como AnimationClip importado. Tras el fix, los 26 takes se mantienen sincronizados.

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

## Estado actual del pipeline (2026-05-02)

✅ Import .psa → Blender (27 actions tras recovery de DashOut-Idle1_Montage; rename de seq names "DefaultSlot" para evitar colisión silenciosa)
✅ Synthesize root motion para clips con desplazamiento (Y bone → Z object negated, normalizado a frame 0 = origen)
✅ Export Blender → FBX (NLA strips unmuted, named con armature prefix, ~190 MB en ~160 s)
✅ Import FBX → Unity (`preserveHierarchy=true`, `motionNodeName="SK_Curator_Aline"`, avatar copy, loopTime auto, keepOriginalPositionY=false en clips de motion)
✅ Generación AnimatorController (27 estados + triggers + chain-overrides para destinos contextuales)
✅ Animator en prefab root, scale curves no-op (no hay 100x bug)
✅ Aline visible en BS a tamaño correcto, animaciones reproduciéndose
✅ Preview del FBX inspector animando con la mesh de Aline.fbx
✅ Locomotion sandbox (`EasyStandard.dat`) validado en BS: idles, transiciones, dashes, stuns encadenan limpio. DashIn traslada el GO forward (~6m world Z), DashOut lo devuelve. Sin snap-back. Apply Root Motion = ON activo en el Animator del prefab.
✅ Pose mismatch cross-clip absorbido vía blend en transitions (DashOut-Idle1: `exitTime=0.7, duration=0.3` exit + `duration=0.3` entry); el saltito Y de ~5cm al transitar grounded↔floating eliminado (2026-05-02).
