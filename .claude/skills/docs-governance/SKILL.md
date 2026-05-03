---
name: docs-governance
description: Use whenever you change behavior, decisions, paths, or workflows that the documentation describes. Trigger when introducing/removing scripts, when changing a non-negotiable rule, when revisiting a deferred decision, when finishing a task that was tracked in NEXT_STEPS, when a session-learning is worth persisting, or when the user asks "is this documented?". Also when you spot drift between docs and code.
---

# Docs governance

Reglas para mantener la documentación viva: dónde vive cada hecho, cuándo actualizar qué, qué NO hacer.

## Principio raíz

**Cada hecho técnico vive en exactamente UN sitio (la fuente autoritativa). Todo lo demás enlaza, no copia.** Si un hecho aparece en dos sitios, en cuanto cambie habrá drift. CLAUDE.md es router, no contenedor.

## Mapa: qué va dónde

| Si lo que aprendes/cambias es... | Va a... | NO va a... |
|---|---|---|
| Una decisión grande con su porqué | [`docs/DECISIONES.md`](../../../docs/DECISIONES.md) | NEXT_STEPS, memory |
| Estructura del pipeline, paths, stack, junctions, recovery | [`docs/ARQUITECTURA.md`](../../../docs/ARQUITECTURA.md) | NEXT_STEPS (solo summary line si aplica) |
| Estado actual del proyecto / próxima cosa a hacer | [`docs/NEXT_STEPS.md`](../../../docs/NEXT_STEPS.md) | DECISIONES, memory |
| Concepto del producto, narrativa, criterios de éxito | [`docs/PRODUCTO.md`](../../../docs/PRODUCTO.md) | otros |
| Receta operativa de un dominio (cómo editar `.dat`, cómo construir mesh, cómo build, cómo material, cómo animaciones) | Skill correspondiente en `.claude/skills/<area>/SKILL.md` | DECISIONES (solo si la decisión sobre la receta es no-negociable) |
| Catálogo de familias de ataque | [`.claude/skills/vivify-mapping/families.md`](../vivify-mapping/families.md) | otros |
| Idea / duda / scratch sin sitio definitivo | [`docs/my-notes.md`](../../../docs/my-notes.md) — emigra cuando madure | docs autoritativos |
| Comportamiento de un script | Docstring del script | docs (solo summary + link si aplica) |
| Versión exacta de un mod | [`BS_Dependencies.txt`](../../../BS_Dependencies.txt) | otros |
| Personal memory (`~/.claude/projects/.../memory/`) | **Nada del proyecto.** Memory queda vacío. | cualquier hecho del proyecto |

## Cuándo actualizar docs (en el MISMO commit que el cambio)

Cualquier cambio que invalide una afirmación existente de la documentación debe actualizar el doc autoritativo en el mismo commit. Si el commit cambia comportamiento y no toca docs, falta algo.

Triggers concretos para revisar y actualizar:

- **Añades / borras un script** → ARQUITECTURA.md tabla "Dentro del repo" + posible referencia en skill correspondiente.
- **Cambias formato de un archivo del proyecto** (V2/V3, schema, encoding) → DECISIONES.md (la decisión) + skill operativa (las recetas).
- **Cambias regla de gitignore** → ARQUITECTURA.md "Recovery" + tabla de versionado.
- **Cierras un step de NEXT_STEPS** → NEXT_STEPS.md (estado del step + estado actual de cabecera si cambió).
- **Decides algo grande** (architectural, scope, deadline) → DECISIONES.md (entrada nueva).
- **Encuentras un gotcha repetible** (`SetRenderingSettings.skybox` solo no rinde, `DestroyPrefab` no existe, etc) → skill del área correspondiente.
- **Cambias un workflow** (cómo se buildea, cómo se sincroniza, cómo se importa) → skill operativa.

## Cuándo NO meter algo en docs

- **No documentar especulación.** Si "creo que funciona así" pero no está validado, va a `my-notes.md` flagged como hipótesis. Cuando se valide, emigra a su sitio definitivo. Hechos no verificados en docs autoritativos = trampa para sesiones futuras.
- **No documentar relato histórico.** "Antes esto era X, lo migramos a Y" no aporta — solo aporta el estado actual. Excepción: una entrada de DECISIONES.md sí captura el porqué de la decisión, pero no archaeology de pasos intermedios.
- **No duplicar.** Si lo dice ARQUITECTURA.md, no lo repitas en CLAUDE.md ni en una skill — link.
- **No meter nada en CLAUDE.md** que no sea router, perfil del usuario, estilo de colaboración, o regla pura sin versión que pueda drift.
- **No usar memory** para hechos del proyecto. Memory está intencionalmente vacío para este proyecto. Toda info persistente va a docs versionados.

## Checklist antes de cerrar un commit con cambio de comportamiento

1. ¿He tocado un script, regla, schema, workflow, decisión? → ¿está actualizado el doc/skill autoritativo?
2. ¿He añadido un hecho técnico nuevo? → ¿vive en UN solo sitio?
3. ¿El commit borra/renombra algo referenciado? → grep por el nombre viejo en `docs/` y `.claude/`.
4. ¿Cierro un item de NEXT_STEPS? → marca el item + actualiza "Estado actual" si cambió.
5. ¿Memoria personal modificada en el camino? → migrar a docs y borrar (memory queda vacío para este proyecto).

## Auditoría periódica

Cuando el usuario pida una revisión ("repasar cada letra de la documentación") o cuando la sesión sea larga y haya pivots:

1. **`grep` por referencias rotas**: `memoria \`X\``, paths a archivos borrados, links a docs/secciones que ya no existen.
2. **Releer docs como cold-clone**: ¿alguien que se baja el repo hoy puede arrancar? ¿sabe qué se versiona y qué no? ¿sabe cómo recuperar lo que se pierda? → actualizar Bootstrap / Recovery en ARQUITECTURA.md.
3. **Verificar internal consistency**: estado de cabecera de NEXT_STEPS vs estado real de los subpasos, decisiones contradictorias entre DECISIONES.md y skills, formatos en ejemplos vs realidad del código.
4. **Borrar lo que ya no aplica**: docs de tareas terminadas, secciones que cubrían un gotcha ya resuelto y obsoleto, etc.
