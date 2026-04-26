---
name: vivify-animations
description: Use when working on character animations for a Vivify bundle — pipeline `.psa` → Blender → FBX → Unity Animator → Vivify `SetAnimatorProperty`. Trigger when user mentions 'animaciones', 'animar', 'AnimatorController', 'Idle1', 'SetAnimatorProperty', 'psa', 'rig', 'bone', 'state machine', 'AnimationClip', 'fcurve' or sees errors like 'T-pose', 'modelo gigante', 'rest pose mismatch', 'scale curve'. Covers the canonical pipeline and the gotchas.
---

# Vivify Animations Workflow

Pipeline para animar personajes que viven en un bundle Vivify, desde dump de Unreal hasta runtime BS.

## Pipeline canónico

```
.psa de FModel  (Unreal animation file, varios por personaje)
    │  scripts/blender/import_all_psa.py  (Blender MCP o Scripting workspace)
    ▼
Blender actions  (una por .psa, en bpy.data.actions)
    │  scripts/blender/export_anims_fbx.py  (NLA tracks per action)
    ▼
Aline_Anims.fbx  (rig + N takes; gitignored, .meta sí versionado)
    │  Unity FBX importer + AlineAnimsImporter (loopTime auto)
    ▼
N AnimationClips como sub-assets del FBX
    │  Tools > Aline > Build Animator Controller
    ▼
Aline_AC.controller con state machine (Any State → X via trigger; auto-return a Idle1 al exit time)
    │  Asignado al Animator del HIJO `SK_Curator_Aline` (no del prefab root)
    ▼
Runtime: Vivify `SetAnimatorProperty` con id=prefab_id + properties[].id=trigger_name
```

## Tools del flujo

| File | Qué hace | Cuándo correr |
|---|---|---|
| `scripts/blender/import_all_psa.py` | Batch-importa todos los `.psa` de `Sandfall/.../Animation/` como Blender actions vía la API programática del addon DarklightGames PSK/PSA. Idempotente (skip si action existe). | Una vez al inicio. Si añades `.psa` nuevos. |
| `scripts/blender/export_anims_fbx.py` | Exporta el armature `SK_Curator_Aline` con todas las actions a `Aline_Anims.fbx`. Pushea actions a NLA tracks muted antes de exportar para forzar bake per-take. | Cada vez que cambien las actions en Blender. |
| `Assets/Aline/Editor/AlineAnimsImporter.cs` | AssetPostprocessor: marca `loopTime=true` en clips de idle (lista canónica explícita) al importar `Aline_Anims.fbx`. Workaround del Inspector bug de 2019.4. | Auto al reimportar el FBX. |
| `Assets/Aline/Editor/BuildAlineAnimator.cs` | Menu `Tools > Aline > Build Animator Controller`. Lee los clips del FBX, regenera `Aline_AC.controller` (idempotente, borra+recrea). 1 estado + 1 trigger por clip; `Any State → X`; auto-return a Idle1 para no-loops. | Tras el reimport del FBX. |
| `Assets/Aline/Editor/InspectAlineClips.cs` | Diagnóstico. Menu `Tools > Aline > Inspect Clip Curves (Idle1 / Summary all)`. Vuelca curves de un clip a Console. | Cuando algo va mal y necesitas ver fcurves. |

## Reglas no negociables

1. **El Animator vive en `SK_Curator_Aline`, NO en el prefab root**. Si lo pones en root, el `localScale: 0.01` baked se pisa por las scale curves constantes 1.0 que vienen en cada clip → modelo 100x grande. Ver [DECISIONES.md](../../../docs/DECISIONES.md).
2. **`Aline.fbx` (mesh) tiene Rig = Generic + Avatar = "Create From This Model"** con Root node = `SK_Curator_Aline`. El avatar generado se reusa en el Animator del prefab.
3. **`Aline_Anims.fbx` (animaciones) tiene Rig = Generic + Avatar = "Copy From Other Avatar"** apuntando al avatar de `Aline.fbx`. Sin esto, los clips no cuelgan correctamente del rig en runtime.
4. **Naming de triggers**: nombre del clip menos prefijo `Paintress_`. Ej: clip `SK_Curator_Aline|Paintress_Idle1` → trigger `Idle1`. Eso es lo que va en el `properties[].id` del evento `SetAnimatorProperty`.
5. **`Aline_Anims.fbx` está gitignored** (~185 MB binary). Solo se versiona el `.meta`. Re-export desde Blender es la forma de regenerarlo.

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

