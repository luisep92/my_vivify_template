---
name: vivify-materials
description: Use when creating or modifying materials/shaders for prefabs that ship in a Vivify bundle (characters, props, environments). Trigger when user mentions 'crear material', 'asignar material', 'shader Vivify', 'texturizar', 'aplicar texturas', 'magenta en BS', 'missing material', or after importing a model from FModel that needs materials. Covers the unlit cutout recipe, FModel JSON-to-Unity material mapping, and common errors.
---

# Vivify Materials Workflow

Cómo construir materiales para prefabs que viven dentro de un bundle Vivify. Los shaders por defecto de Unity (Standard, URP) no compilan en bundles de Vivify (Built-in render pipeline + restricciones). Hay que ir con shader custom + materiales locales del proyecto.

## Receta default: unlit cutout, double-sided

Para un personaje 3D que aparece en escena BS (caso típico: boss, NPC, prop animado), el shader por defecto recomendado es **unlit con cutout y `Cull Off`**. Razones:

1. **BS no ilumina los bundles de Vivify por defecto**. Si el shader es lit, el modelo se ve gris/oscuro o requiere luces metidas dentro del prefab — y la luz direccional siempre deja la cara opuesta a oscuras.
2. **Texturas exportadas de Unreal con FModel** suelen tener BlendMode=Masked + TwoSided (cutout + caras dobles). Replicar esto en Unity = `Cull Off` + `clip(col.a - cutoff)`.
3. **Unlit es performante** y predecible. Sin sorpresas de cálculo de iluminación.

Ejemplo: [Assets/Aline/Shaders/AlineStandard.shader](../../../VivifyTemplate/Assets/Aline/Shaders/AlineStandard.shader). Patrón reutilizable para cualquier personaje.

```hlsl
Shader "Aline/Standard"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _AlphaCutoff ("Alpha Cutoff", Range(0,1)) = 0
    }
    SubShader
    {
        Tags { "RenderType"="TransparentCutout" "Queue"="AlphaTest" }
        Cull Off
        Pass
        {
            // ... vert/frag standard ...
            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv) * _Color;
                clip(col.a - _AlphaCutoff);
                return col;
            }
        }
    }
}
```

`_MainTex` con default `"white"` + `_Color` permite reutilizar el mismo shader para materiales sin texture (e.g., negro sólido) sin necesidad de un shader separado.

## El template `Hidden/Vivify/Templates/Standard` no se puede usar tal cual

[VivifyTemplate/.../Templates/Standard.shader](../../../VivifyTemplate/Assets/VivifyTemplate/Utilities/Shaders/Templates/Standard.shader) es la base recomendada por VivifyTemplate, pero su nombre empieza por `Hidden/` → no aparece en el dropdown del Inspector de Material. **Hay que duplicarlo** a `Assets/<Project>/Shaders/` y renombrar el shader path a algo visible (e.g., `"Aline/Standard"`).

Es también opaque y single-side por defecto — al duplicar añadir cutout + Cull Off según receta de arriba.

## Mapping de FModel → Unity (texturas a material slots del FBX)

Cuando importas un FBX exportado vía FModel→Blender→FBX, el FBX trae **N material slots con nombres tipo `MI_<algo>` o `M_<algo>`**. La fuente de verdad de qué textura va con qué slot vive en los `MaterialInstanceConstant` originales del juego — y a partir de 2026-05-03 los inspeccionamos vía **fmodel-mcp** en lugar de exportar JSONs y leerlos a mano.

### Flujo canónico (con fmodel-mcp)

1. **Inventariar slots del FBX** — igual que antes: Inspector de Unity → SkinnedMeshRenderer → Materials, o leer el `.prefab` (`m_Materials` con guids → mapear a `.mat.meta`). Para mallas sin importar todavía: el `.json` del `SkeletalMesh` da el orden en `SkeletalMaterials`. Ejemplo para Aline:
   ```
   mcp__fmodel__fmodel_search ("**/SK_Curator_Aline*")
   mcp__fmodel__fmodel_read   ("Sandfall/Content/.../SK_Curator_Aline")
   ```
   `SkeletalMaterials[i].MaterialSlotName` te da el orden + el path del MI por defecto.

