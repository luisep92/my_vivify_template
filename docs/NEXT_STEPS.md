# NEXT_STEPS

## Estado actual

Pipeline funcionando end-to-end:

- Vivify carga el bundle de Unity e instancia `aline.prefab` en escena.
- **Aline texturizada** con shader unlit cutout double-sided. 3 materiales: `M_Aline_Body_1`, `M_Aline_Body_2`, `M_Aline_Black`.
- **Sync de CRCs automático**: `Editor/PostBuildSyncCRCs.cs` dispara `scripts/sync-crcs.ps1` cada vez que Vivify reescribe `bundleinfo.json`. Cero pasos manuales tras F5.
- Mapa V2 con `_customEvents` operativo (`InstantiatePrefab` testeado).
- **Unity MCP operativo end-to-end** (fork local en `d:\vivify_repo\unity-mcp/`, bridge stdio en port 6400). Tools `read_console`, `refresh_unity`, `execute_code`, `manage_animation`, `manage_asset`, `manage_material`, `manage_prefabs`, etc.
- **Animaciones reproduciéndose en BS**: pipeline `.psa` → Blender → FBX → Unity Animator → Vivify funcionando, con preview del FBX inspector animando correctamente. Detalle operativo en la skill `vivify-animations`.

---

## Próximos pasos (en orden)

> **Scope (2026-05-02): Phase 1 + intro cosmética.** Recorte por deadline (1 semana). Mapa se entrega como "Phase 1", deja la puerta abierta a Phase 2/3 después. Detalle en [DECISIONES.md → "Scope cut a Phase 1"](DECISIONES.md). Las familias de ataque a prototipar quedan reducidas a las que aparecen en Phase 1.

> Pivot anterior: con la decisión de **showcase map** ([DECISIONES.md](DECISIONES.md)), el orden cambia. La canción y el state machine narrativo dependen de tener primero los **sistemas de ataque** definidos como contratos reutilizables. Componer fases sobre sistemas inestables es la receta del embolado.

### 1. Catálogo de familias de ataque + contratos — **hecho**

Cinco familias (A/B/D/E/F) + modificador C apilable formalizadas en [`families.md`](../.claude/skills/vivify-mapping/families.md): inputs, secuencia de eventos, encoding del parry, parámetros tunables, no-conflicto. Mapeo completo Animator→familia incluido. Visión de fase a fase en [PRODUCTO.md](PRODUCTO.md).

### 2. Sandbox de locomoción — hecho

Implementado en `beatsaber-map/EasyStandard.dat` (difficulty Easy del mapa Test, registrada en `Info.dat`). Cadena de `SetAnimatorProperty` recorre idles, transiciones, dashes y stuns canónicos. Validado e2e en BS (2026-05-01): idles, transiciones y dashes encadenan limpio sin snap-back; DashIn traslada el GO ~6m forward, DashOut lo devuelve.

### 2.5. Re-export `Aline_Anims.fbx` con root motion canónico — hecho

Pipeline final operativo:
1. Los `.psa` bakean motion forward en `pose.bones["root"].location[1]` (Y bone-local). Verificable con `scripts/blender/inspect_motion.py`.
2. Unity 2019.4 con `Generic + Copy From Other Avatar` no extrae motion de un bone interno como root motion, da igual lo que se ponga en `motionNodeName` del clip importer o del avatar source. Sí extrae si el motion vive en `location` del armature object.
3. Solución: `scripts/blender/synthesize_root_motion.py` mueve el motion del bone "root" al armature object con axis remap (Y bone → Z object negated) compensando la cadena de transformaciones del FBX exporter (`axis_up="Y"`) + rotación 270°X que el armature object adquiere en Unity.
4. `AlineAnimsImporter` setea `motionNodeName="SK_Curator_Aline"` + desbakea XZ e Y por clip (`XzRootMotionSuffixes`).
5. Animator del prefab con Apply Root Motion = ON aplica el delta al root del prefab.

