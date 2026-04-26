# NEXT_STEPS

## Estado actual

Pipeline funcionando end-to-end:

- Vivify carga el bundle generado por Unity y instancia el prefab `aline.prefab` en escena.
- **Aline texturizada** con shader unlit cutout double-sided. 3 materiales: `M_Aline_Body_1`, `M_Aline_Body_2` (con BaseColor de FModel) y `M_Aline_Black` (para los 3 slots sin diffuse — BlackPart, BlackPart1, CuratorFace).
- Luces direccionales removidas de Aline y del cube de testeo (ya no hacen falta con unlit).
- **Sync de CRCs automatizado**: Editor watcher dispara `scripts/sync-crcs.ps1` cada vez que Vivify reescribe `bundleinfo.json`. Cero pasos manuales tras F5.
- Mods de Aeroluna instalados a mano desde GitHub (versiones en [BS_Dependencies.txt](../BS_Dependencies.txt)).
- Mapa V2 con `_customEvents` operativo: `InstantiatePrefab` testeado.

Lo que **no** está hecho todavía: animaciones de combate, canción definitiva, scripting con ReMapper, narrativa por fases concreta.

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

### 2026-04-26 — Texturizado de Aline + auto-sync de CRCs

- **Texturizado**: 2 PNG (`Curator_Body_BaseColor`, `Curator_Body_BaseColor_1`) copiados del dump de Sandfall a `VivifyTemplate/Assets/Aline/Textures/`. Shader nuevo `Aline/Standard` (unlit + alpha cutout 0.333 + `Cull Off`) en `Assets/Aline/Shaders/`. 3 materiales en `Assets/Aline/Materials/` asignados a los 5 slots del prefab según mapping deducido del byte-order del FBX y de los `MI_*.json` / `M_*.json` exportados por FModel. Luces direccionales borradas de Aline y del cube de testeo. FBX movido de `Assets/Test/` a `Assets/Aline/`.
- **Skill `vivify-materials`** rellenada con la receta unlit-cutout-double-sided, el flow de mapping FModel→Unity, y troubleshooting.
- **`scripts/sync-crcs.ps1`**: PowerShell que lee `bundleCRCs` de `bundleinfo.json` y patcha surgically (regex) los CRCs en `Info.dat._customData._assetBundle`. Preserva el formato exacto del `.dat` (sin churn de hash en snapshots), tolerante a junction missing, idempotente (no escribe si no hay cambio).
- **`Assets/Aline/Editor/PostBuildSyncCRCs.cs`**: Editor script con `[InitializeOnLoad]` que monta un `FileSystemWatcher` sobre `bundleinfo.json` y lanza el `.ps1` cada vez que Vivify hace build. Toggleable desde `Tools/Aline/Auto-sync CRCs after Vivify build`. Skill `unity-rebuild` actualizada en consecuencia.

---

## Próximos pasos (en orden)

### 1. Canción definitiva

Decidir pieza concreta del OST de Expedition 33. Importar `.ogg` al `beatsaber-map/`, ajustar BPM y duración. Anotar la decisión en `DECISIONES.md`.

### 2. Animaciones de combate

Importar animaciones `.psa` de FModel → Blender → Unity (Animator + AnimationClips). Hookear al prefab. Probar con eventos `AnimateTrack` desde el mapa.

### 3. Setup de ReMapper

Levantar Deno + primer script en `ReMapper-master/` (o en un subdir local). Output target: directo a `beatsaber-map/ExpertPlusStandard.dat` o staging intermedio. **Rellenar la skill `remapper-scripting`** durante este paso.

### 4. Diseño narrativo del boss fight

Traducir la estructura por fases de [PRODUCTO.md](PRODUCTO.md) en eventos concretos. Definir transiciones, animaciones por fase, patrones de notas que respondan a cada fase.

---

## Known issues / pendientes

- (vacío de momento)

---

## Lo que NO toca esta sesión (apuntado para luego)

- Configurar remote en GitHub. Decidir público vs privado y qué hacer con texturas si en algún momento se versionan (¿LFS?).
- `remapper-scripting/SKILL.md` con contenido real — empieza junto al setup de ReMapper.
- Quest support — fuera de scope salvo decisión expresa.

## Diferido post-torneo

Cuando el mapa esté entregado y haya margen, sesión de limpieza:

- **Rename `my_vivify_template/` → `aline-boss-fight/`**. Bloqueado durante la sesión de setup porque VSCode tiene handle abierto en `.git/`. Procedimiento: cerrar VSCode, `cd d:\vivify_repo && ren my_vivify_template aline-boss-fight`, reabrir VSCode en la nueva ruta. El `.git`, los junctions y todo lo demás viajan con la carpeta (los junctions apuntan a paths absolutos de Steam, no se rompen).
- **Traducir docs/skills al inglés** si en algún momento se quiere compartir el repo con la comunidad de Vivify (que es internacional). Decisión actual: español, proyecto personal.
- **Limpiar `.idea/` y `.vscode/` de VivifyTemplate** del staging si entran cambios espurios en commits.
- **Cambiar `origin/main`** del template upstream (`Swifter1243/VivifyTemplate`) al remote propio cuando se monte en GitHub.
- **Upgrade unlit → lit/PBR para Aline**. Los Normal/ORM/Emissive de los `MI_Curator_Aline_Body_*.json` y `MI_Curator_Aline_Palette*.json` ya están descritos en el dump de Sandfall (`Sandfall/Content/Characters/Enemies/HumanEnnemies/Aline/Textures/`). Implica: copiar las PNGs adicionales, ampliar el shader `Aline/Standard` (o crear `Aline/Lit`) con muestreo de Normal + ORM + Emissive, decidir modelo de iluminación (lambert + ambient, PBR completo, o cel-shading). Tradeoff: mejor look vs complejidad de tunear iluminación dentro del bundle de Vivify.
- **Polish visual de los slots negros** (BlackPart, BlackPart1, CuratorFace). Hoy son negro plano. Originalmente en Unreal usan fresnel + alpha + paint procedural. Para recrear: shader fresnel simple para los BlackPart (edge darkening con `1 - dot(viewDir, normal)`), y para `M_CuratorFace` componer `Mask_Curator.png` (`Sandfall/.../Curator/Textures/`) + `T_Paint1.png` + `T_Aura.png` con un blend translucent.
- **Importar `palette.pskx` y `palette1.pskx`** del dump (`Sandfall/.../Aline/`) si se quiere que Aline sostenga sus paletas (las "armas" del Curator). Las texturas Palette y los `MI_Curator_Aline_Palette*.json` ya están preparados; falta importar las pskx vía Blender → FBX y añadirlas como child del prefab.