2. **Inspeccionar cada MaterialInstance** con `mcp__fmodel__fmodel_inspect_material(path)` — devuelve **solo lo accionable**: Textures, Scalars, Vectors, parent material, BlendMode, TwoSided, OpacityMaskClipValue. Mucho más liviano que el JSON crudo.

   **Mejor en paralelo** (un mensaje, N tool calls): los inspects son independientes y de <1s cada uno. Para Aline (5 slots) era una sola tanda.

3. **Exportar las texturas referenciadas** con `mcp__fmodel__fmodel_export_texture(path)`. También paralelizable. Salen como PNG a `D:\vivify_repo\Output\Exports\<package_path>.png`.

4. **Mover las PNGs** desde `Output/Exports/...` directamente a `VivifyTemplate/Assets/Aline/Textures/` (o donde toque). Las texturas no necesitan paso por Blender ni espejo en `Sandfall/`. Lo que sí pasa por `Sandfall/` son los **meshes** (`.pskx` → Blender → `.fbx`).

5. **Mapping decisions** — convertir lo del MI al material Unity:
   - `BlendMode: BLEND_Masked` + `OpacityMaskClipValue` → cutout, `_AlphaCutoff` = ese valor.
   - `TwoSided: true` → `Cull Off`.
   - `BlendMode: BLEND_Translucent` → blending alpha real (más caro), no cutout.
   - Texturas sueltas tipo `Normal`, `ORM`, `Opacity_Mask`, `Mask_Face` → enchufar a properties del shader. Si el shader actual no las soporta, extender (ver sección "Upgrade path").

### Cuándo NO usar fmodel-mcp

- **Material padre / UMaterial puro** (no MI): el inspect devuelve casi vacío porque la lógica vive en el graph de nodos del shader, no en parámetros. Ahí usar `fmodel_export_raw` o aceptar que el padre define un shader que vamos a aproximar a mano.
- **Buscar referencias inversas** ("¿qué materiales usan esta textura?"): no soportado en Tier 1. Workaround: `fmodel_search` por nombre + `fmodel_inspect_material` en cada candidato.

### Lo que el SK pide ≠ lo que el juego renderiza

El `SkeletalMaterials[]` del SK es el material "por defecto" del asset, pero los Blueprints que spawnan ese SK pueden override slots concretos via `OverrideMaterials[]`. Para portar el look correcto del juego no basta con leer el SK — hay que trazar **al BP que efectivamente lo usa** (cinemático, gameplay, etc.) y mirar sus overrides.

Caso canónico Aline (2026-05-03):
- `SK_Curator_Aline` slot 4 (`Curator_Aline_Hole`) → padre `M_CuratorFace` (UMaterial puro, sin params accesibles).
- `BP_Cine_Curator_Aline` → `OverrideMaterials[4] = MI_CuratorFace_Aline` (con `Mask_Curator_Aline` específica de Aline).

Si solo lees el SK, asumes el padre. Si lees también el BP cinemático, descubres que en el render real va el MI con su mask propia. Receta:

1. `fmodel_search "**/BP_*<Personaje>*"` para listar los BPs que pueden spawn al personaje.
2. `fmodel_export_raw` del BP candidato y grep `"OverrideMaterials"` — los nulls heredan del SK, los objects son override.
3. Decidir basándote en qué BP corresponde a tu uso (cinemático para reference visual, gameplay BP para spawn dinámico, etc.).

### Limitación: UMaterial puro vs MaterialInstanceConstant

`fmodel_inspect_material` extrae `TextureParameterValues / ScalarParameterValues / VectorParameterValues / Parent / BlendMode`. Eso vive en MIs (`MaterialInstanceConstant`), no en el padre `UMaterial`. Para el padre el inspect devuelve casi vacío (la lógica vive en el graph de nodos del shader y en `CachedExpressionData`, que el tool actual no extrae).