Detalle operativo y gotchas en la skill [`vivify-animations`](../.claude/skills/vivify-animations/SKILL.md) sección "Root motion para clips con desplazamiento" + "Caminos cerrados". Decisión consolidada en [`DECISIONES.md`](DECISIONES.md).

### 3. Environment custom + materiales de Aline (bloqueador) — **en curso**

El environment por defecto de BS (TimbalandEnvironment) se come visualmente a Aline: los materiales `BlackPart`/`BlackPart1`/`CuratorFace` negros desaparecen sobre fondo oscuro. Cualquier trabajo de fresnel/face shader sobre Aline es no-juzgable hasta tener un contexto visual correcto. Por eso environment va antes que materiales en este paso. Capacidades Vivify validadas en `docs/heckdocs-main/docs/vivify/events.md` + `environment/environment.md`.

Subpasos en orden:

1. **Skybox custom** — **hecho 2026-05-02**. Material `M_Skybox_E33` con shader `Skybox/Panoramic`, textura `T_Skybox_6_HybrydNoiseVT` (4096×2048 equirect, ripeada de Sandfall via FModel), tint blanco, exposure 1.0, rotación 180°. Bundleado bajo `aline_bundle`. Eventos `SetRenderingSettings` + `SetCameraProperty.clearFlags=Skybox` (ambos necesarios — el primero solo no rinde). Source canónico identificado pero no usado: `M_Flowmap_Nebula_9_Inst_2` → `T_Skybox_12_HybridNoiseVT` en `Monolith_Interior_PaintressGrandFinale`. Skybox_6 (blue-grey nocturno) elegido sobre el _12 (cosmic-red) por encaje al look misty/azul de la pelea original. Metodología del rip + receta del skybox en skill [`vivify-environment`](../.claude/skills/vivify-environment/SKILL.md).

2. **Switch a DefaultEnvironment + disable + Settings Setter** — **hecho 2026-05-02**. `Info.dat._environmentName` cambiado a `DefaultEnvironment`. Disable del env via `customData.environment[]` con tres comandos: yeet `Environment|GameCore` (regex, position -69420), `active: false` para `DustPS` y `PlayersPlace`. Settings Setter en `Info.dat._customData._settings` por dificultad: starter pack + HUD off. Validado en BS. Receta consolidada en [`vivify-environment`](../.claude/skills/vivify-environment/SKILL.md) y [`vivify-mapping`](../.claude/skills/vivify-mapping/SKILL.md).

3. **Ambient lighting** — **diferido a Phase 2** (intentado y revertido 2026-05-03, commits `2fd1d7a`/`163a2f9` y reverts `b68ab0f`/`cf1fe45`).

   Implementación arquitectural (`AlineLighting.cginc` con `AlineShade` modulativo + `AlineRimTint` aditivo, refactor de 4 shaders, `_AmbientFloor=0` para que lights-out sea lights-out de verdad) llegó a funcionar end-to-end via `unity_AmbientSky/Equator/Ground` (gotcha del `ShadeSH9=0` en bundles Vivify: ver [`vivify-materials → Ambient en bundles Vivify`](../.claude/skills/vivify-materials/SKILL.md)).

   **Por qué el revert:** con un solo skybox y cero cambios de iluminación en Phase 1, el sistema añadía tuning constante sin valor narrativo. Cada combinación skybox×ambientMode×ambientValues requería iterar visualmente. Lección de timing en [`DECISIONES.md → Construir sistemas de capa baja cuando hay caso de uso`](DECISIONES.md).

   **Cuándo retomar (Phase 2):** cuando haya cambios de lighting con propósito narrativo (cambio de fase, fade outs, partículas con luz real, recolor de skybox como FX). Commits cherry-pickeables como punto de partida.

   Estado actual: cada material tiene su `_LightDir/_LightStrength/_Ambient` hardcoded (BodyLit) o sin lighting (Hair/Fresnel/EnergyMask/Face). Aline lee bien sobre el skybox blue-grey sin reaccionar al entorno. Suficiente para Phase 1.

