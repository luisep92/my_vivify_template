# Catálogo de familias de ataque

Este archivo formaliza los **contratos de ataque** del boss fight. Lo describe [PRODUCTO.md](../../../docs/PRODUCTO.md): cada habilidad de Aline es una **familia reutilizable** (prefab + animación + secuencia de eventos `.dat` + encoding del parry). Una vez una familia está definida y validada con un prototipo, instanciarla N veces en el mapa con timings/posiciones distintos es trabajo mecánico.

Si añades un ataque nuevo, **busca primero en este catálogo** una familia existente que encaje. Solo crea familia nueva (G, H...) si el ataque no encaja en ninguna existente.

## Tabla de identificación de triggers

Mapeo confirmado del Animator de Aline (`Aline_AC.controller`) a las familias de ataque. El nombre del **trigger** (parámetro del Animator) no lleva prefijo `Paintress_`; el **clip** sí lo lleva en algunos casos (artefacto del FBX importer).

| Trigger | Clip | Fase | Familia | Notas |
|---|---|---|---|---|
| `Idle1` | `Paintress_Idle1` | 1 | — | Idle base fase 1 (en suelo) |
| `Idle2` | `Paintress_Idle2` | 2 | — | Idle base fase 2 (flotando) |
| `Idle3` | `Paintress_Idle3` | 3 | — | Idle derrotada (en suelo) |
| `Idle1_to_idle2_transition` | `Paintress_Idle1_to_idle2_transition` | 1→2 | — | Transición entre idles |
| `Idle2_to_idle3_transition` | `Paintress_Idle2_to_Idle3_transition` | 2→3 | — | Cae de flotar al suelo |
| `Idle2_Stun` | `Paintress_Idle2_Stun` | 2 | — | Encorvada hacia adelante (stun) |
| `Idle_Countered` | `Paintress_Idle_Countered` | 2 | — | Reacción a impacto, encorvada hacia atrás |
| `DashIn-Idle1` | `Paintress_DashIn-Idle1` | 1 | **B** | Dash in + golpe mele |
| `DashOut-Idle2` | `Paintress_DashOut-Idle2` | 1 | B (post) | Retirada tras mele, devuelve a posición lejana |
| `DefaultSlot` | (sin prefijo) | 1 | B (alias) | Mismo clip que `DashIn-Idle1` |
| `DefaultSlot (1)` | (sin prefijo) | 1 | B (alias) | Mismo clip que `DashIn-Idle1` |
| `Skill1` | `Paintress_Skill1` | 1 | **E** | Aspavientos con explosiones (multi-hit chain con VFX explosivo) |
| `Skill2_Start` | `Paintress_Skill2_Start` | 1 | **F** (intro) | Aline se eleva, levanta brazo |
| `Skill2_Loop` | `Paintress_Skill2_Loop` | 1 | **F** (sustain) | Idle elevada, bola de energía cargando |
| `Skill2_End` | `Paintress_Skill2_End` | 1 | **F** (resolve) | Aline baja a tierra tras la explosión |
| `Skill3` | `Paintress_Skill3` | 1 | **A** | "Toca el harpa" + 3 piedras gigantes secuenciales |
| `Skill4` | `Paintress_Skill4` | 1 | **A** | "Toca el harpa" + giro + N proyectiles pequeños |
| `Skill5` | `Paintress_Skill5` | 1 | **B + modificador C** | Mele con distorsión (entorno gris al jugador) |
| `Skill6` | `Paintress_Skill6` | 1→2 | — | Transición narrativa: salta, flota, se arma con pincel grande, distorsión |
| `Skill7` | `Paintress_Skill7` | 2 | **E** | 5 golpes con dash-back-return, pincel grande |
| `Skill7_MaelleBurningCanvasVersion` | (variante) | 2 | E (variante) | Casi idéntico a `Skill7` visualmente |
| `Skill8` | `Paintress_Skill8` | 2 | **caso especial** | Aline gigante de fondo + bolas de energía + serie de golpes (ver "Diferidos" en NEXT_STEPS) |
| `Skill9` | (NO existe en clips) | 2? | — | Sospechoso: ataque de Aline gigante; extracción pendiente desde FModel |
| `Skill10` | `Paintress_Skill10` | 2 | **E** | Serie de golpes en sitio |
| `Skill11` | (NO existe en clips) | — | — | Gap en numeración del Animator |
| `Skill12` | `Paintress_Skill12` | 2 | **E** | Serie larga con saltos |
| `Skill_Aline_P3_Skill1` | (sin prefijo Paintress_) | 3 | — | Curación al jugador, Aline ya no pelea |
| `Skill_Aline_P3_Skill2` | (sin prefijo Paintress_) | 3 | — | Variante de curación |

