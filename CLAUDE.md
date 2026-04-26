# Aline Boss Fight — instrucciones para Claude Code

## Producto

Mapa de Beat Saber con [Vivify](https://github.com/Aeroluna/Vivify): boss fight contra **Aline (Curatress)** del juego *Expedition 33*. Custom prefab 3D animado en escena, narrativa por fases, mapa jugable con mods de Aeroluna sobre Beat Saber 1.34.2.

Los detalles creativos viven en [docs/PRODUCTO.md](docs/PRODUCTO.md). El stack técnico y el pipeline en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

---

## Perfil del usuario

Mapper de Beat Saber con experiencia técnica. Primer proyecto serio con Vivify.

Trato de **colega senior**, no de tutorial. Propuestas directas, justificación breve de las decisiones, esperar a que pregunte si algo no le cuadra. No explicar conceptos básicos salvo que sean específicos de Vivify/Heck/CustomJSONData.

Idioma de la documentación: español. **Idioma de los commits: inglés** (a partir de 2026-04-26 — los iniciales en español se quedan como están). Cuando se abra el repo, los commits cuentan la historia técnica y debe leerse en inglés.

---

## Dónde vive cada cosa

| Qué | Dónde | Notas |
|---|---|---|
| Concepto creativo, narrativa, criterios de éxito | [docs/PRODUCTO.md](docs/PRODUCTO.md) | El "qué" |
| Pipeline técnico, stack, paths | [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | El "cómo" |
| Estado actual, changelog, próximos pasos | [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) | Empezar a leer aquí cada sesión |
| Decisiones grandes con su porqué | [docs/DECISIONES.md](docs/DECISIONES.md) | ADR ligero |
| Notas vivas, scratchpad | [docs/my-notes.md](docs/my-notes.md) | Lo que aún no encaja en otro sitio |
| Snapshots manuales del mapa | [docs/map-snapshots/](docs/map-snapshots/) | Generados con `scripts/snapshot-map.ps1` |
| Mapa Beat Saber (junction al juego) | `beatsaber-map/` | NO se versiona. Junction local. |
| Logs de Beat Saber (junction) | `beatsaber-logs/` | NO se versiona. `_latest.log` para la sesión actual; `*.log.gz` para sesiones anteriores. |
| Proyecto Unity (prefabs, materiales, shaders) | `VivifyTemplate/` | Su propio `.gitignore` cubre Library/Temp/etc |
| Skills de Claude Code | `.claude/skills/` | vivify-mapping, unity-rebuild, vivify-materials, vivify-animations, remapper-scripting |
| Dependencias del juego | [BS_Dependencies.txt](BS_Dependencies.txt) | Versiones de mods exactas |

Fuera del repo (en `d:\vivify_repo\`):

- `Sandfall/` — dump de assets de Expedition 33 (FModel). ~40 GB.
- `ReMapper-master/` — tool Deno/TypeScript para scripting del mapa.
- `FModel.exe` — explorador de assets de Unreal Engine.

---

## Reglas no negociables

1. **Asset paths siempre en lowercase** dentro de eventos del mapa. `assets/aline/prefabs/aline.prefab`, no `Assets/Aline/...`. Match exacto con `bundleinfo.json`.
2. **Map format V2.** Todas las claves del root con underscore (`_time`, `_type`, `_data`, `_customEvents`). Dentro de `_data` SIN underscore (`asset`, `id`, `track`, `position`).
3. **Sync de CRCs automático tras F5** vía Editor watcher (`Assets/Aline/Editor/PostBuildSyncCRCs.cs` → `scripts/sync-crcs.ps1`). Sin pasos manuales si Unity está abierto. Manual fallback: `.\scripts\sync-crcs.ps1`. La skill `unity-rebuild` cubre el flujo.
4. **No commitear** archivos pesados. Lista en `.gitignore`: `*.vivify`, `*.ogg`, modelos 3D (`.fbx`, `.blend`, `.psa`...), texturas binarias (`.png`, `.tga`, `.exr`...). Los `.meta` de Unity sí se versionan.
5. **Snapshots del mapa**:
   - Manual con label antes de cambios grandes: `.\scripts\snapshot-map.ps1 -Label "antes-de-X"`. Persiste hasta que se borre.
   - Automático: el git pre-commit hook llama a `snapshot-map.ps1 -Auto`. Ring buffer de 5, dedup por hash (no duplica si los `.dat` no cambiaron). Configurado vía `core.hooksPath = scripts/hooks`.
6. **Mods de Aeroluna instalados a mano desde GitHub.** Mod Assistant trae versiones obsoletas que rompen dependencias.

---

## Pipeline de un cambio típico

```
Editar prefab/material/shader en Unity
  → F5 (build uncompressed) o Vivify > Build > Build Configuration Window
  → Unity escribe bundles + bundleinfo.json en beatsaber-map/
  → Leer bundleinfo.json y copiar bundleCRCs._windows2021 a Info.dat._customData._assetBundle._windows2021
  → Probar en Beat Saber (relanzar mapa)
  → Si va a producción: snapshot-map.ps1 + commit
```

Los `.dat` del mapa (notas, eventos, custom events) se editan directamente, sin rebuild de Unity. Solo necesitan rebuild los assets de `VivifyTemplate/Assets/`.

---

## Skills disponibles

- **vivify-mapping** — editar `.dat`, V2 syntax, eventos Vivify, CRC sync, debugging de prefabs que no cargan.
- **unity-rebuild** — flujo F5 / Build Configuration Window, sync de CRCs, errores de build.
- **vivify-materials** — receta unlit-cutout-double-sided, mapping FModel→Unity de materiales, troubleshooting magenta/missing/missing-shader.
- **vivify-animations** — pipeline `.psa` → Blender → FBX → Unity Animator → Vivify `SetAnimatorProperty`. Scripts de import/export en `scripts/blender/`, Editor scripts en `Assets/Aline/Editor/`. Gotchas conocidos del export Blender→FBX.
- **remapper-scripting** — `TO BE DONE`. Se rellena cuando empecemos a usar ReMapper.