4. **Mesh del escenario E33** — **hecho 2026-05-02 con custom mesh, iterado a versión rocosa**. Probamos primero rip directo (`SM_Rock_A_CliffEdge` + textura `Albedo_2K_vlzkba1fw` de Megascans/Jagged_Rock que el juego usa) — la geometría natural irregular hacía imposible alinear pies de Aline a milímetro. Switch a custom mesh en Blender via blender-mcp.

   **v1 (2026-05-02 mediodía):** óvalo plano 6m × 10m × 0.5m, dips sutiles (max 8cm), `position: [0, 0.97, 4]`. Funcional pero el cap NGON dejaba el top como un solo polígono y la textura mostraba rayos radiales (UV planar desde arriba).

   **v2 (2026-05-02 tarde):** versión rocosa estilo cima de montaña. Builder reusable en `scripts/blender/build_rock_platform.py`. Óvalo 12×18m con corredor central plano 5×11m (jugador en `z=0` al centro, Aline en `z=8` al borde del eje largo), silueta perimetral irregular vía noise(cos θ, sin θ), relieve en flancos hasta +50cm/-18cm con falloff de 2m hacia el corredor, smart UVs (sin rayos), shading smooth. `position: [0, 0.97, 0]` (centrado en el jugador). Pipeline: Blender → FBX → Unity import → `Vivify/Build/Build Working Version Uncompressed` → PostBuildSyncCRCs auto-sync. Iteraciones para ajustar amplitud relieve y empujar bumps fuera del corredor. Patrón consolidado en skill `vivify-environment` (secciones "Receta del mesh custom" y "Gotcha: FBX axis flip").

   **Decoración del escenario — pétalos azules (hecho 2026-05-03):** scatter merged en el mismo `RockPlatform.fbx` como segundo material slot/submesh. Mesh source: `Sandfall/Content/EnviroPacks/Real_Ivy_Pack/Meshes/foliage/ivy/SM_ivy_floor_plane_dense_spread_01_leaves.pskx` (asset stock de Unreal Marketplace que Sandfall reutilizó). 5 patches asimétricos rotados, foco aline-side + flanks, mínimo tras jugador (cámara fija no lo ve). Pipeline:
   - `scripts/blender/build_rock_platform.py:build_ivy_scatter()` — importa el FBX del template, aplica Decimate ratio 0.5 (300K → 150K tris), duplica N copias en posiciones explícitas `IVY_PATCHES`, scale no-uniforme `(s, s, s*IVY_HEIGHT_SCALE=0.15)` para aplastar las leaves verticales del ivy nativo a look "petalos tirados", merged en rock_obj
   - Material `M_BlueIvy` con shader `Aline/Standard` + keyword `LUMINANCE_TINT` (ver más abajo) → recolor real azul saturado
   - Preview en Blender: el script ahora crea placeholder materials con texturas reales + EEVEE nodes que reproducen el luminance-tint (`_make_preview_material()`) — viewport en Material Preview muestra resultado casi-final sin round-trip a BS
   - Decisión clave: probamos 4 approaches (cluster scatter discreto, dense cluster scatter, rock-top duplicate + atlas-tile shader, ivy floor_plane scatter) → solo el último funcionó. Lección: para ground decoration en BS Vivify, **mesh asset choice > shader gymnastics** — un asset pack pre-built de "scattered carpet" gana siempre a tilear un atlas vía shader.

   **Decoración del escenario — bushes rosas 3D (hecho 2026-05-03):** tercer submesh de `RockPlatform.fbx`, scatter aleatorio determinista (seed=23, BUSH_COUNT=14) de mesh `Sandfall/Content/EnviroPacks/Environment_Set/Environment/Foliage/Models/SM_ground_foliage_03_*.pskx` (~64 tris nativos según JSON, ~4.4K después de pskx import; 62K total tras 14 instancias). Restringido a `y >= 0.5` Blender pre-mirror = solo en frente del jugador (cámara fija no ve atrás). Material `M_PinkBush` con luminance tint pink-magenta overbright `(1.5, 0.4, 0.8)`. Aporta toques de color contrastante al ivy carpet azul + pequeñas protrusiones 3D. Receta consolidada en skill `vivify-environment` sección "Capa 3 — bushes 3D scatter".

   **Estado escenario Phase 1**: completo. Total ~217K polys, 1 mesh, 3 submeshes (rock 9.8K + ivy 145K + bush 62K), 3 draw calls. Holgado para BS PC, OK para Quest si se necesita.

