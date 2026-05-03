# Checkpoint Skill4 — 2026-05-04

Documento auto-contenido para retomar el polish del Skill4 attack tras compact. Lee primero esto, luego ya sabes dónde estás.

## Estado actual del .dat

`beatsaber-map/NormalStandard.dat` (V3) tiene el ataque **Skill4 v3 (Plan A activo)**:
- Boilerplate beat 0: skybox, env disable, rockPlatform, alineMain.
- Beat 8: `SetAnimatorProperty Skill4` trigger sobre `alineMain`.
- 7 esferas Vivify (`TelegraphSphere.prefab` scale 1.5) spawnean en arc semicircular sobre Aline:
  - Centro arc: `(0, 3, 8)` world meters.
  - Radio: 3m.
  - Beats spawn: 14.67, 16.00, 17.34, 18.67, 20.00, 21.34, 22.67 (step 1.333 beats = 0.8s).
- Beats launch: 24.67, 26.34, 28.00, 29.67, 31.34, 33.00, 34.67 (step 1.667 beats = 1s).
- A cada launch beat: `AnimateTrack position` mueve la esfera de su posición arc → `(0, 1, 0.5)` world (jugador hand-reach centrado), duración 2 beats = 1.2s.
- 7 notas BS standard, `_time = launch + 2 beats`. Invisibles via `dissolve = [[0,0],[0,1]]`. Sin `track` (no comparten con la esfera). `lineIndex=1, lineLayer=1` (cerca del centro hand-reach).
- 7 `DestroyObject` events a `cut_beat + 0.1` para limpiar las esferas.

## Última iteración pendiente de validación

**No validado todavía en BS:** se acaba de corregir un bug donde `DestroyPrefab` (event inexistente) no destruía las esferas — se acumulaban encima del jugador. **Fix aplicado**: usar `DestroyObject` (nombre correcto del Vivify event). Pendiente de un launch en BS para confirmar:

1. **Esferas despawn** a su `cut_beat + 0.1`.
2. **Cut detection funciona**: la nota invisible está cerca del jugador cuando llega la esfera. Player slash a la zona → BS registra cut → score popup / chunk del cubo desintegrándose.
3. Si **no se registra cut**, la nota completamente invisible puede ser non-interactable. Fix probable: dissolve curve que la haga visible muy levemente al final (e.g. `[[0,0],[0,0.95],[0.1,1.0]]`).

## Decisión arquitectural pendiente

User propuso un **Plan F** alternativo durante la sesión, no implementado aún. Decisión a tomar antes de seguir polishing:

### Plan A (lo que está activo)
- Esfera = visual completo del proyectil. Hace dos roles: telegraph (estática en arc) + proyectil (vuela al jugador).
- Cubo BS = hitbox invisible. Standard jump-in pero dissolve permanente. _time alineado con cut_beat para cut detection por timing.
- Match esfera↔nota es **temporal** (mismo cut_beat), no espacial (esfera a `(0,1,0.5)`, nota a `(-0.3, 1.0, 0)` lane default). Cut detection funciona porque saber sweep cubre el delta de 30cm.
- **Pro:** simple. Una sola arquitectura, sin `definitePosition`, sin coord conversion en notas, sin custom `coordinates`.
- **Con:** "magia oculta" — el cube técnicamente está en otro sitio que el visual. Funcional pero no 1:1.

### Plan F (propuesto, no implementado)
- Esfera = **solo telegraph**. Despawn al launch beat (no AnimateTrack).
- Cubo BS = el **proyectil real**. Visible desde launch.
- Lane-first thinking: **diseñador piensa en lane units** (NE acepta `coordinates: [x, y]` con floats, no limitado a 0-3).
  - Define posiciones telegraph en lanes (e.g. semicircle arriba de Aline en `(2.5, 4)`, `(0, 5)`, ... lanes).
  - Sphere world position = `lane × 0.6 + offset` (la conversión calibrada: `LANE_X_ZERO_WORLD=-0.9, LANE_Y_ZERO_WORLD=1.0`).
  - Note `coordinates` = mismas lanes → su default world position ≈ telegraph world position.
  - Note `definitePosition` path: hold en telegraph position hasta launch_norm → descend a jugador.
  - Note `dissolve`: invisible 0→launch_norm, visible launch_norm→1 (snap visible al desaparecer la sphere).
  - `noteJumpStartBeatOffset` para que el HJD no tenga al cube spawning a 24m de far Z (la cosa "vienen del fondo del mundo").
