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
   (Any State → X via trigger, auto-return a Idle1 al exit time para no-loops)
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
   - `OnPreprocessAnimation` → marca `loopTime = true` en los idles canónicos.

4. **Configurar avatar manual una vez**:
   - `Aline.fbx` (mesh+rig): Animation Type = `Generic`, Avatar Definition = `Create From This Model`, Root node = `SK_Curator_Aline`. Apply.
   - `Aline_Anims.fbx`: Animation Type = `Generic`, Avatar Definition = `Copy From Other Avatar` → `AlineAvatar` (sub-asset del Aline.fbx). Apply.

5. **Generar el AnimatorController** — menu `Tools > Aline > Build Animator Controller`. Idempotente (borra y recrea). 26 estados + 26 triggers (`Idle1`, `Skill1`, …, sin prefijo `Paintress_`). Default = `Idle1`.

6. **Animator en el prefab** — el component `Animator` vive en el prefab root (`aline.prefab` raíz), NO en el child `SK_Curator_Aline`. Avatar = `AlineAvatar`, Controller = `Aline_AC`.

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
✅ Generación AnimatorController (26 estados + triggers)
✅ Animator en prefab root, scale curves no-op (no hay 100x bug)
✅ Aline visible en BS a tamaño correcto, animaciones reproduciéndose
✅ Preview del FBX inspector animando con la mesh de Aline.fbx