4.5. **Dash Y-jump bug — cerrado 2026-05-02** con fix en tres capas:
   - **Blender / synthesize_root_motion v5**: normalizar frame 0 a origen por axis. Las curvas de los `.psa` traen baselines absolutos del rig de Unreal y no coinciden cross-clip (DashOut-Idle2 arrancaba a Z=604.49 mientras DashIn-Idle1 a Z=0); v5 resta el valor del frame 0 a todas las keyframes para que todos los clips arranquen en `(0,0,0)` object space. Idempotente con marca custom property.
   - **Blender / import_all_psa**: detectar seq names genéricos ("DefaultSlot" en `_Montage.psa`) y renombrar usando el basename del archivo. `Paintress_DashOut-Idle1_Montage.psa` se silenciaba por colisión con DashIn-Idle1_Montage (alfabéticamente primero, ambos con seq "DefaultSlot"); el rename libera la colisión y recupera la action faltante.
   - **Unity AnimatorController**: pose-mismatch entre clips se absorbe con blend > 0 en las transitions. DashOut-Idle1 (state nuevo, exit a Idle1 grounded) usa `exitTime=0.7 + duration=0.3` para que el blend se solape con los últimos 30% del clip — el aterrizaje ocurre durante el movimiento del dash en vez de "Aline llega a destino flotando y luego baja". Entry blend 0.3s para amortiguar despegue desde grounded. DashOut-Idle2 (floating→floating) sigue sin blend.

   Hallazgo clave: `Paintress_DashOut-Idle1_Montage.psa` y `Paintress_DashOut-Idle2.psa` contienen skeletal animation idéntica en Aline (verificado: 2604 fcurves, zero diferencia). El "grounded vs floating" semántico del juego original vivía en blueprints/Montage metadata de UE que no viajan al `.psa`. Replicamos el aterrizaje vía blend en Animator (técnica equivalente al "Blend Out duration" del Montage de UE). Patrón consolidado en skill `vivify-animations`.

