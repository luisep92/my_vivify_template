# NEXT_STEPS

## Estado actual

Pipeline funcionando end-to-end:

- Vivify carga el bundle generado por Unity y instancia el prefab `aline.prefab` en escena.
- Aline visible, escalada (0.01) e iluminada (Directional Lights dentro del propio prefab).
- Mods de Aeroluna instalados a mano desde GitHub (versiones en [BS_Dependencies.txt](../BS_Dependencies.txt)).
- Mapa V2 con `_customEvents` operativo: `InstantiatePrefab` testeado.

Lo que **no** está hecho todavía: texturas aplicadas, animaciones de combate, canción definitiva, scripting con ReMapper, narrativa por fases concreta.

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

---

## Próximos pasos (en orden)

### 1. Texturizado de Aline

Aplicar las texturas de `VivifyTemplate/Assets/Aline/Textures/` a materiales del prefab. Implica:

- Crear materiales en Unity con shader compatible con bundles Vivify.
- Asignarlos al prefab.
- Rebuild (F5) y verificar en BS que Aline ya no es gris/rosa de "missing material".
- **Rellenar la skill `vivify-materials`** durante esta tarea (ahora está vacía).

### 2. Canción definitiva

Decidir pieza concreta del OST de Expedition 33. Importar `.ogg` al `beatsaber-map/`, ajustar BPM y duración. Anotar la decisión en `DECISIONES.md`.

### 3. Animaciones de combate

Importar animaciones `.psa` de FModel → Blender → Unity (Animator + AnimationClips). Hookear al prefab. Probar con eventos `AnimateTrack` desde el mapa.

### 4. Setup de ReMapper

Levantar Deno + primer script en `ReMapper-master/` (o en un subdir local). Output target: directo a `beatsaber-map/ExpertPlusStandard.dat` o staging intermedio. **Rellenar la skill `remapper-scripting`** durante este paso.

### 5. Diseño narrativo del boss fight

Traducir la estructura por fases de [PRODUCTO.md](PRODUCTO.md) en eventos concretos. Definir transiciones, animaciones por fase, patrones de notas que respondan a cada fase.

---

## Known issues / pendientes

- (vacío de momento)

---

## Lo que NO toca esta sesión (apuntado para luego)

- Configurar remote en GitHub. Decidir público vs privado y qué hacer con texturas si en algún momento se versionan (¿LFS?).
- `vivify-materials/SKILL.md` con contenido real — empieza junto al texturizado.
- `remapper-scripting/SKILL.md` con contenido real — empieza junto al setup de ReMapper.
- Quest support — fuera de scope salvo decisión expresa.

## Diferido post-torneo

Cuando el mapa esté entregado y haya margen, sesión de limpieza:

- **Rename `my_vivify_template/` → `aline-boss-fight/`**. Bloqueado durante la sesión de setup porque VSCode tiene handle abierto en `.git/`. Procedimiento: cerrar VSCode, `cd d:\vivify_repo && ren my_vivify_template aline-boss-fight`, reabrir VSCode en la nueva ruta. El `.git`, los junctions y todo lo demás viajan con la carpeta (los junctions apuntan a paths absolutos de Steam, no se rompen).
- **Traducir docs/skills al inglés** si en algún momento se quiere compartir el repo con la comunidad de Vivify (que es internacional). Decisión actual: español, proyecto personal.
- **Limpiar `.idea/` y `.vscode/` de VivifyTemplate** del staging si entran cambios espurios en commits.
- **Cambiar `origin/main`** del template upstream (`Swifter1243/VivifyTemplate`) al remote propio cuando se monte en GitHub.
