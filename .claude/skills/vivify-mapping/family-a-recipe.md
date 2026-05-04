# Recipe — Familia A (Indicator + Projectile Sequence)

Implementación reutilizable de un ataque familia A. Validado con Skill4 en `NormalStandard.dat` el 2026-05-04.

> **Cuándo aplicar este recipe:** un ataque donde Aline ejecuta una animación que lanza N proyectiles secuenciales sobre el jugador (Skill3, Skill4, futuras variantes). El jugador parry cada uno con un cubo nativo BS.
>
> **Cuándo NO aplicar:** ataques mele (B), AoE de un solo parry (F), cadenas multi-hit donde Aline genera el VFX en su propia mano (E). Familias diferentes, recetas diferentes.

## Modelo conceptual

Cada proyectil es una pareja **indicador + cubo**:

- **Indicador** = Vivify prefab (esfera semitransparente) que aparece en una posición fija "encima de Aline" durante una ventana de aviso (~10 beats), se hace visible con un pop animation, mantiene posición, y desaparece justo cuando dispara su cubo.
- **Cubo** = nota BS nativa con `definitePosition` que la mantiene "anclada" a la posición del indicador durante todo el aviso, y al `launch_beat` se mueve al jugador en `~2 beats`.

El cubo **es** el sistema de parry — cortable, scoreable. El indicador es solo telegraph visual; tras el `launch_beat` se reemplazará por partículas (polish pendiente).

## Inputs (parámetros por instancia del ataque)

| Parámetro | Tipo | Notas |
|---|---|---|
| `trigger_id` | string | Trigger del Animator (`Skill4`, `Skill3`, …) |
| `trigger_beat` | float | Beat al que se manda `SetAnimatorProperty` (== cuándo Aline empieza la animación) |
| `N` | int | Número de proyectiles (5-7 típico, dictado por la animación) |
| `spheres[]` | array de objects | Por proyectil i: `{world_pos: [x,y,z], spawn_beat, launch_beat}` |
| `travel_beats` | float | Cuántos beats tarda el cubo en llegar al jugador desde su `launch_beat` (default 2 = 1.2s @ BPM 100) |
| `sphere_scale` | float | Escala del prefab de indicador (default 1.5) |
| `attack_id` | string | `atk_a_NNN` para namespacing de tracks (ver families.md "Track namespacing") |

Constantes globales del ataque (no varían por instancia salvo experimento explícito):

| Constante | Valor | Por qué |
|---|---|---|
| `NJS` | 16 | Estándar Normal-difficulty BS |
| `noteJumpStartBeatOffset` | 13 | Da HJD ≈ 14 beats. Suficiente para que el cubo viva desde su sphere_spawn_beat hasta player_arrival sin clipping |
| `player_world_pos` | `[0, 1, 0]` | Centro pecho del jugador. En lane: `(1.5, 0, 0)` |
| `pop_scale_duration` | `0.015` (de lifetime) | Duración del pop animation (~0.34s @ HJD=14, BPM=100) |
| `pop_rotation_duration` | `0.020` (de lifetime) | Una vuelta CW; scale termina al 75% del giro |

## Constantes calibradas (lane ↔ world)

Validadas empíricamente con `scripts/build-calibration.ps1` (ver doc del script). **No re-tunear sin re-calibrar.**

```
LANE_UNIT_M       = 0.6   # 1 lane = 0.6 m
LANE_X_ZERO_WORLD = -0.9  # x=0 lane → x=-0.9 world
LANE_Y_ZERO_WORLD =  1.0  # y=0 lane → y=+1.0 world
```

### Conversión world → lane

```
lane_x = (world_x - LANE_X_ZERO_WORLD) / LANE_UNIT_M = (world_x + 0.9) / 0.6
lane_y = (world_y - LANE_Y_ZERO_WORLD) / LANE_UNIT_M = (world_y - 1.0) / 0.6
lane_z =  world_z                       / LANE_UNIT_M =  world_z       / 0.6
```

Lo invertido (lane → world) raramente hace falta — los inputs van en world, los outputs en lane.

## Cálculo del path normalizado (definitePosition)

