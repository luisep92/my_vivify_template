# Catálogo de familias de ataque

Este archivo formaliza los **contratos de ataque** del boss fight. Lo describe [PRODUCTO.md](../../../docs/PRODUCTO.md): cada habilidad de Aline es una **familia reutilizable** (prefab + animación + secuencia de eventos `.dat` + encoding del parry). Una vez una familia está definida y validada con un prototipo, instanciarla N veces en el mapa con timings/posiciones distintos es trabajo mecánico.

Si añades un ataque nuevo, **busca primero en este catálogo** una familia existente que encaje. Solo crea familia nueva (E, F...) si el ataque no encaja en ninguna existente.

> **Dependencia de identificación de triggers.** Los inputs marcados `TBD` en cada familia (qué `Skill_X` del Animator es la animación correcta) se resuelven en el paso 2 de [NEXT_STEPS.md](../../../docs/NEXT_STEPS.md) — sandbox de locomoción/identificación. Hasta que ese paso esté hecho, los prototipos de cada familia están bloqueados. Cuando se identifiquen, sustituir los `TBD` por el nombre concreto y rellenar la tabla de abajo.

## Tabla de identificación de triggers (a rellenar)

| Trigger | Clip identificado | Familia destino | Notas |
|---|---|---|---|
| `Idle1` | TBD | — | idle base |
| `Idle2` | TBD | — | — |
| `Idle3` | TBD | — | — |
| `Idle1_to_idle2_transition` | TBD | — | — |
| `Idle2_to_idle3_transition` | TBD | — | — |
| `DashIn-Idle1` | TBD | — | aterrizaje? entrada en escena? |
| `DashOut-Idle2` | TBD | — | salida? |
| `Idle2_Stun` | TBD | — | — |
| `Idle_Countered` | TBD | — | reacción a parry exitoso? |
| `Skill1` | TBD | TBD (B?) | — |
| `Skill2_Start` / `_Loop` / `_End` | TBD | TBD | skill multi-fase |
| `Skill3` | TBD | TBD | — |
| `Skill4` | TBD | TBD | — |
| `Skill5` | TBD | TBD (A?) | — |
| `Skill6` | TBD | TBD | — |
| `Skill7` | TBD | TBD (A?) | candidato a ranged sequence |
| `Skill7_MaelleBurningCanvasVersion` | TBD | TBD | variante visual |
| `Skill8` | TBD | TBD | — |
| `Skill9` | TBD | TBD | — |
| `Skill10` | TBD | TBD | — |
| `Skill12` | TBD | TBD | — |
| `Skill_Aline_P3_Skill1` | TBD | TBD | fase 3 |
| `Skill_Aline_P3_Skill2` | TBD | TBD (C?) | fase 3, candidato a distortion window |

---

## Contrato compartido (válido para todas las familias)

Reglas que toda instancia de cualquier familia respeta. Romperlas == ataques que se pisan, fugas en escena, debug imposible.

### Track namespacing

Cada **instancia** de un ataque genera un **track ID único**. Convención:

```
atk_<familia>_<NNN>
```

Donde `<familia>` ∈ `{a, b, c, d, ...}` y `<NNN>` es un contador de 3 dígitos por familia (`atk_a_001`, `atk_a_002`, ..., `atk_b_017`). Si una instancia genera múltiples objetos (p.ej. familia A con N proyectiles), añade sufijo `_iN`: `atk_a_001_i0`, `atk_a_001_i1`, etc.

**Por qué:** el `AssignTrackParent` y el `DestroyPrefab` necesitan localizar el track sin ambigüedad. Sin namespace estructurado, tracks de ataques distintos colisionan y limpiar uno borra otro.

**Lo que NO usa este namespace:**
- Animaciones de Aline → siempre track `alineTrack` (definido en el `InstantiatePrefab` original de Aline al cargar el mapa).
- Filtros de post-process (familia C) → track `postFx_<NNN>` aparte, no `atk_*`.

### Separación de tracks de Aline vs ataque

