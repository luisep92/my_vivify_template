---
name: remapper-scripting
description: Use when working with ReMapper (Deno/TypeScript) to script Beat Saber map content programmatically. Trigger when user mentions 'ReMapper', 'remapper', 'script the map', or wants to generate notes/walls/events programmatically instead of placing them by hand in ChroMapper.
---

# ReMapper Scripting

ReMapper is a Deno/TypeScript tool to generate map content programmatically
(notes, walls, custom events) instead of placing them by hand in ChroMapper.

## Status: TO BE DONE

This skill is a **skeleton**. The real content gets filled in when we actually
start using ReMapper (step 4 of [docs/NEXT_STEPS.md](../../../docs/NEXT_STEPS.md)).

## Where it lives

ReMapper is at `d:\vivify_repo\ReMapper-master\` — outside the main repo,
in the containing folder. It has its own `.git`. Decision documented in
[docs/DECISIONES.md](../../../docs/DECISIONES.md).

## Pending to cover when we start

- Initial setup (install Deno, first "hello world" script)
- Invocation pattern from the repo (wrapper script in `scripts/`?)
- Output target: write directly to `beatsaber-map/ExpertPlusStandard.dat`? Intermediate staging?
- How to combine ReMapper with existing Vivify events (not stomp on them)
- Common errors in Deno runtime
- Useful patterns: pattern generators, wall arts, synced events

## In the meantime

If the user asks about ReMapper before the setup is done:
- The reference repo is at `d:\vivify_repo\ReMapper-master\src/`
- Official documentation: see `docs/heckdocs-main/` and the README inside ReMapper itself
- Before starting, decide the output flow — that decision conditions everything else
