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

### 2. Sandbox de locomoción — validación de transiciones encadenadas

Identificación de los 26 triggers ya hecha por inspección visual contra vídeo (mapeo completo en [`families.md`](../.claude/skills/vivify-mapping/families.md)). **Falta** validar que las animaciones, una vez disparadas vía eventos `SetAnimatorProperty` en Vivify, encadenan limpio en Beat Saber sin saltos, T-poses entre estados, o desincronizaciones.

**Por qué paso aparte y no mezclado con el primer prototipo:** si un ataque falla con VFX + parry + animación a la vez, no se sabe cuál sistema está roto. Validar locomoción en aislamiento **antes** acota el espacio de debug del primer ataque al VFX y al encoding del parry.

**Concreto a testear** (en un mapa/dificultad sandbox, sin notas ni VFX):

```
T+0   : Idle1 baseline (Aline en suelo)
T+3   : DashIn-Idle1   (aproximación)
T+6   : DashOut-Idle2  (retirada)
T+9   : Idle1_to_idle2_transition  (sube)
T+12  : Idle2          (flotando)
T+15  : Idle2_Stun     (encorvada adelante)
T+18  : Idle_Countered (encorvada atrás)
T+21  : Idle2_to_Idle3_transition  (cae)
T+24  : Idle3          (derrotada)
```

Opcional: añadir un par de skill triggers ligeros (`Skill1`, `Skill7`) sin VFX ni notas para confirmar que las skill-anims también dispatchan limpio.

**Output esperado:** vídeo o nota en `docs/my-notes.md` confirmando que las transiciones se ven correctas, o lista de las que necesitan ajuste antes de seguir.

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
