# ARQUITECTURA — Pipeline técnico

## Visión general

```
┌──────────────────────────────────────────────────────────────────────┐
│ FUENTE: Expedition 33 (Unreal Engine 5)                              │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼  FModel.exe (UE asset explorer)
┌──────────────────────────────────────────────────────────────────────┐
│ Sandfall/Content/Characters/Enemies/HumanEnnemies/Aline/             │
│   .uasset, .uexp, .ubulk, .psa (animaciones)                         │
│   ~40 GB de dump, fuera del repo                                     │
└──────────────────────────────────────────────────────────────────────┘
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
│   Prefabs/aline.prefab          (Animator en SK_Curator_Aline child) │
│   Textures/                      (PNG de FModel)                     │
│   Materials/                     (M_Aline_Body_1/2, M_Aline_Black)   │
│   Shaders/Aline/Standard.shader  (unlit + alpha cutout + Cull Off)   │
│   Animations/Aline_AC.controller (state machine 26 estados)          │
│   Editor/PostBuildSyncCRCs.cs    (auto CRC sync)                     │
│   Editor/AlineAnimsImporter.cs   (loopTime auto al importar FBX)     │
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
| Asset explorer | FModel | (última) | Extracción de UE5 assets. |
| Map editor | ChroMapper | (última) | Editor visual del mapa. |
| Scripting | ReMapper | (master) | Generación programática de notas/eventos. **Aún sin usar.** |
| Unity automation | unity-mcp (CoplayDev) | requiere Unity 2021.3+ | **No instalado** en este proyecto (incompat. 2019.4). Side-project: port mínimo a 2019.4 documentado en NEXT_STEPS. |

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
| `VivifyTemplate/Assets/**` (sin binarios) | Prefabs, scripts, materiales (`.mat`), shaders, `.meta` | Sí |
| `VivifyTemplate/Assets/**/*.png/.fbx/.psa/...` | Texturas, modelos 3D, animaciones binarias | **No** |
| `VivifyTemplate/Library/`, `Temp/`, `Logs/`, `UserSettings/` | Cache de Unity | **No** (cubierto por `VivifyTemplate/.gitignore`) |
| `VivifyTemplate/Packages/`, `ProjectSettings/` | Manifest de paquetes y settings | Sí |

### Fuera del repo (en `d:\vivify_repo\`)

| Path | Qué | Por qué fuera |
|---|---|---|
| `Sandfall/` | Dump de UE5 de Expedition 33 | ~40 GB. Tool de extracción, no parte del producto. |
| `ReMapper-master/` | Tool de scripting Deno/TS | Tiene su propio `.git`. Mejor accesible al lado del repo. |
| `FModel.exe` | Tool .exe ~47 MB | Binario, mejor fuera. |

### Junctions a la instalación de Beat Saber

Dos junctions de Windows (`mklink /J`) — ninguno versionado, hay que recrearlos a mano por máquina.

#### `beatsaber-map/` → `CustomWIPLevels\Test\`

```cmd
mklink /J beatsaber-map "C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Beat Saber_Data\CustomWIPLevels\Test"
```

Permite leer `Info.dat`, `ExpertPlusStandard.dat`, `BPMInfo.dat`, `bundleinfo.json` y `bundle*.vivify` con un path relativo desde el repo.

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

## Setup inicial Unity (one-time)

En un proyecto Vivify nuevo: `Vivify > Setup Project`. **Ya hecho** en este repo, queda apuntado por si se rehace desde cero.

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
Blender actions en bpy.data.actions (372 bones matched, scale fcurves no se importan)
   │  scripts/blender/export_anims_fbx.py
   │     - push actions a NLA tracks muted (force per-take baking)
   │     - export armature only, takes via bake_anim_use_nla_strips
   ▼
Aline_Anims.fbx (185 MB, gitignored, .meta sí versionado)
   │  Unity 2019.4 FBX importer + Editor/AlineAnimsImporter (loopTime auto en idles)
   ▼
26 AnimationClips como sub-assets (path "<root>", "root", "root/pelvis", ...)
   │  Tools > Aline > Build Animator Controller (Editor/BuildAlineAnimator)
   ▼
Aline_AC.controller con 26 estados, 26 triggers (Any State → X), auto-return a Idle1
   │  Asignado al Animator component DEL HIJO SK_Curator_Aline (no del prefab root)
   ▼
Runtime: Vivify SetAnimatorProperty con id del prefab + trigger name
```

### Por qué el Animator vive en `SK_Curator_Aline`, no en `aline` (root)

El prefab root `aline` tiene `localScale: 0.01` baked (conversión Unreal cm → Unity m, ver [DECISIONES.md](DECISIONES.md)). Los AnimationClips exportados desde Blender contienen curvas `m_LocalScale` en path `<root>` (la GameObject del Animator) por cómo bakea el FBX exporter — son curvas constantes 1.0 que no animan nada pero al sample sobreescribirían el localScale del GameObject del Animator. Si el Animator está en el root, el 0.01 se pisa con 1.0 → modelo 100x grande. Ponerlo en `SK_Curator_Aline` (que ya está a scale 1) hace que el sample sea no-op.

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

Documenta este pipeline incluyendo gotchas concretos (PSA addon no auto-linkea action, `bake_anim_use_all_actions` poco fiable bajo MCP context, scale curve scope, FBX rig settings, Generic vs Humanoid). Consultar antes de tocar nada del flujo.

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

## TextMeshPro caveat

Unity 2019.4.28f1 trae un TextMeshPro más nuevo que el que usa Beat Saber 1.29.1. Esto rompe alineamientos de texto en BS 1.29.1. Fix:

```
Window > Package Manager → eliminar TextMeshPro
+ → Add package from git URL → com.unity.textmeshpro@1.4.1
```

**No aplica a 1.34.2** (este proyecto). Apuntado por si en algún momento se quiere compatibilidad multi-versión.

## Mods — instalación manual

Mod Assistant a veces instala versiones obsoletas de CustomJSONData/Heck/Chroma/NoodleExtensions que rompen dependencias entre sí. Para este proyecto, los mods de Aeroluna se instalan a mano desde GitHub:

- https://github.com/Aeroluna/Heck/releases
- https://github.com/Aeroluna/Vivify/releases

Versiones exactas en [BS_Dependencies.txt](../BS_Dependencies.txt).
