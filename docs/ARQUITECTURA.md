# ARQUITECTURA — Pipeline técnico

## Bootstrap desde cold clone

Pasos para arrancar el proyecto en una máquina nueva, en orden estricto.

1. **Instalar Beat Saber 1.34.2** + cadena de mods de Aeroluna (Vivify, Heck, CustomJSONData, Chroma, NoodleExtensions). Versiones exactas en [BS_Dependencies.txt](../BS_Dependencies.txt). **No usar Mod Assistant** — instalar a mano desde [github.com/Aeroluna/Heck/releases](https://github.com/Aeroluna/Heck/releases) y [github.com/Aeroluna/Vivify/releases](https://github.com/Aeroluna/Vivify/releases). Mod Assistant a veces sirve versiones obsoletas que rompen las dependencias entre sí.

2. **Instalar Unity 2019.4.28f1** (versión exacta) desde Unity Hub. Distinta versión = bundle no compatible con BS.

3. **Instalar Blender 4.2 LTS** + addon `io_scene_psk_psa` (Befzz/DarklightGames) habilitado en Preferences > Extensions. Necesario para procesar `.psa` (animaciones) y `.pskx` (meshes) de FModel.

4. **Clonar el repo**:
   ```
   git clone <url> d:\vivify_repo\my_vivify_template
   ```

5. **Crear los junctions** (cmd, no PowerShell — `mklink` es interno de cmd):
   ```cmd
   cd d:\vivify_repo\my_vivify_template
   mklink /J beatsaber-map  "C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Beat Saber_Data\CustomWIPLevels\Test"
   mklink /J beatsaber-logs "C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Logs"
   ```
   Crear el directorio `CustomWIPLevels\Test\` antes si no existe. Tras esto, los `.dat` versionados (`Info.dat`, `*Standard.dat`, `BPMInfo.dat`, `bundleinfo.json`) ya están accesibles en `beatsaber-map/` (vía junction al directorio del juego).

6. **Conseguir los binarios no versionados**. Lo que falta tras el clone:
   - **Audio del mapa** (`beatsaber-map/La-mandanga.ogg`, ~2.3 MB) — **no hay backup**. Si no lo tienes, el mapa no carga audio y BS puede rechazarlo. Pendiente decidir cómo distribuirlo (ver "Recovery" abajo).
   - **Sandfall dump** (`d:\vivify_repo\Sandfall/`, ~40 GB) — re-rip del juego con FModel. Setup: `%APPDATA%\FModel\AppSettings.json` con game dir = `D:\SteamLibrary\steamapps\common\Expedition 33`, UE version = 5.4, mappings = `Expedition33Mappings-1.5.4.usmap` (también en `d:\vivify_repo\fmodel-mcp\mappings\`). Output dir esperado: `D:\vivify_repo\Output\Exports\`.
   - **Aline_project.blend** (`Sandfall/Content/Characters/Enemies/HumanEnnemies/Aline/Aline_project.blend`) — **no hay backup**. Es el `.blend` de trabajo donde están las 27 actions importadas de `.psa` con el axis remap del root motion ya aplicado. Si se pierde, hay que reconstruir desde cero con `scripts/blender/import_all_psa.py` + `synthesize_root_motion.py`. Pendiente decidir si versionarlo (gitignored hoy por la regla `*.blend`).
   - **Texturas, FBXes, PSAs** dentro de `VivifyTemplate/Assets/Aline/` — gitignored por extensión. Recuperables vía pipeline de re-rip (ver "Recovery").

7. **Tools fuera del repo**. Si no están en `d:\vivify_repo/`:
   ```
   cd d:\vivify_repo
   git clone https://github.com/luisep92/unity_vivify_mcp.git unity-mcp
   git clone https://github.com/luisep92/fmodel-mcp.git fmodel-mcp
   ```
   Detalles de wireado y arranque en [unity-mcp/README.md](../../unity-mcp/README.md) y [fmodel-mcp/README.md](../../fmodel-mcp/README.md). El proyecto Aline ya referencia `unity-mcp` vía `VivifyTemplate/Packages/manifest.json` (path local).

8. **Abrir el proyecto Unity**: `VivifyTemplate/` desde Unity Hub. Primer import tarda ~5 min (regenera `Library/`). Si falta algún binario (FBX, PSA, PNG), saldrán warnings de "missing reference" — recuperar según el procedimiento de "Recovery" abajo.

9. **Primer build**: F5 (o `Vivify > Build > Build Configuration Window`). Genera `bundleWindows2021.vivify` + `bundleinfo.json` en `beatsaber-map/`. PostBuildSyncCRCs sincroniza el CRC a `Info.dat` automáticamente.

10. **Lanzar BS**, ir a `Custom WIP Levels`, mapa `Test`. Las dificultades Easy/Normal/ExpertPlus deben aparecer.

## Recovery — qué pasa si borras X

Tabla de "si borras X, ¿es recuperable y cómo?". Versionado = en git, recuperable con `git checkout`. Regenerable = se reconstruye con un comando local. Lost = no hay backup, hay que re-conseguir desde fuera.

| Si borras... | Estado | Recovery |
|---|---|---|
| Cualquier `.md`, `.cs`, `.shader`, `.mat`, `.prefab`, `.meta` | Versionado | `git checkout <path>` |
| `beatsaber-map/*.dat`, `bundleinfo.json` | Versionado | `git checkout beatsaber-map/<file>` |
| `beatsaber-map/bundleWindows2021.vivify` (~128 MB) | Regenerable | F5 en Unity (regenera bundle + bundleinfo.json + sync CRC) |
| `beatsaber-map/La-mandanga.ogg` (~2.3 MB) | **Lost (sin backup)** | No hay procedimiento. **Pendiente:** decidir si versionar el `.ogg` (excepción a `*.ogg` en `.gitignore`) o documentar fuente externa. |
| `VivifyTemplate/Library/`, `Temp/`, `Logs/` | Regenerable | Abrir Unity, regenera solo (~5 min primer arranque) |
| `VivifyTemplate/Assets/Aline/Textures/*.png` | Regenerable | Re-rip de `Sandfall/` con `mcp__fmodel__fmodel_export_texture` y mover el PNG de `Output/Exports/.../*.png` a la carpeta. Receta en [`vivify-materials`](../.claude/skills/vivify-materials/SKILL.md) sección "Mapping de FModel → Unity". |
| `VivifyTemplate/Assets/Aline/Animations/Aline_Anims.fbx` (~185 MB) | Regenerable | Re-export desde Blender: `scripts/blender/export_anims_fbx.py` (requiere `Aline_project.blend` con las 27 actions importadas). |
| `VivifyTemplate/Assets/Aline/Hair/*.fbx` | Regenerable | Re-correr `scripts/blender/pskx_to_fbx.py` sobre el `.psk` de `Sandfall/Content/Characters/Hair/Mirror_Family/Aline/`. |
| `VivifyTemplate/Assets/Aline/Scenery/Meshes/RockPlatform.fbx` | Regenerable | Re-correr `scripts/blender/build_rock_platform.py` (idempotente, construye + exporta FBX). |
| `Sandfall/` (~40 GB) | Regenerable | Re-rip del juego con FModel (ver paso 6 del Bootstrap). Selectivo: solo lo que `VivifyTemplate/` referencia. |
| `Aline_project.blend` (en `Sandfall/`) | **Lost (sin backup)** | Reconstruir: `scripts/blender/import_all_psa.py` (importa los 27 `.psa` como actions) + `scripts/blender/synthesize_root_motion.py` (axis remap del root motion para clips con desplazamiento). El estado del `.blend` es determinístico desde ese pipeline, así que en teoría reproducible — **pero no validado tras pérdida real**. **Pendiente:** decidir si versionar el `.blend` (excepción a `*.blend`) o aceptar el tiempo de reconstrucción. |
| `unity-mcp/` o `fmodel-mcp/` (fuera del repo) | Regenerable | `git clone` de los repos públicos (URLs en CLAUDE.md). |
| `ReMapper-master/`, `FModel.exe` (fuera del repo) | Regenerable | Re-descargar de sus respectivas fuentes. Sin uso activo todavía. |

**Decisiones pendientes** (flagged arriba):
- ¿Versionar `La-mandanga.ogg`? Pro: backup garantizado. Contra: 2.3 MB en cada checkout, y técnicamente IP del autor de la canción.
- ¿Versionar `Aline_project.blend`? Pro: backup determinístico. Contra: tamaño del `.blend` (probable 50-200 MB con todas las actions importadas), y en teoría reproducible desde scripts.

## Visión general

```
┌──────────────────────────────────────────────────────────────────────┐
│ FUENTE: Expedition 33 (Unreal Engine 5)                              │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  fmodel-mcp (CLI .NET sobre CUE4Parse + MCP server Python)
                                 GUI fallback: FModel.exe para browsing visual
┌──────────────────────────────────────────────────────────────────────┐
│ D:\vivify_repo\Output\Exports\Sandfall\Content\...                   │
│   PNGs, .pskx, .psa, .json (selectivos, no dump completo)            │
│   Scratch: lo confirmado se mueve a su destino                       │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  Texturas: directo a Unity. Meshes: por Sandfall/ + Blender
                              │
                              ▼  Blender 4.2 LTS + Blender MCP server
┌──────────────────────────────────────────────────────────────────────┐
│ .blend (rig + N actions importadas de .psa)                          │
│ scripts/blender/import_all_psa.py    (batch import .psa → actions)   │
│ scripts/blender/export_anims_fbx.py  (export armature + actions)     │
│ → Aline.fbx       (mesh + rig)                                       │
│ → Aline_Anims.fbx (rig only + animation takes)                       │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  Unity 2019.4.28f1 + VivifyTemplate
┌──────────────────────────────────────────────────────────────────────┐
│ VivifyTemplate/Assets/Aline/                                         │
│   Prefabs/aline.prefab          (Animator en el PREFAB ROOT)         │
│   Textures/                      (PNG de FModel)                     │
│   Materials/                     (M_Aline_Body_1/2, M_Aline_Black)   │
│   Shaders/Aline/Standard.shader  (unlit + alpha cutout + Cull Off)   │
│   Animations/Aline_AC.controller (state machine 26 estados)          │
│   Editor/PostBuildSyncCRCs.cs    (auto CRC sync)                     │
│   Editor/AlineAnimsImporter.cs   (preserveHierarchy=true + loopTime) │
│   Editor/BuildAlineAnimator.cs   (Tools menu: regenera AC)           │
│   Editor/InspectAlineClips.cs    (Tools menu: dump fcurves)          │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  F5 / Vivify > Build > Build Configuration Window
┌──────────────────────────────────────────────────────────────────────┐
│ beatsaber-map/  (junction a CustomWIPLevels/Test/)                   │
│   bundleWindows2021.vivify   (asset bundle, ~MB)                     │
│   bundleWindows2019.vivify   (opcional)                              │
│   bundleinfo.json            (CRCs + paths de assets)                │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  Sync auto de CRCs (Editor watcher)
┌──────────────────────────────────────────────────────────────────────┐
│ beatsaber-map/Info.dat                                               │
│   _customData._assetBundle._windows2021 = <CRC>                      │
│ beatsaber-map/ExpertPlusStandard.dat                                 │
│   _customEvents → InstantiatePrefab, AnimateTrack, DestroyPrefab,    │
│                   SetAnimatorProperty (Bool/Float/Int/Trigger)       │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  Beat Saber 1.34.2 + Vivify mod
┌──────────────────────────────────────────────────────────────────────┐
│ Runtime: Vivify carga el bundle, instancia el prefab, anima tracks   │
└──────────────────────────────────────────────────────────────────────┘
```

## Stack — versiones exactas

| Capa | Tool | Versión | Por qué esta exacta |
|---|---|---|---|
| Juego | Beat Saber | **1.34.2** (build 7115288407) | Última compatible con la cadena de mods de Aeroluna. |
| Mod core | Vivify | **1.0.7+1.34.2** | Estable sobre 1.34.2. |
| Mod core | Heck | **1.8.1+1.34.2** | Required por Vivify. |
| Mod core | CustomJSONData | **2.6.8+1.34.2** | Required por Heck. |
| Mod | Chroma | **2.9.22+1.34.2** | Iluminación custom. |
| Mod | NoodleExtensions | **1.7.20+1.34.2** | Movimiento custom de notas. |
| Editor | Unity | **2019.4.28f1** | Versión obligada por VivifyTemplate (Single Pass Instanced para Windows 2021). |
| 3D | Blender | **4.2 LTS** | Importar `.psa` (addon DarklightGames PSK/PSA), exportar FBX para Unity. |
| 3D — automation | Blender MCP | `uvx blender-mcp` (ahujasid/blender-mcp) | Permite a Claude Code ejecutar Python en Blender (inspección de rig, batch imports, export FBX). |
| Asset explorer (GUI) | FModel | (última) | Browsing visual de UE5 assets. Para automation no-GUI usamos fmodel-mcp. |
| Asset explorer (programático) | fmodel-mcp | propio (CUE4Parse 1.2.2 + .NET 9) | CLI + MCP server. Repo en `d:\vivify_repo\fmodel-mcp/`. Tools `mcp__fmodel__*` en Claude. |
| Map editor | ChroMapper | (última) | Editor visual del mapa. |
| Scripting | ReMapper | (master) | Generación programática de notas/eventos. **Aún sin usar.** |
| Unity automation | unity-mcp (fork local) | port a 2019.4 | Fork minimal en `d:\vivify_repo\unity-mcp/` enganchado vía `Packages/manifest.json`. Bridge stdio en port 6400. Ver [unity-mcp/README.md](../../unity-mcp/README.md). |

## Qué archivo vive dónde y por qué

### Dentro del repo

| Path | Qué | Versionado |
|---|---|---|
| `CLAUDE.md`, `docs/*.md`, `BS_Dependencies.txt` | Documentación | Sí |
| `.gitignore` | Reglas de versionado | Sí |
| `.claude/skills/*/SKILL.md` | Instrucciones para Claude Code | Sí |
| `scripts/snapshot-map.ps1` | Tool local para snapshots manuales | Sí |
| `scripts/sync-crcs.ps1` | CRC sync post-build (invocado por Editor watcher) | Sí |
| `scripts/blender/import_all_psa.py` | Batch import `.psa` → Blender actions | Sí |
| `scripts/blender/export_anims_fbx.py` | Export armature + actions a FBX para Unity | Sí |
| `docs/map-snapshots/.gitkeep` | Marcador de carpeta | Sí |
| `docs/map-snapshots/*/` | Snapshots de los `.dat` antes de cambios grandes | **No** (ignorado por carpeta) |
| `beatsaber-map/*.dat`, `bundleinfo.json` | Mapa: dificultades V3, manifest V2, BPM, info de bundle | **Sí** (desde 2026-05-04, commit `ef5bb7d`) |
| `beatsaber-map/*.vivify`, `*.ogg`, `*.bak`, `*.v2bak` | Bundles compilados, audio, backups manuales | **No** |
| `VivifyTemplate/Assets/**` (sin binarios) | Prefabs, scripts, materiales (`.mat`), shaders, `.meta` | Sí |
| `VivifyTemplate/Assets/**/*.png/.fbx/.psa/...` | Texturas, modelos 3D, animaciones binarias | **No** |
| `VivifyTemplate/Library/`, `Temp/`, `Logs/`, `UserSettings/` | Cache de Unity | **No** (cubierto por `VivifyTemplate/.gitignore`) |
| `VivifyTemplate/Packages/`, `ProjectSettings/` | Manifest de paquetes y settings | Sí |

### Fuera del repo (en `d:\vivify_repo\`)

| Path | Qué | Por qué fuera |
|---|---|---|
| `Sandfall/` | Dump de UE5 de Expedition 33 | ~40 GB. Tool de extracción, no parte del producto. |
| `ReMapper-master/` | Tool de scripting Deno/TS | Tiene su propio `.git`. Mejor accesible al lado del repo. |
| `FModel.exe` | Tool .exe ~47 MB | Binario, mejor fuera. GUI fallback. |
| `fmodel-mcp/` | Wrapper canónico programático sobre CUE4Parse (CLI .NET 9 + MCP server Python) | Repo propio (`luisep92/fmodel-mcp`). Bridge stdio MCP. Ver [fmodel-mcp/README.md](../../fmodel-mcp/README.md). |
| `Output/Exports/` | Scratch dir donde escriben FModel GUI y `mcp__fmodel__fmodel_export_*` | Tamaño variable. Lo confirmado se mueve a `my_vivify_template/Sandfall/` (meshes) o `VivifyTemplate/Assets/<area>/Textures/` (PNGs). |

### Junctions a la instalación de Beat Saber

Dos junctions de Windows (`mklink /J`) — el **link en sí** no se versiona (cada máquina lo crea), pero el **contenido del mapa** sí (los `.dat` y `bundleinfo.json` son fuente de verdad versionada en git desde commit `ef5bb7d`, 2026-05-04). Logs no se versionan.

#### `beatsaber-map/` → `CustomWIPLevels\Test\`

```cmd
mklink /J beatsaber-map "C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Beat Saber_Data\CustomWIPLevels\Test"
```

Permite leer `Info.dat`, `*Standard.dat`, `BPMInfo.dat`, `bundleinfo.json` y `bundle*.vivify` con un path relativo desde el repo. Tras crear el junction en una máquina nueva, los `.dat` versionados ya están en git — solo faltan los binarios pesados (`*.vivify` se generan con F5/Build, `*.ogg` se copia manual una vez).

#### `beatsaber-logs/` → `Beat Saber\Logs\`

```cmd
mklink /J beatsaber-logs "C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Logs"
```

Permite leer logs de IPA + Vivify desde el repo. Estructura:

- **`_latest.log`** — sesión actual sin comprimir. Es el que normalmente leemos.
- **`<timestamp>.log`** — sesión actual sin comprimir (mismo contenido que `_latest.log`).
- **`<timestamp>.log.gz`** — sesiones anteriores comprimidas con gzip. Para leer una concreta: `gzip -dc <archivo>` (Git Bash) o `Expand-Archive` desde PowerShell.

Útiles para diagnosticar:

- `[Vivify/InstantiatePrefab] Enabled` (positivo: el evento se procesa).
- `Could not find UnityEngine.GameObject` (path mal escrito en el evento).
- `[Vivify/AssetBundleManager] Checksum not defined` (CRCs desactualizados).
- `Asset bundle could not be loaded` (bundle ausente o corrupto).
- `[Vivify] Track does not exist` (orden temporal de eventos roto).

(Comando `cmd`, no PowerShell — `mklink` es interno de cmd.)

## Flujo de rebuild

Dos opciones equivalentes:

- **F5** — atajo. Equivale a "Build Working Version Uncompressed". Para iteración.
- **`Vivify > Build > Build Configuration Window`** — ventana con control sobre plataformas (Windows 2019 / Windows 2021 / Android 2021) y modo de compresión.

Salida: bundles + `bundleinfo.json` en `beatsaber-map/`.

### Uncompressed vs Compressed

| Modo | Cuándo | Notas |
|---|---|---|
| **Uncompressed** | Iteración, probar cambios | Default de F5. Bundle más grande, build casi instantáneo. **No distribuir.** |
| **Compressed** | Antes de publicar el mapa | Build mucho más lento. Obligatorio para release. |

### Plataformas

| Bundle | Para | Single Pass Mode |
|---|---|---|
| `_windows2019` | PC Beat Saber 1.29.1 | Single Pass |
| `_windows2021` | PC Beat Saber 1.34.2+ (este proyecto) | Single Pass Instanced |
| `_android2021` | Quest | Single Pass Instanced |

Por defecto solo construimos `_windows2021`. Si en algún momento queremos sacar versión Quest, marcar también `_android2021` en la Build Configuration y sincronizar su CRC.

## Pipeline de animaciones

Sub-flujo independiente del de prefab/material. Se ejecuta una vez para generar los AnimationClips, después solo se invocan vía evento `SetAnimatorProperty`.

```
.psa de FModel
   │  scripts/blender/import_all_psa.py  (vía Blender MCP o Scripting workspace)
   ▼
Blender actions en bpy.data.actions (372 bones matched, scale fcurves stripped)
   │  scripts/blender/export_anims_fbx.py
   │     - push actions a NLA tracks UNMUTED, strip name = "<armature>|<action>"
   │     - export armature only, takes via bake_anim_use_nla_strips=True
   ▼
Aline_Anims.fbx (~185 MB, gitignored, .meta sí versionado)
   │  Unity 2019.4 FBX importer + Editor/AlineAnimsImporter:
   │     - preserveHierarchy=true (mantiene SK_Curator_Aline como GO)
   │     - loopTime=true en idles canónicos
   ▼
26 AnimationClips como sub-assets, paths "SK_Curator_Aline/root/pelvis/..."
   │  Tools > Aline > Build Animator Controller (Editor/BuildAlineAnimator)
   ▼
Aline_AC.controller con 26 estados, 26 triggers (Any State → X), auto-return a Idle1
   │  Asignado al Animator component DEL PREFAB ROOT (no del child SK_Curator_Aline)
   ▼
Runtime: Vivify SetAnimatorProperty con id del prefab + trigger name
```

### Por qué el Animator vive en el prefab root + `preserveHierarchy=true`

El export armature-only de Blender colapsa el armature object como nodo raíz del FBX. Unity, además, colapsa por defecto nodos top-level con un solo hijo. Sin contramedida, las clip paths salen como `root/pelvis/...` sin prefijo `SK_Curator_Aline`. La preview del FBX inspector usa `Aline.fbx` como modelo (vía avatar source) cuya jerarquía sí preserva `SK_Curator_Aline` → mismatch → T-pose.

`preserveHierarchy=true` (set por `AlineAnimsImporter.OnPreprocessModel`) hace que Unity no colapse — `SK_Curator_Aline` sigue como GO en el FBX importado y todas las clip paths quedan prefijadas con `SK_Curator_Aline/...`. Con esas paths, el Animator puede vivir en el root del prefab y las paths matchean directamente.

Las scale curves que el FBX exporter mete por defecto en el armature object (path `""` original → `"SK_Curator_Aline"` con preserveHierarchy) caen en el GO `SK_Curator_Aline` (scale 1) → no-op. El root del prefab mantiene `localScale: 0.01` baked sin que las clips lo pisen. Decisión documentada en [DECISIONES.md#2026-05-01](DECISIONES.md).

### Naming convention de triggers

Los triggers en el AnimatorController tienen el nombre del clip menos el prefijo `Paintress_`:

| Clip name | Trigger name |
|---|---|
| `SK_Curator_Aline\|Paintress_Idle1` | `Idle1` |
| `SK_Curator_Aline\|Paintress_Skill3` | `Skill3` |
| `SK_Curator_Aline\|Paintress_Idle1_to_idle2_transition` | `Idle1_to_idle2_transition` |
| `SK_Curator_Aline\|Skill_Aline_P3_Skill1` | `Skill_Aline_P3_Skill1` |

Eso es lo que va en `properties[].id` del evento `SetAnimatorProperty` en el `.dat`.

### Skill `vivify-animations`

Guía operativa del pipeline: setup once-per-character paso a paso + tabla de tools + reglas no negociables + 6 gotchas documentados (NLA strips muted, addon PSA action linking, preserveHierarchy, no SetEditorCurves plural en 2019.4, Inspector loopTime bug, rest pose mismatch). Consultar antes de tocar nada del flujo.

---

## `bundleinfo.json` como fuente de verdad

Tras cada rebuild, `bundleinfo.json` queda con esta forma:

```json
{
  "materials": {
    "alineBody": {
      "path": "assets/aline/materials/aline_body.mat",
      "properties": { "_Color": { "type": { "Color": null }, "value": [...] } }
    }
  },
  "prefabs": {
    "alineMain": "assets/aline/prefabs/aline.prefab"
  },
  "bundleFiles": [
    "C:/.../bundleWindows2021.vivify"
  ],
  "bundleCRCs": {
    "_windows2021": 2051513366
  },
  "isCompressed": false
}
```

Dos usos:

1. **Validar paths antes de referenciarlos**: `prefabs.{name}` y `materials.{name}.path` listan los assets reales del bundle. Antes de añadir un `InstantiatePrefab` o un `SetMaterialProperty` al `.dat`, comprobar aquí que el path existe (lowercase, exacto).
2. **CRC sync**: copiar `bundleCRCs._windows2021` (y `_windows2019`/`_android2021` si construyes esas plataformas) a `Info.dat._customData._assetBundle`.

## CRC sync — formato en `Info.dat`

```json
"_customData": {
  "...": "...",
  "_assetBundle": {
    "_windows2021": <CRC_DE_BUNDLEINFO>
  }
}
```

Si los CRCs no matchean: error `[Vivify/AssetBundleManager] Checksum not defined` en el log de BS y el mapa no carga assets.

Bypass de iteración: lanzar BS con flag `-aerolunaisthebestmodder` (desactiva validación). **Quitar antes de publicar.**

## Mods — instalación manual

Mod Assistant a veces instala versiones obsoletas de CustomJSONData/Heck/Chroma/NoodleExtensions que rompen dependencias entre sí. Para este proyecto, los mods de Aeroluna se instalan a mano desde GitHub:

- https://github.com/Aeroluna/Heck/releases
- https://github.com/Aeroluna/Vivify/releases

Versiones exactas en [BS_Dependencies.txt](../BS_Dependencies.txt).
