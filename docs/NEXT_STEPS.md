# NEXT_STEPS

## Estado actual

Pipeline funcionando end-to-end:

- Vivify carga el bundle generado por Unity y instancia el prefab `aline.prefab` en escena.
- **Aline texturizada** con shader unlit cutout double-sided. 3 materiales: `M_Aline_Body_1`, `M_Aline_Body_2` (con BaseColor de FModel) y `M_Aline_Black` (para los 3 slots sin diffuse — BlackPart, BlackPart1, CuratorFace).
- Luces direccionales removidas de Aline y del cube de testeo (ya no hacen falta con unlit).
- **Sync de CRCs automatizado**: Editor watcher dispara `scripts/sync-crcs.ps1` cada vez que Vivify reescribe `bundleinfo.json`. Cero pasos manuales tras F5.
- Mods de Aeroluna instalados a mano desde GitHub (versiones en [BS_Dependencies.txt](../BS_Dependencies.txt)).
- Mapa V2 con `_customEvents` operativo: `InstantiatePrefab` testeado.
- **Pipeline de animaciones — infrastructure montada, last mile pendiente**:
  - 26 actions importadas en Blender desde `.psa` de FModel vía `scripts/blender/import_all_psa.py`.
  - Export a `Aline_Anims.fbx` vía `scripts/blender/export_anims_fbx.py` (NLA tracks).
  - `Aline_AC.controller` generado con 26 estados + triggers vía `Editor/BuildAlineAnimator.cs`.
  - Animator component reubicado en `SK_Curator_Aline` child para evitar el bug de scale curves a path `<root>`.
  - Aline aparece en BS a tamaño correcto en T-pose (estado de `git HEAD` antes de animaciones funcionando).
  - **Pendiente**: las clips llegan a Unity sin movimiento real (fcurves identity). Probable bug del bake al exportar bajo MCP context. Investigar al volver con Unity MCP funcionando.

Lo que **no** está hecho todavía: animaciones reproduciéndose en runtime, canción definitiva, scripting con ReMapper, narrativa por fases concreta.

---

## Changelog

### Pre-2026-04-26 — Sesión inicial

- Setup del proyecto Unity con VivifyTemplate.
- Importación de Aline desde dump de Sandfall (FModel) → Blender → Unity.
- Decisión de modelo (Aline sobre Dualliste), formato V2, scale 0.01.
- Primer bundle exportado y verificado en Beat Saber.

### 2026-04-26 — Setup de repo y documentación

