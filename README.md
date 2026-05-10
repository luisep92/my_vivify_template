# my_vivify_template

A working repo around a Beat Saber **boss fight against Aline (Curatress)** from *Expedition 33*, built on top of [Vivify](https://github.com/Aeroluna/Vivify) — Aeroluna's mod that runs a full Unity 2019.4 scene inside Beat Saber 1.34.2.

The map is the *validation case*. What I'm actually shaping inside this repo is one layer above: **a Vivify mapping harness any mapper can take to drive their own map with AI assistance, regardless of the source IP** — Unity template, MCP servers, Claude Code skills covering every layer of the workflow.

**Status:** WIP. Repo is public and under active development. The Aline map is not yet released; the harness is still consolidating. The public artifacts (MCP servers, skills, Unity template) get separated and hardened as they stabilise.

---

## Demos

- **First integrated ability** — [youtu.be/3nEch2zoHHY](https://youtu.be/3nEch2zoHHY)
- **Animation playground** — [youtu.be/XEcCdVtlG4g](https://youtu.be/XEcCdVtlG4g)

Both are short. The portfolio writeup with more context lives at [luisescolano.com/projects/aline-boss-fight](https://luisescolano.com/projects/aline-boss-fight).

---

## What's in here

- [`VivifyTemplate/`](VivifyTemplate/) — Unity 2019.4 project. Custom Aline prefab, scene, materials, animation rigs. The Unity template a new mapper would fork.
- [`beatsaber-map/`](beatsaber-map/) — the playable `.dat` (V3 beatmap + V2 Info), event timing, custom data.
- [`docs/`](docs/) — internal product/architecture/decisions docs. The split mirrors the [`docs-governance`](.claude/skills/docs-governance/SKILL.md) skill: `PRODUCTO.md` (goal), `ARQUITECTURA.md` (technical pipeline), `DECISIONES.md` (decision log), `NEXT_STEPS.md` (work queue).
- [`scripts/`](scripts/) — Blender scripts for the `.psa` → FBX pipeline, CRC sync, map snapshotting, calibration build.
- [`.claude/skills/`](.claude/skills/) — Claude Code skills, one per workflow layer:
  - `vivify-mapping` — `.dat` editing, Vivify events, families catalogue, settings setter
  - `vivify-materials` — custom shaders for Vivify bundles, FModel→Unity mapping
  - `vivify-animations` — `.psa` → Blender → FBX → Unity Animator → Vivify pipeline
  - `vivify-environment` — skybox, custom scenery, FBX axis flip
  - `unity-rebuild` — F5 / Build Configuration Window, CRC sync, Unity 2019.4 gotchas
  - `docs-governance` — what fact goes where, what NOT to put in CLAUDE.md or memory
  - `remapper-scripting` — placeholder, to be filled when ReMapper enters the loop
- [`CLAUDE.md`](CLAUDE.md) — router for Claude Code: pointers to the authoritative docs and skills, plus collaboration rules for this repo.
- [`BS_Dependencies.txt`](BS_Dependencies.txt) — exact mod versions (mods of Aeroluna installed by hand from GitHub; Mod Assistant ships outdated builds that break dependencies).

---

## External tools the harness wires in

The first two are mine — built when the friction of the manual loop got in the way. The third is community-maintained and slots into the same chain:

- **[`fmodel-mcp`](https://github.com/luisep92/fmodel-mcp)** — MCP wrapper around FModel + CUE4Parse for inspecting and exporting Unreal Engine assets from Claude. Driver was 30+ FModel GUI queries per session for E33; the MCP turns each into one tool call.
- **[`unity_vivify_mcp`](https://github.com/luisep92/unity_vivify_mcp)** — minimal fork of [`CoplayDev/unity-mcp`](https://github.com/CoplayDev/unity-mcp) backported to Unity 2019.4 (BS modding targets 2019.4; upstream requires 2021.3+). Strips post-2020 APIs, rewrites ~41 sites of C# 8/9 syntax to 7.3.
- **[`blender-mcp`](https://github.com/ahujasid/blender-mcp)** — community MCP that exposes Blender to Claude. Sits between `fmodel-mcp` (asset extraction) and `unity_vivify_mcp` (in-engine assembly), driving the `.psa` → FBX conversion and the prep work needed before Unity import.

The pattern: build tooling rather than absorb the friction. The two MCPs I wrote came out of problems I couldn't solve at the speed I needed; the harness wires them together with `blender-mcp` and the skills below into a single workflow Claude can drive end to end.

---

## Stack

- Beat Saber 1.34.2 + Vivify 1.0.7+ / Heck 1.8.1+ / CustomJSONData / Chroma / NoodleExtensions. See [`BS_Dependencies.txt`](BS_Dependencies.txt) for exact versions and install notes.
- Unity 2019.4 LTS.
- Blender for animation conversion (`.psa` → FBX).
- Claude Code with the skills under `.claude/skills/` and the two MCP servers above.

---

## License

See [`LICENSE`](LICENSE). The Aline character and *Expedition 33* assets used during development belong to Sandfall Interactive / Kepler Interactive — the map is a personal, non-commercial fan project, not for distribution of source assets.