El cubo tiene `b = sphere_spawn_beat` (en absolutos), HJD = 14 beats. Su tiempo normalizado va `[0, 1]` desde `b - HJD` hasta `b + HJD`. Time `0.5` = `b` = momento en que el sphere aparece (jump-in acaba aquí).

Para cada cubo i:

```
gap_i        = launch_beat[i] - spawn_beat[i]   # típicamente 10-12 beats, varía por cubo
fire_time_i  = 0.5 + gap_i / (2 * HJD) = 0.5 + gap_i / 28
arrival_time_i = fire_time_i + travel_beats / (2 * HJD)   # debe ser ≤ 1.0
```

> **Constraint clave:** `arrival_time_i ≤ 1.0`. Si falla, sube `noteJumpStartBeatOffset`. Para `gap_max + travel_beats <= 14` (con HJD=14) está OK. Si una instancia tiene gaps > 12 beats, replantear timing o subir HJD.

`pointDefinition` por cubo:

```json
"<attack_id>_cube_<i>_path": [
  [sphere_lane_x, sphere_lane_y, sphere_lane_z, 0],
  [sphere_lane_x, sphere_lane_y, sphere_lane_z, fire_time_i],
  [player_lane_x, player_lane_y, player_lane_z, arrival_time_i],
  [player_lane_x, player_lane_y, player_lane_z, 1]
]
```

Hold en sphere desde `time=0` hasta `fire_time` (durante jump-in se queda en el primer keyframe igualmente — Heck no anima durante jump-in, ver "Dissolve trick" abajo). En `[fire_time, arrival_time]` sweep al jugador. Después se queda en player hasta despawn.

## Cálculo de rotación static-face-player

BS pone el "dot/arrow" del cubo en su cara **-Z local**. Para que el dot mire al jugador, el +Z del cubo apunta **AWAY del jugador**.

```
direction_away = sphere_world - player_world
direction_normalized = direction_away / |direction_away|

pitch (X) = -asin(direction_normalized.y)       # Unity ZXY extrinsic, positive X = look down
yaw   (Y) = atan2(direction_normalized.x, direction_normalized.z)
roll  (Z) = 0  (animado para el spin del pop, ver abajo)
```

Verificación: el cubo central (sphere directamente encima del jugador) sale con `yaw=0`. Los del lateral salen con yaw simétrico positivo/negativo.

## Spin animation del pop (localRotation Z)

El cubo aparece en `time=0.5` y rota una vuelta clockwise mientras escala. **Importante:** Heck/Unity usan quaternion slerp entre keyframes — una rotación 0→-360 con 2 keyframes se interpreta como "misma orientación" → no hay rotación visible. **Hay que partir el path en pasos ≤ 90°** para forzar el camino largo.

### Curva easeOut (deceleración progresiva)

Heck soporta `easing` per-keyframe (5to elemento), pero como cada easing aplica solo al segmento que termina en ese keyframe, conseguir un easeOut **global** sobre toda la rotación con multi-keyframe es lioso.

Approach limpio: **mantener interpolación lineal entre keyframes pero distribuir los timestamps según la shape de easeOutQuad** (`f(t) = 1 - (1-t)²`). Cada segmento sigue siendo 90° lineal, pero los segmentos van progresivamente más largos en tiempo → la velocidad efectiva decrece. Visualmente "fast start, slow end".

Para 4 segmentos de 90° sobre la ventana `time=0.5 → 0.520`:

| Rotación acumulada | Norm progress | t en window | Timestamp absoluto |
|---|---|---|---|
| 0° | 0% | 0 | 0.5000 |
| -90° | 25% | 0.134 | 0.5027 |
| -180° | 50% | 0.293 | 0.5059 |
| -270° | 75% | 0.500 | 0.5100 |
| -360° | 100% | 1.000 | 0.5200 |