### Composición por fase

- **Fase 1 (suelo, `Idle1`):** A (Skill3, Skill4), B (DashIn-Idle1), B+C (Skill5), E (Skill1), F (Skill2 multi-stage). Transiciona a fase 2 vía `Idle1_to_idle2_transition` + `Skill6`.
- **Fase 2 (flotando, `Idle2`):** E (Skill7, Skill10, Skill12), caso especial (Skill8). Transiciona a fase 3 vía `Idle2_to_idle3_transition`.
- **Fase 3 (derrotada, `Idle3`):** sin combate. P3_Skill1 / P3_Skill2 son curaciones narrativas.

---

## Contrato compartido (válido para todas las familias)

Reglas que toda instancia de cualquier familia respeta. Romperlas == ataques que se pisan, fugas en escena, debug imposible.

### Track namespacing

Cada **instancia** de un ataque genera un **track ID único**. Convención:

```
atk_<familia>_<NNN>
```

Donde `<familia>` ∈ `{a, b, d, e, f, ...}` y `<NNN>` es un contador de 3 dígitos por familia (`atk_a_001`, `atk_a_002`, ..., `atk_e_017`). Si una instancia genera múltiples objetos (p.ej. familia A con N proyectiles), añade sufijo `_iN`: `atk_a_001_i0`, `atk_a_001_i1`, etc.

**Por qué:** el `AssignTrackParent` y el `DestroyPrefab` necesitan localizar el track sin ambigüedad. Sin namespace estructurado, tracks de ataques distintos colisionan y limpiar uno borra otro.

**Lo que NO usa este namespace:**
- Animaciones de Aline → siempre track `alineTrack` (definido en el `InstantiatePrefab` original de Aline al cargar el mapa).
- Filtros de post-process (modificador C) → track `postFx_<NNN>` aparte, no `atk_*`.

### Separación de tracks de Aline vs ataque

**Animaciones de Aline** (`SetAnimatorProperty` con triggers `Skill1`, `Skill5`, etc.) van **siempre** sobre `alineTrack`. El prefab de Aline se instancia una vez al inicio del mapa y vive toda la canción.

**Prefabs de ataque** (proyectiles, indicadores, slashes) van sobre tracks `atk_*` y se destruyen al final del ataque. **Nunca** se hace parent de un prefab de ataque a `alineTrack` salvo que el ataque siga visualmente a Aline durante su movimiento (caso raro; documentarlo en la instancia).

### Cleanup obligatorio

Toda familia termina su secuencia con un `DestroyPrefab` por cada track `atk_*` que abrió. Sin excepciones. Los `id`s de prefabs instanciados también se destruyen explícitamente. Verificar al prototipar: instanciar el ataque dos veces seguidas no debe dejar residuo en escena.

### NJS y reaction time

Las notas del parry se colocan en el `_notes` array del `.dat` con su `_time` calculado **al revés**: `_time = T_impacto - (jumpDuration / 2)`. Para showcase con NJS bajo (~10) la jump duration es generosa, pero **legibilidad del telegraph manda**: si el ataque no se lee a tiempo, baja NJS o adelanta el `_time` del telegraph.

---

## Familia A — Ranged Sequence

**Mecánica:** Aline lanza N proyectiles que aparecen sobre/junto a ella y caen secuencialmente sobre el jugador. Cada proyectil = un parry.

