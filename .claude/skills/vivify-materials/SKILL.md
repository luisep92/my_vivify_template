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