- **AT launch beat**: sphere despawn + cube se hace visible **EN MISMA POSICIÓN** → vuela al jugador (definitePosition).
- **Pro:** match esfera↔cube es espacial 1:1 por construcción (lane coords compartidas). Cube ES el proyectil. Cleaner mental model.
- **Con:** rehacer el helper. Más complejo (definitePosition + dissolve + sphere despawn separado).

### Mi voto
**Plan A si solo es Skill4** (ya casi funciona, faltan validation + un par de polish). **Plan F si miramos a Phase 1 entera**, porque el patrón se reusa en 5 familias. Probablemente F a futuro pero confirmar Plan A primero (validar destroyObject + cut detection) para tener algo funcionando como baseline.

## Lecciones aprendidas en esta serie (qué NO repetir)

1. **CustomNotes mod intercepta `dissolve`** — notas siempre visibles en Vivify si el player tiene CustomNotes activo. Documentado en `Info.dat._customData._warnings` por dificultad. Para testing, user debe desactivarlo.
2. **Vivify event para destruir prefab es `DestroyObject`, NO `DestroyPrefab`**. El segundo no existe; BS lo ignora silenciosamente. **No se puede confiar en doc de los nombres — verificar contra `docs/heckdocs-main/docs/vivify/events.md`**.
3. **NE V2 dissolve tiene drift contra docs (V3)**. Migración a V3 hecha (commit `aa23eee`). Memory `project_v3_migration` con cheatsheet V2→V3.
4. **PowerShell ConvertTo-Json serializa `@()` (empty array) como `{}` (objeto)** — BS rechaza el archivo. Fix: usar `,@()` (comma-prefix) para forzar array vacío. También strip BOM con `[System.Text.UTF8Encoding]::new($false)` porque BS no parsea con BOM.
5. **Sintaxis V3 tiene un schema completo requerido**: `version, bpmEvents, rotationEvents, colorNotes, bombNotes, obstacles, sliders, burstSliders, waypoints, basicBeatmapEvents, colorBoostBeatmapEvents, lightColorEventBoxGroups, lightRotationEventBoxGroups, lightTranslationEventBoxGroups, basicEventTypesWithKeywords:{d:[]}, useNormalEventsAsCompatibleEvents:false, customData:{}`. Si falta, BS no parsea el .dat (dificultad no carga).
6. **Coords lane vs world**: NE definitePosition usa lane units (0.6m), Vivify InstantiatePrefab usa world meters. Calibración empírica (validada con calibration test de 5 marcadores): `LANE_X_ZERO_WORLD=-0.9, LANE_Y_ZERO_WORLD=1.0`. La doc Beatwalls sugiere X=0=center pero empíricamente necesita el offset. Usar la calibración, no la doc.
7. **AnimateTrack `position` no es uniforme entre tipos**: world meters en Vivify prefabs, offset relativo a default lane en NE notes. NO se puede compartir track para movimiento de ambos al mismo position.
8. **`noteJumpStartBeatOffset`**: positivo = HJD más largo (jump-in más lento/largo), negativo = más corto. Fácil confundir el signo.
9. **PowerShell `$variable:`** se interpreta como drive notation. Usar `${variable}:` cuando hay colon después.
10. **Execution policy**: scripts no se pueden dot-source si la policy lo bloquea. Workaround: `Get-Content $script -Raw | Invoke-Expression` o ejecutar con `powershell.exe -ExecutionPolicy Bypass -File ... `.

## Archivos relevantes