```json
"localRotation": [
  [pitch, yaw,    0, 0],
  [pitch, yaw,    0, 0.5],     // jump-in usa primer kf — irrelevante porque cubo invisible aquí
  [pitch, yaw,  -90, 0.5027],  // 13.4% del tiempo, primer 25% de la rotación (rápido)
  [pitch, yaw, -180, 0.5059],
  [pitch, yaw, -270, 0.510],
  [pitch, yaw, -360, 0.520],   // último 25% toma la mitad del tiempo (lento)
  [pitch, yaw, -360, 1]        // hold final
]
```

X (pitch) e Y (yaw) constantes en todos los keyframes (= rotación static-face-player). Solo Z cambia (spin).

Para 2 vueltas: extender con 4 keyframes más (-450 → -540 → -630 → -720) usando los mismos timestamps escalados al doble de duración. O usar más keyframes (8 pasos de 90°) si se quiere shape de easeOut sobre la longitud completa.

Para suavizar la deceleración (eliminar los stutter visuales entre segmentos): aumentar a 8 keyframes (45° cada uno) con timestamps siguiendo la misma shape easeOutQuad. Los segmentos se vuelven más cortos pero la curva es más suave.

## Dissolve trick (ocultar el "primer viaje")

Sin esto, los cubes son visibles durante todo el NJS jump-in desde far Z (parecen "puntitos pequeños viajando" porque la scale curve los mantiene a `scale=0.1` o similar). Eso rompe el efecto de "aparecen materializándose en la sphere".

**Fix canónico (validado 2026-05-04 con cube swap):** primer punto de `scale` curve a `(0, 0, 0)`. Doc heck: durante el jump-in los objetos "strictly use the first point in the point definition" → cubes invisibles efectivamente porque `scale=0` colapsa los vértices al origen.

```json
"scale": [[0, 0, 0, 0], [0, 0, 0, 0.499], [1, 1, 1, 0.515], [1, 1, 1, 1]]
```

- NJS jump-in: usa primer punto `(0, 0, 0)` → invisible.
- `t=0..0.499`: scale=0 → invisible.
- `t=0.499..0.515`: pop scale 0→1 (sync con sphere spawn `t=0.5` y rotation curve `t=0.5..0.52`).
- `t=0.515..1`: scale=1 → visible toda la fase sphere hold + launch + despawn.

**Por qué no usar `dissolve` curve:** Vivify sí pasa `_Cutout` per-instance al shader del prefab, pero el valor está driven por proximidad al player (no por la `dissolve` curve). Si el shader implementa `clip(cutout)` con cualquier semántica, los cubes se ocultan justo al dispararse al player — opuesto a lo que queremos. Detalle del gotcha en skill [`vivify-materials`](../vivify-materials/SKILL.md) sección "Outline shader". `dissolve` y `dissolveArrow` curves se quedaron en el `.dat` del Skill4 actual pero **no aportan al efecto** y son removibles si se prefiere limpieza.

## Cube swap via `AssignObjectPrefab` (parte de la receta default)

El note BS default tiene su propia geometría con arrow/dot indicator que sufre `dissolveArrow` desync (`DisappearingArrowControllerBase` race condition documentada en source de NoodleExtensions: el controller vanilla machaca el valor que NE escribe, porque NE no patchea su LateUpdate).

**Fix permanente:** swap del visual del cube por un prefab propio sin geometría de arrow. Prefab canónico [`NoteCube.prefab`](../../../VivifyTemplate/Assets/Aline/Prefabs/projectiles/NoteCube.prefab) con shader [`Aline/Outline`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineOutline.shader). Receta del shader (inverted-hull + SPI + GPU instancing para saber color per-instance) en skill [`vivify-materials`](../vivify-materials/SKILL.md) sección "Outline shader". El prefab queda en `aline_bundle` y aplica globalmente al resto de notes BS por `track` (no afecta a notes fuera de los tracks listados en el evento).