**Patrón pendiente de validar.** Approach que se baraja: telegraph estático (`InstantiatePrefab` de decoración + `DestroyObject` al launch) + cubo BS como proyectil real (visible desde launch via `dissolve`, trayectoria del telegraph al jugador via `definitePosition`). La conversión world meters ↔ lane units (1 lane = 0.6m, offsets calibrados) está en [`vivify-mapping`](SKILL.md). Antes de tirar código nuevo: leer Heckdocs sobre `definitePosition`/`dissolve`/`noteJumpStartBeatOffset`/`_noteJumpDurationTypeSettings: "Dynamic"` para no operar sobre suposiciones.

### Inputs requeridos

| Input | Valor | Notas |
|---|---|---|
| Animator trigger | `Skill3` (3 piedras gigantes, fase 1) o `Skill4` (N proyectiles pequeños tras giro, fase 1) | Las dos variantes encajan en A; cambia VFX y N |
| Prefab proyectil | `assets/aline/prefabs/projectile_*.prefab` (TBD — pendiente crear/extraer) | Skill3: piedras grandes; Skill4: proyectiles pequeños tipo pincelada/tinta |
| Prefab spawner (opcional) | indicador visual del origen (encima de Aline) | El propio movimiento de "tocar harpa" lo telegraph; spawner separado puede no ser necesario |

### Secuencia de eventos `.dat`

Tiempos relativos al instante de impacto del **primer** proyectil (`T_impact_0`). Asume `delta` = separación entre proyectiles consecutivos.

```
T_impact_0 - 2.5s : SetAnimatorProperty (Skill3 ó Skill4) → alineTrack
T_impact_0 - 1.5s : InstantiatePrefab × N (projectile_i0..iN-1) sobre Aline → atk_a_NNN_i0..iN-1
T_impact_0 - 1.0s : AnimateTrack (orbit/hold sobre Aline) en cada atk_a_NNN_iX por 0.5s
T_impact_0 - 0.5s : AnimateTrack (descenso a posición de impacto) sobre atk_a_NNN_i0 por 0.5s
T_impact_0 + 0.0s : nota de parry #0 llega al jugador
T_impact_0 + 0.0s : DestroyPrefab atk_a_NNN_i0
T_impact_0 + delta : (repetir descenso/nota/destroy para i1)
...
```

> Los offsets exactos hay que afinarlos con la duración real del clip (`Skill3` y `Skill4` tienen duración distinta — el descenso de los proyectiles debe sincronizar con el "lanzamiento" visible en la animación).

### Encoding del parry

- Tipo: `_notes` con `_cutDirection` codificando **el cuadrante de origen del proyectil**.
- Distribución típica: proyectiles caen en arco frontal → notas en filas medias/altas.
- Cada nota va separada de la siguiente por `delta` (60/BPM × beats).
- Color (`_type` 0/1) puede alternar para forzar parries con ambas manos.

### Parámetros tunables (por instancia)

| Parámetro | Rango típico | Notas |
|---|---|---|
| `T_impact_0` | cualquier `_time` | inicio del ataque |
| `N` | 3 (Skill3) o 5-7 (Skill4) | dictado por la animación |
| `delta` | 0.3s-0.8s | bajo = más intenso, menos legible |
| Direcciones de notas | 8 valores BS | una por proyectil |

### NO tunable

- Estructura de eventos (orden y deltas relativos del telegraph).
- Que cada proyectil tenga su propio track `_iX`.
- N debe matchear el lanzamiento visible en la animación.

### Reglas de no-conflicto

- Tracks usados: `atk_a_NNN`, `atk_a_NNN_i0..iN-1`.
- No solapar dos familia A en `T_impact_0 ± 2s`: confunde la lectura.
- Compatible con B/D/E/F simultáneas si están en otra zona del grid.

---

## Familia B — Melee Directional Slash

**Mecánica:** Aline ejecuta un golpe mele tras aproximarse al jugador. Telegraph = aproximación (DashIn) + línea/streak en la dirección del slash. Parry = una nota con dirección **opuesta** (parry real).

