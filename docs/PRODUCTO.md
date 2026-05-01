# PRODUCTO — Aline Boss Fight

## Concepto

**Showcase map** de Beat Saber tipo **boss fight** contra **Aline**, la Curatress de *Expedition 33*. El prefab 3D de Aline aparece en escena como enemigo y va lanzando habilidades; cada habilidad es un **ataque telegrafiado** con una **ventana de parry** que el jugador resuelve golpeando una nota direccional. La traducción es directa: el sistema de parry de E33 (timing + dirección) ya es, mecánicamente, lo que hace BS.

No es un mapa "normal" con gimmicks Vivify, ni un mapa rítmico al uso. Las notas son la encarnación del parry, no el flow rítmico de la canción. La música va de ambiente.

## Tono

**Showcase cinemático, no scored.** Decisión cerrada en [DECISIONES.md](DECISIONES.md). Implica:

- Densidad libre — silencios largos entre ataques son aceptables si la fase narrativa lo pide.
- Legibilidad del telegraph manda sobre el flow rítmico al elegir NJS, posición y timing de notas.
- No optimizamos para leaderboard ni ranqueo. Lo que optimizamos es el **wow-factor** y el valor demostrativo del repo.

## Canción

Pendiente de elegir definitivamente. Probable: pieza del OST de *Expedition 33* asociada a Aline o al combate. La elección final condiciona tempo, fases y duración.

> Marcador de decisión: ver entrada en [DECISIONES.md](DECISIONES.md) cuando se cierre.

## Duración objetivo

~2-3 minutos. Suficiente para una estructura por fases sin que el prefab cansante visualmente.

## Narrativa / arc del boss fight

Estructura por fases (a rellenar conforme avance el diseño):

El boss fight tiene tres fases canónicas en E33, identificadas por el idle de Aline: en el suelo, flotando, derrotada. La estructura del mapa las respeta:

| Fase | Idle base | Skills disponibles | Familias en juego | Estado |
|---|---|---|---|---|
| Intro / aparición | — | — | arranca con flow más convencional (BS estándar) antes de pivotar al primer ataque | Pendiente |
| Fase 1 — combate en suelo | `Idle1` | `Skill1`, `Skill2`, `Skill3`, `Skill4`, `Skill5` | A (Skill3, Skill4), B (DashIn-Idle1), B+C (Skill5 con distorsión), E (Skill1), F (Skill2 multi-stage) | Pendiente |
| Transición 1→2 | `Idle1_to_idle2_transition` + `Skill6` | — | beat narrativo: Aline flota, se arma con pincel grande, distorsión | Pendiente |
| Fase 2 — flotando con pincel | `Idle2` | `Skill7`, `Skill8`, `Skill10`, `Skill12` | E (Skill7, Skill10, Skill12), caso especial clímax (Skill8) | Pendiente |
| Transición 2→3 | `Idle2_to_idle3_transition` | — | Aline cae al suelo, derrotada | Pendiente |
| Outro / fase 3 | `Idle3` | `Skill_Aline_P3_Skill1`, `Skill_Aline_P3_Skill2` | sin combate (curaciones narrativas), resolución, fade | Pendiente |

Cuando se concrete cada fase, va a [DECISIONES.md](DECISIONES.md) si hay un porqué grande detrás.

## Familias de ataque

Cada habilidad de Aline se modela como una **familia de ataque reutilizable**: prefab + animación + secuencia de eventos `.dat` + codificación de parry, definida una vez como contrato y instanciada N veces a lo largo del mapa con timings/direcciones distintos.

| Familia | Mecánica | Parry | Source en Aline |
|---|---|---|---|
| **A — Ranged Sequence** | Aline lanza N proyectiles que caen secuencialmente sobre el jugador | Cadena de N notas, cada una codifica origen del proyectil | `Skill3` (3 piedras), `Skill4` (N pequeños) |
| **B — Melee Directional Slash** | Aproximación + corte con línea/streak telegrafiando dirección + retirada | Una nota con dirección **opuesta** al slash | `DashIn-Idle1`, `Skill5` (con C) |
| **D — Shrinking Indicator** | Anillo que se contrae alrededor del bloque, parry de precisión | Nota única en el momento exacto del cierre | invento nuestro (no source clip) |
| **E — Multi-hit Chain** | Cadena de N parries en sucesión rápida durante una animación con N hits embebidos | N notas con separación dictada por la anim | `Skill1` (fase 1), `Skill7`, `Skill10`, `Skill12` (fase 2) |
| **F — Charging AoE Ball** | Aline carga una bola que crece, parry único en la explosión | Nota única en el momento de explosión | `Skill2_Start` / `_Loop` / `_End` |
| **Modificador C — Distortion Overlay** | Filtro post-process grayscale apilable sobre cualquier familia | (no impone parry; lo dicta la familia base) | `Skill5` (canónico, sobre B) |

El catálogo formal con templates de eventos y el mapeo completo Animator→familia vive en [`.claude/skills/vivify-mapping/families.md`](../.claude/skills/vivify-mapping/families.md). Extensible — si surge un patrón que no encaja en ninguna existente, se añade como familia G/H siguiendo el mismo contrato.

## Criterios de éxito

- **Jugable end-to-end**: el mapa se carga, el prefab aparece, las notas se pueden completar sin crashes.
- **Narrativa legible** incluso para alguien que no conoce *Expedition 33*: el espectador entiende que es un boss fight aunque no sepa quién es Aline.
- **Cada ataque es legible**: el telegraph deja claro qué viene y por dónde, antes de que la nota llegue al jugador. Si el ataque no se "lee" sin instrucciones, no está terminado.
- **Performance estable** en hardware medio (no usar shaders pesados sin necesidad).
- **Compatible con BS 1.34.2** (PC). Quest queda fuera de scope salvo decisión expresa.

## Deadlines

- **Torneo**: fecha pendiente.
- **Checkpoint personal**: si en una semana desde el inicio del texturizado no hay progreso visible, pivot a un mapa normal sin Vivify. Mejor un mapa terminado que un boss fight a medias.

## Referencias visuales / inspiración

Pendiente. Apuntar mapas Vivify de la comunidad que sirvan de referencia (notas + prefab interactuando, transiciones de fase, etc.).

## Audiencia

Yo (mapper) + jurado del torneo + comunidad Vivify. **Audiencia secundaria**: espectadores que no juegan BS pero conocen *Expedition 33* — el repo es público y el caso de uso (E33 + BS + Vivify) tiene potencial viral. La calidad de docs y la legibilidad de cada ataque importan también para esta audiencia, que va a ver clips, no a jugarlo.
