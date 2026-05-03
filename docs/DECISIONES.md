# DECISIONES

Reglas fuertes del proyecto, una entrada por decisión. Solo el "qué" y un párrafo de "por qué". Si necesitas explorar la historia o lo que se descartó, mira `git log` y los hilos de chat.

---

### Tono: showcase cinemático, no scored

**Regla:** El mapa es un **showcase map** (experiencia cinemática). No optimizamos para scoring, leaderboards ni ranqueo. Densidad de notas, NJS y patrones quedan subordinados a la legibilidad de cada ataque telegrafiado de Aline. Los huecos largos entre ataques son aceptables. La música es ambiente, no driver rítmico.

**Por qué:** El combate de *Expedition 33* es por turnos orquestado, no continuo — traducirlo "como mapa BS al uso" pelearía con la naturaleza del juego origen. La mecánica de parry direccional de E33 encaja 1:1 con el cubo direccional de BS, así que cada habilidad de Aline pasa a ser un ataque telegrafiado con ventana de parry. Asumimos como coste que el mapa no será rejugable competitivamente; lo compensa el wow-factor, el valor demostrativo del repo (Vivify + Unity 2019.4 + pipeline animaciones) y el hecho de que el caso de uso (E33 boss fight en BS) es viral incluso para quien no conoce BS.

---

### Personaje: Aline (Curatress) de Expedition 33

**Regla:** El boss del mapa es Aline.

**Por qué:** Vista frontal cinemática nativa del juego (encaja con la cámara fija de BS), formato humanoide proporcionado, detalle visual suficiente para sostener un boss fight de 2-3 min.

---

### Beatmap format V3 (los `.dat` de dificultad)

**Regla:** Las dificultades (`EasyStandard.dat`, `NormalStandard.dat`, `ExpertPlusStandard.dat`) y `BPMInfo.dat` usan V3 (`"version": "3.x.x"`, claves cortas `b/x/y/c/d/t`, `customData` sin underscore). El cheatsheet V2→V3 (útil al copiar snippets de ejemplos antiguos) vive en la skill [`vivify-mapping`](../.claude/skills/vivify-mapping/SKILL.md).

`Info.dat` no entra en esta decisión — es el manifest del mapa (registra dificultades, declara requirements, settings setter), no un beatmap, y BS 1.34.2 espera su único schema (`_version: "2.x.x"`, claves con underscore: `_difficultyBeatmapSets`, etc.).

**Por qué V3:** NoodleExtensions y los ejemplos modernos del corpus (`vivify_examples/`) son todos V3. Las docs de Heck también. Mantenerse alineado con el corpus actual y la docs evita drift y fricción de traducción.

---

### Mapa de Beat Saber versionado en git (`beatsaber-map/*.dat`)

**Regla:** Los `.dat` del mapa (`Info.dat`, `*Standard.dat`, `BPMInfo.dat`) y `bundleinfo.json` se versionan en git como cualquier otro archivo. Los binarios pesados (`*.vivify`, `*.ogg`) y backups manuales (`*.bak`, `*.v2bak`) están ignorados. El junction sigue siendo el deploy target del juego.

**Por qué:** El contenido textual JSON es el contenido más importante del proyecto y la fuente de verdad de cada ataque. Versionarlo da `git diff`, `git blame`, PR review y rollback granular. Junction y git son ortogonales — git ve archivos, no junctions, así que no hay conflicto.

---

### Scale 0.01 en el evento `InstantiatePrefab`

**Regla:** El evento `InstantiatePrefab` aplica `scale: [0.01, 0.01, 0.01]` (o el prefab tiene `localScale: 0.01` baked).

**Por qué:** Conversión Unreal cm → Unity m. Sin esto el modelo aparece 100x. La corrección vive en el evento (no en Blender) para mantener el modelo source limpio y la conversión explícita.

---

### Iluminación con Directional Lights dentro del prefab

**Regla:** Los prefabs Vivify que necesiten iluminación llevan sus propias luces como hijos. Hoy Aline va con shader unlit y no las usa, pero la regla aplica al añadir cualquier shader lit.

**Por qué:** Las luces vanilla del entorno de Beat Saber no afectan a objetos cargados por Vivify (otra layer/scene). La única forma de iluminar es luz que viaje dentro del bundle.

---

### DefaultEnvironment como base

**Regla:** El mapa usa `DefaultEnvironment`.