Workaround: `fmodel_export_raw` del padre te da `RuntimeEntries[].ParameterInfoSet` (nombres de los params) + `ScalarValues / VectorValues / TextureValues` (defaults). Suficiente para inferir qué knobs hay y arrancar la portabilidad. Una mejora futura del MCP (Tier 1.5) sería extraer eso directamente desde `inspect`.

## Material creation flow

1. Folders esperados (crear si faltan):
   - `Assets/<Project>/Shaders/` — el .shader duplicado/custom
   - `Assets/<Project>/Materials/` — los .mat
   - `Assets/<Project>/Textures/` — los PNGs (gitignored, .meta versionados)

2. **Crear shader**: duplicar `Hidden/Vivify/Templates/Standard.shader`, renombrar el shader path, añadir cutout + Cull Off + properties extra que necesites.

3. **Importar texturas**: usar `mcp__fmodel__fmodel_export_texture` y mover los PNGs desde `Output/Exports/.../*.png` a `Assets/<Project>/Textures/`. Unity los importa al volver al Editor.

4. **Crear .mat**: Right-click → Create → Material en `Materials/`. Inspector → Shader dropdown → tu shader nuevo. Asignar `_MainTex`, `_Color`, `_AlphaCutoff`.

5. **Asignar al prefab**: abrir el `.prefab`, seleccionar el Renderer, arrastrar tus .mat a los Element 0..N (en el orden que descubriste en el paso "Mapping").

6. **Verificar en escena**: el modelo se ve texturizado en la Scene view de Unity, sin warnings de "missing material" en consola.

7. **Build**: F5. Sync de CRCs es automático vía el Editor watcher (ver skill `unity-rebuild`).

## Errores comunes

| Síntoma | Causa | Fix |
|---|---|---|
| Aline/personaje en magenta en BS | Shader no compila en el bundle | Revisar que el shader sigue la receta (Built-in pipeline, no URP/HDRP). Mirar consola Unity al hacer build. |
| Aline en magenta pero solo desde un ángulo | Falta `Cull Off` | Añadir `Cull Off` al SubShader. |
| Cara/back oscura en BS | Shader es lit y BS no manda luces | Migrar a unlit (la receta default). |
| Bordes duros en pelo/ropa donde debería haber alpha cutout | `_AlphaCutoff` = 0 o falta `clip()` | `_AlphaCutoff` = 0.333 (o el valor del `OpacityMaskClipValue` del JSON Unreal). |
| Slot mal asignado (parte del cuerpo con textura equivocada) | Orden de Element 0..N no match con lo que asumiste | Verificar nombres de Material en el Inspector. Reasignar acordemente. |
| `Material has no _MainTex` warning | Material asignado a un shader que no tiene esa property | Pasar al shader correcto, o usar default `"white"` en la property declaration. |
| Cambios en .mat no se ven en BS | F5 no se ha hecho, o CRCs no synced | F5 (auto-sync via Editor watcher hace el resto). Si auto-sync está off, run `.\scripts\sync-crcs.ps1`. |

## Upgrade path: unlit → lit/PBR

Si en algún momento se quiere PBR completo (normales, roughness, metallic, emissive):

1. Importar las texturas adicionales que ya hay en el dump (Normal, ORM, Emissive). Los `.json` ya describen qué van con cada material slot.
2. Construir un shader nuevo que samplee esas texturas (typical: `_NormalMap`, `_ORM`, `_Emissive`).
3. Decidir el modelo de iluminación: lambert simple, PBR completo (BRDF), o stylized (cel-shaded, matcap).
4. Si va a haber luces en el bundle: meterlas como child del prefab y diseñarlas para que iluminen razonablemente desde varios ángulos (no una sola directional). O activar ambient en Unity y configurarlo para que el bundle lo respete.

### Receta práctica: "unlit con fake-light + normal" (lo que usamos en Aline body)