> **Root motion operativo (2026-05-01).** DashIn/DashOut trasladan el GO via root motion sintetizado en Blender (`scripts/blender/synthesize_root_motion.py`) + `motionNodeName="SK_Curator_Aline"` en el FBX importer + Apply Root Motion = ON en el Animator del prefab. Validado e2e en `EasyStandard.dat`: Aline avanza ~6m forward en DashIn, vuelve en DashOut, sin snap-back. Detalles operativos y caminos descartados en la skill [`vivify-animations`](../vivify-animations/SKILL.md) sección "Root motion para clips con desplazamiento" + "Caminos cerrados".

### Inputs requeridos

| Input | Valor | Notas |
|---|---|---|
| Animator trigger de aproximación | `DashIn-Idle1` (acaba en pose Idle1, vuelve a default) o `DashIn-Idle2` (acaba en pose Idle2, encadena directo a Idle2) | Ambos llevan motion forward (~6m world Z) extraído como root motion. La elección depende de qué pose quieres post-dash: Idle1 si el ataque es one-off, Idle2 si Aline encadena más combat en pose alerta |
| Animator trigger del golpe | `Skill1` (golpe estándar) o `Skill5` (golpe con distorsión — combina con modificador C) | Clips con motion menor (256/75 cm en Y bone-local) que termina en pose neutra — no se sintetiza root motion (no hay snap-back porque no terminan desplazadas). |
| Trigger de retirada | `DashOut-Idle2` | Devuelve a Aline a posición lejana, encadena a Idle2 |
| Prefab streak | `assets/aline/prefabs/slash_streak.prefab` (TBD — pendiente crear) | Línea/trail dibujando el eje del slash |
| Material streak | unlit emissive con alpha; reutilizable para todas las instancias B | — |

### Choreography (parte del contrato)

El ataque consume tres beats: **aproximación → golpe → retirada**. Tiempos aproximados:

- `T_impact - 1.5s` : `DashIn-Idle1` trigger (Aline empieza aproximación)
- `T_impact - 0.6s` : streak aparece, Aline ya cerca
- `T_impact + 0.0s` : golpe + nota
- `T_impact + 0.5s` : `DashOut-Idle2` trigger (retirada)

Si la fase ya tiene a Aline cerca por contexto previo, se puede saltar el `DashIn-Idle1` y entrar desde `Idle1` directamente al impacto, pero entonces el ataque **no es Familia B canónica** — documentarlo como instancia atípica.

### Secuencia de eventos `.dat`

```
T_impact - 1.5s : SetAnimatorProperty (DashIn-Idle1 ó Skill5) → alineTrack
T_impact - 0.6s : InstantiatePrefab (slash_streak) → atk_b_NNN
T_impact - 0.6s : AnimateTrack (escalado/extensión del streak) sobre atk_b_NNN por 0.6s
T_impact + 0.0s : nota de parry llega al jugador
T_impact + 0.2s : DestroyPrefab atk_b_NNN
T_impact + 0.5s : SetAnimatorProperty (DashOut-Idle2) → alineTrack
```

### Encoding del parry

- **Una sola nota.** Dirección = **opuesta al eje del streak** (Si el streak va izquierda→derecha, la nota es horizontal hacia la izquierda).
- Posición típica: centro de pantalla — un slash es un golpe único.
- Color: el que corresponda por flow.

### Parámetros tunables

| Parámetro | Rango | Notas |
|---|---|---|
| `T_impact` | cualquier `_time` | — |
| Eje del slash | 8 direcciones | el VFX del streak debe matchear |
| Anim trigger | `DashIn-Idle1` ó `Skill5` | Skill5 implica modificador C activo |
| Saltar DashIn | bool | si la fase ya tiene a Aline cerca |

### NO tunable

- Que la nota sea **una sola**.
- Que su dirección sea **opuesta** al streak.
- Ventana telegraph→impacto (~0.6s).

### Reglas de no-conflicto