**Por qué:** Las luces vanilla son irrelevantes con Vivify, así que el environment elegido es el que mete menos ruido visual que pueda competir con Aline. Además simplifica el disable: `Environment|GameCore` regex captura todo lo relevante, no hace falta enumerar nombres específicos del environment (que cambian entre `TimbalandEnvironment`, `BillieEnvironment`, etc.). Aeroluna y nasafrasa también lo eligen para sus mapas Vivify (corpus 2026-05-02).

---

### Pose mismatch cross-clip se absorbe con blend en Animator, no editando data

**Regla:** Cuando dos AnimationClips tienen poses de inicio/fin distintas (típico: floating vs grounded), no editar las curvas para que matcheen — usar `duration > 0` en las transitions del AnimatorController para que Unity interpole pose A → pose B durante el blend. Para mismatches grandes, combinar con `exitTime < 1.0` para que el blend se solape con el final del clip y el cambio de pose ocurra durante el movimiento.

**Por qué:** Editar curvas para forzar match cross-clip es frágil (cualquier re-import del FBX las pierde) y puede romper la animación intra-clip. El blend del Animator es la herramienta nativa para esto y replica exactamente lo que UE hace por default vía "Blend Out duration" en sus AnimMontages. Validado 2026-05-02 con DashOut-Idle1: `exitTime=0.7, duration=0.3` en exit + `duration=0.3` en AnyState entry disuelve un teleport visible de ~5cm UP/DOWN al transitar entre grounded↔floating. La data del clip no se toca.

---

### Custom mesh propio para "suelo" en lugar de rip directo del juego

**Regla:** Para superficies donde Aline (u otros prefabs) deben "apoyarse", construir el mesh ad-hoc en Blender en lugar de usar un rip directo del juego, **siempre que el rip tenga geometría irregular**. Aplicar textura ripeada del juego encima para mantener el look auténtico.

**Por qué:** Los meshes ripeados de E33 (rocas, terrenos) son geometría natural irregular. Alinear pies de personaje sobre ese terreno es función no-constante de XZ — no hay un Y único válido. Iterar a ojo desde BS para encontrar el Y aceptable cuesta 5-6 ciclos de ajuste manual y nunca queda exacto. Un mesh custom con pivot en el TOP-CENTER y superficie controlada hace el placement determinístico de UN solo evento. Trade-off: pierdes la geometría auténtica del juego (los detalles de la roca real), pero mantienes la TEXTURA auténtica encima — visualmente pasa por "asset de E33". Probado 2026-05-02 con `SM_Rock_A_CliffEdge` (rip) vs custom plate Blender — el custom encaja Aline exacto en una pasada vs 6 iteraciones del rip y nunca exacto. Tiempo de Blender: ~30-45 min con blender-mcp interactivo.

---

### Settings Setter siempre presente, con starter pack mínimo

**Regla:** Cada dificultad declara `_customData._requirements` en `Info.dat` (al menos `["Vivify", "Chroma"]`, añadir `"Noodle Extensions"` si el .dat usa `coordinates`/`definitePosition`/etc.) y un bloque `_customData._settings` que fuerza al menos: `_playerOptions._noteJumpDurationTypeSettings: "Dynamic"` (universal en el corpus), `_environments._overrideEnvironments: false`, `_chroma._disableEnvironmentEnhancements: false`, y `_environmentEffectsFilterDefault/ExpertPlusPreset: "AllEffects"`. Para showcase cinemático añadimos `_noTextsAndHuds: true` + `_countersPlus._mainEnabled: false` + bloque `_uiTweaks` con todo a `false`.

**Por qué:** Sin el bloque, el mapa puede cargarse en condiciones que rompen Vivify silenciosamente: jugador con env override global (no se ve nuestro environment), modo Static NJS (ignora nuestro NJS), Chroma env enhancements desactivado por el jugador (no se aplica nuestro `environment[]` disable), HUD competition entre vanilla + Counters+ + UITweaks. El prompt de Settings Setter es cancelable por el jugador, pero si lo acepta zanjamos todo el ecosistema. Starter pack completo + justificación por línea + cobertura del corpus en la skill [`vivify-mapping`](../.claude/skills/vivify-mapping/SKILL.md) sección "Settings Setter".

---

### Mods de Aeroluna instalados a mano

**Regla:** Vivify, Heck, CustomJSONData, Chroma y NoodleExtensions se instalan a mano desde los releases de GitHub de Aeroluna. Versiones exactas en [BS_Dependencies.txt](../BS_Dependencies.txt).

**Por qué:** Mod Assistant a veces sirve versiones obsoletas que rompen las dependencias entre estos cinco mods.

---

### Junction (`mklink /J`) para `beatsaber-map/` y `beatsaber-logs/`