`id` = el id del `InstantiatePrefab` que metió a Aline en escena. `properties[].id` = el nombre del trigger del Animator (sin prefijo `Paintress_`). Vivify busca todos los Animator components dentro del prefab con ese id y aplica.

Ver [`docs/heckdocs-main/docs/vivify/events.md:299`](../../../docs/heckdocs-main/docs/vivify/events.md) para Bool/Float/Integer.

## Gotchas conocidos

### El addon PSK/PSA no auto-linkea la action al armature

Tras `import_psa(...)` la action se crea en `bpy.data.actions` pero `arm.animation_data.action` queda en `None`. Hay que setear manualmente:

```python
arm.animation_data.action = bpy.data.actions["Paintress_Idle1"]
```

El batch import lo hace por todas. Si lo haces manual, no olvides este paso.

### `bake_anim_use_all_actions` no itera fiable bajo MCP context

Cuando se ejecuta `bpy.ops.export_scene.fbx(..., bake_anim_use_all_actions=True)` desde Blender MCP (sin event loop interactivo), el exporter no parece switchear `armature.animation_data.action` correctamente entre actions, y bakea todas las takes con la action que estaba activa al inicio. **Workaround**: pushear cada action a su propio NLA track muted antes de exportar y usar `bake_anim_use_nla_strips=True, bake_anim_use_all_actions=False`. Implementado en `export_anims_fbx.py`.

**Status (2026-04-26):** este workaround tampoco está produciendo clips con datos no-identity. Pendiente diagnóstico — probar export desde la UI de Blender (no MCP) como control, o iterar manualmente set/export por action.

### Scale curves a path `<root>` rompen el prefab si el Animator está en root

Síntoma: modelo a tamaño 100x correcto en Beat Saber. El bake del FBX exporter de Blender mete una curva `m_LocalScale` (constante 1.0, 2 keys) en cada bone Y en path `<root>` por defecto, aunque la action fuente no tenga scale fcurves. Esa curva es no-op si el GameObject del Animator está a scale 1, pero si está a 0.01 (caso del prefab root para conversión cm→m), la pisa con 1 → 100x.

**Fix**: Animator en `SK_Curator_Aline` (scale 1), no en `aline` root (scale 0.01). Ver [DECISIONES.md](../../../docs/DECISIONES.md). Stripping a posteriori desde Unity es lento (~10 min hang con `AnimationUtility.SetEditorCurve(..., null) × 30k+`).

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

Tamaño 185 MB con 26 takes × 4480 curves × hasta 480 frames cada una. Es lo que es. Si añades un AssetPostprocessor que itere todas las curves (e.g. `AlineClipScaleStripper.cs` que escribió Claude antes), multiplica por 5-10x el tiempo de import → cuelgues de 10+ min. Evitar manipulación per-curve en post-process; preferir fix en el FBX export desde Blender.

## Estado actual del pipeline (2026-04-26)

✅ Import .psa → Blender (26 actions, addon manual fix)  
✅ Export Blender → FBX (NLA tracks workaround)  
✅ Import FBX → Unity (avatar copy, loopTime auto)  
✅ Generación AnimatorController (26 estados + triggers)  
✅ Animator placement arquitectural (en SK_Curator_Aline child)  
✅ Aline visible en BS a tamaño correcto en T-pose  
❌ **Clips llegan con fcurves identity — animaciones no se ven en runtime ni en preview**

Last mile: diagnosticar el bake. Ver [NEXT_STEPS.md#animaciones](../../../docs/NEXT_STEPS.md) y "Known issues".
