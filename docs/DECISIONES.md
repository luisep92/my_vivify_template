# DECISIONES

Reglas fuertes del proyecto, una entrada por decisión. Solo el "qué" y un párrafo de "por qué". Si necesitas explorar la historia o lo que se descartó, mira `git log` y los hilos de chat.

---

### Tono: showcase cinemático, no scored

**Regla:** El mapa es un **showcase map** (experiencia cinemática). No optimizamos para scoring, leaderboards ni ranqueo. Densidad de notas, NJS y patrones quedan subordinados a la legibilidad de cada ataque telegrafiado de Aline. Los huecos largos entre ataques son aceptables. La música es ambiente, no driver rítmico.

**Por qué:** El combate de *Expedition 33* es por turnos orquestado, no continuo — traducirlo "como mapa BS al uso" pelearía con la naturaleza del juego origen. La mecánica de parry direccional de E33 encaja 1:1 con el cubo direccional de BS, así que cada habilidad de Aline pasa a ser un ataque telegrafiado con ventana de parry. Asumimos como coste que el mapa no será rejugable competitivamente; lo compensa el wow-factor, el valor demostrativo del repo (Vivify + Unity 2019.4 + pipeline animaciones) y el hecho de que el caso de uso (E33 boss fight en BS) es viral incluso para quien no conoce BS.

---

### Personaje: Aline (Curatress) de Expedition 33

**Regla:** El boss del mapa es Aline.

**Por qué:** Vista frontal cinemática nativa del juego (encaja con la cámara fija de BS), formato humanoide proporcionado, detalle visual suficiente para sostener un boss fight de 2-3 min.

---

### Map format V2

**Regla:** El mapa usa V2 (claves `_time`, `_type`, `_data`, `_customData`, etc. con underscore en root; sin underscore dentro de `_data`).

**Por qué:** Compatibilidad probada con Vivify 1.0.7+1.34.2 + cadena de mods de Aeroluna sobre BS 1.34.2. La docs de Heck es más extensa para V2.

---

### Scale 0.01 en el evento `InstantiatePrefab`

**Regla:** El evento `InstantiatePrefab` aplica `scale: [0.01, 0.01, 0.01]` (o el prefab tiene `localScale: 0.01` baked).

**Por qué:** Conversión Unreal cm → Unity m. Sin esto el modelo aparece 100x. La corrección vive en el evento (no en Blender) para mantener el modelo source limpio y la conversión explícita.

---

### Iluminación con Directional Lights dentro del prefab

**Regla:** Los prefabs Vivify que necesiten iluminación llevan sus propias luces como hijos. Hoy Aline va con shader unlit y no las usa, pero la regla aplica al añadir cualquier shader lit.

**Por qué:** Las luces vanilla del entorno de Beat Saber no afectan a objetos cargados por Vivify (otra layer/scene). La única forma de iluminar es luz que viaje dentro del bundle.

---

### DefaultEnvironment como base

**Regla:** El mapa usa `DefaultEnvironment`.

**Por qué:** Las luces vanilla son irrelevantes con Vivify, así que el environment elegido es el que mete menos ruido visual que pueda competir con Aline.

---

### Mods de Aeroluna instalados a mano

**Regla:** Vivify, Heck, CustomJSONData, Chroma y NoodleExtensions se instalan a mano desde los releases de GitHub de Aeroluna. Versiones exactas en [BS_Dependencies.txt](../BS_Dependencies.txt).

**Por qué:** Mod Assistant a veces sirve versiones obsoletas que rompen las dependencias entre estos cinco mods.

---

### Junction (`mklink /J`) para `beatsaber-map/` y `beatsaber-logs/`

**Regla:** Acceso al mapa real (`CustomWIPLevels/Test/`) y a los logs de BS desde el repo via Windows junctions. No se versionan.

**Por qué:** Junction = link real a nivel de filesystem (cualquier programa lo trata como carpeta normal), no requiere privilegios elevados como `mklink /D`, y un `.lnk` no funciona programáticamente.

---

### `ReMapper-master/` y `FModel.exe` fuera del repo