**Animaciones de Aline** (`SetAnimatorProperty` con triggers `Skill1`, `Skill5`, etc.) van **siempre** sobre `alineTrack`. El prefab de Aline se instancia una vez al inicio del mapa y vive toda la canción.

**Prefabs de ataque** (proyectiles, indicadores, slashes) van sobre tracks `atk_*` y se destruyen al final del ataque. **Nunca** se hace parent de un prefab de ataque a `alineTrack` salvo que el ataque siga visualmente a Aline durante su movimiento (caso raro; documentarlo en la instancia).

### Cleanup obligatorio

Toda familia termina su secuencia con un `DestroyPrefab` por cada track `atk_*` que abrió. Sin excepciones. Los `id`s de prefabs instanciados también se destruyen explícitamente. Verificar al prototipar: instanciar el ataque dos veces seguidas no debe dejar residuo en escena.

### NJS y reaction time

Las notas del parry se colocan en el `_notes` array del `.dat` con su `_time` calculado **al revés**: `_time = T_impacto - (jumpDuration / 2)`. Para showcase con NJS bajo (~10) la jump duration es generosa, pero **legibilidad del telegraph manda**: si el ataque no se lee a tiempo, baja NJS o adelanta el `_time` del telegraph.

---

## Familia A — Ranged Sequence

**Mecánica:** Aline lanza N proyectiles que orbitan brevemente y caen secuencialmente sobre el jugador. Cada proyectil = un parry.

### Inputs requeridos

| Input | Valor | Notas |
|---|---|---|
| Animator trigger | `Skill5` o `Skill7` (TBD por inspección visual de clips) | Anim de Aline lanzando los proyectiles al aire |
| Prefab proyectil | `assets/aline/prefabs/projectile.prefab` (TBD — pendiente crear) | VFX del proyectil; si no existe aún se prototipa con un cubo unlit emisivo |
| Prefab ring (opcional) | `assets/aline/prefabs/projectile_ring.prefab` (TBD) | Spawner visual: el círculo de origen donde orbitan los N proyectiles antes de caer |

### Secuencia de eventos `.dat`

Tiempos relativos al instante de impacto del **primer** proyectil (`T_impact_0`). Asume `delta` = separación entre proyectiles consecutivos.

```
T_impact_0 - 2.0s : SetAnimatorProperty (Skill5 trigger) → alineTrack
T_impact_0 - 1.5s : InstantiatePrefab (projectile_ring) → atk_a_NNN_ring
T_impact_0 - 1.5s : InstantiatePrefab × N (projectile_i0..iN-1) → atk_a_NNN_i0..iN-1
T_impact_0 - 1.5s : AnimateTrack (orbit) sobre cada atk_a_NNN_iX por 1.0s
T_impact_0 - 0.5s : AnimateTrack (descenso a posición de impacto) sobre atk_a_NNN_i0 por 0.5s
T_impact_0 + 0.0s : nota de parry #0 llega al jugador
T_impact_0 + 0.0s : DestroyPrefab atk_a_NNN_i0
T_impact_0 + delta : (repetir descenso/nota/destroy para i1)
...
T_impact_0 + (N-1)*delta + 0.5s : DestroyPrefab atk_a_NNN_ring
```

### Encoding del parry

- Tipo: `_notes` con `_cutDirection` codificando **el cuadrante de origen del proyectil** desde el ring spawner.
- Distribución típica: ring centrado encima de Aline → proyectiles caen en arco frontal → notas en filas 1-2 (medio/alto), cualquier columna 0-3.
- Cada nota va separada de la siguiente por `delta` (60/BPM × beats).
- Color (`_type` 0/1) puede alternar para forzar parries con ambas manos, o monocolor si la fase pide tensión.

### Parámetros tunables (por instancia)

| Parámetro | Rango típico | Notas |
|---|---|---|
| `T_impact_0` | cualquier `_time` del mapa | inicio del ataque |
| `N` | 3-9 | E33 usa 7 en este patrón concreto |
| `delta` | 0.2s-0.8s | más bajo = más intenso, menos legible |
| Direcciones de notas | 8 valores BS | una por proyectil, codifica cuadrante de origen |

### NO tunable (parte del contrato)