Como BS no manda luces a los bundles Vivify, un shader lit "real" se ve plano. Patrón canónico (ver [`AlineBodyLit.shader`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineBodyLit.shader)):

```hlsl
// Sample base con cutout (igual que AlineStandard)
fixed4 base = tex2D(_MainTex, uv) * _Color;
clip(base.a - _AlphaCutoff);

// Reconstruir normal en world-space desde tangente + normal map
float3 worldN = normalize(nTan.x*T + nTan.y*B + nTan.z*N);

// Fake key light fija world-space (no necesita Light en escena)
float3 L = normalize(_LightDir.xyz);
float ndotl = saturate(dot(worldN, L));
float lambert = lerp(_Ambient, 1.0, ndotl);  // _Ambient evita shadow side pure black
float shading = lerp(1.0, lambert, _LightStrength);  // _LightStrength=0 → unlit

return fixed4(base.rgb * shading, base.a);
```

**Tunables (defaults razonables):** `_LightDir=(0.3, 0.7, -0.6)` (key from above-front), `_LightStrength=0.45` (visible pero no caricaturesco), `_Ambient=0.55` (shadow side ~half intensity), `_BumpScale=1.5` (matchea UE Normal/Bump Multiplier).

### Ambient en bundles Vivify — usar `unity_AmbientSky/Equator/Ground`, NO `ShadeSH9`

Cuando un shader custom dentro de un Vivify bundle quiere reaccionar al ambient state que setea `SetRenderingSettings.ambient*`, **NO usar `ShadeSH9(unity_SHAr/g/b)`**. Los coeficientes SH están a 0 en bundles Vivify standalone porque requieren un environment probe precomputado (`Lighting → Generate Lighting` en Unity Editor) y los bundles no llevan ese precompute.

**Vía válida — uniforms directos:**
```hlsl
float3 sky     = unity_AmbientSky.rgb;       // Sky color (siempre poblado)
float3 equator = unity_AmbientEquator.rgb;   // Sólo Trilight; en Flat = 0
float3 ground  = unity_AmbientGround.rgb;    // Sólo Trilight; en Flat = 0
```

Unity los puebla per-frame desde `RenderSettings.ambientMode/ambientLight/ambientSkyColor/ambientEquatorColor/ambientGroundColor` automáticamente, sin GI baking.

**Pattern para los tres modos (Skybox, Trilight, Flat) en una sola función:**
```hlsl
float3 SampleAmbient(float3 worldN) {
    float upWeight    = saturate(worldN.y);
    float downWeight  = saturate(-worldN.y);
    float horizWeight = 1.0 - upWeight - downWeight;

    float3 sky     = unity_AmbientSky.rgb;
    float3 equator = unity_AmbientEquator.rgb;
    float3 ground  = unity_AmbientGround.rgb;

    // Flat mode: Equator + Ground vienen a 0; reusar Sky para no oscurecer
    // lados/abajo del modelo a negro.
    float trilightActive = step(0.001, dot(equator + ground, float3(1,1,1)));
    equator = lerp(sky, equator, trilightActive);
    ground  = lerp(sky, ground,  trilightActive);

    return sky*upWeight + equator*horizWeight + ground*downWeight;
}
```

`RenderSettings.ambientIntensity` también afecta — multiplica los uniforms automáticamente. No hay que multiplicarlo en shader.

**Lo que NO hay en bundles Vivify** (no perder tiempo):
- `ShadeSH9` / `unity_SHAr/g/b` (env probe SH, requiere GI baking).
- `_LightColor0` / `_WorldSpaceLightPos0` (forward base directional light, requiere `LightMode="ForwardBase"` y una luz real en escena que BS no manda).
- `unity_SpecCube0` (skybox reflection probe — quizás funcione, no probado).

### MonoBehaviour custom NO sobrevive al stripping del bundle

