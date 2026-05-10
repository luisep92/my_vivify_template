---
name: docs-governance
description: Use whenever you change behavior, decisions, paths, or workflows that the documentation describes. Trigger when introducing/removing scripts, when changing a non-negotiable rule, when revisiting a deferred decision, when finishing a task that was tracked in NEXT_STEPS, when a session-learning is worth persisting, or when the user asks "is this documented?". Also when you spot drift between docs and code.
---

# Docs governance

Rules to keep documentation alive: where each fact lives, when to update what, what NOT to do.

## Root principle

**Each technical fact lives in exactly ONE place (the authoritative source). Everything else links, doesn't copy.** If a fact shows up in two places, the moment it changes there will be drift. CLAUDE.md is a router, not a container.

## Map: what goes where

| If what you're learning/changing is... | Goes to... | Does NOT go to... |
|---|---|---|
| A big decision with its rationale | [`docs/DECISIONES.md`](../../../docs/DECISIONES.md) | NEXT_STEPS, memory |
| Pipeline structure, paths, stack, junctions, recovery | [`docs/ARQUITECTURA.md`](../../../docs/ARQUITECTURA.md) | NEXT_STEPS (only summary line if applicable) |
| Current state of the project / next thing to do | [`docs/NEXT_STEPS.md`](../../../docs/NEXT_STEPS.md) | DECISIONES, memory |
| Product concept, narrative, success criteria | [`docs/PRODUCTO.md`](../../../docs/PRODUCTO.md) | others |
| Operational recipe for a domain (how to edit `.dat`, how to build a mesh, how to build, how to material, how to animations) | Corresponding skill in `.claude/skills/<area>/SKILL.md` | DECISIONES (only if the decision about the recipe is non-negotiable) |
| Attack families catalogue | [`.claude/skills/vivify-mapping/families.md`](../vivify-mapping/families.md) | others |
| Idea / question / scratch without a definitive home | [`docs/my-notes.md`](../../../docs/my-notes.md) — migrates when it matures | authoritative docs |
| Behavior of a script | The script's docstring | docs (only summary + link if applicable) |
| Exact version of a mod | [`BS_Dependencies.txt`](../../../BS_Dependencies.txt) | others |
| Personal memory (`~/.claude/projects/.../memory/`) | **Nothing project-related.** Memory stays empty. | any project fact |

## When to update docs (in the SAME commit as the change)

Any change that invalidates an existing statement in the documentation should update the authoritative doc in the same commit. If the commit changes behavior and doesn't touch docs, something's missing.

Concrete triggers to review and update:

- **You add / delete a script** → ARQUITECTURA.md "Inside the repo" table + possible reference in the corresponding skill.
- **You change the format of a project file** (V2/V3, schema, encoding) → DECISIONES.md (the decision) + operational skill (the recipes).
- **You change a gitignore rule** → ARQUITECTURA.md "Recovery" + versioning table.
- **You close a NEXT_STEPS step** → NEXT_STEPS.md (step state + header current-state if it changed).
- **You decide something big** (architectural, scope, deadline) → DECISIONES.md (new entry).
- **You find a repeatable gotcha** (`SetRenderingSettings.skybox` alone doesn't render, `DestroyPrefab` doesn't exist, etc) → skill of the corresponding area.
- **You change a workflow** (how it builds, how it syncs, how it imports) → operational skill.

## When NOT to put something in docs

- **Don't document speculation.** If "I think it works like this" but it's not validated, it goes to `my-notes.md` flagged as a hypothesis. When validated, migrate to its final home. Unverified facts in authoritative docs = trap for future sessions.
- **Don't document historical narrative.** "This used to be X, we migrated to Y" doesn't help — only the current state helps. Exception: a DECISIONES.md entry does capture the why of the decision, but no archaeology of intermediate steps.
- **Don't duplicate.** If ARQUITECTURA.md says it, don't repeat it in CLAUDE.md or a skill — link.
- **Don't put anything in CLAUDE.md** that isn't router, user profile, collaboration style, or pure rule with no version that could drift.
- **Don't use memory** for project facts. Memory is intentionally empty for this project. All persistent info goes into versioned docs.

## Checklist before closing a commit with a behavior change

1. Did I touch a script, rule, schema, workflow, decision? → is the authoritative doc/skill updated?
2. Did I add a new technical fact? → does it live in ONE place only?
3. Does the commit delete/rename something referenced? → grep for the old name in `docs/` and `.claude/`.
4. Closing a NEXT_STEPS item? → mark the item + update "Current state" if it changed.
5. Personal memory modified along the way? → migrate to docs and delete (memory stays empty for this project).

## Periodic audit

When the user asks for a review ("go over every letter of the documentation") or when the session is long and there have been pivots:

1. **`grep` for broken references**: `memory \`X\``, paths to deleted files, links to docs/sections that no longer exist.
2. **Re-read docs as a cold-clone**: can someone who clones the repo today get started? Do they know what's versioned and what isn't? Do they know how to recover what gets lost? → update Bootstrap / Recovery in ARQUITECTURA.md.
3. **Verify internal consistency**: NEXT_STEPS header state vs actual state of substeps, contradictory decisions between DECISIONES.md and skills, formats in examples vs reality of the code.
4. **Delete what no longer applies**: docs of finished tasks, sections that covered a gotcha that's now resolved and obsolete, etc.