- Estructura de eventos (orden y deltas relativos del telegraph).
- Que cada proyectil tenga su propio track `_iX`.
- Que el ring se destruya **después** del último proyectil, no a la vez.

### Reglas de no-conflicto

- Tracks usados: `atk_a_NNN`, `atk_a_NNN_ring`, `atk_a_NNN_i0..iN-1`. Reservar el rango `NNN` antes de añadir otra instancia.
- No solapar con otra familia A en `T_impact_0 ± 2s`: confunde la lectura.
- Sí compatible con familia B/C/D simultánea **si están en otra zona del grid** (no encima del ring).

---

## Familia B — Melee Directional Slash

**Mecánica:** Aline ejecuta un corte rápido. Telegraph = línea/streak en la dirección del slash. Parry = una nota con dirección **opuesta** (parry real).

### Inputs requeridos

| Input | Valor | Notas |
|---|---|---|
| Animator trigger | `Skill1`, `Skill3`, o `Skill_Aline_P3_Skill1` (TBD por inspección de clips melee) | Anim del corte |
| Prefab streak | `assets/aline/prefabs/slash_streak.prefab` (TBD — pendiente crear) | Línea/trail que dibuja el eje del slash |
| Material streak | unlit emissive con alpha; reutilizable para todas las instancias B | — |

### Secuencia de eventos `.dat`

```
T_impact - 1.2s : SetAnimatorProperty (Skill1 trigger) → alineTrack
T_impact - 0.6s : InstantiatePrefab (slash_streak) → atk_b_NNN
T_impact - 0.6s : AnimateTrack (escalado/extensión del streak) sobre atk_b_NNN por 0.6s
T_impact + 0.0s : nota de parry llega al jugador
T_impact + 0.2s : DestroyPrefab atk_b_NNN (fade-out del streak)
```

### Encoding del parry

- **Una sola nota.** Dirección = **opuesta al eje del streak**. Si el streak va izquierda→derecha (horizontal), la nota es horizontal hacia la izquierda.
- Posición típica: centro de pantalla (línea 1, layer 1) — un slash es un golpe único, no un patrón espacial.
- Color: el que corresponda por flow de la fase. Familia B no impone color.

### Parámetros tunables

| Parámetro | Rango típico | Notas |
|---|---|---|
| `T_impact` | cualquier `_time` | — |
| Eje del slash | 8 direcciones | el VFX del streak debe matchear |
| Anim trigger | varios `Skill_*` melee | depende de fase |

### NO tunable

- Que la nota sea **una sola**.
- Que su dirección sea **opuesta** al streak (es la representación del parry, no del corte).
- Ventana telegraph→impacto (~0.6s): más rápido es ilegible, más lento pierde tensión.

### Reglas de no-conflicto

- Track usado: `atk_b_NNN`.
- Compatible con cualquier otra familia simultánea siempre que no usen el mismo cuadrante visual (no quieres un proyectil de familia A cruzándose con el streak de B).

---

## Familia C — Distortion Window

**Mecánica:** filtro post-process desaturado se activa, abre la "ventana de distorsión" durante la cual viene un golpe garantizado. Parry = una nota dentro de la ventana grayscale.

### Inputs requeridos

| Input | Valor | Notas |
|---|---|---|
| Animator trigger | `Skill_Aline_P3_Skill2` o similar fase 3 (TBD) | Anim contemplativa/cargada que justifica el "tiempo se ralentiza" |
| Material Blit | `assets/aline/materials/m_distortion.mat` (TBD — **pendiente crear**) | Shader que aplica desaturación + viñeta opcional |
| Propiedad animable | `_Saturation` (float, 0.0 grayscale → 1.0 normal) | Expuesta en el shader del material |

### Secuencia de eventos `.dat`

```
T_impact - 1.5s : SetAnimatorProperty (trigger) → alineTrack
T_impact - 1.0s : Blit (m_distortion) → postFx_NNN
T_impact - 1.0s : SetMaterialProperty (_Saturation 1.0 → 0.0) sobre m_distortion por 0.5s
T_impact + 0.0s : nota de parry llega al jugador
T_impact + 0.3s : SetMaterialProperty (_Saturation 0.0 → 1.0) sobre m_distortion por 0.3s
T_impact + 0.6s : Blit clear (o desactivar postFx_NNN)
```