- Track usado: `atk_b_NNN`.
- Compatible con cualquier otra familia simultánea siempre que no usen el mismo cuadrante visual.

---

## Familia D — Shrinking Indicator

**Mecánica:** indicador (cuadrado con esquinas + ring concéntrico, estilo E33) aparece alrededor de un punto y se contrae. Parry = nota única en el momento exacto del cierre.

> Referencia visual: el marker que usa E33 cuando un enemigo telegrafia ataques de precisión. Adaptación, no réplica — el feel es: cuadrado con esquinas marcadas + ring exterior que se contrae hasta tocar las esquinas.

> **Sin source animation en el Animator de Aline.** Esta familia es **invento nuestro**, no traducción directa de un clip existente. Se usa donde queramos forzar un parry de precisión, típicamente como overlay sobre el momento clave de otra familia (último proyectil de A, explosión de F) o como ataque standalone en el clímax.

### Inputs requeridos

| Input | Valor | Notas |
|---|---|---|
| Animator trigger | flexible — el indicador es independiente de la animación de Aline | Si se combina con otra familia, el animator trigger lo dicta esa familia, no D |
| Prefab indicador | `assets/aline/prefabs/indicator_ring.prefab` (TBD — **pendiente crear**) | Cuadrado + ring concéntrico, animable por scale |
| Material | unlit emissive blanco/dorado para matchear estética E33 | reutilizable |

### Secuencia de eventos `.dat`

```
T_impact - 1.0s : InstantiatePrefab (indicator_ring) → atk_d_NNN, scale [s_max, s_max, s_max]
T_impact - 1.0s : AnimateTrack (scale s_max → s_min) sobre atk_d_NNN por 1.0s, easing easeIn
T_impact + 0.0s : nota de parry llega al jugador (ring tocando las esquinas del cuadrado)
T_impact + 0.1s : DestroyPrefab atk_d_NNN
```

### Encoding del parry

- **Una sola nota** posicionada **exactamente donde está el indicador**: si el indicador está a `[x=2, y=1]` del grid de notas, la nota va en `_lineIndex=2, _lineLayer=1`.
- La dirección de la nota puede ser cualquiera; lo que define el ataque es el **timing** (cierre del ring).

### Parámetros tunables

| Parámetro | Rango | Notas |
|---|---|---|
| `T_impact` | cualquier `_time` | — |
| Posición del indicador | grid 4×3 de BS | dicta la posición de la nota |
| `s_max` | 1.5-3.0 (escala mundo) | tamaño inicial del ring |
| `s_min` | 0.3-0.5 | tamaño final = el bloque dentro del ring |
| Duración cierre | 0.6s-1.5s | corto = parry de precisión; largo = parry contemplativo |

### NO tunable

- Que el cierre del ring sea **monotónico** (no se expande otra vez antes del impacto).
- Que la nota llegue **al instante exacto del cierre**, no antes.

### Reglas de no-conflicto

- Track usado: `atk_d_NNN`.
- Múltiples familia D simultáneas son **OK** (varios indicadores en grid distinto = combo de precisión).
- Combinable como overlay sobre A (último proyectil), F (momento de explosión), o E (último hit de la cadena).

---

## Familia E — Multi-hit Chain

**Mecánica:** cadena de N parries en sucesión rápida durante una única animación de Aline que tiene N hits embebidos. Diferente de A en que el ataque es mele (no proyectiles). Diferente de B en que son N hits, no 1.

### Inputs requeridos

| Input | Valor | Notas |
|---|---|---|
| Animator trigger | `Skill1` (fase 1, magia gestual con explosiones) / `Skill7` o `Skill7_MaelleBurningCanvasVersion` (fase 2, pincel grande, dash-back-return × 5) / `Skill10` (fase 2, en sitio) / `Skill12` (fase 2, larga con saltos) | Cada uno tiene N hits embebidos en el clip |
| VFX por hit | depende del trigger: explosión (Skill1), trazo de pincel (Skill7-12) | parametrizable por instancia |
| Prefab/material del VFX | TBD según skill | extraer de FModel o crear custom |