5. **Pelo de Aline** — **hecho 2026-05-03 (Fases 1 + 2)**.

   Asset en `Sandfall/Content/Characters/Hair/Mirror_Family/Aline/` (NO en `Bun_Hairstyle/`). PSK + 4 texturas + Skeleton + AnimBlueprint + 3 MaterialInstances. **Cero `.psa` para el pelo** — Sandfall lo simulaba en runtime con AnimBlueprint (grafo de UE con constraints físicos sobre los strand bones), no porteable a Vivify.

   **Pipeline final operativo:**
   - PSK + texturas exportadas via `mcp__fmodel__*`.
   - PSK → FBX **rigged** via `scripts/blender/pskx_to_fbx.py` (preserva armature + skin weights). Output a `Sandfall/.../Aline/Aline_curator_hair_skl.fbx` + copia manual a `VivifyTemplate/Assets/Aline/Hair/`.
   - El FBX incluye 163 bones (`Root` → 19 `Strand_X_1` top-level → cadenas hasta `Strand_X_Y_Z`), 32K verts, SkinnedMeshRenderer.
   - Shader `Aline/Hair` (cards unlit cutout: `_MainTex` Color + `_AlphaMap` mask separada + `_Brightness` + `_AlphaCutoff=0.08` muy bajo para preservar mechones finos).
   - Material `M_Aline_Hair` con `T_Hair_Aline_Color` + `T_Hair_Aline_Mask`, brightness 1.0.
   - Instanciado como child del bone `head` del prefab. Path: `SK_Curator_Aline/root/pelvis/spine_*/.../neck_02/head/Aline_curator_hair_skl`.
   - **Scale fix crítico:** `localScale = (100, 100, 100)` para compensar el chain scale 0.01 del rig de Aline.
   - Pose final: `localPosition=(0,0,0) localRotation=identity` — el bind pose natural del rig de Sandfall posiciona el pelo "wind-blown / etereo" hacia arriba+atrás, encaja con el look del personaje en E33 sin tocar nada.
   - Animator dedicado en el GameObject top con `HairSway.anim`: 19 bones top-level × 4 quaternion curves (`m_LocalRotation.x/y/z/w`) compuestas alrededor del bind pose de cada bone. Sway `±6° X / ±4° Z` con phase shift `i × 2π/19` para que los strands no se muevan en sync. Loop 2.5s a 30fps. Los sub-bones siguen por jerarquía → movimiento natural sin animarlos.

   **Por qué bones (rig original) y NO DynamicBone:** bundles Vivify hacen script stripping → MonoBehaviour custom no se ejecuta en BS. DynamicBone/SpringBones/Magica Cloth simularían en Unity Editor pero quedarían inertes en BS. Animar bones via AnimationClip pre-baked es la única ruta viable. Detalle en [`vivify-materials → MonoBehaviour custom NO sobrevive al stripping`](../.claude/skills/vivify-materials/SKILL.md).

   **Performance:** 32K verts skinned + 163 bones + 19×4 curve evals por frame. Holgado en BS PC; ~0.3-0.5ms extra de Aline en Quest. Margen amplio.

   **Gotchas resueltos en el camino (consolidados en `feedback_pskx_to_fbx_rigged`):**
   - Si escalas armature + mesh por separado en Blender y aplicas, la deformación se compone con el bind pose y queda 100× más pequeña. Solución: **delegar el scale al FBX exporter** via `global_scale=0.01 + apply_scale_options='FBX_SCALE_ALL'` cuando hay armature. Pre-scale en Blender solo para mesh estático.
   - Re-import del FBX resetea el material del SMR al default `MI_Hair_NPCs_Aline_Curator/Standard`. Reasignar `M_Aline_Hair` post-import.
   - `localScale=100` se preserva tras re-import; pose `(0,0,0)` también.
   - Bind pose del hair viene rotado +X 270° por el FBX axis flip Blender→Unity, pero está absorbido en el child intermedio `Aline_curator_hair_skl/Aline_curator_hair_skl`. No tocar.

6. **Materiales Aline (BlackPart fresnel + CuratorFace)** — **hecho 2026-05-03**. Cinco slots auditados contra `SK_Curator_Aline.uasset` + override de `BP_Cine_Curator_Aline`:
   - Slot 0 `Curator_Black_Body` → `M_Aline_BlackBody` con shader nuevo `Aline/Fresnel` (cutout fresnel; normal map `Curator_Black_Body_Normal`; params del MI BlackPart1: Alpha 0.35, Fresnel 0.5, FresnelR 2). Tuneado a `_Alpha=1.0, _FresnelExponent=3.0, _RimBoost=1.5, _AlphaCutoff=0.5` para que el rim solo aparezca en silueta (los parches de "piel quemada" se integran sin parecer overlay).
   - Slot 1/2 `Curator_Body_001 / Curator_Body` → `M_Aline_Body_2 / M_Aline_Body_1` con shader nuevo `Aline/BodyLit` (BaseColor + Normal + AO + fake-light dirección). Tuneado a `_LightStrength=0.45, _Ambient=0.55, _BumpScale=1.5, _OcclusionStrength=0`. **Hallazgo:** la "ORM" (`OcclusionRoughnessMetallic`) que ripeó FModel **NO es una ORM packed estándar** — es una textura pseudocolor multichannel (naranja/verde/magenta) que probablemente codifica paint masks u otros effects, no AO/Roughness/Metallic. AO desactivado. Normal map sí da relief a las grietas.
   - Slot 3 `Curator_Dress` → `M_Aline_Dress` con shader nuevo `Aline/EnergyMask` (translucent blend, sin clip — alpha gradient suave; usa `Curator_Dress_Normal` + `Curator_Dress_Opacity`). Tuneado a `_Alpha=0.85, _FresnelExponent=1.5, _RimBoost=1.0` para look "vestido de energía / wispy". `Cull Off` puede dar overdraw; valorar `Cull Back` si molesta.
   - Slot 4 `Curator_Aline_Hole` → `M_Aline_Face` con shader nuevo `Aline/Face` (translucent + radial fade aproximando el M_CuratorFace de UE). Implementa también UV transform (`_UVScale`, `_UVOffset`, `_UVAngleDeg`) para soportar `Mask_Curator_Aline` mask-driven, pero la versión actual usa **solo radial** (`_Radius=0.40, _Hardness=0.2`) por simplicidad y control. La mask queda como opt-in para futuras iteraciones (más fiel pero menos predecible).

   **Hallazgo importante:** el SK directamente referencia el padre `M_CuratorFace` (UMaterial puro), no el MI `MI_CuratorFace_Aline`. El override correcto vive en el `BP_Cine_Curator_Aline.OverrideMaterials[4]`. Receta de "trazar SK + BP que lo usa" consolidada en skill `vivify-materials`.

   **Workflow nuevo confirmado:** iterar shaders/materials via Scene view screenshot en lugar de Vivify Build + relaunch BS. Ahorra ~1min por iteración. Receta + gotcha del Toggle keyword no sincronizando via API en [`unity-rebuild → Iterar materiales/shaders sin round-trip a BS`](../.claude/skills/unity-rebuild/SKILL.md).

