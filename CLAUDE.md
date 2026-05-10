# Aline Boss Fight — instructions for Claude Code

This file is a **router**: pointers to the source of truth for each thing, not technical content. If you add a technical rule here, it'll end up contradicting the authoritative doc when that one changes. Any technical fact lives in EXACTLY one place (skill or dedicated doc), CLAUDE.md only links.

## Product

Beat Saber map using [Vivify](https://github.com/Aeroluna/Vivify): boss fight against **Aline (Curatress)** from the game *Expedition 33*. Custom animated 3D prefab on scene, narrative by phases, playable map with Aeroluna's mods on Beat Saber 1.34.2.

| Topic | Doc |
|---|---|
| Concept, narrative, success criteria | [docs/PRODUCTO.md](docs/PRODUCTO.md) |
| Technical pipeline, stack, paths, junctions | [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) |
| Current state and next steps | [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) |
| Big decisions with their rationale | [docs/DECISIONES.md](docs/DECISIONES.md) |
| Exact mod versions | [BS_Dependencies.txt](BS_Dependencies.txt) |
| Live notes / scratchpad | [docs/my-notes.md](docs/my-notes.md) |

**Start every session by reading `docs/NEXT_STEPS.md`.**

---

## User profile

Beat Saber mapper with technical background. First serious project with Vivify.

Treat as a **senior colleague**, not a tutorial. Direct proposals, brief justification, wait to see if they ask when something doesn't add up. Don't explain basic concepts unless they're specific to Vivify/Heck/CustomJSONData. The user verifies outside the conversation (Unity, Beat Saber) and reports back — trust their validation.

---

## Collaboration style

Behavior rules the user has explicitly requested. Keep across sessions.

### Learn from small obstacles — don't sanitize the debugging

The user values going through "small stones" (dead ends, one-off failures, why something doesn't work and what it reveals about the stack) over a clean path that hides the journey. They use it to build intrinsic knowledge. This *does* apply to small stones; it does NOT apply to real risk of losing work or hour-long yak-shaves that probably won't pay off.

- When a tool/script fails: walk through the diagnosis explicitly, no silent retries or "sweep under the rug".
- Framing: "Found: X fails because Y". Don't apologize for running into an obstacle.
- For risky moves (Library/, caches, manifest.json): declare blast radius up front and confirm — but don't avoid the diagnosis just because it might fail.

### Isolate validations — one new system at a time

When a prototype introduces N new systems (animations + VFX + event timing + parry + ...), break it into discrete steps before combining them. Phrases like "we'll validate X during Y" are the failure pattern — that composes X and Y, and a failure can't be pinpointed. If a step exercises more than one new thing, propose explicit sub-steps.

### Bias toward building tooling — manual estimates are optimistic

My estimates of manual friction are systematically low. Past cases (unity-mcp, fmodel-mcp): "5 minutes per query isn't worth it" → 2 actual days lost before building the wrapper.

- If we're going to do >3 queries against an external tool we don't control (FModel GUI, Blender GUI, etc.) in the near term, propose building the wrapper before the 4th query.
- Don't use the deadline as a universal argument against tooling — ask the user; the user's time matters more than my friction estimate.

### Language

- Project documentation (`docs/`, `.claude/skills/`, `README.md`, `CLAUDE.md`): **English** (since 2026-05-11).
- Git messages: **English** (since 2026-04-26).
- Conversation with the user: **Spanish** (user preference).
- Inline code comments / script docstrings: existing Spanish stays as-is; default new ones to English.
- Detail in [docs/DECISIONES.md → "Language"](docs/DECISIONES.md).

---

## Non-negotiable repo rules

Pure rules only (no versions that can drift). For technical facts with a version (map format, schema, unit conversion, etc.) see the authoritative doc or skill linked from here.

1. **Asset paths in lowercase** inside map events. `assets/aline/prefabs/aline.prefab`, not `Assets/Aline/...`. Exact match with `bundleinfo.json`.
2. **Don't commit heavy files.** Exact list in `.gitignore` (`*.vivify`, `*.ogg`, 3D models, binary textures). Unity's `.meta` files do go in. The map (`beatsaber-map/*.dat`, `bundleinfo.json`) **is** versioned — the binaries aren't.
3. **Aeroluna's mods installed by hand** from GitHub. Mod Assistant sometimes serves outdated versions that break dependencies. Versions in [BS_Dependencies.txt](BS_Dependencies.txt).
4. **Any new technical statement in CLAUDE.md → rewrite as a pointer.** If a technical rule starts living here, as soon as it changes there'll be drift. Move the statement to its authoritative doc/skill and leave only the pointer.
5. **Living documentation: every behavior change updates the authoritative doc/skill in the SAME commit.** If the commit changes code/scripts/schema/workflow and doesn't touch docs, something's missing. Concrete rules + checklist + "what goes where" map in the [`docs-governance`](.claude/skills/docs-governance/SKILL.md) skill.

---

## Available skills

Skills live in `.claude/skills/<name>/SKILL.md` and are the **authoritative source** for the operational flows. If a skill contradicts this list, the skill wins (this list is just an index).

- [`vivify-mapping`](.claude/skills/vivify-mapping/SKILL.md) — edit `.dat` (V3 beatmap + V2 Info), Vivify events, CRC sync, families.md (attack catalogue), settings setter, prefab debugging.
- [`unity-rebuild`](.claude/skills/unity-rebuild/SKILL.md) — F5 / Build Configuration Window, CRC sync, build errors, Unity 2019.4 gotchas.
- [`vivify-materials`](.claude/skills/vivify-materials/SKILL.md) — custom shaders for Vivify bundles, FModel→Unity mapping, ambient without SH, magenta/missing troubleshooting.
- [`vivify-animations`](.claude/skills/vivify-animations/SKILL.md) — `.psa` → Blender → FBX → Unity Animator → Vivify pipeline. Scripts in `scripts/blender/` + Editor scripts in `Assets/Aline/Editor/`.
- [`vivify-environment`](.claude/skills/vivify-environment/SKILL.md) — skybox, disable BS env, custom scenery, 3D decoration, FBX axis flip.
- [`docs-governance`](.claude/skills/docs-governance/SKILL.md) — which fact goes to which doc, when to update what, what NOT to put in CLAUDE.md or memory.
- [`remapper-scripting`](.claude/skills/remapper-scripting/SKILL.md) — skeleton. Gets filled in when we start using ReMapper.

## Tools outside the repo

They live in `d:\vivify_repo\` (containing folder). Detail in [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) section "Outside the repo".

- `fmodel-mcp/` — canonical wrapper for inspecting/exporting E33 assets. .NET CLI over CUE4Parse + Python MCP server. Tools `mcp__fmodel__fmodel_*` in Claude Code. Public repo at [github.com/luisep92/fmodel-mcp](https://github.com/luisep92/fmodel-mcp).
- `unity-mcp/` — minimal fork of MCP for Unity ported to Unity 2019.4. Tools `mcp__unity-mcp__*` in Claude. Wired in via `Packages/manifest.json`. Detail in [unity-mcp/README.md](../unity-mcp/README.md).
- `FModel.exe`, `ReMapper-master/` — fallback GUI / Deno scripting (the latter not used yet).
- `CustomNotesUnityProject/` — reference Unity project from [legoandmars/CustomNotesUnityProject](https://github.com/legoandmars/CustomNotesUnityProject), used as a base for the visual cube polish (mesh + prefab structure). No `NoteDescriptor` (CustomNotes-only component).
- `_outline-shader-ref/` — `.shader` files from Ronja downloaded directly (CC-BY 4.0) as the base for the inverted-hull shader for the custom cubes.
