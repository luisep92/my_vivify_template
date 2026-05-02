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

1. **Skybox custom** — **hecho 2026-05-02**. Material `M_Skybox_E33` con shader `Skybox/Panoramic`, textura `T_Skybox_6_HybrydNoiseVT` (4096×2048 equirect, ripeada de Sandfall via FModel), tint blanco, exposure 1.0, rotación 180°. Bundleado bajo `aline_bundle`. En `EasyStandard.dat` van DOS eventos a beat 0: `SetRenderingSettings` con `skybox` + `SetCameraProperty` con `clearFlags: "Skybox"` (este último es necesario; el primero solo no hace nada — gotcha en skill `vivify-environment`). Source canónico identificado pero no usado: `M_Flowmap_Nebula_9_Inst_2` → `T_Skybox_12_HybridNoiseVT` en `Monolith_Interior_PaintressGrandFinale`. Decidimos usar el Skybox_6 (Hybryd, blue-grey nocturno) sobre el _12 (cosmic-red gold-tinted) por mejor encaje estético al look misty/azul de la pelea original. Metodología del rip en memoria `project_sandfall_hunt_pattern`.

2. **Switch a DefaultEnvironment + disable + Settings Setter** — **hecho 2026-05-02**. `Info.dat._environmentName` cambiado de `TimbalandEnvironment` a `DefaultEnvironment` (el que menos ruido mete con Vivify). Disable del environment via Chroma `_customData._environment[]` en `EasyStandard.dat` con tres comandos: yeet `Environment|GameCore` regex al `position: [0,-69420,0]` (más robusto que `_active: false` para geometría que puede reactivarse), `_active: false` para `DustPS` y `PlayersPlace`. Pattern derivado de `vivify_examples/43a24` (Chaimzy). En `Info.dat._customData._settings` por dificultad: starter pack de Settings Setter (Dynamic NJS, EffectsFilter AllEffects, leftHanded false, overrideEnvironments false, Chroma overrides) + HUD off (`_noTextsAndHuds: true` + `_countersPlus._mainEnabled: false` + bloque `_uiTweaks`). Validado en BS: el prompt de settings sale, env y HUD desaparecen al aceptar (queda solo el HUD del chat de Twitch, que es overlay externo del jugador). Receta consolidada en skill `vivify-environment`. Gotcha V2/V3 del nombre del array (debe ser `_environment` con underscore en V2) consume una iteración por silent ignore — documentado en memoria `feedback_v2_v3_syntax`. Decisión del Settings Setter starter pack en `DECISIONES.md`.

3. **Ambient lighting** — pending. Una vez fondo limpio, ajustar `ambientLight`/`ambientIntensity`/`ambientMode` via `SetRenderingSettings` para que los materiales negros de Aline ganen contraste sin perder mood oscuro.

4. **Mesh del escenario E33** — **hecho 2026-05-02 con custom mesh**. Probamos primero rip directo (`SM_Rock_A_CliffEdge` + textura `Albedo_2K_vlzkba1fw` de Megascans/Jagged_Rock que el juego usa) — la geometría natural irregular hacía imposible alinear pies de Aline a milímetro. Switch a custom mesh en Blender via blender-mcp: óvalo plano 6m × 10m × 0.5m grosor, top con dips sutiles (max 8cm), pivot exacto en TOP-CENTER. Material reutiliza la textura ripeada de E33 (Jagged Rock) — pierde la geometría auténtica pero mantiene el look de roca de E33. Placement determinístico: `position: [0, 0.97, 4]` con scale 1.0, rotación identity. Receta consolidada en skill `vivify-environment` (sección "Instanciar escenario custom"). El BP_Monolith stone de E33 se descartó: solo se ve desde abajo del monolito, no desde la cima donde la pelea ocurre. Decoración (pétalos, plantas) diferida a Phase 1.5. **Bug pendiente:** Aline da un mini-saltito vertical de ~5cm al inicio y fin de DashOut — pre-existente, no relacionado con el escenario; documentado en memoria `project_dash_jump_bug` con dos hipótesis fallidas y dos pendientes.

5. **Pelo de Aline** — pending. Asset separado del modelo base. Hipótesis fuerte: vive en `Bun_Hairstyle/` en Sandfall (en E33 los hairstyles son intercambiables). Pendiente de scouting FModel + import (pskx → Blender → FBX → child del prefab).

6. **Materiales Aline (BlackPart fresnel + CuratorFace)** — pending. Una vez con contexto visual correcto, iterar shaders sobre los slots negros planos para añadir lectura. Receta inicial:
   - **BlackPart / BlackPart1**: fresnel shader simple sobre material existente. Normal map debe estar enchufado.
   - **M_CuratorFace**: blend translucent de `Mask_Curator.png` + `T_Paint1.png` + `T_Aura.png`. JSONs del dump (`MI_Curator_Aline_*.json`) listan tiling/offset; reusar literal cuando se pueda.

7. **Intro cosmética** — pending. Aline volando + posicionándose + fade-in de luces. Cosmético no jugable, da contexto narrativo y esconde setup técnico (instanciado, fade del skybox, etc.). Implementación: AnimateTrack sobre el track del prefab + trigger del Animator (`Hover` o equivalente del catálogo).

**Diferido a post-Phase-1:**
- **Pelo "completo"** si el alpha cutout del material atlas resulta tener bordes durillos (verificar primero si molesta).
- **Paletas (`palette.pskx`, `palette1.pskx`)** que Aline sostiene. Validar primero si la cámara fija de BS las ve antes de invertir en el rip.

Cuando esté hecho, mover este bloque y la entrada equivalente de "Diferido post-torneo" abajo.

### 4. Prototipo de cada familia en sandbox

Una instancia funcional de cada familia en un mapa/dificultad sandbox antes de tocar el mapa real. Criterio de éxito por prototipo: animación + VFX + parry + cleanup, instanciable dos veces sin estado residual. Snapshot por prototipo (`-Label "proto-fam-X"`).

**Orden sugerido:**
1. **A con `Skill3`** (3 piedras gigantes, fase 1) — el más cómodo: VFX claro, N pequeño, encoding de notas obvio. Sirve también para validar que las animaciones de Aline encadenan limpio en BS.
2. **B con `DashIn-Idle1`** (mele estándar, fase 1) — valida la choreography de tres beats (DashIn + golpe + DashOut).
3. **F con `Skill2_Start/Loop/End`** (carga + explosión, fase 1) — valida secuencia multi-stage de triggers y timing largo.
4. **E con `Skill1`** (multi-hit chain, fase 1) — valida cadena de N parries sincronizados con N hits embebidos en el clip.
5. **D standalone** (shrinking indicator, sin source anim) — valida que el indicador construido en Unity transmite el feel de E33.
6. **B + modificador C con `Skill5`** — valida composición familia + modificador (Blit + SetMaterialProperty).

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