7. **Intro cosmética** — pending. Aline volando + posicionándose + fade-in de luces. Cosmético no jugable, da contexto narrativo y esconde setup técnico (instanciado, fade del skybox, etc.). Implementación: AnimateTrack sobre el track del prefab + trigger del Animator (`Hover` o equivalente del catálogo).

**Diferido a post-Phase-1:**
- **Paletas (`palette.pskx`, `palette1.pskx`)** que Aline sostiene. Validar primero si la cámara fija de BS las ve antes de invertir en el rip.

Cuando esté hecho, mover este bloque y la entrada equivalente de "Diferido post-torneo" abajo.

### 4. Prototipo de cada familia en sandbox

Una instancia funcional de cada familia en un mapa/dificultad sandbox antes de tocar el mapa real. Criterio de éxito por prototipo: animación + VFX + parry + cleanup, instanciable dos veces sin estado residual. Snapshot por prototipo (`-Label "proto-fam-X"`).

**Orden sugerido:**
1. **A con `Skill4`** (proyectiles pequeños tras giro, fase 1) — **pendiente**. `NormalStandard.dat` es la dificultad playground para iterar la familia A (clon de Easy + trigger Skill4 en b=40, sin gameplay). El approach correcto para construir el ataque está aún sin decidir tras varios intentos fallidos: necesario leer Heckdocs (`docs/heckdocs-main/docs/animation/properties.md` para `definitePosition`/`dissolve`, `docs/heckdocs-main/docs/items/objects.md` para `noteJumpStartBeatOffset`, `docs/heckdocs-main/docs/settings.md` para `_noteJumpDurationTypeSettings`) en frío y cuajar un mini-spec antes de tirar código.
2. **A con `Skill3`** (3 piedras gigantes, fase 1) — variante de Skill4 (mismo patrón hold-then-launch, N=3, NJS más baja, scale grande).
3. **B con `DashIn-Idle1`** (mele estándar, fase 1) — valida la choreography de tres beats (DashIn + golpe + DashOut). Caso aparte (Aline se mueve, no hay proyectil).
4. **F con `Skill2_Start/Loop/End`** (carga + explosión, fase 1) — valida secuencia multi-stage de triggers y timing largo.
5. **E con `Skill1`** (multi-hit chain, fase 1) — valida cadena de N parries sincronizados con N hits embebidos en el clip.
6. **D standalone** (shrinking indicator, sin source anim) — valida que el indicador construido en Unity transmite el feel de E33.
7. **B + modificador C con `Skill5`** — valida composición familia + modificador (Blit + SetMaterialProperty).

**Cuando 2-3 familias estén implementadas:** consolidar el patrón en una función helper que parametrice (N, posiciones, NJS, scale, prefab) — evitar copy-paste por familia.

### 5. Canción definitiva