**Regla:** Las herramientas externas (ReMapper, FModel, dump de Sandfall) viven en `d:\vivify_repo\` (carpeta contenedora), no dentro del repo.

**Por qué:** Son tools/dumps externos, no parte del producto. ReMapper además trae su propio `.git` que rompería `git status` si quedara dentro.

---

### Animaciones que desplazan a Aline usan root motion (no AnimateTrack compensation)

**Regla:** Para clips donde Aline se desplaza horizontalmente (DashIn-Idle1, DashOut-Idle2, sus aliases, futuros mele), la posición del prefab cambia vía **root motion extraído del FBX** + `Apply Root Motion = ON` en el Animator. NO se gestiona la posición vía eventos `AnimateTrack` cross-clip en el `.dat`.

**Por qué:** los clips de la `.psa` están diseñados para encadenar via root delta — donde un clip acaba, el siguiente empieza (DashIn termina en posición melee, DashOut arranca desde melee). Compensar manualmente con `AnimateTrack` clip-a-clip se vuelve insostenible: cada nuevo clip suma un nivel más de coordinación cumulativa, y los teleports/blends entre eventos rompen la continuidad. Probado y descartado: `_offsetPosition` se ignora en tracks Vivify-prefab; `_position` con valores en world o lane units introduce teleports en cada AnimateTrack y exige cálculo manual de displacement por clip. El path correcto es preparar el FBX para que Unity extraiga root motion estándar y dejar que el Animator traslade el GO automáticamente.

**Coste asumido:** depende de que Blender exporte el motion en el bone raíz del rig (no distribuido en pelvis/spine). Si el `.psa` actual no lo expone, hay que re-exportar desde Blender. Detalle operativo en la skill `vivify-animations`.

---

### Animator en prefab root + `preserveHierarchy=true` en `Aline_Anims.fbx`

**Regla:** El componente `Animator` vive en el root del prefab `aline.prefab`. El importer de `Aline_Anims.fbx` tiene `preserveHierarchy=true` (forzado por `AlineAnimsImporter.OnPreprocessModel`).

**Por qué:** El export armature-only de Blender colapsa el armature object como nodo raíz del FBX y Unity colapsa además nodos top-level con un solo hijo. Sin `preserveHierarchy=true`, las clip paths salen sin prefijo `SK_Curator_Aline` y rompen la preview del FBX inspector (T-pose). Con la flag, las paths quedan prefijadas, el Animator puede vivir en el root y las scale curves del armature object caen en el GO `SK_Curator_Aline` (scale 1) → no-op. El root mantiene `localScale: 0.01`.

---

### Snapshots del mapa con `scripts/snapshot-map.ps1` (manual + auto)

**Regla:** Manual con label (`-Label X`, sin rotación) para momentos intencionales. Auto vía git pre-commit hook (`scripts/hooks/pre-commit`, ring buffer de 5, dedup por hash) para iteración. `core.hooksPath = scripts/hooks` activa el hook en clones nuevos.

**Por qué:** El mapa vive fuera del repo (junction) y no se versiona. Necesitamos puntos de retorno: los etiquetados son intencionales y no rotan; el ring buffer cubre "iteré durante horas y se rompió algo". Tolerante a junction missing (no rompe el commit).

---

### Fork minimal de unity-mcp (Unity 2019.4)

**Regla:** El `unity-mcp` que usamos es un fork minimal en `d:\vivify_repo\unity-mcp/` portado a Unity 2019.4, enganchado al proyecto vía `Packages/manifest.json` (path local). Bridge stdio en port 6400.

**Por qué:** El upstream `CoplayDev/unity-mcp` declara `unity: 2021.3+` y depende de C# 8/9 + UI Toolkit + APIs 2020+. Vivify recomienda 2019.4.28f1 oficialmente para max compat con BS 1.34.2. El fork strippa lo no esencial y reescribe lo justo a C# 7.3, manteniendo commits cherry-pickables por si en algún momento se propone PR upstream. Detalle en [unity-mcp/README.md](../../unity-mcp/README.md).