DynamicBone, FinalIK, Magica Cloth, JiggleBones, SpringBones — cualquier asset paid/free que dependa de **scripts en runtime** queda inerte en bundle Vivify. Vivify hace whitelist agresivo: **sí sobreviven** Materials, Shaders (con keyword rewriter), AnimationClips, AnimatorControllers, Meshes, Textures, Prefab hierarchies, Transform animations, MeshRenderer/SkinnedMeshRenderer; **no sobreviven** scripts custom (MonoBehaviour), assets paid con runtime code, shaders con compute/tessellation, plugins nativos, scripts editor.

Para efectos tipo physics-on-bones (sway, jiggle, secondary motion), la única ruta viable es **AnimationClip pre-baked** que mueve los bones via `m_LocalRotation`/`m_LocalPosition` curves, looped via Animator. Sí funciona en bundle. Para deformaciones que requieran reaccionar a inputs en tiempo real (collision, wind direction): no factible en Vivify, diferir a "post-Phase-2" o aceptar como limitación.

### Outline shader (inverted-hull con saber color per-instance)

Para reemplazar el visual del note cube via `AssignObjectPrefab` en ataques familia A. Adaptado del tutorial "020 Inverted Hull Unlit" de Ronja (CC-BY 4.0, atribución en header).

Source canónico: [`Assets/Aline/Shaders/AlineOutline.shader`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineOutline.shader). Validado con `NoteCube.prefab` el 2026-05-04.

**Forma del look:** cuerpo casi-negro azulado + outline neón del color del saber (rojo si el note es `c=0`, azul si `c=1`). El outline aparece automáticamente porque Vivify pasa `_Color` per-instance al shader del prefab cuando se usa `colorNotes.{asset, anyDirectionAsset, debrisAsset}` en `AssignObjectPrefab` (doc heckdocs Vivify events).

**Patrón clave:**

1. **2 passes opacos.** Pass 1: cuerpo (`Cull Back`, color sólido `_BodyColor`). Pass 2: outline (`Cull Front`, vértices extruidos a lo largo de la normal, color sólido `_Color × _OutlineIntensity`). Ambos `ZWrite On`.

2. **Offset del outline en world space, no object space.** `worldPos += worldNormal * _OutlineThickness` antes del clip projection. Razón: el prefab típico tiene `localScale=45` (compensa que la mesh `Default Base.fbx` de CustomNotes viene en 0.011 raw). En object space, `_OutlineThickness=0.02` se convierte en ~1m world (un disparate). En world space queda en metros directamente, slider predecible.

3. **GPU instancing en pass 2 para `_Color` per-instance.** Sin esto, Vivify no puede pasar el saber color por nota:
   ```hlsl
   #pragma multi_compile_instancing

   UNITY_INSTANCING_BUFFER_START(Props)
       UNITY_DEFINE_INSTANCED_PROP(fixed4, _Color)
   UNITY_INSTANCING_BUFFER_END(Props)

   // En vert: UNITY_TRANSFER_INSTANCE_ID(v, o);
   // En frag: UNITY_SETUP_INSTANCE_ID(i);
   //         fixed4 c = UNITY_ACCESS_INSTANCED_PROP(Props, _Color);
   ```
   Y `mat.enableInstancing = true` en el material. Sin el flag, Unity no compila la variant correcta.

4. **SPI macros en ambas passes** (BS 1.34.2 = Single Pass Instanced VR). Estándar del repo: `UNITY_VERTEX_INPUT_INSTANCE_ID` en `appdata`, `UNITY_VERTEX_OUTPUT_STEREO` en `v2f`, `UNITY_SETUP_INSTANCE_ID + UNITY_INITIALIZE_OUTPUT + UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO` en vert.

5. **Sin `_MainTex`.** La mesh `Default Base.fbx` de CustomNotes no trae UVs. Body y outline son colores sólidos, sin samplers. Ahorro de complejidad y zero cost de texturizado.

6. **`[HDR] _Color` con `_OutlineIntensity` multiplier.** Default `_OutlineIntensity=2.0`. BS aplica bloom interno al rendering — valores HDR > 1 hacen que el outline brille en lugar de quedar plano. Bajar a 1.5 si queda lavado, subir a 2.5+ si se quiere más punch.