### Secuencia de eventos `.dat`

Tiempos relativos al **primer hit** (`T_first_hit`). Asume `delta` = separación entre hits consecutivos, dictado por la animación.

```
T_first_hit - 1.0s : SetAnimatorProperty (trigger) → alineTrack
T_first_hit + 0.0s : InstantiatePrefab (vfx_hit_0) → atk_e_NNN_h0
T_first_hit + 0.0s : nota de parry #0
T_first_hit + 0.3s : DestroyPrefab atk_e_NNN_h0
T_first_hit + delta : (repetir InstantiatePrefab/nota/destroy para h1..hN-1)
```

> El `delta` y N están **dictados por el clip** — afinarlo con la animación real (Skill7 ≈ 5 hits, Skill10 ≈ varios en sitio, Skill12 ≈ los más largos con saltos, Skill1 ≈ aspavientos en serie).

### Encoding del parry

- Cadena de N notas con separación `delta` (típicamente 0.4-0.7s).
- Direcciones pueden ser variadas si la anim sugiere movimiento (Skill12 con saltos), o más uniformes si la anim es estática (Skill10).
- Skill7 con dash-back-return: cada hit viene "desde lejos" — la dirección puede codificar el ángulo de aproximación de Aline.

### Parámetros tunables

| Parámetro | Rango | Notas |
|---|---|---|
| `T_first_hit` | cualquier `_time` | — |
| Trigger | `Skill1` / `Skill7` / `Skill7_Maelle...` / `Skill10` / `Skill12` | cada uno con su N y delta canónicos |
| Direcciones de notas | 8 valores | una por hit |
| VFX por hit | prefab path | varía por instancia visual |

### NO tunable

- N debe matchear el número de hits embebido en la animación. No se puede pedir 3 hits si el clip tiene 5 — la anim seguirá hasta el final y los hits sin nota golpearán "en vacío".
- El primer hit no puede llegar antes de que la animación arranque.

### Reglas de no-conflicto

- Tracks: `atk_e_NNN`, `atk_e_NNN_hX` (X = 0..N-1).
- No solapar dos familia E simultáneas — la cadena de notas se vuelve ilegible.
- E + modificador C funciona bien para un hit clave dentro de la cadena (no toda la cadena).

---

## Familia F — Charging AoE Ball

**Mecánica:** Aline se eleva, carga una bola de energía visible que crece, explota. Parry único en el momento de explosión. Telegraph muy largo (~3-4s) lo distingue de B.

### Inputs requeridos

| Input | Valor | Notas |
|---|---|---|
| Animator trigger Start | `Skill2_Start` | Aline se eleva levantando brazo |
| Animator trigger Loop | `Skill2_Loop` | Sustained mientras la bola crece |
| Animator trigger End | `Skill2_End` | Aline baja a tierra tras la explosión |
| Prefab bola | `assets/aline/prefabs/energy_ball.prefab` (TBD — pendiente crear o extraer de FModel) | Bola de energía, escalable, emissive |
| Material bola | unlit emissive con bloom (si se puede dentro de la pipeline Vivify actual) | reutilizable |

### Secuencia de eventos `.dat`

```
T_explosion - 4.0s : SetAnimatorProperty (Skill2_Start) → alineTrack
T_explosion - 3.0s : InstantiatePrefab (energy_ball, scale s_min) → atk_f_NNN
T_explosion - 3.0s : SetAnimatorProperty (Skill2_Loop) → alineTrack
T_explosion - 3.0s : AnimateTrack (scale s_min → s_max) sobre atk_f_NNN por 3.0s
T_explosion + 0.0s : nota de parry llega al jugador
T_explosion + 0.0s : DestroyPrefab atk_f_NNN (acompañar con VFX de explosión opcional)
T_explosion + 0.3s : SetAnimatorProperty (Skill2_End) → alineTrack
```

### Encoding del parry

- **Una sola nota** en posición central (la bola está delante del jugador).
- Dirección: la que el flow pida.
- Tip: combinable con D (shrinking indicator) sobre la nota para reforzar el "parry de precisión" en el momento exacto de explosión.