- `scripts/familyA-builder.ps1` — helper Plan A activo. Funciones: `New-FamilyAAttack`, `New-FamilyAProjectile`, `Get-SemicircleArc`. Convención metros para todo (sin lane units).
- `scripts/build-skill4.ps1` — script ejecutable que reconstruye el Skill4. Constantes editables al top.
- `scripts/build-calibration.ps1` — test de 5 marcadores que validó la conversión metros↔lane units. Backup automático del NormalStandard a `.bak` para restaurar tras tests.
- `beatsaber-map/NormalStandard.dat` — playground de ataques en V3. Contiene Skill4 actualmente.
- `beatsaber-map/EasyStandard.dat` — sandbox de locomoción (animator triggers), sin gameplay.
- `beatsaber-map/Info.dat` — manifest V2, registra Easy/Normal/ExpertPlus. Contiene `_customData._warnings` por difficulty avisando del CustomNotes.
- `VivifyTemplate/Assets/Aline/Prefabs/projectiles/TelegraphSphere.prefab` — placeholder white semi-transparent sphere scale 0.4 (en build se escala a 1.5 vía Vivify).
- `.claude/skills/vivify-mapping/families.md` — sección "Familia A" actualizada con referencia a los scripts.

## Memory relevante (`C:\Users\Luis\.claude\projects\d--vivify-repo\memory\`)

- `feedback_skill4_projectile_pattern.md` — receta del patrón viejo (V2, definitePosition + dissolve). **Outdated** por el pivot a Plan A. Re-escribir cuando cerremos qué Plan queda.
- `project_v3_migration.md` — V3 cheatsheet completo (V2→V3 mapping). Sigue válido.
- `feedback_v2_v3_syntax.md` — drift de docs entre V2 y V3.

## Si retomas con Plan A (validar baseline)

1. User abre BS, dificultad Normal (con CustomNotes off).
2. Verifica:
   - Esferas spawnean en arc ✓ (ya validado).
   - Esferas viajan al jugador a launch beats ✓ (ya validado).
   - **Esferas despawn correctamente** (acaba de fix, no validado).
   - **Cuts se registran al pasar saber por la esfera al llegar al jugador** (no validado).
3. Si cut no se registra: cambiar dissolve a `[[0,0],[0,0.95],[0.1,1.0]]` (visible 5% del tiempo final, por si dissolve=0 throughout es non-interactable).
4. Si todo OK: commit + a polish (mejor mesh para el proyectil, partículas en spawn/launch, validación VR).

## Si retomas con Plan F (refactor lane-first)

1. Reescribir `familyA-builder.ps1`:
   - Funciones internas en lane units (no metros).
   - Designer pasa positions en lanes a la API.
   - Convertir a world meters via `LANE_X_ZERO_WORLD/LU` para Vivify InstantiatePrefab.
   - Notas con `coordinates: [lane_x, lane_y]` (floats), `definitePosition` path en lane units (sin conversion porque ya estamos en lane units).
   - Sphere despawn al launch beat (no AnimateTrack en sphere).
   - Cube tiene dissolve invisible→visible al launch_norm.
   - Cube tiene `noteJumpStartBeatOffset` que reduzca HJD a algo razonable (e.g. `+3` para HJD=1 beat).
2. Reescribir `build-skill4.ps1` con el helper nuevo.
3. Validar en BS.

## Próximo paso una vez Skill4 cierra

Polish del attack:
- Decidir visual del proyectil: ¿esfera blanca actual? ¿spike negro inky? ¿paint stroke? ¿swap del cube via `AssignObjectPrefab`?
- Partículas en spawn (telegraph aparece) y/o launch (telegraph dispara).
- Validación VR (FPFC engaña sobre profundidad y timing).

Después: aplicar el helper para Skill3 (mismo patrón A, N=3, NJS más baja, scale grande). Y luego B/E/F que son más distintas.

## Estado de Phase 1 (NEXT_STEPS subpaso 4)

| Skill | Familia | Estado |
|---|---|---|
| Skill4 | A | **En progreso (este checkpoint)** |
| Skill3 | A | Pendiente. Reusar helper. |
| DashIn-Idle1 | B | Pendiente. Caso aparte (mele, sin proyectil). |
| Skill2 | F | Pendiente. Multi-stage. |
| Skill1 | E | Pendiente. Multi-hit chain. |
| D standalone | D | Pendiente. Sin source anim, indicador custom. |
| Skill5 | B+C | Pendiente. Composición. |
