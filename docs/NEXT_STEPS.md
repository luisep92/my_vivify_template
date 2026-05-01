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

> Pivot: con la decisión de **showcase map** ([DECISIONES.md](DECISIONES.md)), el orden cambia. La canción y el state machine narrativo dependen de tener primero los **sistemas de ataque** definidos como contratos reutilizables. Componer fases sobre sistemas inestables es la receta del embolado.

### 1. Catálogo de familias de ataque + contratos

Las cuatro familias iniciales (Ranged Sequence, Melee Slash, Distortion Window, Shrinking Indicator) están descritas a alto nivel en [PRODUCTO.md](PRODUCTO.md). Falta formalizarlas como **contratos** en la skill `vivify-mapping/`: inputs requeridos, secuencia de eventos `.dat`, encoding del parry, parámetros tunables, reglas de no-conflicto entre tracks.

### 2. Sandbox de locomoción + identificación de animaciones

**Antes de prototipar ataques.** El Animator tiene 26 triggers (`Skill1`-`Skill12`, idles, transiciones, `Skill_Aline_P3_*`) y visualmente **no sabemos cuál es cuál**. Construir un sandbox que dispare cada trigger secuencialmente con un label en pantalla (o, más simple, dispararlos a mano y anotar en vídeo) para:

- Identificar qué clip es cada `Skill_X` (cuál es ranged, cuál melee, cuál distortion-window).
- Validar que las transiciones entre idles encadenan limpio (ver a Aline flotar / aterrizar / mirar / volver a idle, sin saltos bruscos).
- Probar combinaciones (`Idle1` → `DashIn-Idle1` → `Skill1` → vuelta a `Idle1`).
- Actualizar [`families.md`](../.claude/skills/vivify-mapping/families.md) reemplazando los `TBD` de inputs por nombres concretos.

Output: tabla de "trigger → clip identificado" en `families.md`, y un sandbox map reutilizable (probablemente la propia intro del boss fight nace de aquí).

### 3. Prototipo de cada familia en sandbox

Con los triggers ya identificados (paso 2). Una instancia funcional de cada familia en un mapa/dificultad sandbox antes de tocar el mapa real. Criterio de éxito por prototipo: animación + VFX + parry + cleanup, instanciable dos veces sin estado residual. Snapshot por prototipo (`-Label "proto-fam-X"`).

**Orden sugerido de prototipado:** Familia A primero (ranged, más cómoda — VFX simple, encoding de notas claro). Después B/C/D según interesen.

### 4. Canción definitiva

Cuando los 4 contratos estén probados. Decidir pieza concreta del OST de E33 con criterio: duración suficiente para 5 fases, clima coherente con showcase. Importar `.ogg` al `beatsaber-map/`, ajustar BPM y duración. Anotar en `DECISIONES.md`.

### 5. Wireado narrativo del state machine

Depende del catálogo de familias (paso 1) y de la identificación de triggers (paso 2). Definir qué familia (y qué `Skill_X` del Animator) dispara cada fase del boss fight. Componer la línea de tiempo del mapa instanciando templates de la skill, no escribiendo eventos a mano cada vez. Snapshot del mapa antes de bloque grande de events.

### 6. Setup de ReMapper

Levantar Deno + primer script en `ReMapper-master/`. Probable pero no obligatorio: si la composición se beneficia de scriptear instanciaciones de familias, ReMapper es el sitio. Output target: directo a `beatsaber-map/ExpertPlusStandard.dat` o staging intermedio. Rellenar la skill `remapper-scripting` durante este paso.

### 7. Diseño narrativo y pulido

Traducir la estructura por fases de [PRODUCTO.md](PRODUCTO.md) en secuencia concreta de ataques. Iteración de legibilidad con feedback externo (VR + ojos de tercero).

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
