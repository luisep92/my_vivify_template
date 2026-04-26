---
name: remapper-scripting
description: Use when working with ReMapper (Deno/TypeScript) to script Beat Saber map content programmatically. Trigger when user mentions 'ReMapper', 'remapper', 'script the map', or wants to generate notes/walls/events programmatically instead of placing them by hand in ChroMapper.
---

# ReMapper Scripting

ReMapper es una tool de Deno/TypeScript para generar contenido del mapa
programáticamente (notas, paredes, eventos custom) en lugar de colocarlos a
mano en ChroMapper.

## Estado: TO BE DONE

Esta skill es un **esqueleto**. El contenido real se rellena cuando empecemos
a usar ReMapper de verdad (paso 4 de [docs/NEXT_STEPS.md](../../../docs/NEXT_STEPS.md)).

## Dónde vive

ReMapper está en `d:\vivify_repo\ReMapper-master\` — fuera del repo principal,
en la carpeta contenedora. Tiene su propio `.git`. Decisión documentada en
[docs/DECISIONES.md](../../../docs/DECISIONES.md).

## Pendiente de cubrir cuando empecemos

- Setup inicial (instalar Deno, primer script "hello world")
- Patrón de invocación desde el repo (script wrapper en `scripts/`?)
- Output target: ¿escribir directo a `beatsaber-map/ExpertPlusStandard.dat`? ¿Staging intermedio?
- Cómo combinar ReMapper con eventos Vivify ya existentes (no pisarlos)
- Errores comunes en runtime de Deno
- Patrones útiles: generadores de patrones, wall arts, eventos sincronizados

## Mientras tanto

Si el usuario pregunta por ReMapper antes de que esté hecho el setup:
- El repo de referencia está en `d:\vivify_repo\ReMapper-master\src/`
- Documentación oficial: ver `docs/heckdocs-main/` y el README dentro del propio ReMapper
- Antes de empezar, decidir el flujo de output — esa decisión condiciona todo lo demás
