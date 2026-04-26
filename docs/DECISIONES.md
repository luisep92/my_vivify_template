# DECISIONES

Decisiones grandes con su porqué. Formato ADR ligero.

---

### Pre-2026-04-26 — Aline (Curatress) en lugar de Dualliste

**Contexto:** Necesitábamos elegir un personaje de *Expedition 33* como boss del mapa. Candidatos principales: Aline (Curatress) y Dualliste.

**Decisión:** Aline.

**Por qué:**
- Vista frontal cinemática nativa del juego — encaja con la cámara de Beat Saber (jugador frente al boss).
- Formato humanoide proporcionado, fácil de escalar para el espacio jugable.
- Modelo con detalle visual suficiente para sostener un boss fight de 2-3 minutos.

**Alternativas descartadas:** Dualliste — más complejo de adaptar a una única cámara frontal, formato menos "humanoide clásico".

---

### Pre-2026-04-26 — Map format V2

**Contexto:** Vivify soporta V2 (legacy, con underscores) y V3 (sin underscores). Hay que elegir uno y mantenerlo.

**Decisión:** V2.

**Por qué:**
- Compatibilidad probada con Vivify 1.0.7+1.34.2 y la cadena de mods de Aeroluna sobre BS 1.34.2.
- Documentación de Heck más extensa para V2.
- Menos sorpresas con eventos custom (`InstantiatePrefab`, `AnimateTrack`...) en V2.

**Alternativas descartadas:** V3 — habría requerido validar compatibilidad evento a evento, sin ganancia clara para el alcance del proyecto.

---

### Pre-2026-04-26 — Scale 0.01 en el prefab Aline

**Contexto:** Los assets vienen de Unreal Engine 5, donde la unidad nativa es el centímetro. Unity usa metros.

**Decisión:** Aplicar `scale: [0.01, 0.01, 0.01]` al evento `InstantiatePrefab` (o equivalente en el prefab).

**Por qué:** Conversión directa cm → m. Sin esto, Aline aparecería 100 veces más grande que el espacio jugable.

**Alternativas descartadas:** Reescalar el mesh en Blender y exportar a 1:1. Descartado para mantener el modelo original limpio y hacer la corrección de escala explícita en el evento (más fácil de revisar).

---

### Pre-2026-04-26 — Iluminación con Directional Lights dentro del prefab

**Contexto:** Por defecto, Aline aparecía completamente negra/oscura en BS aunque el escenario tuviera luces vanilla.

**Decisión:** Añadir Directional Lights como hijos del propio prefab Aline en Unity.

**Por qué:** Las luces vanilla del entorno de Beat Saber NO afectan a objetos cargados por Vivify (están en otra layer / scene). La única forma de iluminar el prefab es con luces que viajan dentro del propio bundle.

**Alternativas descartadas:** Confiar en luces del DefaultEnvironment — comprobado que no afecta.

---

### Pre-2026-04-26 — DefaultEnvironment como base

**Contexto:** Beat Saber tiene varios entornos. Hay que elegir uno como base del mapa.

**Decisión:** DefaultEnvironment.

**Por qué:** Las luces vanilla son irrelevantes con Vivify (decisión anterior), así que da igual el entorno desde un punto de vista de iluminación. DefaultEnvironment minimiza geometría visible que pudiera competir con Aline.

**Alternativas descartadas:** Environments con identidad propia (Origins, Crab Rave...) — meten ruido visual que distrae del prefab.

---

### Pre-2026-04-26 — Mods de Aeroluna instalados manualmente

**Contexto:** Mod Assistant es la forma "oficial" de instalar mods de Beat Saber.

**Decisión:** Para este proyecto, instalar Vivify, Heck, CustomJSONData, Chroma y NoodleExtensions a mano desde los releases de GitHub.

**Por qué:** Mod Assistant a veces sirve versiones obsoletas que rompen las dependencias entre estos cinco mods. Aeroluna mantiene los releases en GitHub con versiones consistentes etiquetadas (`+1.34.2`).

**Alternativas descartadas:** Mod Assistant — descartado tras incidentes de versiones cruzadas.

---

### 2026-04-26 — Junction (`mklink /J`) en lugar de symlink o shortcut

