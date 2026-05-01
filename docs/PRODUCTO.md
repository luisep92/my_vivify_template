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

| Fase | Idea | Estado |
|---|---|---|
| Intro / aparición | Aline entra en escena. Puede arrancar como BS más convencional para anclar al jugador antes de pivotar. | Pendiente |
| Combate base | Cascada de ataques telegrafiados con ventana de parry. Mezcla de familias A/B (ranged + melee). | Pendiente |
| Transición / cambio de fase | Cambio visual del prefab, intensificación, primera aparición de la familia C (distortion window). | Pendiente |
| Climax | Pico de espectáculo. Combinaciones de familias y/o introducción de la familia D (shrinking indicator). | Pendiente |
| Outro | Resolución, fade, créditos visuales si aplica. | Pendiente |

Cuando se concrete cada fase, va a [DECISIONES.md](DECISIONES.md) si hay un porqué grande detrás.

## Familias de ataque

Cada habilidad de Aline se modela como una **familia de ataque reutilizable**: prefab + animación + secuencia de eventos `.dat` + codificación de parry, definida una vez como contrato y instanciada N veces a lo largo del mapa con timings/direcciones distintos.

| Familia | Mecánica | Parry |
|---|---|---|
| **A — Ranged Sequence** | Aline lanza N proyectiles que caen secuencialmente sobre el jugador | Cadena de N notas, cada una codifica origen del proyectil |
| **B — Melee Directional Slash** | Corte rápido con línea/streak telegrafiando la dirección | Una nota con dirección **opuesta** al slash |
| **C — Distortion Window** | Filtro post-process desaturado abre ventana de parry | Nota única dentro de la ventana grayscale |
| **D — Shrinking Indicator** | Anillo que se contrae alrededor del bloque, parry de precisión | Nota única en el momento exacto del cierre |

El catálogo formal con templates de eventos vive en la skill [`.claude/skills/vivify-mapping/`](../.claude/skills/vivify-mapping/). Extensible — si surgen más patrones (multi-hit chain, AoE, contraataque) se añaden como familias E/F siguiendo el mismo contrato.

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