**Mesh source:** `Default Base.fbx` de [legoandmars/CustomNotesUnityProject](https://github.com/legoandmars/CustomNotesUnityProject). El proyecto entero queda fuera del repo en `d:/vivify_repo/CustomNotesUnityProject/`. Solo usamos la mesh; **NO** copiamos `NoteDescriptor` (componente del mod CustomNotes que Vivify no consume). Bevel suave de la mesh da el look "comic", sin arrow geometry → resuelve el `dissolveArrow desync` documentado en `family-a-recipe.md`.

**Convertir a prefab:** Empty root con `MeshFilter + MeshRenderer` apuntando a la mesh `Cube` interna del FBX, material `M_NoteOutline` asignado, `localScale=45` (compensa los 0.011 raw → world ~0.5m, equivalente al note BS default). Asignar al `aline_bundle`.

**Gotcha — Vivify pasa `_Cutout` por proximidad, no por `animation.dissolve`:**

El doc heckdocs dice que `AssignObjectPrefab` setea `_Color`, `_Cutout`, `_CutoutTexOffset` per-instance. Los shaders del template Vivify (`CustomBomb`, `CustomNoteArrow`, `CustomNoteBase`) leen `_Cutout` con convención `0=visible, 1=dissolved`.

**Pero comportamiento observado en BS 1.34.2 con Vivify (validado 2026-05-04):** `_Cutout` per-instance NO sigue la curve `customData.animation.dissolve`. Parece estar driven por proximidad del note al player (probablemente para preparar el cut animation post-hit). Resultado: si el shader implementa `clip(cutout - 0.5)`, los notes se ocultan **justo al dispararse al player** — comportamiento no deseado para ataques familia A donde queremos verlos durante todo el launch.

**Workaround:** declarar `_Cutout` per-instance en el instancing buffer (queda como hook para parry / debris fade futuros) pero **no usarla para clip activo**. El "dissolve trick" de ocultar los notes durante NJS jump-in se hace via `customData.animation.scale` con primer punto `(0,0,0)` (Heck usa el primer punto durante jump-in y los objetos quedan invisibles efectivamente). Detalle en `family-a-recipe.md`.

**No probado en este proyecto** pero plausible para iteraciones futuras: si quisiéramos un dissolve real (ej. fade post-cut), sería más fiable controlar via `AnimateTrack` setando una property custom en el material per-track, en lugar de depender de `_Cutout` automático de Vivify.

### Dot/Arrow indicator overlay shader (`Aline/DotOverlay`)

Para indicators flat (dot, arrow) que viven sobre la cara del cube y deben ser **siempre visibles** sobre el body+outline, sin pelear con z-buffer. Source: [`Assets/Aline/Shaders/AlineDotOverlay.shader`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineDotOverlay.shader).

**Patrón:** color sólido HDR + `ZTest Always` + `ZWrite Off` + `Cull Off` + `Queue=Geometry+10`. Sin clip, sin sampler. SPI macros estándar.

```hlsl
Tags { "RenderType"="Opaque" "Queue"="Geometry+10" }
Cull Off
ZTest Always
ZWrite Off
```

`ZTest Always` hace que el indicator siempre pase el depth test → visible aunque esté detrás del body o al mismo depth que el outline (caso típico cuando el child GameObject del indicator está cerca de la cara del cube). `ZWrite Off` evita que el indicator contamine el depth buffer para frames posteriores. `Cull Off` permite verlo desde ambos lados (defensivo si la rotación child queda al revés).

**Por qué no `Aline/Standard` para esto:** Standard tiene `Cull Off` y queue normal (`AlphaTest`), pero respeta el ZTest LEqual que pelea con el outline pass del body. El indicator queda al mismo depth que la geometría inflada del outline (en el caso del NoteCube, outline thickness 0.02m world cubre exactamente la distancia desde la cara del cube hasta donde está el indicator). El z-fight oculta el indicator algunos frames sí otros no — bug visual constante.

**Posicionamiento del indicator child** (Dot/Arrow):
- `localPosition=(0,0,0)` — centro del cube. ZTest Always hace que el indicator se vea proyectado al centro de la silueta del cube desde cualquier ángulo, sin importar la rotación face-to-player del cube.
- `localRotation=Euler(90, 0, 0)` — gira el plano XY de la mesh `Dot`/`Arrow` (ambas mesas planas en XY) para alinearlo con la cara visible del cube. Sin esta rotación el plano queda paralelo al view direction del player y se ve "de canto" (línea fina).
- Material en `aline_bundle`. Color HDR overbright `(3, 3, 3, 1)` para neón blanco visible.

Validado 2026-05-04 con `NoteCube.prefab` + child `Dot` (mesh `Dot` de `Default Arrows.fbx` de CustomNotes).

### Particle shaders en bundles Vivify

Para `ParticleSystem` (built-in Unity) que renderiza dentro de un bundle Vivify. Validado 2026-05-05 con `SphereBurst.prefab` + cube child smoke (E33-style envelope + world trail). ParticleSystem **sí** sobrevive al stripping del bundle (es componente core de Unity, no MonoBehaviour custom — ver "MonoBehaviour custom NO sobrevive al stripping" arriba).

**Gotcha 1 — los shaders de mesh estática (POSITION-only) NO valen para billboard particles.**

`Aline/DotOverlay` y similares declaran `appdata { float4 vertex : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID }`. Eso vale para `MeshRenderer` con vertex buffer estático. `ParticleSystemRenderer` en `Billboard` mode genera quads con `POSITION + COLOR + TEXCOORD0` por particle (color es la modulación per-particle, UV el cuadrante del quad para máscara). Si el shader no declara `COLOR/TEXCOORD0`, los particles emiten OK pero salen invisibles (color por defecto a 0 + sin máscara = nada).

Diagnóstico empírico: el log `[Vivify/InstantiatePrefab] Enabled [...prefab]` confirma instanciación + bundle correcto, así que el silencio visual = shader incompatible, no stripping.

**Patrón shader compatible (ver [`AlineParticleSmoke.shader`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineParticleSmoke.shader) y [`AlineParticle.shader`](../../../VivifyTemplate/Assets/Aline/Shaders/AlineParticle.shader)):**

```hlsl
struct appdata {
    float4 vertex : POSITION;
    float4 color  : COLOR;       // modulación per-particle (gradient + startColor)
    float2 uv     : TEXCOORD0;   // 0..1 across quad, para procedural mask
    UNITY_VERTEX_INPUT_INSTANCE_ID
};

struct v2f {
    float4 position : SV_POSITION;
    float4 color    : COLOR;
    float2 uv       : TEXCOORD0;
    UNITY_VERTEX_OUTPUT_STEREO
};

// vert: o.position = UnityObjectToClipPos(v.vertex); o.color = v.color; o.uv = v.uv;
// frag: máscara procedural desde uv * tint * v.color
```

SPI macros idénticas al resto de shaders del repo (BS 1.34.2 SinglePassInstanced VR).

**Gotcha 2 — aditivo HDR para "energía", alpha-blend para "humo oscuro".**

Aditivo (`Blend SrcAlpha One`) sobre fondo bright (skybox blanquecino) **no muestra negros** porque suma. Smoke oscuro requiere alpha-blend (`Blend SrcAlpha OneMinusSrcAlpha`).

| Caso | Shader | Blend | Tint |
|---|---|---|---|
| Sparks / energía / glow | `Aline/Particle` | `SrcAlpha One` (additive) | HDR overbright `(3,3,3,1)` o más |
| Humo / dust / dark wisps | `Aline/ParticleSmoke` | `SrcAlpha OneMinusSrcAlpha` (alpha) | LDR oscuro `(0.04,0.04,0.06,1)` |

`Cull Off`, `ZWrite Off` para los dos. `ZTest LEqual` (default — humo respeta z-buffer; queda detrás del cube body si va detrás).

**Gotcha 3 — `simulationSpace=Local` vs `World` define si el efecto sigue al parent o se queda en el mundo.**

| simulationSpace | Comportamiento | Cuándo usar |
|---|---|---|
| `Local` | Particles attached al transform del parent. Mover/rotar parent → particles se mueven con él. | Envoltura contenida que viaja con el proyectil (smoke envelope). |
| `World` | Particles emitidos en world coords. Mover parent → particles previamente emitidos quedan donde estaban. | Trail / scia que se queda atrás cuando el parent se mueve. Burst de humo en posición fija. |

Combinar ambos en el mismo prefab para un efecto rico: un emitter Local (envelope) + otro World (trail). Ejemplo en [`NoteCube.prefab`](../../../VivifyTemplate/Assets/Aline/Prefabs/projectiles/NoteCube.prefab) con `SmokeEnvelope` + `SmokeTrailWorld` siblings.

**Gotcha 4 — Hacer particles invisibles durante NJS jump-in via `scalingMode=Hierarchy` + `localScale=1/parent_scale`.**

Cuando un ParticleSystem es child de un BS note prefab (ej. `NoteCube.prefab` con `localScale=45` y customData.animation.scale curve `[0,0,0]` durante jump-in), queremos que las particles también sean invisibles durante el jump-in y aparezcan al `scale-pop`. Pero por default Unity scala particles "Local" — solo respeta el `localScale` del propio GO del PS, no el lossyScale del parent.

**Solución:**
- `MainModule.scalingMode = Hierarchy` — ahora el sistema usa lossyScale (parent × child).
- `child.localScale = (1/parent_scale, 1/parent_scale, 1/parent_scale)` — neutraliza el factor 45 del parent. Resultado: lossyScale efectivo = 1 cuando parent.lossyScale=45 (post scale-pop), y = 0 cuando parent.lossyScale=0 (durante jump-in y antes del pop).

Sin esto, hay que recurrir a `MainModule.startDelay` aproximando la duración del NJS jump-in en segundos — frágil porque depende de NJS+BPM y de cuándo el ParticleSystem awake'a.

**Gotcha 5 — fade-in de alpha en trails crea "gap" visible entre cube y cola.**

Si la `colorOverLifetime` curve arranca en alpha=0 ("fade in"), las particles recién emitidas son invisibles ~0.2-0.3s. Durante ese tiempo el cube se mueve varios metros → la cola visible arranca lejos del cube, no pegada.

**Solución:** alpha curve para trails arranca ya en el peak (`0.85` o lo que toque) y solo hace fade-out al final. El "soft start" lo aporta la máscara procedural del shader (suave en el borde del quad), no la curva de lifetime. Para envelope (Local sim, attached al cube) sí se puede usar fade-in sin gap visible — porque el particle se mueve con el cube y "aparece progresivamente" en su sitio.

### Gotcha: la "ORM" de Sandfall NO es una ORM standard

Confirmado 2026-05-03 con `Curator_Body_OcclusionRoughnessMetallic.png`: aunque el nombre sigue la convención UE (Occlusion R, Roughness G, Metallic B packed grayscale), el contenido visual es **pseudocolor multichannel** (naranja+verde+magenta saturados, no grayscale). El R channel tiene valores ~0.5-1.0 mayoritariamente — multiplicado como AO da prácticamente identidad, no oscurece nada.

Probable: Sandfall usa estos PNG para encoder paint masks / channel-packed effects de su pipeline UE específico, no para PBR estándar. **AO real está bakeada en BaseColor.**

Implicación práctica: **`_OcclusionStrength=0` para los body materials de Aline** (y probablemente de cualquier personaje E33). El Normal map sí es estándar y se enchufa normalmente.

Si quieres validar antes de dar por inútil un ORM, abre la PNG con el Read tool y mira los canales: si la R channel se ve grayscale-like, es ORM real; si se ve coloreado, es lo otro.
