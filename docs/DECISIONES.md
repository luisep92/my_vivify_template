# DECISIONES

Hard project rules, one entry per decision. Just the "what" and a paragraph of "why". If you need to dig into the history or what got discarded, check `git log` and the chat threads.

---

### Tone: cinematic showcase, not scored

**Rule:** The map is a **showcase map** (cinematic experience). We don't optimize for scoring, leaderboards, or ranking. Note density, NJS, and patterns are subordinate to the readability of each telegraphed attack from Aline. Long gaps between attacks are acceptable. The music is ambient, not a rhythmic driver.

**Why:** *Expedition 33* combat is orchestrated turn-based, not continuous — translating it "as a typical BS map" would fight the nature of the source game. E33's directional parry mechanic maps 1:1 with BS's directional cube, so each of Aline's skills becomes a telegraphed attack with a parry window. We accept as a cost that the map won't be competitively replayable; what compensates is the wow-factor, the demonstrative value of the repo (Vivify + Unity 2019.4 + animation pipeline), and the fact that the use case (E33 boss fight in BS) is viral even for people who don't know BS.

---

### Character: Aline (Curatress) from Expedition 33

**Rule:** The map's boss is Aline.

**Why:** Native cinematic frontal view from the game (fits BS's fixed camera), proportioned humanoid format, enough visual detail to sustain a 2-3 min boss fight.

---

### Beatmap format V3 (the difficulty `.dat` files)

**Rule:** The difficulties (`EasyStandard.dat`, `NormalStandard.dat`, `ExpertPlusStandard.dat`) and `BPMInfo.dat` use V3 (`"version": "3.x.x"`, short keys `b/x/y/c/d/t`, `customData` without underscore). The V2→V3 cheatsheet (useful when copying snippets from older examples) lives in the [`vivify-mapping`](../.claude/skills/vivify-mapping/SKILL.md) skill.

`Info.dat` is not in scope for this decision — it's the map's manifest (registers difficulties, declares requirements, settings setter), not a beatmap, and BS 1.34.2 expects its single schema (`_version: "2.x.x"`, underscored keys: `_difficultyBeatmapSets`, etc.).

**Why V3:** NoodleExtensions and the modern examples in the corpus (`vivify_examples/`) are all V3. The Heck docs too. Staying aligned with the current corpus and docs avoids drift and translation friction.

---

### Beat Saber map versioned in git (`beatsaber-map/*.dat`)

**Rule:** The map's `.dat` files (`Info.dat`, `*Standard.dat`, `BPMInfo.dat`) and `bundleinfo.json` are versioned in git like any other file. Heavy binaries (`*.vivify`, `*.ogg`) and manual backups (`*.bak`, `*.v2bak`) are gitignored. The junction is still the game's deploy target.

**Why:** The JSON textual content is the most important content of the project and the source of truth for each attack. Versioning it gives you `git diff`, `git blame`, PR review, and granular rollback. Junction and git are orthogonal — git sees files, not junctions, so there's no conflict.

---

### Scale 0.01 on the `InstantiatePrefab` event

**Rule:** The `InstantiatePrefab` event applies `scale: [0.01, 0.01, 0.01]` (or the prefab has `localScale: 0.01` baked in).

**Why:** Unreal cm → Unity m conversion. Without this the model shows up 100x bigger. The correction lives in the event (not in Blender) to keep the source model clean and make the conversion explicit.

---

### Lighting with Directional Lights inside the prefab

**Rule:** Vivify prefabs that need lighting carry their own lights as children. Today Aline uses an unlit shader and doesn't need them, but the rule applies the moment you add any lit shader.

**Why:** Beat Saber's vanilla environment lights don't affect objects loaded by Vivify (different layer/scene). The only way to light them is light that travels inside the bundle.

---

### DefaultEnvironment as base

**Rule:** The map uses `DefaultEnvironment`.

**Why:** Vanilla lights are irrelevant with Vivify, so the chosen environment is the one with the least visual noise that could compete with Aline. It also simplifies the disable: `Environment|GameCore` regex catches everything relevant, no need to enumerate specific environment names (which change between `TimbalandEnvironment`, `BillieEnvironment`, etc.). Aeroluna and nasafrasa also pick it for their Vivify maps (corpus 2026-05-02).

---

### Cross-clip pose mismatch is absorbed with Animator blend, not by editing data

**Rule:** When two AnimationClips have different start/end poses (typical: floating vs grounded), don't edit the curves to make them match — use `duration > 0` in the AnimatorController transitions so Unity interpolates pose A → pose B during the blend. For large mismatches, combine with `exitTime < 1.0` so the blend overlaps with the end of the clip and the pose change happens during the motion.

**Why:** Editing curves to force a cross-clip match is fragile (any FBX re-import loses them) and can break the intra-clip animation. The Animator blend is the native tool for this and replicates exactly what UE does by default via "Blend Out duration" in its AnimMontages. Validated 2026-05-02 with DashOut-Idle1: `exitTime=0.7, duration=0.3` on exit + `duration=0.3` on AnyState entry dissolves a visible ~5cm UP/DOWN teleport when transitioning between grounded↔floating. The clip data is not touched.

---

### Custom mesh for "ground" instead of ripping directly from the game

**Rule:** For surfaces where Aline (or other prefabs) must "rest on", build the mesh ad-hoc in Blender instead of using a direct rip from the game, **as long as the rip has irregular geometry**. Apply a ripped texture from the game on top to keep the authentic look.

**Why:** E33 ripped meshes (rocks, terrains) are natural irregular geometry. Aligning a character's feet on that terrain is a non-constant function of XZ — there's no single valid Y. Iterating by eye from BS to find an acceptable Y costs 5-6 cycles of manual adjustment and never lands exact. A custom mesh with the pivot at TOP-CENTER and a controlled surface makes placement deterministic from ONE single event. Trade-off: you lose the authentic geometry of the game (real rock details), but you keep the authentic TEXTURE on top — visually it passes as "E33 asset". Tested 2026-05-02 with `SM_Rock_A_CliffEdge` (rip) vs custom Blender plate — the custom one fits Aline exact in one pass vs 6 iterations on the rip and never exact. Blender time: ~30-45 min with blender-mcp interactive.

---

### Settings Setter always present, with a minimal starter pack

**Rule:** Each difficulty declares `_customData._requirements` in `Info.dat` (at least `["Vivify", "Chroma"]`, add `"Noodle Extensions"` if the .dat uses `coordinates`/`definitePosition`/etc.) and a `_customData._settings` block that forces at minimum: `_playerOptions._noteJumpDurationTypeSettings: "Dynamic"` (universal in the corpus), `_environments._overrideEnvironments: false`, `_chroma._disableEnvironmentEnhancements: false`, and `_environmentEffectsFilterDefault/ExpertPlusPreset: "AllEffects"`. For a cinematic showcase we also add `_noTextsAndHuds: true` + `_countersPlus._mainEnabled: false` + a `_uiTweaks` block with everything `false`.

**Why:** Without the block, the map can be loaded under conditions that break Vivify silently: player with a global env override (our environment doesn't show), Static NJS mode (ignores our NJS), Chroma env enhancements disabled by the player (our `environment[]` disable doesn't apply), HUD competition between vanilla + Counters+ + UITweaks. The Settings Setter prompt is cancelable by the player, but if they accept we settle the whole ecosystem. Full starter pack + line-by-line justification + corpus coverage in the [`vivify-mapping`](../.claude/skills/vivify-mapping/SKILL.md) skill, "Settings Setter" section.

---

### Aeroluna mods installed by hand

**Rule:** Vivify, Heck, CustomJSONData, Chroma, and NoodleExtensions are installed by hand from Aeroluna's GitHub releases. Exact versions in [BS_Dependencies.txt](../BS_Dependencies.txt).

**Why:** Mod Assistant sometimes serves stale versions that break the dependencies among these five mods.

---

### Junction (`mklink /J`) for `beatsaber-map/` and `beatsaber-logs/`

**Rule:** Access to the real map (`CustomWIPLevels/Test/`) and to BS logs from the repo via Windows junctions. The junction itself (a filesystem-level link) is NOT versioned — each machine recreates it with `mklink /J`. What IS versioned is the textual content of `beatsaber-map/` (`.dat`, `bundleinfo.json`); see the "Beat Saber map versioned in git" entry above.

**Why junction (vs `.lnk` or `mklink /D`):** Junction = real link at the filesystem level (any program treats it as a normal folder), doesn't require elevated privileges like `mklink /D`, and a `.lnk` doesn't work programmatically.

---

### `ReMapper-master/` and `FModel.exe` outside the repo

**Rule:** External tools (ReMapper, FModel, Sandfall dump) live in `d:\vivify_repo\` (container folder), not inside the repo.

**Why:** They're external tools/dumps, not part of the product. ReMapper also brings its own `.git`, which would break `git status` if it stayed inside.

---

### Animations that displace Aline use root motion synthesized in Blender

**Rule:** For clips where Aline moves horizontally (DashIn-Idle1, DashOut-Idle2, their aliases, future melee), the motion is synthesized in Blender via `scripts/blender/synthesize_root_motion.py` moving `pose.bones["root"].location` to the armature object with axis remap (Y bone → Z object negated). Unity with `motionNodeName="SK_Curator_Aline"` and `Apply Root Motion = ON` translates the GO. We do NOT use `AnimateTrack` cross-clip, and we don't try to extract from the "root" bone on the Unity side.

**Why (cross-clip via AnimateTrack ❌):** the clips are designed to chain via root delta. Manually compensating with `AnimateTrack` clip-to-clip becomes unsustainable: each new clip adds cumulative coordination and the teleports/blends between events break continuity. `_offsetPosition` is silently ignored on Vivify-prefab tracks; `_position` introduces teleports on every call and requires manual displacement calculation per clip.

**Why (Unity-side extraction from the internal bone ❌):** `.psa` files bake motion into `pose.bones["root"].location[1]` (Y bone-local). The FBX does expose it as `m_LocalPosition.y` on the `SK_Curator_Aline/root` path, but Unity 2019.4 with `Generic + Copy From Other Avatar` doesn't extract motion from an internal bone as root motion in this flow, regardless of what you put in `motionNodeName` (tested: name, full path, avatar rebuild, `keepOriginalPositionY=false`). `hasGenericRootTransform` stays `False` and `averageSpeed=(0,0,0)` always.

**Why (synthesize in Blender + axis remap ✅):** when the motion lives in `location` of the armature object (top GO of the rig), Unity does extract it automatically. The axis remap `Y bone → Z object negated` is not cosmetic: it compensates the chain `axis_up="Y"` from the FBX exporter (which swaps Blender Y↔Z) + the `(270°, 0, 0)` rotation that the armature object picks up in Unity (Z-up→Y-up conversion). Without the remap or without negation, Aline falls vertically or moves backwards. Validated e2e in the sandbox (2026-05-01): DashIn translates ~6m forward, DashOut returns, with no snap-back.

**Assumed cost:** depends on `synthesize_root_motion.py` running every time you re-import `.psa` with motion. It's idempotent and marks each processed action with its axis-mapping mode. Operational detail in the `vivify-animations` skill.

---

### Animator on prefab root + `preserveHierarchy=true` on `Aline_Anims.fbx`

**Rule:** The `Animator` component lives on the root of the `aline.prefab`. The `Aline_Anims.fbx` importer has `preserveHierarchy=true` (forced by `AlineAnimsImporter.OnPreprocessModel`).

**Why:** Blender's armature-only export collapses the armature object as the FBX's root node, and Unity additionally collapses top-level nodes with a single child. Without `preserveHierarchy=true`, clip paths come out without the `SK_Curator_Aline` prefix and break the FBX inspector preview (T-pose). With the flag, paths stay prefixed, the Animator can live on the root, and the armature object's scale curves land on the `SK_Curator_Aline` GO (scale 1) → no-op. The root keeps `localScale: 0.01`.

---

### Map snapshots with `scripts/snapshot-map.ps1` (complement to git)

**Rule:** Manual with a label (`-Label X`, no rotation) for intentional moments. Auto via git pre-commit hook (`scripts/hooks/pre-commit`, ring buffer of 5, dedup by hash) for iteration. `core.hooksPath = scripts/hooks` activates the hook on fresh clones.

**Why:** Tag playable points without polluting commit history. Working backup of the state between commits when iterating fast. Tolerant to a missing junction.

**To revisit:** now that the map is versioned in git, the system might be redundant. Decide in the next audit.

---

### Minimal fork of unity-mcp (Unity 2019.4)

**Rule:** The `unity-mcp` we use is a minimal fork in `d:\vivify_repo\unity-mcp/` ported to Unity 2019.4, wired to the project via `Packages/manifest.json` (local path). stdio bridge on port 6400.

**Why:** The upstream `CoplayDev/unity-mcp` declares `unity: 2021.3+` and depends on C# 8/9 + UI Toolkit + 2020+ APIs. Vivify officially recommends 2019.4.28f1 for max compat with BS 1.34.2. The fork strips out everything non-essential and rewrites just enough to C# 7.3, keeping commits cherry-pickable in case we propose an upstream PR at some point. Detail in [unity-mcp/README.md](../../unity-mcp/README.md).

---

### Scope: Phase 1 + cosmetic intro; soft deadline

**Rule:** The map covers Phase 1 of the boss fight + a short cosmetic intro (Aline appears flying in and gets in position). It ships as "Phase 1", leaving the door open to Phase 2/3 later. The attack families to prototype are reduced to the ones that appear in Phase 1. The tournament date (2026-05-09) **is soft**: quality > speed. The "skip the tournament or deliver partial" call is the user's, handled separately.

**Why:** A polished Phase 1 has more demonstrative value than 3 mediocre phases. The cosmetic intro provides narrative context and hides the technical setup (instancing, fade); not playable, doesn't count as "Phase 0".

**Assumed cost:** big decisions explicitly deferred — `Skill8` with giant Aline (phase 2 climax), `Skill9`/`Skill11` absent, definitive song, full state machine wiring. Parked in "Open design decisions" of `NEXT_STEPS.md` to revisit in Phase 2/3.

---

### Build low-layer systems when there's a use case, not in the abstract

**Rule:** Before introducing a new architectural system (especially low-layer: lighting, post-process, shader pipeline, etc.), verify that **there is an ACTIVE use case** that needs it. "It'll come in handy in the future" doesn't count. Preserve the knowledge (doc, reversible commit) but don't ship the system without concrete demand.

**Exception:** systems whose retrofit cost is HIGH (asset format, bundle structure, the whole shader pipeline) — there, getting ahead pays off because migrating later is disproportionate. Canonical case in this project: auto-sync of CRCs (`PostBuildSyncCRCs.cs`).

**Why:** "Lowest layer" is still the right principle, but "lowest layer" applies AT the moment of solving the problem, not before the problem exists. Building capability without demand = dead inventory + constant ongoing tuning. Documented case: ambient lighting for Aline got to end-to-end working but was reverted because without a concrete narrative FX every skybox+ambientMode+colors combo required visual iteration with no payoff. Technical knowledge (how to dodge the `ShadeSH9=0` of Vivify bundles) preserved in [`vivify-materials`](../.claude/skills/vivify-materials/SKILL.md).

---

### Cube swap via `AssignObjectPrefab` + inverted-hull outline shader

**Rule:** The BS notes for family A attacks are rendered with our own prefab ([`NoteCube.prefab`](../VivifyTemplate/Assets/Aline/Prefabs/projectiles/NoteCube.prefab) + [`Aline/Outline`](../VivifyTemplate/Assets/Aline/Shaders/AlineOutline.shader) shader) instead of BS's default visual, via `AssignObjectPrefab` with `anyDirectionAsset` listing the affected tracks. Mesh from `Default Base.fbx` (CustomNotes), inverted-hull shader with SPI + GPU instancing so Vivify can pass `_Color` per-instance (red/blue saber color automatic).

**Why:** Solves the `dissolveArrow desync` at the root (no arrow geometry → the vanilla `DisappearingArrowControllerBase` has nothing to touch → no race condition with the `dissolveArrow` written by NoodleExtensions). Gives full control of the "darker comic + neon outline" look that fits Aline's boss fight feel. And the pattern is reusable for any future family A attack without having to touch the shader/material again.

**Assumed cost:** the `_Cutout` that Vivify passes per-instance is driven by player proximity (not by the `customData.animation.dissolve` curve), so the shader can't use it for active clipping (hides the notes right as they fire, undesired). The "dissolve trick" to hide the NJS jump-in is done via `customData.animation.scale` with first point `(0, 0, 0)` (Heck uses the first point during jump-in → cubes effectively invisible). Mechanics documented in [`family-a-recipe.md → Dissolve trick`](../.claude/skills/vivify-mapping/family-a-recipe.md).

**Pending:** the cube currently doesn't show a dot/arrow indicator. For `d=8` (any direction, Phase 1) it's not blocking, but it stays as a sub-step of Skill4 polish when we move to real parry with specific directions.

---

### Particle visuals via 3 coordinated ParticleSystems (no texture)

**Rule:** For family A attacks, the particles that bring the telegraph + cube to life are **3 separate `ParticleSystem`s** (all `Aline/ParticleSmoke` shader, procedural circular mask without texture):

1. `SphereBurst.prefab` (1 PS, World sim) — initial burst at `spawn_beat` of each sphere. Visually replaces the old "telegraph spheres". Auto-destroy via `stopAction=Destroy`.
2. `NoteCube.prefab → SmokeEnvelope` child (PS Local sim) — contained envelope stuck to the cube for its whole lifetime, travels with it during hover and launch.
3. `NoteCube.prefab → SmokeTrailWorld` child (PS World sim) — tail left behind when the cube moves, emitted particles persist in world space.

The two cube children use **`scalingMode=Hierarchy` + `localScale=(1/parent_scale)`** to inherit `lossyScale=0` from the cube root during NJS jump-in → automatically invisible, no `startDelay` needed (which would be fragile because it depends on NJS+BPM).

**Why not Trail Renderer (the original idea in (b2)):** Trail Renderer is a different component (a continuous geometric line stuck to the transform), but (a) it duplicates knowledge because the equivalent with a World ParticleSystem already gives the same effect, (b) Trail Renderers don't produce the "contained envelope" that a Local PS does, and (c) custom shaders over Trail Renderer require another shader pattern that doesn't add anything over the already-written `Aline/ParticleSmoke`. With ParticleSystem we cover all 3 roles (burst, envelope, trail) with the same shader+material stack, the same scaling techniques, the same knowledge.

**Why procedural shader without texture:** the circular masks + procedural cross/star are computed cheaply in the frag shader, it avoids dropping extra PNGs into the bundle, and it lets you tune shape/falloff via `_SoftEdge`/`_CoreOpacity` properties without re-exporting textures. For wispy smoke it's enough; if something more complex is needed (noise patterns, animated texture sheets), it can be added when there's a use case. See operational details in [`vivify-materials → Particle shaders`](../.claude/skills/vivify-materials/SKILL.md).

**Assumed cost:** 3 ParticleSystems vs a single more complex one increases the component count, but the costs (drawcalls, batching) are trivial at the amount of notes in the map (Phase 1 ~50-100 notes total). Validated 2026-05-05.

---

### Language: docs and skills in English, conversation in Spanish

**Rule:** Project documentation (`docs/`, `.claude/skills/`, `README.md`, `CLAUDE.md`) in **English** since 2026-05-11. Git messages **in English** since 2026-04-26. Conversation between the user and Claude stays in **Spanish** (the user's native language; doesn't affect repo readers). Inline code comments and script docstrings: leave existing Spanish ones as-is, default new ones to English. Early commits in Spanish (`Initial commit`, `Configurar repo: ...`) stay as they are — no retroactive translation.

**Why:** The repo is being published to a wider audience (GitHub link from LinkedIn, international Vivify/Beat Saber community). The translation was deferred until there was demand — once there was, we did it in one batch via multi-agent translation, ~3600 lines across 17 doc/skill files. The conversation stays in Spanish because that's the channel where the user works directly with Claude — readability for them matters more than uniformity across artifacts.