### Encoding del parry

- **Una sola nota** en posición central.
- Lo que define la familia es **lo visual**, no la nota.
- Tip de diseño: la nota debería entrar en escena exactamente cuando el `_Saturation` toca 0.0 (jugador siente que la nota "aparece desde la distorsión").

### Parámetros tunables

| Parámetro | Rango típico | Notas |
|---|---|---|
| `T_impact` | cualquier `_time` | — |
| Duración fade-in | 0.3s-0.7s | a más fade, más cinematográfico |
| Duración fade-out | 0.2s-0.5s | normalmente más corto que fade-in |
| Intensidad min `_Saturation` | 0.0-0.3 | 0.0 = grayscale puro, 0.3 = solo apagado |

### NO tunable

- Que el ataque tenga ventana de post-process activo durante el parry (es el sello de la familia).
- Que el shader del Blit sea reutilizable: una sola instancia de `m_distortion` para todas las familias C en el mapa, no clonarlo por instancia.

### Reglas de no-conflicto

- Track post-fx: `postFx_NNN`.
- **Solo una familia C activa simultáneamente** — dos Blits de saturación pisándose es ilegible.
- Compatible con familia A/B/D simultánea siempre que el filtro no oculte el telegraph del otro ataque (revisar visualmente al prototipar combos).

---

## Familia D — Shrinking Indicator

**Mecánica:** indicador (cuadrado con esquinas + ring concéntrico, estilo E33) aparece alrededor de un punto y se contrae. Parry = nota única en el momento exacto del cierre.

> Referencia visual: el marker que usa E33 cuando un enemigo telegrafia ataques de precisión. Adaptación, no réplica — el feel es: cuadrado con esquinas marcadas + ring exterior que se contrae hasta tocar las esquinas.

### Inputs requeridos

| Input | Valor | Notas |
|---|---|---|
| Animator trigger | flexible — el indicador es independiente de la animación de Aline; combinable con cualquier `Skill_*` o sin animación | Si se combina con melee/ranged, el animator trigger lo dicta esa familia, no la D |
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
- La dirección de la nota puede ser cualquiera; lo que define el ataque es el **timing** (cierre del ring), no la dirección.

### Parámetros tunables

| Parámetro | Rango típico | Notas |
|---|---|---|
| `T_impact` | cualquier `_time` | — |
| Posición del indicador | grid 4×3 de BS | dicta la posición de la nota |
| `s_max` | 1.5-3.0 (escala mundo) | tamaño inicial del ring |
| `s_min` | 0.3-0.5 | tamaño final = el bloque dentro del ring |
| Duración cierre | 0.6s-1.5s | corto = parry de precisión; largo = parry contemplativo |

### NO tunable

- Que el cierre del ring sea **monotónico** (no se expande otra vez antes del impacto): rompe la lectura.
- Que la nota llegue **al instante exacto del cierre**, no antes.

### Reglas de no-conflicto

- Track usado: `atk_d_NNN`.
- Múltiples familia D simultáneas son **OK** (varios indicadores en grid distinto = combo de precisión). Cuidado con saturar la pantalla.
- Combinable con A/B/C como modificador: indicador D superpuesto a un proyectil de A "convierte" el último proyectil del cluster en parry de precisión.

---

## Hueco para familias futuras

Si surge un patrón que no encaja en A/B/C/D, añadir aquí siguiendo el mismo schema (Inputs / Secuencia / Encoding / Tunables / NO tunable / No-conflicto). Candidatos identificados pero no necesarios todavía:

- **E — Multi-hit chain:** combo de slashes encadenados que parecen uno solo (parry chain). Probable en fase 3.
- **F — AoE telegraphed area:** zona del grid se marca como "no estar aquí cuando el timer cierre". Cambia la mecánica: en lugar de golpear, el jugador **evita**. Posible si encontramos cómo encajar "no golpear" con el cubo de BS (¿walls? ¿bombas?).
