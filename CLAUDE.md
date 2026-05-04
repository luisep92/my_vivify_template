# Aline Boss Fight — instrucciones para Claude Code

Este archivo es **router**: pointers a la fuente de verdad de cada cosa, no contenido técnico. Si añades una regla técnica aquí, terminará contradiciendo la doc autoritativa cuando esa cambie. Cualquier hecho técnico vive en EXACTAMENTE un sitio (skill o doc dedicado), CLAUDE.md solo enlaza.

## Producto

Mapa de Beat Saber con [Vivify](https://github.com/Aeroluna/Vivify): boss fight contra **Aline (Curatress)** del juego *Expedition 33*. Custom prefab 3D animado en escena, narrativa por fases, mapa jugable con mods de Aeroluna sobre Beat Saber 1.34.2.

| Tema | Doc |
|---|---|
| Concepto, narrativa, criterios de éxito | [docs/PRODUCTO.md](docs/PRODUCTO.md) |
| Pipeline técnico, stack, paths, junctions | [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) |
| Estado actual y próximos pasos | [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) |
| Decisiones grandes con su porqué | [docs/DECISIONES.md](docs/DECISIONES.md) |
| Versiones exactas de mods | [BS_Dependencies.txt](BS_Dependencies.txt) |
| Notas vivas / scratchpad | [docs/my-notes.md](docs/my-notes.md) |

**Empezar cada sesión leyendo `docs/NEXT_STEPS.md`.**

---

## Perfil del usuario

Mapper de Beat Saber con experiencia técnica. Primer proyecto serio con Vivify.

Trato de **colega senior**, no de tutorial. Propuestas directas, justificación breve, esperar a que pregunte si algo no le cuadra. No explicar conceptos básicos salvo que sean específicos de Vivify/Heck/CustomJSONData. El usuario verifica fuera de la conversación (Unity, Beat Saber) y reporta — confiar en su validación.

---

## Estilo de colaboración

Reglas de comportamiento que el usuario ha pedido explícitamente. Mantener entre sesiones.

### Aprender de los obstáculos pequeños — no sanitizar el debugging

El usuario valora pasar por "piedras pequeñas" (dead ends, fallos puntuales, por qué algo no funciona y qué revela del stack) por encima de un camino limpio que esconde el journey. Lo usa para construir conocimiento intrínseco. *Sí* aplica a piedras pequeñas; NO aplica a riesgo real de pérdida de trabajo o yak-shaves de horas que probablemente no rindan.

- Cuando un tool/script falla: walk through el diagnóstico explícitamente, no retry silente ni "sweep under the rug".
- Framing: "Encontrado: X falla porque Y". No disculparse por encontrarse un obstáculo.
- Para movimientos arriesgados (Library/, caches, manifest.json): declarar blast radius arriba y confirmar — pero no evitar la diagnosis solo porque puede fallar.

### Aislar validaciones — un sistema nuevo a la vez

Cuando un prototipo introduce N sistemas nuevos (animaciones + VFX + event timing + parry + ...), partir en pasos discretos antes de combinarlos. Frases como "validamos X durante Y" son la failure pattern — eso compone X y Y, y un fallo no se puede pinpointar. Si un paso ejercita más de una cosa nueva, proponer sub-pasos explícitos.

### Bias hacia construir tooling — los estimates manuales son optimistas

Mis estimates de fricción manual son sistemáticamente bajos. Casos pasados (unity-mcp, fmodel-mcp): "5 minutos por consulta no merece la pena" → 2 días reales perdidos antes de construir el wrapper.

- Si vamos a hacer >3 consultas a una herramienta externa que no controlamos (FModel GUI, Blender GUI, etc.) en el horizonte cercano, proponer construir el wrapper antes de la 4ª consulta.
- No usar el deadline como argumento universal contra tooling — preguntar al usuario; el tiempo del usuario importa más que mi estimate de fricción.

### Idioma

- Conversación y archivos del proyecto (docs, código, comments): **español**.
- Mensajes de git desde 2026-04-26: **inglés**. Los iniciales en español se quedan como están. Detalle en [docs/DECISIONES.md → "Idioma"](docs/DECISIONES.md).

---

## Reglas no negociables del repo

Solo reglas puras (sin versiones que puedan drift). Para hechos técnicos con versión (formato del mapa, schema, conversión de unidades, etc.) ver el doc o skill autoritativos enlazados desde aquí.

1. **Asset paths en lowercase** dentro de eventos del mapa. `assets/aline/prefabs/aline.prefab`, no `Assets/Aline/...`. Match exacto con `bundleinfo.json`.
2. **No commitear archivos pesados.** Lista exacta en `.gitignore` (`*.vivify`, `*.ogg`, modelos 3D, texturas binarias). Los `.meta` de Unity sí. El mapa (`beatsaber-map/*.dat`, `bundleinfo.json`) **sí se versiona** — los binarios no.
3. **Mods de Aeroluna instalados a mano** desde GitHub. Mod Assistant a veces sirve versiones obsoletas que rompen dependencias. Versiones en [BS_Dependencies.txt](BS_Dependencies.txt).
4. **Cualquier afirmación técnica nueva en CLAUDE.md → reescribir como pointer.** Si una regla técnica empieza a vivir aquí, en cuanto cambie habrá drift. Mover la afirmación a su doc/skill autoritativo y dejar solo el pointer.
5. **Documentación viva: cada cambio de comportamiento actualiza el doc/skill autoritativo en el MISMO commit.** Si el commit cambia código/scripts/schema/workflow y no toca docs, falta algo. Reglas concretas + checklist + mapa "qué va dónde" en la skill [`docs-governance`](.claude/skills/docs-governance/SKILL.md).

---

## Skills disponibles

Skills viven en `.claude/skills/<name>/SKILL.md` y son la **fuente autoritativa** de los flujos operativos. Si una skill se contradice con esta lista, prevalece la skill (esta lista es solo índice).

- [`vivify-mapping`](.claude/skills/vivify-mapping/SKILL.md) — editar `.dat` (V3 beatmap + V2 Info), eventos Vivify, CRC sync, families.md (catálogo de ataques), settings setter, debugging de prefabs.
- [`unity-rebuild`](.claude/skills/unity-rebuild/SKILL.md) — F5 / Build Configuration Window, sync de CRCs, errores de build, gotchas de Unity 2019.4.
- [`vivify-materials`](.claude/skills/vivify-materials/SKILL.md) — shaders custom para bundles Vivify, mapping FModel→Unity, ambient sin SH, troubleshooting magenta/missing.
- [`vivify-animations`](.claude/skills/vivify-animations/SKILL.md) — pipeline `.psa` → Blender → FBX → Unity Animator → Vivify. Scripts en `scripts/blender/` + Editor scripts en `Assets/Aline/Editor/`.
- [`vivify-environment`](.claude/skills/vivify-environment/SKILL.md) — skybox, disable BS env, escenario custom, decoración 3D, FBX axis flip.
- [`docs-governance`](.claude/skills/docs-governance/SKILL.md) — qué hecho va a qué doc, cuándo actualizar qué, qué NO meter en CLAUDE.md ni en memory.
- [`remapper-scripting`](.claude/skills/remapper-scripting/SKILL.md) — esqueleto. Se rellena cuando empecemos a usar ReMapper.

## Tools fuera del repo

Viven en `d:\vivify_repo\` (carpeta contenedora). Detalle en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) sección "Fuera del repo".

- `fmodel-mcp/` — wrapper canónico para inspeccionar/exportar assets de E33. CLI .NET sobre CUE4Parse + MCP server Python. Tools `mcp__fmodel__fmodel_*` en Claude Code. Repo público en [github.com/luisep92/fmodel-mcp](https://github.com/luisep92/fmodel-mcp).
- `unity-mcp/` — fork minimal del MCP for Unity portado a Unity 2019.4. Tools `mcp__unity-mcp__*` en Claude. Wireado vía `Packages/manifest.json`. Detalle en [unity-mcp/README.md](../unity-mcp/README.md).
- `FModel.exe`, `ReMapper-master/` — fallback GUI / scripting Deno (este último aún sin usar).
- `CustomNotesUnityProject/` — reference Unity project de [legoandmars/CustomNotesUnityProject](https://github.com/legoandmars/CustomNotesUnityProject), usado como base para el polish del cube visual (mesh + estructura de prefab). Sin `NoteDescriptor` (componente CustomNotes-only).
- `_outline-shader-ref/` — `.shader` files de Ronja descargados directos (CC-BY 4.0) como base del shader inverted-hull para los cubos custom.