### Parámetros tunables

| Parámetro | Rango | Notas |
|---|---|---|
| `T_explosion` | cualquier `_time` | — |
| Duración carga | 2.0s-4.0s | el `Skill2_Loop` puede sostenerse arbitrario |
| `s_min` / `s_max` | 0.3 / 1.5-3.0 (escala mundo) | tamaño inicial / final de la bola |

### NO tunable

- La estructura `Skill2_Start` → `Skill2_Loop` → `Skill2_End` del trigger animator. Saltarse Loop = Aline se queda mal posicionada.
- Que el parry sea una sola nota (es el sello de F).

### Reglas de no-conflicto

- Track: `atk_f_NNN`.
- Solo una F activa simultáneamente. Dos bolas crecientes confunden el telegraph.
- F + modificador C combina muy bien para clímax de fase 1.

---

## Modificador C — Distortion Overlay

**No es una familia.** Es una **transformación visual** apilable sobre A/B/D/E/F en una instancia concreta del ataque, que aplica un filtro post-process al jugador (desaturación / grayscale) durante una ventana específica del telegraph o del parry. Replica la mecánica de "distorsión" de E33 (`Skill5`, posiblemente otros futuros).

### Inputs requeridos

| Input | Valor | Notas |
|---|---|---|
| Material Blit | `assets/aline/materials/m_distortion.mat` (TBD — **pendiente crear**) | Shader que aplica desaturación + viñeta opcional |
| Propiedad animable | `_Saturation` (float, 0.0 grayscale → 1.0 normal) | Expuesta en el shader del material |

### Eventos a inyectar (snippet)

Se compone con la secuencia de la familia base sumando estos eventos. Típicamente la ventana abre antes del impacto y cierra justo después.

```
T_window_start - 0.5s : Blit (m_distortion) → postFx_NNN
T_window_start - 0.5s : SetMaterialProperty (_Saturation 1.0 → 0.0) sobre m_distortion por 0.5s
T_window_end + 0.0s  : SetMaterialProperty (_Saturation 0.0 → 1.0) sobre m_distortion por 0.3s
T_window_end + 0.3s  : Blit clear postFx_NNN
```

### Composabilidad

- **B + C** → mele con distorsión (caso canónico, `Skill5` vanilla).
- **A + C** → cascada de proyectiles con distorsión sobre el descenso final.
- **E + C** → cadena multi-hit con distorsión durante 1-2 hits clave.
- **F + C** → bola cargando con distorsión durante el momento de explosión.
- **D + C** → indicador de precisión con distorsión (clímax).

### NO tunable

- Que el shader del Blit sea **reutilizable**: una sola instancia de `m_distortion` para todo el mapa, no clonarlo por instancia.
- Que **solo haya un C activo simultáneamente** en el mapa. Dos distorsiones se pisan visualmente.

### Restricciones

- Track post-fx: `postFx_NNN` (separado del namespace `atk_*`).
- Si la familia base ya satura visualmente la pantalla, C puede ser redundante o ilegible — verificar al prototipar.

---

## Hueco para familias futuras

Si surge un patrón que no encaja en A/B/D/E/F, añadir aquí siguiendo el mismo schema (Inputs / Secuencia / Encoding / Tunables / NO tunable / No-conflicto). Candidatos identificados pero no necesarios todavía:

- **G — AoE telegraphed area:** zona del grid se marca como "no estar aquí cuando el timer cierre". Cambia la mecánica: en lugar de golpear, el jugador **evita**. Posible si encontramos cómo encajar "no golpear" con BS (¿walls? ¿bombas? ¿saber-clear?).
- **Caso especial Skill8 (clímax fase 2):** Aline gigante de fondo + bolas de energía + serie de golpes. No es familia reutilizable — es un beat narrativo único. Ver "Diferidos" en NEXT_STEPS.md, requiere conversación de diseño dedicada (ataque "impresionante" identificado por el usuario).