Cuando los 4 contratos estén probados. Decidir pieza concreta del OST de E33 con criterio: duración suficiente para 5 fases, clima coherente con showcase. Importar `.ogg` al `beatsaber-map/`, ajustar BPM y duración. Anotar en `DECISIONES.md`.

### 6. Wireado narrativo del state machine

Depende del catálogo de familias (paso 1) y de la identificación de triggers (paso 2). Definir qué familia (y qué `Skill_X` del Animator) dispara cada fase del boss fight. Componer la línea de tiempo del mapa instanciando templates de la skill, no escribiendo eventos a mano cada vez. Snapshot del mapa antes de bloque grande de events.

### 7. Setup de ReMapper

Levantar Deno + primer script en `ReMapper-master/`. Probable pero no obligatorio: si la composición se beneficia de scriptear instanciaciones de familias, ReMapper es el sitio. Output target: directo a `beatsaber-map/ExpertPlusStandard.dat` o staging intermedio. Rellenar la skill `remapper-scripting` durante este paso.

### 8. Diseño narrativo y pulido

Traducir la estructura por fases de [PRODUCTO.md](PRODUCTO.md) en secuencia concreta de ataques. Iteración de legibilidad con feedback externo (VR + ojos de tercero).

---

## Side-projects

### Port mínimo de unity-mcp a Unity 2019.4 — DONE

Fork operativo en `d:\vivify_repo\unity-mcp/` (`luisep92/unity_vivify_mcp`), enganchado al proyecto Aline. Pendiente: cuando lleve unas sesiones rodando, evaluar PR a upstream `CoplayDev/unity-mcp`. Los commits están organizados con un cambio conceptual cada uno y mensajes en inglés, pensados para cherry-pick limpio. Detalle en [unity-mcp/README.md](../../unity-mcp/README.md).

---

## Decisiones de diseño abiertas

Beats narrativos identificados pero pendientes de decisión, antes del wireado del state machine (paso 5):

- **Clímax fase 2 — `Skill8` con Aline gigante.** El usuario lo identifica como "ataque que sería realmente impresionante meter". La animación tal cual depende de una segunda Aline (gigante, en el fondo) que da bolas de energía, más una serie de golpes propios. Tres opciones a evaluar: (a) **rip de FModel** del modelo de la Aline gigante + segundo prefab + animator separado — gran scope; (b) **recortar `Skill8`** a solo la serie de golpes y aceptar que el espectáculo de la fase 2 venga de otro sitio; (c) **reemplazar el contexto** con algo distinto que sostenga el momento sin la gigante. Conversación dedicada antes de prototipar fase 2.
- **`Skill9` ausente.** Trigger declarado en el Animator pero **sin clip importado**. Sospecha del usuario: era el ataque de la Aline gigante en E33. Si el clímax (decisión anterior) va por la opción (a), `Skill9` es candidato a extraer del dump (`Sandfall/`) vía FModel y meterlo en el FBX. Si va por (b)/(c), `Skill9` se descarta.
- **`Skill11` ausente.** Gap en numeración del Animator, sin pista de qué era. No prioritario.

## Diferido post-torneo

Limpieza para cuando el mapa esté entregado:

- **Rename `my_vivify_template/` → `aline-boss-fight/`**. Procedimiento: cerrar VSCode, `cd d:\vivify_repo && ren my_vivify_template aline-boss-fight`, reabrir VSCode. Junctions y `.git` viajan con la carpeta.
- **Traducir docs/skills al inglés** si en algún momento se publica el repo a la comunidad de Vivify (internacional).
- **Cambiar `origin/main`** del template upstream (`Swifter1243/VivifyTemplate`) al remote propio cuando se monte en GitHub.
- **Upgrade unlit → lit/PBR para Aline**. Normal/ORM/Emissive ya descritos en `MI_Curator_Aline_*.json` del dump. Implica copiar PNGs adicionales, ampliar `Aline/Standard` (o crear `Aline/Lit`), decidir modelo de iluminación. (Los slots negros y las paletas están subidos al paso 3 del orden activo.)