- Repo organizado: `CLAUDE.md`, `docs/PRODUCTO.md`, `docs/ARQUITECTURA.md`, `docs/NEXT_STEPS.md`, `docs/DECISIONES.md`. `my-notes.md` queda como scratchpad.
- `.gitignore` que cubre Sandfall, ReMapper-master, FModel.exe, bundles, audio, modelos 3D, texturas binarias y el junction del mapa.
- Junction `beatsaber-map/` creado con `mklink /J` apuntando a `CustomWIPLevels/Test/`. Lectura de `.dat` desde el repo sin paths absolutos.
- `ReMapper-master/` y `FModel.exe` movidos fuera del repo (a `d:\vivify_repo\`).
- `scripts/snapshot-map.ps1` con dos modos: manual (`-Label X`, sin rotación) y automático (`-Auto`, ring buffer de 5 con dedup por hash). El modo automático lo invoca un git pre-commit hook (`scripts/hooks/pre-commit`) configurado vía `core.hooksPath = scripts/hooks`. Tolerante a fallos: si no hay junction, no rompe el commit.
- Skills `vivify-mapping` y `unity-rebuild` ampliadas con tablas de errores comunes y validación de paths vía `bundleinfo.json`. Skill nueva `remapper-scripting` (esqueleto).

### 2026-04-26 — Animaciones (infrastructure) + investigación unity-mcp port

- **Blender MCP** (ahujasid/blender-mcp) registrado para automatización del flujo de Blender desde Claude Code. Funciona bajo Unity 2019.4 sin problemas (no toca Unity).
- **Import batch de `.psa`**: `scripts/blender/import_all_psa.py` carga las 27 .psa de Sandfall vía la API programática del addon DarklightGames (fork del Befzz). Diagnóstico clave: el addon no auto-linkea la action al armature tras importar; `arm.animation_data.action = action` requiere set manual. 26 actions resultantes (1 colisión de nombre `DefaultSlot` entre dos Montages).
- **Export FBX**: `scripts/blender/export_anims_fbx.py` exporta armature + actions vía NLA tracks (workaround porque `bake_anim_use_all_actions` no itera fiable bajo MCP context). Output: `VivifyTemplate/Assets/Aline/Animations/Aline_Anims.fbx` (185 MB, gitignored). Avatar de `Aline.fbx` reusado vía `Copy From Other Avatar`.
- **Editor scripts** en `Assets/Aline/Editor/`:
  - `AlineAnimsImporter.cs` — AssetPostprocessor, fija `loopTime=true` en idles canónicos al importar (workaround del bug del Inspector de 2019.4 donde toggles per-clip se descartan al cambiar de clip sin Apply).
  - `BuildAlineAnimator.cs` — Tools menu, regenera `Aline_AC.controller` con 26 estados + triggers (`Idle1`, `Skill1`, etc., sin prefijo `Paintress_`). `Any State → X` por trigger, auto-return a Idle1 al exit time para no-loops.
  - `InspectAlineClips.cs` — Tools menu de diagnóstico, vuelca curves de un clip a Console.
- **Bug arquitectural del Animator**: clips contienen scale curves en path `<root>` (forzadas por bake_anim del FBX export aunque las actions no tengan fcurves de scale). Si el Animator vive en el root del prefab (que tiene `localScale: 0.01` baked), las curves pisan el 0.01 con 1.0 → modelo 100x. Solución: mover el Animator a `SK_Curator_Aline` (child del prefab a scale 1) — el scale curve sample queda no-op.
- **unity-mcp investigación + abort**: el addon UPM de [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) requiere Unity 2021.3+. Intento de instalar en 2019.4 dejó el proyecto roto temporalmente (USS post-2021, dependency `com.unity.nuget.newtonsoft-json 3.0.2` no en registry de 2019). Removed de `Packages/manifest.json` y `packages-lock.json`. Decisión: mantener Unity 2019.4 (recomendación oficial de Vivify para max compat BS) y plantear el port mínimo del unity-mcp a 2019.4 como side-project — ver sección "Side-projects".
- **Memorias guardadas**: `feedback_learn_from_obstacles.md` (estilo de debugging que valida small rocks), `project_unity_2019_choice.md` (recordar que 2019.4 es canónico, no deuda).

### 2026-04-26 — Texturizado de Aline + auto-sync de CRCs

- **Texturizado**: 2 PNG (`Curator_Body_BaseColor`, `Curator_Body_BaseColor_1`) copiados del dump de Sandfall a `VivifyTemplate/Assets/Aline/Textures/`. Shader nuevo `Aline/Standard` (unlit + alpha cutout 0.333 + `Cull Off`) en `Assets/Aline/Shaders/`. 3 materiales en `Assets/Aline/Materials/` asignados a los 5 slots del prefab según mapping deducido del byte-order del FBX y de los `MI_*.json` / `M_*.json` exportados por FModel. Luces direccionales borradas de Aline y del cube de testeo. FBX movido de `Assets/Test/` a `Assets/Aline/`.
- **Skill `vivify-materials`** rellenada con la receta unlit-cutout-double-sided, el flow de mapping FModel→Unity, y troubleshooting.
- **`scripts/sync-crcs.ps1`**: PowerShell que lee `bundleCRCs` de `bundleinfo.json` y patcha surgically (regex) los CRCs en `Info.dat._customData._assetBundle`. Preserva el formato exacto del `.dat` (sin churn de hash en snapshots), tolerante a junction missing, idempotente (no escribe si no hay cambio).
- **`Assets/Aline/Editor/PostBuildSyncCRCs.cs`**: Editor script con `[InitializeOnLoad]` que monta un `FileSystemWatcher` sobre `bundleinfo.json` y lanza el `.ps1` cada vez que Vivify hace build. Toggleable desde `Tools/Aline/Auto-sync CRCs after Vivify build`. Skill `unity-rebuild` actualizada en consecuencia.

---

## Próximos pasos (en orden)

### 1. Canción definitiva

Decidir pieza concreta del OST de Expedition 33. Importar `.ogg` al `beatsaber-map/`, ajustar BPM y duración. Anotar la decisión en `DECISIONES.md`.

### 2. Animaciones de combate (infrastructure DONE, last mile pendiente)

Pipeline `.psa` → Blender → FBX → Unity Animator → Vivify `SetAnimatorProperty` montado al completo (ver Changelog 2026-04-26 e [ARQUITECTURA.md#pipeline-de-animaciones](ARQUITECTURA.md)). Pendiente:

- **Diagnosticar por qué los clips llegan con fcurves identity** (no animan en preview ni runtime). Sospechas:
  - `bake_anim_use_all_actions` o `bake_anim_use_nla_strips` no muestreando los keyframes de cada action correctamente bajo MCP context.
  - Posible mismatch entre el rig exportado y el avatar de Aline.fbx (rest pose dispar).
  - Investigar inspeccionando el FBX exportado directamente o reabriendo el `.blend` y exportando con la UI de Blender (no MCP) como control.
- Una vez Idle1 anime en BS: añadir un evento `SetAnimatorProperty` con trigger `Idle1` al `.dat` para confirmar que Vivify dispara el state machine. Snapshot + commit como checkpoint.
- Después: wireado del state machine narrativo (qué skill dispara qué transición). Esto es contenido, no infra.

### 3. Setup de ReMapper

Levantar Deno + primer script en `ReMapper-master/` (o en un subdir local). Output target: directo a `beatsaber-map/ExpertPlusStandard.dat` o staging intermedio. **Rellenar la skill `remapper-scripting`** durante este paso.

### 4. Diseño narrativo del boss fight

Traducir la estructura por fases de [PRODUCTO.md](PRODUCTO.md) en eventos concretos. Definir transiciones, animaciones por fase, patrones de notas que respondan a cada fase.

---

## Known issues / pendientes

- **Animation clips llegan a Unity sin movimiento**. Las clips se ven como T-pose en el preview del FBX a pesar de que en Blender la action sí tiene datos de bone transforms no-identity (verificado con sampling en frames 0/50/140 — pelvis loc cambia). Hipótesis: `bake_anim_use_nla_strips=True` con tracks muted no produce takes correctos bajo MCP context. Probable fix: probar export desde la UI de Blender directamente, o pushear NLA tracks no-muted, o iterar manualmente set/export por action. Bloquea el end-to-end de step 2.

---

## Lo que NO toca esta sesión (apuntado para luego)

- Configurar remote en GitHub. Decidir público vs privado y qué hacer con texturas si en algún momento se versionan (¿LFS?).
- `remapper-scripting/SKILL.md` con contenido real — empieza junto al setup de ReMapper.
- Quest support — fuera de scope salvo decisión expresa.

---

## Side-projects (portfolio)

### Port mínimo de unity-mcp a Unity 2019.4

[CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) declara `"unity": "2021.3"` en `package.json` y los Vivify mappers están atados a 2019.4.28f1 por la doc oficial (`docs/heckdocs-main/docs/vivify/getting-started-with-vivify.md:10` — "for maximum compatibility, you should use 2019.4.28f"). Un fork compatible con 2019 desbloquea el ecosistema BS Vivify para usar AI-driven Unity tooling. Valor de portfolio + comunidad agradecida.

**Hallazgos del clone preliminar** (2026-04-26, repo en `d:\vivify_repo\unity-mcp/`):

- `package.json:6` declara constraint `"unity": "2021.3"` — aflojarlo es 1 línea pero no es suficiente.
- Depende de `com.unity.nuget.newtonsoft-json 3.0.2` (ese package se añadió al registry en 2020.1; en 2019.4 hay que vendorizar la DLL en `Plugins/`).
- `com.unity.test-framework 1.1.31` — relajar a 1.1.24 (es la que ship 2019.4).
- 257 archivos C# en `MCPForUnity/`. **41 usos de C# 8+** (switch expressions, pattern matching avanzado, `with`-expressions) repartidos en 17 archivos. Unity 2019.4 fija C# 7.3 sin override; cada sitio hay que reescribirlo. Ficheros con más densidad: `Services/MCPServiceLocator.cs` (11), `Tools/ManageScriptableObject.cs` (4), `Tools/ManageScript.cs` (3), `Tools/Animation/ClipCreate.cs` (3), `External/Tommy.cs` (3).
- El wizard UI usa **UI Toolkit** post-2021. Unity 2019 tiene UIElements legacy con API distinta — migración no trivial, posiblemente infactible sin reescribir la ventana.
- 22 Configurators para clientes MCP (Claude Code, Cursor, Windsurf, Cline, Codex, Gemini, Trae, Kilo, Kiro, OpenClaw, OpenCode, etc.), dependency manager, ProBuilder/VFX/profiler tools — superficie post-2021 que se puede strippar para una versión mínima.

**Estrategia recomendada — port mínimo (4-8 h)**:

1. Strip wizard UI y los 22 configurators (los clientes se configuran a mano vía `claude mcp add`).
2. Vendorizar `Newtonsoft.Json.dll` en `Plugins/`, eliminar dependencia del package.
3. Mantener core: Python server (sin tocar) + Unity-side WebSocket bridge + 8-10 tools clave (`ManageScript`, `ManageAsset`, `ControllerCreate`, `ClipCreate`, `ManagePrefab`, `BuildAssetBundle`, `RefreshUnity`, etc.).
4. Reescribir los 41 sitios C# 8+ a C# 7.3.
5. Test en VivifyTemplate 2019.4 con `uvx` server desde Python.

**Estrategia full (1-2 días)** — para PR a upstream:

Lo de arriba + migración UI Toolkit→UIElements del wizard + tests pasando + actualización de docs y README. Output: PR a CoplayDev mergeable. Mayor valor para portfolio porque toca todo el repo, no solo un subset.

**Estado actual**: clone shallow en `d:\vivify_repo\unity-mcp/` (no versionado en este repo, igual que `ReMapper-master/`). Investigación documentada arriba — al retomar, partir de aquí sin re-explorar.

---

## Diferido post-torneo

Cuando el mapa esté entregado y haya margen, sesión de limpieza:

- **Rename `my_vivify_template/` → `aline-boss-fight/`**. Bloqueado durante la sesión de setup porque VSCode tiene handle abierto en `.git/`. Procedimiento: cerrar VSCode, `cd d:\vivify_repo && ren my_vivify_template aline-boss-fight`, reabrir VSCode en la nueva ruta. El `.git`, los junctions y todo lo demás viajan con la carpeta (los junctions apuntan a paths absolutos de Steam, no se rompen).
- **Traducir docs/skills al inglés** si en algún momento se quiere compartir el repo con la comunidad de Vivify (que es internacional). Decisión actual: español, proyecto personal.
- **Limpiar `.idea/` y `.vscode/` de VivifyTemplate** del staging si entran cambios espurios en commits.
- **Cambiar `origin/main`** del template upstream (`Swifter1243/VivifyTemplate`) al remote propio cuando se monte en GitHub.
- **Upgrade unlit → lit/PBR para Aline**. Los Normal/ORM/Emissive de los `MI_Curator_Aline_Body_*.json` y `MI_Curator_Aline_Palette*.json` ya están descritos en el dump de Sandfall (`Sandfall/Content/Characters/Enemies/HumanEnnemies/Aline/Textures/`). Implica: copiar las PNGs adicionales, ampliar el shader `Aline/Standard` (o crear `Aline/Lit`) con muestreo de Normal + ORM + Emissive, decidir modelo de iluminación (lambert + ambient, PBR completo, o cel-shading). Tradeoff: mejor look vs complejidad de tunear iluminación dentro del bundle de Vivify.
- **Polish visual de los slots negros** (BlackPart, BlackPart1, CuratorFace). Hoy son negro plano. Originalmente en Unreal usan fresnel + alpha + paint procedural. Para recrear: shader fresnel simple para los BlackPart (edge darkening con `1 - dot(viewDir, normal)`), y para `M_CuratorFace` componer `Mask_Curator.png` (`Sandfall/.../Curator/Textures/`) + `T_Paint1.png` + `T_Aura.png` con un blend translucent.
- **Importar `palette.pskx` y `palette1.pskx`** del dump (`Sandfall/.../Aline/`) si se quiere que Aline sostenga sus paletas (las "armas" del Curator). Las texturas Palette y los `MI_Curator_Aline_Palette*.json` ya están preparados; falta importar las pskx vía Blender → FBX y añadirlas como child del prefab.
