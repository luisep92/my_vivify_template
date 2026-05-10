# PRODUCTO — Aline Boss Fight

## Concept

**Showcase map** for Beat Saber, **boss fight** style, against **Aline**, the Curatress from *Expedition 33*. Aline's 3D prefab appears on scene as the enemy and starts throwing abilities; each ability is a **telegraphed attack** with a **parry window** the player resolves by hitting a directional note. The translation is direct: E33's parry system (timing + direction) is already, mechanically, what BS does.

It's not a "normal" map with Vivify gimmicks, nor a regular rhythmic map. The notes are the embodiment of the parry, not the song's rhythmic flow. The music plays as ambience.

## Tone

**Cinematic showcase, not scored.** Decision locked in [DECISIONES.md](DECISIONES.md). Implies:

- Density is free — long silences between attacks are acceptable if the narrative phase calls for it.
- Telegraph legibility wins over rhythmic flow when picking NJS, position and note timing.
- We don't optimize for leaderboard or ranking. What we optimize for is the **wow-factor** and the demonstrative value of the repo.

## Song

Pending final pick. Likely: a piece from the *Expedition 33* OST associated with Aline or the combat. The final pick conditions tempo, phases and duration.

> Decision marker: see entry in [DECISIONES.md](DECISIONES.md) when it closes.

## Target duration

~2-3 minutes. Enough for a phase structure without the prefab getting visually tiring.

## Narrative / boss fight arc

Phase structure (to fill in as design progresses):

The boss fight has three canonical phases in E33, identified by Aline's idle: on the ground, floating, defeated. The map structure respects them:

| Phase | Base idle | Available skills | Families in play | State |
|---|---|---|---|---|
| Intro / appearance | — | — | starts with a more conventional flow (standard BS) before pivoting to the first attack | Pending |
| Phase 1 — ground combat | `Idle1` | `Skill1`, `Skill2`, `Skill3`, `Skill4`, `Skill5` | A (Skill3, Skill4), B (DashIn-Idle1), B+C (Skill5 with distortion), E (Skill1), F (Skill2 multi-stage) | Pending |
| Transition 1→2 | `Idle1_to_idle2_transition` + `Skill6` | — | narrative beat: Aline floats, arms herself with the big brush, distortion | Pending |
| Phase 2 — floating with brush | `Idle2` | `Skill7`, `Skill8`, `Skill10`, `Skill12` | E (Skill7, Skill10, Skill12), special climax case (Skill8) | Pending |
| Transition 2→3 | `Idle2_to_idle3_transition` | — | Aline falls to the ground, defeated | Pending |
| Outro / phase 3 | `Idle3` | `Skill_Aline_P3_Skill1`, `Skill_Aline_P3_Skill2` | no combat (narrative healing), resolution, fade | Pending |

When each phase gets nailed down, it goes to [DECISIONES.md](DECISIONES.md) if there's a big rationale behind it.

## Attack families

Each of Aline's abilities is modeled as a **reusable attack family**: prefab + animation + `.dat` event sequence + parry encoding, defined once as a contract and instantiated N times across the map with different timings/directions.

| Family | Mechanic | Parry | Source in Aline |
|---|---|---|---|
| **A — Ranged Sequence** | Aline throws N projectiles that fall sequentially on the player | Chain of N notes, each one encodes the projectile's origin | `Skill3` (3 stones), `Skill4` (N small ones) |
| **B — Melee Directional Slash** | Approach + slash with a line/streak telegraphing direction + retreat | A single note with direction **opposite** to the slash | `DashIn-Idle1`, `Skill5` (with C) |
| **D — Shrinking Indicator** | Ring contracting around the block, precision parry | Single note at the exact moment of closure | our own invention (no source clip) |
| **E — Multi-hit Chain** | Chain of N parries in rapid succession during an animation with N hits embedded | N notes with separation dictated by the anim | `Skill1` (phase 1), `Skill7`, `Skill10`, `Skill12` (phase 2) |
| **F — Charging AoE Ball** | Aline charges a ball that grows, single parry on the explosion | Single note at the moment of explosion | `Skill2_Start` / `_Loop` / `_End` |
| **Modifier C — Distortion Overlay** | Grayscale post-process filter stackable on any family | (doesn't impose a parry; the base family dictates it) | `Skill5` (canonical, on top of B) |

The formal catalogue with event templates and the full Animator→family mapping lives in [`.claude/skills/vivify-mapping/families.md`](../.claude/skills/vivify-mapping/families.md). Extensible — if a pattern shows up that doesn't fit any existing one, it's added as family G/H following the same contract.

## Success criteria

- **Playable end-to-end**: the map loads, the prefab appears, the notes can be completed without crashes.
- **Legible narrative** even for someone who doesn't know *Expedition 33*: the viewer understands it's a boss fight even if they don't know who Aline is.
- **Every attack is legible**: the telegraph makes clear what's coming and from where, before the note reaches the player. If the attack doesn't "read" without instructions, it's not finished.
- **Stable performance** on mid-range hardware (don't use heavy shaders unnecessarily).
- **Compatible with BS 1.34.2** (PC). Quest is out of scope unless explicitly decided otherwise.

## Deadlines

- **Tournament**: date pending.
- **Personal checkpoint**: if a week from the start of texturing there's no visible progress, pivot to a normal map without Vivify. Better a finished map than a half-done boss fight.

## Visual references / inspiration

Pending. Note down Vivify community maps that can serve as reference (notes + prefab interacting, phase transitions, etc.).

## Audience

Me (mapper) + tournament jury + Vivify community. **Secondary audience**: viewers who don't play BS but know *Expedition 33* — the repo is public and the use case (E33 + BS + Vivify) has viral potential. The quality of docs and the legibility of each attack matter for this audience too, who will watch clips, not play it.
