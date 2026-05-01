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

### 1. Catálogo de familias de ataque + contratos — **hecho**

Cinco familias (A/B/D/E/F) + modificador C apilable formalizadas en [`families.md`](../.claude/skills/vivify-mapping/families.md): inputs, secuencia de eventos, encoding del parry, parámetros tunables, no-conflicto. Mapeo completo Animator→familia incluido. Visión de fase a fase en [PRODUCTO.md](PRODUCTO.md).

### 2. Sandbox de locomoción — validado modulo open issue

Implementado en `beatsaber-map/EasyStandard.dat` (difficulty Easy del mapa Test, registrada en `Info.dat`). Cadena de `SetAnimatorProperty` recorre idles, transiciones, dashes y stuns canónicos. Validado en BS: el AnimatorController encadena limpio cuando los triggers son discretos y no redundantes (ver patrón y gotchas en la skill [`vivify-animations`](../.claude/skills/vivify-animations/SKILL.md)).

**Open issue: snap-back de DashIn/DashOut.** Los clips con motion horizontal (`DashIn-Idle1`, `DashOut-Idle2`, `DefaultSlot`, `DefaultSlot (1)`) tienen el desplazamiento baked en bones internos (pelvis/spine) en vez de en root delta. Apply Root Motion ON no extrae nada porque el root bone del rig no tiene curve de posición. Resultado: la mesh se ve moverse durante el clip pero el GameObject no se traslada, y al terminar el clip los bones vuelven a neutral y la mesh "salta" al GO (origin).

Probado y descartado:
- `AnimateTrack` con `_offsetPosition` o `_position` para compensar — primero se ignora silenciosamente, segundo introduce teleports y exige cálculo manual de displacement por clip (insostenible al añadir clips intermedios).
- `Apply Root Motion = ON` por sí solo — no extrae si el FBX bakea motion en bones, no en root.
- `AlineAnimsImporter` con `lockRootPositionXZ = false` + `keepOriginalPositionXZ = false` por clip — configurado y aplicado, pero los `.psa` actuales no exponen delta extraíble.

### 2.5. Re-export `Aline_Anims.fbx` desde Blender con root motion canónico

**Bloqueante de Familia B (mele) y posiblemente E (multi-hit chain con desplazamiento).** Hasta que los clips expongan motion en el root bone del rig, no podemos prototipar Familia B con coreografía DashIn → idle/skill → DashOut sin el snap-back.

Path probable (a confirmar al tirar):
- Investigar si los `.psa` originales tienen root motion que se está distribuyendo en pelvis/spine al importar a Blender.
- Si sí: configurar el import o un script que lo "consolide" en el root bone antes del export FBX.
- Si no: los `.psa` ya vienen sin root motion (Unreal usa otro sistema), y hay que generar el motion del root sintéticamente desde la posición de pelvis o equivalente.

Fuera de scope de NEXT_STEPS: la solución concreta vive en `vivify-animations` cuando se ataque. Lo único que importa aquí es que es el siguiente paso bloqueante.

### 3. Prototipo de cada familia en sandbox

Una instancia funcional de cada familia en un mapa/dificultad sandbox antes de tocar el mapa real. Criterio de éxito por prototipo: animación + VFX + parry + cleanup, instanciable dos veces sin estado residual. Snapshot por prototipo (`-Label "proto-fam-X"`).

**Orden sugerido:**
1. **A con `Skill3`** (3 piedras gigantes, fase 1) — el más cómodo: VFX claro, N pequeño, encoding de notas obvio. Sirve también para validar que las animaciones de Aline encadenan limpio en BS.
2. **B con `DashIn-Idle1`** (mele estándar, fase 1) — valida la choreography de tres beats (DashIn + golpe + DashOut).
3. **F con `Skill2_Start/Loop/End`** (carga + explosión, fase 1) — valida secuencia multi-stage de triggers y timing largo.
4. **E con `Skill1`** (multi-hit chain, fase 1) — valida cadena de N parries sincronizados con N hits embebidos en el clip.
5. **D standalone** (shrinking indicator, sin source anim) — valida que el indicador construido en Unity transmite el feel de E33.
6. **B + modificador C con `Skill5`** — valida composición familia + modificador (Blit + SetMaterialProperty).

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
- **Upgrade unlit → lit/PBR para Aline**. Normal/ORM/Emissive ya descritos en `MI_Curator_Aline_*.json` del dump. Implica copiar PNGs adicionales, ampliar `Aline/Standard` (o crear `Aline/Lit`), decidir modelo de iluminación.
- **Polish de los slots negros** (BlackPart, BlackPart1, CuratorFace). Hoy negro plano; en Unreal usan fresnel + paint procedural. Recreables con un fresnel shader simple para BlackPart, y blend translucent de `Mask_Curator.png` + `T_Paint1.png` + `T_Aura.png` para `M_CuratorFace`.
- **Importar `palette.pskx` y `palette1.pskx`** del dump si se quiere que Aline sostenga sus paletas. Texturas y materiales ya preparados; falta la geometría (Blender → FBX → child del prefab).
