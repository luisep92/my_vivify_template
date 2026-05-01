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

### 1. Canción definitiva

Decidir pieza concreta del OST de Expedition 33. Importar `.ogg` al `beatsaber-map/`, ajustar BPM y duración. Anotar en `DECISIONES.md`.

### 2. Wireado narrativo del state machine

El pipeline de animación funciona; queda el contenido. Definir qué skill dispara qué transición en cada fase del boss fight (ver [PRODUCTO.md](PRODUCTO.md)). Añadir eventos `SetAnimatorProperty` al `.dat` con los triggers correspondientes (`Skill1`, `Skill2_Loop`, etc.). Snapshot del mapa antes de bloque grande de events.

### 3. Setup de ReMapper

Levantar Deno + primer script en `ReMapper-master/`. Output target: directo a `beatsaber-map/ExpertPlusStandard.dat` o staging intermedio. Rellenar la skill `remapper-scripting` durante este paso.

### 4. Diseño narrativo del boss fight

Traducir la estructura por fases de [PRODUCTO.md](PRODUCTO.md) en eventos concretos: transiciones, animaciones por fase, patrones de notas que respondan a cada fase.

---

## Side-projects

### Port mínimo de unity-mcp a Unity 2019.4 — DONE

Fork operativo en `d:\vivify_repo\unity-mcp/` (`luisep92/unity_vivify_mcp`), enganchado al proyecto Aline. Pendiente: cuando lleve unas sesiones rodando, evaluar PR a upstream `CoplayDev/unity-mcp`. Los commits están organizados con un cambio conceptual cada uno y mensajes en inglés, pensados para cherry-pick limpio. Detalle en [unity-mcp/README.md](../../unity-mcp/README.md).

---

## Diferido post-torneo

Limpieza para cuando el mapa esté entregado:

- **Rename `my_vivify_template/` → `aline-boss-fight/`**. Procedimiento: cerrar VSCode, `cd d:\vivify_repo && ren my_vivify_template aline-boss-fight`, reabrir VSCode. Junctions y `.git` viajan con la carpeta.
- **Traducir docs/skills al inglés** si en algún momento se publica el repo a la comunidad de Vivify (internacional).
- **Cambiar `origin/main`** del template upstream (`Swifter1243/VivifyTemplate`) al remote propio cuando se monte en GitHub.
- **Upgrade unlit → lit/PBR para Aline**. Normal/ORM/Emissive ya descritos en `MI_Curator_Aline_*.json` del dump. Implica copiar PNGs adicionales, ampliar `Aline/Standard` (o crear `Aline/Lit`), decidir modelo de iluminación.
- **Polish de los slots negros** (BlackPart, BlackPart1, CuratorFace). Hoy negro plano; en Unreal usan fresnel + paint procedural. Recreables con un fresnel shader simple para BlackPart, y blend translucent de `Mask_Curator.png` + `T_Paint1.png` + `T_Aura.png` para `M_CuratorFace`.
- **Importar `palette.pskx` y `palette1.pskx`** del dump si se quiere que Aline sostenga sus paletas. Texturas y materiales ya preparados; falta la geometría (Blender → FBX → child del prefab).