Sources del bug original verificados: [Aeroluna/Heck — ObjectInitializer.cs](https://github.com/Aeroluna/Heck/blob/master/NoodleExtensions/HeckImplementation/ObjectInitializer.cs), [CutoutManager.cs](https://github.com/Aeroluna/Heck/blob/master/NoodleExtensions/Managers/CutoutManager.cs), [CutoutEffectPatches.cs](https://github.com/Aeroluna/Heck/blob/master/NoodleExtensions/HarmonyPatches/SmallFixes/CutoutEffectPatches.cs).

## Templates de eventos

### 1. Trigger animator (1 evento por ataque)

```json
{"b": <trigger_beat>, "t": "SetAnimatorProperty", "d": {
  "id": "alineMain",
  "properties": [{"id": "<trigger_id>", "type": "Trigger", "value": true}]
}}
```

### 2. AssignPathAnimation por cubo (N eventos, en `b=0`)

```json
{"b": 0, "t": "AssignPathAnimation", "d": {
  "track": "<attack_id>_cube_<i>",
  "duration": 0,
  "definitePosition": "<attack_id>_cube_<i>_path"
}}
```

### 3. Sphere spawn (N InstantiatePrefab)

```json
{"b": <spawn_beat[i]>, "t": "InstantiatePrefab", "d": {
  "id": "<attack_id>_sphere_<i>",
  "asset": "assets/aline/prefabs/projectiles/telegraphsphere.prefab",
  "position": [<sphere_world[i]>],
  "rotation": [0, 0, 0],
  "scale": [<sphere_scale>, <sphere_scale>, <sphere_scale>]
}}
```

### 4. Sphere despawn (N DestroyObject, en `launch_beat`)

```json
{"b": <launch_beat[i]>, "t": "DestroyObject", "d": {
  "id": "<attack_id>_sphere_<i>"
}}
```

### 5. Cubo BS nativo (N colorNotes, en `b = spawn_beat`)

```json
{
  "b": <spawn_beat[i]>,
  "x": 0, "y": 0, "c": 0, "d": 8,
  "customData": {
    "track": "<attack_id>_cube_<i>",
    "noteJumpMovementSpeed": 16,
    "noteJumpStartBeatOffset": 13,
    "disableNoteGravity": true,
    "disableNoteLook": true,
    "spawnEffect": false,
    "animation": {
      "dissolve":      [[0,0],[0,0.499],[1,0.5],[1,1]],
      "dissolveArrow": [[0,0],[0,0.499],[1,0.5],[1,1]],
      "scale":         [[0.1,0.1,0.1,0.5], [1,1,1,0.515], [1,1,1,1]],
      "localRotation": [[<pitch_i>,<yaw_i>,0,0],
                        [<pitch_i>,<yaw_i>,0,0.5],
                        [<pitch_i>,<yaw_i>,-90,0.5027],
                        [<pitch_i>,<yaw_i>,-180,0.5059],
                        [<pitch_i>,<yaw_i>,-270,0.510],
                        [<pitch_i>,<yaw_i>,-360,0.520],
                        [<pitch_i>,<yaw_i>,-360,1]]
    }
  }
}
```

### 6. pointDefinition por cubo (N entries en `customData.pointDefinitions`)

```json
"<attack_id>_cube_<i>_path": [
  [<sphere_lane_i_x>, <sphere_lane_i_y>, <sphere_lane_i_z>, 0],
  [<sphere_lane_i_x>, <sphere_lane_i_y>, <sphere_lane_i_z>, <fire_time_i>],
  [1.5, 0, 0, <arrival_time_i>],
  [1.5, 0, 0, 1]
]
```

> `c` (color) y `d` (cut direction) actualmente en `0, 8` (rojo, dot/any-direction). Cuando hagamos parry real, **alternar** `c` entre 0/1 por flow y elegir `d` según el ángulo de aproximación del cubo (8 ≠ direccional pero más permisivo; 0-7 fuerzan corte específico).

## Algoritmo paso a paso

1. **Recolectar inputs**: `trigger_id`, `trigger_beat`, `N`, `spheres[]` (con world_pos, spawn_beat, launch_beat por uno), `attack_id`.
2. **Verificar HJD constraint**: para todos los i, `(launch_beat[i] - spawn_beat[i]) + travel_beats <= 14`. Si falla, subir `noteJumpStartBeatOffset`.
3. **Por cada cubo i**:
   - Convertir `sphere_world[i]` → `sphere_lane[i]` con la fórmula calibrada.
   - Calcular `pitch_i, yaw_i` con la fórmula static-face-player (dirección AWAY del jugador).
   - Calcular `fire_time_i = 0.5 + (launch_beat[i] - spawn_beat[i]) / 28`.
   - Calcular `arrival_time_i = fire_time_i + travel_beats / 28`.
4. **Generar JSON**:
   - Trigger animator (template 1)
   - 7× AssignPathAnimation (template 2)
   - 7× sphere InstantiatePrefab (template 3)
   - 7× sphere DestroyObject (template 4)
   - 7× cube colorNote con localRotation/scale/dissolve completos (template 5)
   - 7× pointDefinition (template 6)
5. **Aplicar al `.dat`**: edit directo o via PowerShell con UTF-8 sin BOM (cuidar la gotcha de `ConvertTo-Json` con arrays vacíos — ver SKILL.md).
6. **Verificar**: `ConvertFrom-Json` round-trip + audit del count de eventos.
7. **Lanzar BS** en la difficulty correspondiente, con CustomNotes desactivado.

## Ejemplo completo (Skill4 actual)

Ver `beatsaber-map/NormalStandard.dat`. Inputs concretos:

- `trigger_id` = `Skill4`, `trigger_beat` = 4
- `N` = 7
- `spheres[]`:
  - i=0: world `(-3, 3, 8)`, spawn_beat 10.67, launch_beat 20.67
  - i=1: world `(-2.598, 4.5, 8)`, spawn_beat 12, launch_beat 22.34
  - i=2: world `(-1.5, 5.598, 8)`, spawn_beat 13.33, launch_beat 24
  - i=3: world `(0, 6, 8)`, spawn_beat 14.67, launch_beat 25.67
  - i=4: world `(1.5, 5.598, 8)`, spawn_beat 16, launch_beat 27.34
  - i=5: world `(2.598, 4.5, 8)`, spawn_beat 17.33, launch_beat 29
  - i=6: world `(3, 3, 8)`, spawn_beat 18.67, launch_beat 30.67
- `travel_beats` = 2
- `sphere_scale` = 1.5
- `attack_id` = `skill4` (single instance — no `_NNN` aún porque solo hay una)

Las posiciones forman un semicírculo centrado en `(0, 3, 8)` con radio 3m, ángulos 180°→0° (izquierda → derecha desde POV jugador). Los timings respetan step de 1.333 beats entre spawns y 1.667 entre launches.

## Variables a tunear vs no tocar

**Tunable por instancia:**
- `trigger_beat`, `spawn_beat[]`, `launch_beat[]`, `travel_beats`
- `sphere_world[]` (geometría del arc)
- `N`
- `sphere_scale`
- `attack_id`

**No tocar sin justificación:**
- `NJS = 16` (estándar)
- `offset = 13` (HJD ≈ 14, mínimo para gap max)
- `disableNoteGravity = true`, `disableNoteLook = true`, `spawnEffect = false`
- `dissolve` / `dissolveArrow` paths (la receta del dissolve trick)
- `scale` keyframes del pop (0.1 → 1 en time 0.5 → 0.515)
- `localRotation` Z keyframes del spin (0 → -360 en pasos de 90° con timestamps shape easeOutQuad — ver sección "Curva easeOut")
- Convención: `c=0, d=8` en uninteractable mode. Cuando se quite `uninteractable`, alternar `c` por flow y elegir `d` por dirección.

**Quitar cuando se haga polish:**
- (futuro) `uninteractable: true` está implícito (lo quitamos en la última iteración para que las notas afecten score, pero el cubo está fuera de saber-reach durante el aviso, no se cuenta como miss). Verificar al activar parry real.
- (futuro) `AssignObjectPrefab` para swap del visual y eliminar la inconsistencia del arrow.

## Polish pendiente (no en la receta, anotado)

- Partículas en sphere despawn (cuando el cubo se dispara la sphere "explota" en partículas).
- `AssignObjectPrefab` para swap del cube visual y resolver el dissolveArrow desync.
- Quitar `uninteractable` y configurar `c`/`d` para parry real puntuable.
- Tunear velocidad de disparo (`travel_beats` más bajo para más intenso).