**Contexto:** Necesitábamos acceder al mapa real (en `C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Beat Saber_Data\CustomWIPLevels\Test\`) desde el repo, sin copiar a mano.

**Decisión:** Junction de Windows con `mklink /J beatsaber-map "..."`. No se versiona.

**Por qué:**
- Junction = link real a nivel de filesystem. Cualquier programa (PowerShell, scripts, herramientas de lectura) lo trata como una carpeta normal.
- Symlink (`mklink /D`) requiere privilegios elevados o dev mode en Windows. Junction no.
- Shortcut `.lnk` es solo del shell de Windows, los programas no lo siguen.

**Alternativas descartadas:**
- `.lnk` (lo que había) — no funciona programáticamente.
- Path absoluto hardcodeado en scripts — frágil entre máquinas, ensucia los .md.
- Submodule de git apuntando al mapa — el mapa es un artefacto, no código fuente.

---

### 2026-04-26 — `ReMapper-master/` fuera del repo

**Contexto:** ReMapper viene como repo Git propio (clonado desde GitHub). Si lo dejamos dentro del repo principal, su `.git` anidado da warnings y complica el `git status`.

**Decisión:** Mover `ReMapper-master/` a `d:\vivify_repo\` (carpeta contenedora, fuera del repo). Crear skill `remapper-scripting` para invocarlo cuando empecemos a usarlo.

**Por qué:**
- ReMapper es una herramienta externa, no parte del producto. Cabe junto al repo, no dentro.
- Submodule de Git añadiría fricción a clones y workflow para un proyecto personal con un solo desarrollador.
- Se mantiene a un path corto y predecible para que la skill futura lo invoque.

**Alternativas descartadas:**
- Git submodule — overkill para este caso.
- Dejar dentro con `.gitignore` — el `.git` anidado seguiría dando warnings de Git.

---

### 2026-04-26 — Animator component en `SK_Curator_Aline`, no en el root del prefab

**Contexto:** El prefab `aline` tiene `localScale: 0.01` baked en su Transform raíz (conversión Unreal cm → Unity m). Las AnimationClips exportadas desde Blender contienen curvas `m_LocalScale` en path `<root>` (la GameObject del Animator) — son curvas constantes 1.0 que el bake del FBX exporter mete por defecto aunque la source action no tenga fcurves de scale. Cuando el Animator samplea, escribe scale=1 al GameObject del Animator, pisando el 0.01 → modelo 100x grande.

**Decisión:** El componente `Animator` vive en el GameObject hijo `SK_Curator_Aline` (el armature raíz, scale 1), no en el prefab root `aline`.

**Por qué:**
- El sample del scale curve a path `<root>` se aplica al GameObject del Animator. Si ese GameObject está a scale 1, el sample (que es 1) es no-op. Si está a scale 0.01, el sample lo pisa con 1 → bug.
- Stripping de las scale curves en post-import desde Unity es lento (~10 min de hang con `AnimationUtility.SetEditorCurve(..., null)` × 34944 calls). El export limpio desde Blender no es trivial (`bake_anim` siempre baja scale, no hay flag para skipearlo).
- La separación es además semánticamente correcta: el prefab root maneja la escala extrínseca (cm→m), el armature maneja la animación. Cada cosa en su sitio.

**Alternativas descartadas:**
- **Animator en `aline` root + AssetPostprocessor strippeando curves**: lento e impone reimport caro cada vez que el FBX cambia.
- **Re-exportar desde Blender sin scale curves**: Blender's `bake_anim=True` siempre samplea scale; no hay flag. Modificar el exporter es fragil.
- **Cambiar el `localScale` del prefab a 1 y mover el 0.01 al evento `InstantiatePrefab`**: el evento ya aplica `scale: [0.01, ...]`; con prefab a 1 daría 0.01 final igual, pero rompe consistencia con el committed state previo y obliga a tocar el `.dat`. Más cambios, menos clean.

---

### 2026-04-26 — Snapshots del mapa con `scripts/snapshot-map.ps1` (manual + auto)

**Contexto:** Los `.dat` del mapa viven fuera del repo (en el junction). Queremos versionar momentos clave sin copiarlos a mano y sin meter el `.ogg` ni los bundles.

**Decisión:** Script PowerShell con dos modos:

- **`-Label X`** (manual): snapshot con etiqueta intencional. Sin rotación. Persiste hasta que el usuario lo borra.
- **`-Auto`** (automático): ring buffer de 5 últimos. Dedup por hash SHA-256 — si los `.dat` no han cambiado desde el último auto-snapshot, NO crea uno nuevo.

Disparado por:

- **Manual:** el usuario invoca el script antes de cambios grandes.
- **Auto:** un git **pre-commit hook** en `scripts/hooks/pre-commit` que llama al script en modo `-Auto`. Configurado en el repo con `git config core.hooksPath scripts/hooks`.

**Por qué este diseño:**
- Manual con label sirve para marcar momentos ("before-textures", "v1-jugable") — esos NO se rotan automáticamente porque son intencionales.
- Auto cubre el riesgo de "iteré durante horas y se me ha roto algo, dame el último estado bueno" sin acumular ruido — solo guarda los últimos 5 estados realmente distintos del mapa.
- Pre-commit hook en lugar de file watcher: el usuario itera localmente y commitea cuando avanza algo. El hook captura ese momento sin requerir un proceso en background.
- Dedup por hash: si commiteo solo cambios a docs/ y no toqué el mapa, el hook no crea un duplicado idéntico al anterior.
- Tolerante a fallos: si `beatsaber-map/` no existe (otra máquina sin Beat Saber), el script termina con exit 0 silencioso. El commit no se rompe.
- `core.hooksPath` apuntando a `scripts/hooks`: el hook se versiona con el repo. En un clone nuevo, una sola línea (`git config core.hooksPath scripts/hooks`) lo activa.

**Alternativas descartadas:**
- File watcher (PowerShell con `FileSystemWatcher` vigilando el junction) — más fino pero requiere mantener un proceso en background. Innecesario si los commits ya marcan los momentos importantes.
- Scheduled task cada N minutos — ruidoso, snapshots aunque no haya tocado nada.
- Solo modo manual sin auto — perfecto para momentos intencionales pero deja huecos en iteración pura.
- Versionar el junction completo — pesa MB y no es portable entre máquinas.