**Regla:** Acceso al mapa real (`CustomWIPLevels/Test/`) y a los logs de BS desde el repo via Windows junctions. El junction en sí (link a nivel filesystem) NO se versiona — cada máquina lo recrea con `mklink /J`. Lo que SÍ se versiona es el contenido textual de `beatsaber-map/` (`.dat`, `bundleinfo.json`); ver entrada "Mapa de Beat Saber versionado en git" arriba.

**Por qué junction (vs `.lnk` o `mklink /D`):** Junction = link real a nivel de filesystem (cualquier programa lo trata como carpeta normal), no requiere privilegios elevados como `mklink /D`, y un `.lnk` no funciona programáticamente.

---

### `ReMapper-master/` y `FModel.exe` fuera del repo

**Regla:** Las herramientas externas (ReMapper, FModel, dump de Sandfall) viven en `d:\vivify_repo\` (carpeta contenedora), no dentro del repo.

**Por qué:** Son tools/dumps externos, no parte del producto. ReMapper además trae su propio `.git` que rompería `git status` si quedara dentro.

---

### Animaciones que desplazan a Aline usan root motion sintetizado en Blender

**Regla:** Para clips donde Aline se desplaza horizontalmente (DashIn-Idle1, DashOut-Idle2, sus aliases, futuros mele), el motion se sintetiza en Blender vía `scripts/blender/synthesize_root_motion.py` moviendo `pose.bones["root"].location` al armature object con axis remap (Y bone → Z object negated). Unity con `motionNodeName="SK_Curator_Aline"` y `Apply Root Motion = ON` traslada el GO. NO se usa `AnimateTrack` cross-clip ni se intenta extraer del bone "root" desde Unity-side.

**Por qué (cross-clip por AnimateTrack ❌):** los clips están diseñados para encadenar via root delta. Compensar manualmente con `AnimateTrack` clip-a-clip se vuelve insostenible: cada nuevo clip suma coordinación cumulativa y los teleports/blends entre eventos rompen la continuidad. `_offsetPosition` se ignora silenciosamente en tracks Vivify-prefab; `_position` introduce teleports en cada llamada y exige cálculo manual de displacement por clip.

**Por qué (Unity-side extraction del bone interno ❌):** los `.psa` bakean motion en `pose.bones["root"].location[1]` (Y bone-local). El FBX SÍ lo expone como `m_LocalPosition.y` del path `SK_Curator_Aline/root`, pero Unity 2019.4 con `Generic + Copy From Other Avatar` no extrae motion de un bone interno como root motion en este flujo, da igual lo que se ponga en `motionNodeName` (probado: nombre, path completo, avatar rebuild, `keepOriginalPositionY=false`). `hasGenericRootTransform` se queda en `False` y `averageSpeed=(0,0,0)` siempre.

**Por qué (synthesize en Blender + axis remap ✅):** cuando el motion vive en `location` del armature object (top GO del rig), Unity sí lo extrae automáticamente. El axis remap `Y bone → Z object negated` no es estético: compensa la cadena `axis_up="Y"` del FBX exporter (intercambia Blender Y↔Z) + rotación `(270°, 0, 0)` que adquiere el armature object en Unity (conversión Z-up→Y-up). Sin remap o sin negación, Aline cae verticalmente o avanza al revés. Validado e2e en sandbox (2026-05-01): DashIn traslada ~6m forward, DashOut devuelve, sin snap-back.

**Coste asumido:** depende del `synthesize_root_motion.py` corriendo cada vez que se re-importan `.psa` con motion. Es idempotente y marca cada action procesada con su modo de axis-mapping. Detalle operativo en la skill `vivify-animations`.

---

### Animator en prefab root + `preserveHierarchy=true` en `Aline_Anims.fbx`

**Regla:** El componente `Animator` vive en el root del prefab `aline.prefab`. El importer de `Aline_Anims.fbx` tiene `preserveHierarchy=true` (forzado por `AlineAnimsImporter.OnPreprocessModel`).

**Por qué:** El export armature-only de Blender colapsa el armature object como nodo raíz del FBX y Unity colapsa además nodos top-level con un solo hijo. Sin `preserveHierarchy=true`, las clip paths salen sin prefijo `SK_Curator_Aline` y rompen la preview del FBX inspector (T-pose). Con la flag, las paths quedan prefijadas, el Animator puede vivir en el root y las scale curves del armature object caen en el GO `SK_Curator_Aline` (scale 1) → no-op. El root mantiene `localScale: 0.01`.

---

### Snapshots del mapa con `scripts/snapshot-map.ps1` (complemento a git)

**Regla:** Manual con label (`-Label X`, sin rotación) para momentos intencionales. Auto vía git pre-commit hook (`scripts/hooks/pre-commit`, ring buffer de 5, dedup por hash) para iteración. `core.hooksPath = scripts/hooks` activa el hook en clones nuevos.

**Por qué:** Etiquetar puntos jugables sin contaminar la historia de commits. Working backup del estado entre commits cuando se itera rápido. Tolerante a junction missing.

**Pendiente revisar:** ahora que el mapa está versionado en git, posible que el sistema sea redundante. Decidir en próxima auditoría.

---

### Fork minimal de unity-mcp (Unity 2019.4)

**Regla:** El `unity-mcp` que usamos es un fork minimal en `d:\vivify_repo\unity-mcp/` portado a Unity 2019.4, enganchado al proyecto vía `Packages/manifest.json` (path local). Bridge stdio en port 6400.

**Por qué:** El upstream `CoplayDev/unity-mcp` declara `unity: 2021.3+` y depende de C# 8/9 + UI Toolkit + APIs 2020+. Vivify recomienda 2019.4.28f1 oficialmente para max compat con BS 1.34.2. El fork strippa lo no esencial y reescribe lo justo a C# 7.3, manteniendo commits cherry-pickables por si en algún momento se propone PR upstream. Detalle en [unity-mcp/README.md](../../unity-mcp/README.md).

---

### Scope: Phase 1 + intro cosmética; deadline soft

**Regla:** El mapa cubre Phase 1 del boss fight + una intro cosmética corta (Aline aparece volando y se posiciona). Se sube como "Phase 1", deja la puerta abierta a Phase 2/3 después. Las familias de ataque a prototipar quedan reducidas a las que aparecen en Phase 1. La fecha del torneo (2026-05-09) **es soft**: calidad > speed. La gestión "skip torneo o entregar parcial" la lleva el usuario aparte.

**Por qué:** Phase 1 pulida tiene más valor demostrativo que 3 fases mediocres. La intro cosmética da contexto narrativo y esconde el setup técnico (instanciado, fade); no jugable, no cuenta como "Phase 0".

**Coste asumido:** decisiones grandes diferidas explícitamente — `Skill8` con Aline gigante (clímax fase 2), `Skill9`/`Skill11` ausentes, canción definitiva, wireado completo del state machine. Quedan en "Decisiones de diseño abiertas" de `NEXT_STEPS.md` para retomar en Phase 2/3.

---

### Construir sistemas de capa baja cuando hay caso de uso, no en abstracto

**Regla:** Antes de meter un sistema arquitectural nuevo (sobre todo de capa baja: lighting, post-process, shader pipeline, etc.), verificar que **existe un caso de uso ACTIVO** que lo necesita. "Va a venir bien a futuro" no cuenta. Preservar el conocimiento (doc, commit reversible) pero no meter el sistema sin demanda concreta.

**Excepción:** sistemas cuyo coste de retrofit es ALTO (formato de assets, estructura de bundle, shader pipeline entero) — ahí adelantarse paga porque migrar después es desproporcionado. Caso canónico en este proyecto: auto-sync de CRCs (`PostBuildSyncCRCs.cs`).

**Por qué:** "Lowest layer" sigue siendo el principio correcto, pero "lowest layer" se aplica AL momento de resolver el problema, no antes de que el problema exista. Construir capacidad sin demanda = inventario muerto + tuning ongoing constante. Caso documentado: ambient lighting para Aline llegó a end-to-end funcional pero se revirtió porque sin un FX narrativo concreto cada combinación skybox+ambientMode+colores requería iterar visualmente sin payoff. Conocimiento técnico (cómo evitar el `ShadeSH9=0` de bundles Vivify) preservado en [`vivify-materials`](../.claude/skills/vivify-materials/SKILL.md).

---

### Idioma: docs en español, commits en inglés

**Regla:** Los archivos del proyecto (código, docs, skills, comments) en **español**. Los mensajes de git **en inglés** desde 2026-04-26 inclusive. Los commits iniciales en español (`Initial commit`, `Configurar repo: ...`) se quedan como están — no traducir retroactivamente.

**Por qué:** El audience de los commits es más amplia (potencialmente la comunidad internacional de Vivify cuando el repo se publique) que el de los docs in-project (notas personales del mapper). El historial de commits debe leerse como narrativa técnica coherente. Traducción de docs a inglés diferida a post-torneo.
