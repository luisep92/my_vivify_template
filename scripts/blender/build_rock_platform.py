"""
Procedural builder for the boss-fight platform mesh.

Genera RockPlatform: óvalo de cima rocosa con un corredor central plano (la
ruta dash de Aline) y relieve perimetral. Pivot en TOP-CENTER → el prefab
se posiciona en Unity con `[0, alturaSuelo, 0]` y la cima del platform queda
a esa altura. Aline a `[0, alturaSuelo, ~4]` queda al borde del eje largo.

Idempotente: borra cualquier RockPlatform anterior antes de construir. Diseñado
para ejecutarse via blender-mcp execute_blender_code en la escena de animación
de Aline (no se guarda el .blend; el output útil es el FBX exportado).

Para reusar:
  1. Abrir la escena de Aline en Blender (con MCP wired)
  2. Pegar el contenido de este file en execute_blender_code
  3. El FBX se sobrescribe en Assets/Aline/Scenery/Meshes/RockPlatform.fbx
  4. Unity reimporta solo (PostBuildSyncCRCs sincroniza Info.dat tras el build)

Parámetros:
- HALF_X / HALF_Y: semi-ejes del óvalo (Blender axes; Y → Unity Z)
- CORRIDOR_*: zona plana central donde Aline pisa (no se aplica relief)
- SILHOUETTE_*: amplitud y frecuencia de la mordida del borde
- RELIEF_*: amplitud y escala del ruido del relieve superior
"""

import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector
from mathutils import noise as mnoise

EXPORT_PATH = r"d:/vivify_repo/my_vivify_template/VivifyTemplate/Assets/Aline/Scenery/Meshes/RockPlatform.fbx"

# Mesh-source para los petals (legacy, scatter de clusters discretos pequeños).
# No usado actualmente — la cobertura del suelo viene del ivy carpet (abajo).
# Se mantiene la función build_petals() abajo por si en el futuro se vuelve a
# scatter discreto para meshes de plantas con flores (ej. Sea Thrift).
PETAL_SOURCE_FBX = r"d:/vivify_repo/my_vivify_template/VivifyTemplate/Assets/Aline/Scenery/Meshes/PetalCluster.fbx"
PETAL_COUNT = 22
PETAL_SCALE_MIN = 0.8
PETAL_SCALE_MAX = 1.5
PETAL_LIFT = 0.05
PETAL_TILT_MAX_DEG = 12.0
PETAL_MIN_SPACING = 0.7
PETAL_SCATTER_SEED = 42
PETAL_FAR_BOOST = 0.6

# Mesh-source para el carpet de ivy (Real_Ivy_Pack/SM_ivy_floor_plane_dense_*).
# Es un parche plano de hojas pre-construido de ~7.8x7.8m, 129K verts. Scatter
# de pocas instancias rotadas lo cubre todo con cero patrón visible. Reemplaza
# el approach de duplicate-rock-top + tile-shader.
IVY_SOURCE_FBX = r"d:/vivify_repo/my_vivify_template/VivifyTemplate/Assets/Aline/Scenery/Meshes/IvyFloorDense.fbx"
IVY_LIFT = 0.05  # m sobre el rock top
IVY_SCATTER_SEED = 11
# Decimate ratio aplicado al template ANTES del scatter. 0.5 = halve tris,
# visualmente indistinguible a distancia BS. Bajar a 0.3 si necesitas más
# perf budget para Quest. Subir a 1.0 para skip Decimate.
IVY_DECIMATE_RATIO = 0.5

# Mesh-source para los bushes (capa de "salpicaduras de color" 3D sobre el
# ivy carpet). 64 tris cada uno → 20 instancias = 1280 tris, negligible.
BUSH_SOURCE_FBX = r"d:/vivify_repo/my_vivify_template/VivifyTemplate/Assets/Aline/Scenery/Meshes/BushSmall.fbx"
BUSH_COUNT = 14
BUSH_SCALE_MIN = 0.6
BUSH_SCALE_MAX = 1.2
BUSH_LIFT = 0.10  # ligeramente más alto que IVY_LIFT para asomar sobre el ivy
BUSH_TILT_MAX_DEG = 8.0
BUSH_MIN_SPACING = 0.7
BUSH_SCATTER_SEED = 23
# Solo en-frente-del-jugador (y >= BUSH_Y_MIN en Blender pre-mirror).
# Cámara fija de BS no ve detrás del player → bushes detrás son geometry
# desperdiciada. Mismo razonamiento que IVY_PATCHES (foco aline-side).
BUSH_Y_MIN = 0.5  # 0.5m en frente del player (player en y=0)

# Textures para preview Material Preview en Blender (placeholders se rellenan
# con estas para que el viewport refleje el look final, no gris). No afectan
# al export (Unity reasigna materiales reales en el prefab).
import os as _os
_ASSETS_TEX = r"d:/vivify_repo/my_vivify_template/VivifyTemplate/Assets/Aline/Scenery/Textures"
PREVIEW_ROCK_TEXTURE = _os.path.join(_ASSETS_TEX, "T_JaggedRock_Albedo.png")
PREVIEW_IVY_TEXTURE = _os.path.join(_ASSETS_TEX, "T_ivy_efeu0_Alb_Opacity.png")
PREVIEW_BUSH_TEXTURE = _os.path.join(_ASSETS_TEX, "T_ground_foliage_03_BC_M.png")
# Tint que matchea M_BlueIvy._Color en Unity. Usado vía luminance-tint en EEVEE
# (RGB→BW → multiply tint) para reproducir el shader Aline/Standard con
# LUMINANCE_TINT habilitado.
PREVIEW_IVY_TINT = (0.55, 0.75, 1.6, 1.0)
PREVIEW_BUSH_TINT = (1.5, 0.4, 0.8, 1.0)  # overbright pink-magenta
# Distribución asimétrica matching la propuesta visual del user. Coords en
# Blender pre-mirror: +Y = hacia Aline (delante del jugador), -Y = detrás.
# Cámara fija de BS solo ve frente y lados → el área detrás del jugador no
# justifica geometría. Foco en aline-side + flanks. Cada mesh ~7.8m DIÁMETRO
# nativo, scale 0.3-1.0 = patches de 2.3-7.8m.
# Formato: (x, y, scale)
IVY_PATCHES = [
    (-2.5, 5.0, 1.0),    # grande arriba-izquierda (aline-side, flanco izq)
    ( 3.0, 5.5, 0.75),   # mediana arriba-derecha
    ( 3.5, 1.0, 0.70),   # mediana derecha a nivel jugador
    (-4.0, -1.5, 0.55),  # pequeña abajo-izquierda (ligeramente detrás del jugador, flanco)
    (-5.0, -3.5, 0.35),  # micro borde-izquierda (al fondo izquierdo)
]
IVY_YAW_JITTER_DEG = 360  # rotación Y aleatoria 0-360 (camufla repetición del mesh)
# El mesh nativo de Real_Ivy_Pack tiene leaves "creciendo" verticalmente
# (~40cm altura), demasiado plant-like. Para look "pétalos tirados en el
# suelo" aplastamos agresivo en Z. 0.15 = ~5-6cm height a scale 1.0 — los
# leaves quedan casi planos contra la roca, como pétalos caídos.
IVY_HEIGHT_SCALE = 0.15

HALF_X = 6.0
HALF_Y = 9.0
THICKNESS = 0.6
SEGMENTS = 80

# Corredor central plano (en coords Blender; Y es eje del dash)
# Aline se posiciona en Unity en z=8; el corredor cubre player(0)→Aline(8) con margen.
# Ancho 5m total: deja espacio cómodo de pisada y empuja los bumps a los flancos.
CORRIDOR_HALF_X = 2.5
CORRIDOR_Y_MIN = -1.5
CORRIDOR_Y_MAX = 9.5

# Falloff blend desde el borde del corredor hacia el relieve completo.
# Más alto = transición más suave → menos baches visibles cerca de la pisada.
CORRIDOR_FALLOFF = 2.0

# Silueta perimetral
SILHOUETTE_AMP_OUT = 0.18
SILHOUETTE_AMP_IN = 0.10
SILHOUETTE_NOISE_FREQ = 1.6

# Relieve superior. Amplitud generosa para que los flancos tengan rocas
# llamativas que contrasten con el corredor plano.
RELIEF_AMP = 0.50
RELIEF_NOISE_SCALE = 0.55
RELIEF_DOWN_AMP = 0.18

NOISE_SEED_OFFSET = Vector((31.7, 7.7, 17.3))


def build():
    # Cleanup previous platform
    for obj in list(bpy.data.objects):
        if obj.name.startswith("RockPlatform"):
            bpy.data.objects.remove(obj, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.name.startswith("RockPlatform"):
            bpy.data.meshes.remove(me)

    # Force OBJECT mode (otherwise primitive_cylinder_add poll fails)
    if bpy.context.view_layer.objects.active and bpy.context.view_layer.objects.active.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Cylinder primitive with TRIFAN cap → has center vert + triangles → subdiv generates interior verts
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=SEGMENTS,
        radius=1.0,
        depth=THICKNESS,
        end_fill_type='TRIFAN',
        location=(0, 0, 0),
    )
    obj = bpy.context.active_object
    obj.name = "RockPlatform"
    obj.data.name = "RockPlatform"

    # Scale to oval, apply
    obj.scale = (HALF_X, HALF_Y, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # Subdivide whole mesh once, then top-only twice more → relief detail concentrated arriba
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=2, smoothness=0)

    bm = bmesh.from_edit_mesh(obj.data)
    bpy.ops.mesh.select_all(action='DESELECT')
    for f in bm.faces:
        if all(v.co.z > 0.05 for v in f.verts):
            f.select_set(True)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.subdivide(number_cuts=2, smoothness=0)

    # Top a z=0 (pivot TOP-CENTER)
    bm = bmesh.from_edit_mesh(obj.data)
    for v in bm.verts:
        v.co.z -= THICKNESS / 2.0
    bmesh.update_edit_mesh(obj.data)

    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    bm.verts.ensure_lookup_table()

    EPS_RING = 0.015
    TOP_Z = 0.0

    def silhouette_factor(angle):
        n = mnoise.noise(Vector((
            math.cos(angle) * SILHOUETTE_NOISE_FREQ,
            math.sin(angle) * SILHOUETTE_NOISE_FREQ,
            NOISE_SEED_OFFSET.x,
        )))
        return 1.0 + (n * SILHOUETTE_AMP_OUT if n >= 0 else n * SILHOUETTE_AMP_IN)

    # Mordida del perímetro (radial). Aplica a todas las z porque las paredes
    # comparten X,Y con top y bottom verts del mismo "rayo" radial.
    for v in bm.verts:
        r_norm = math.sqrt((v.co.x / HALF_X) ** 2 + (v.co.y / HALF_Y) ** 2)
        if r_norm > 1.0 - EPS_RING:
            a = math.atan2(v.co.y / HALF_Y, v.co.x / HALF_X)
            f = silhouette_factor(a)
            v.co.x *= f
            v.co.y *= f

    def edge_dist_to_corridor(x, y):
        dx = max(0.0, abs(x) - CORRIDOR_HALF_X)
        dy = 0.0
        if y > CORRIDOR_Y_MAX:
            dy = y - CORRIDOR_Y_MAX
        elif y < CORRIDOR_Y_MIN:
            dy = CORRIDOR_Y_MIN - y
        return math.sqrt(dx * dx + dy * dy)

    # Relieve superior. Skip corridor + ramp blend en sus bordes.
    for v in bm.verts:
        if abs(v.co.z - TOP_Z) >= 0.01:
            continue
        in_corridor = (abs(v.co.x) < CORRIDOR_HALF_X) and (CORRIDOR_Y_MIN < v.co.y < CORRIDOR_Y_MAX)
        if in_corridor:
            continue
        d = edge_dist_to_corridor(v.co.x, v.co.y)
        blend = min(1.0, d / CORRIDOR_FALLOFF)
        n1 = mnoise.noise(Vector((v.co.x * RELIEF_NOISE_SCALE, v.co.y * RELIEF_NOISE_SCALE, 0.0)))
        n2 = 0.45 * mnoise.noise(Vector((v.co.x * RELIEF_NOISE_SCALE * 2.2, v.co.y * RELIEF_NOISE_SCALE * 2.2, NOISE_SEED_OFFSET.y)))
        n = n1 + n2
        if n >= 0:
            disp = min(RELIEF_AMP, n * 0.55)
        else:
            disp = max(-RELIEF_DOWN_AMP, n * 0.20)
        v.co.z += disp * blend

    bmesh.update_edit_mesh(me)

    # UVs: smart project (no planar → no rayos en la cara superior)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)

    bpy.ops.object.mode_set(mode='OBJECT')
    for p in obj.data.polygons:
        p.use_smooth = True

    obj.location = (0, 0, 0)
    return obj


def _sample_top_z(x, y):
    """Reproduce el cálculo del relief para un (x,y) arbitrario, devolviendo
    la altura del top en ese punto. Usado por scatter de petals para que cada
    cluster aterrice exactamente sobre la superficie generada."""
    in_corridor = (abs(x) < CORRIDOR_HALF_X) and (CORRIDOR_Y_MIN < y < CORRIDOR_Y_MAX)
    if in_corridor:
        return 0.0
    dx = max(0.0, abs(x) - CORRIDOR_HALF_X)
    dy = 0.0
    if y > CORRIDOR_Y_MAX:
        dy = y - CORRIDOR_Y_MAX
    elif y < CORRIDOR_Y_MIN:
        dy = CORRIDOR_Y_MIN - y
    d = math.sqrt(dx * dx + dy * dy)
    blend = min(1.0, d / CORRIDOR_FALLOFF)
    n1 = mnoise.noise(Vector((x * RELIEF_NOISE_SCALE, y * RELIEF_NOISE_SCALE, 0.0)))
    n2 = 0.45 * mnoise.noise(Vector((x * RELIEF_NOISE_SCALE * 2.2, y * RELIEF_NOISE_SCALE * 2.2, NOISE_SEED_OFFSET.y)))
    n = n1 + n2
    if n >= 0:
        disp = min(RELIEF_AMP, n * 0.55)
    else:
        disp = max(-RELIEF_DOWN_AMP, n * 0.20)
    return disp * blend


def build_petals(rock_obj):
    """Importa el PetalCluster FBX, scatter N copias sobre el top del rock
    en zonas no-corredor, joina todo en una sola mesh y la attacha al rock_obj
    como segundo material slot. Mantiene 1 mesh + 2 submeshes = arquitectura
    de un solo asset. Usa _sample_top_z para que cada cluster aterrice sobre
    la superficie generada (evita flotar/enterrarse)."""
    import random
    rng = random.Random(PETAL_SCATTER_SEED)

    # Capturar nombres existentes para identificar lo que importemos
    pre_names = {o.name for o in bpy.data.objects}
    bpy.ops.import_scene.fbx(filepath=PETAL_SOURCE_FBX)
    new_names = [o.name for o in bpy.data.objects if o.name not in pre_names]
    petal_template = next((bpy.data.objects[n] for n in new_names if bpy.data.objects[n].type == 'MESH'), None)
    if petal_template is None:
        for n in new_names:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
        raise RuntimeError("PetalCluster FBX no contenía mesh importable")

    # Aplicar el scale del template para hornearlo en los vertex coords. La FBX
    # exportada por pskx_to_fbx.py viene con verts en coords UE (~42m) +
    # object scale=0.01 → dimensions correctas. Al duplicar y setear scale en
    # las copias, sobreescribíamos el 0.01 → cada cluster salía 100x demasiado
    # grande. Apply transforms aquí garantiza que las copias trabajen sobre
    # vertex coords ya escalados (~42cm) y sus scale-multipliers actúen como
    # esperamos (0.4-0.85 → 17-36cm).
    bpy.ops.object.select_all(action='DESELECT')
    petal_template.select_set(True)
    bpy.context.view_layer.objects.active = petal_template
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Posicionado: scatter por bounds del rock evitando corredor
    placed = []
    attempts = 0
    instances = []
    rim_buffer = 0.7  # margen interior para no rebasar la silueta orgánica
    while len(placed) < PETAL_COUNT and attempts < 500:
        attempts += 1
        x = rng.uniform(-(HALF_X - rim_buffer), HALF_X - rim_buffer)
        y = rng.uniform(-(HALF_Y - rim_buffer), HALF_Y - rim_buffer)
        # Skip dentro del corredor
        if (abs(x) < CORRIDOR_HALF_X) and (CORRIDOR_Y_MIN < y < CORRIDOR_Y_MAX):
            continue
        # Skip si demasiado cerca de otro
        too_close = False
        for px, py in placed:
            if (px - x) ** 2 + (py - y) ** 2 < PETAL_MIN_SPACING ** 2:
                too_close = True
                break
        if too_close:
            continue

        z_surface = _sample_top_z(x, y)
        # Duplicar el petal template via copia de mesh
        new_obj = petal_template.copy()
        new_obj.data = petal_template.data.copy()
        new_obj.name = f"PetalScatter_{len(placed):02d}"
        bpy.context.collection.objects.link(new_obj)

        s = rng.uniform(PETAL_SCALE_MIN, PETAL_SCALE_MAX)
        # Boost lineal según distancia al jugador (y > 0 = hacia Aline = lejos)
        far_factor = 1.0 + PETAL_FAR_BOOST * max(0.0, y / HALF_Y)
        s *= far_factor
        new_obj.scale = (s, s, s)
        new_obj.location = (x, y, z_surface + PETAL_LIFT)
        yaw = rng.uniform(0, 360)
        tilt_x = rng.uniform(-PETAL_TILT_MAX_DEG, PETAL_TILT_MAX_DEG)
        tilt_y = rng.uniform(-PETAL_TILT_MAX_DEG, PETAL_TILT_MAX_DEG)
        new_obj.rotation_euler = (math.radians(tilt_x), math.radians(tilt_y), math.radians(yaw))
        instances.append(new_obj)
        placed.append((x, y))

    # Aplicar transforms en cada instancia
    bpy.ops.object.select_all(action='DESELECT')
    for inst in instances:
        inst.select_set(True)
        bpy.context.view_layer.objects.active = inst
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Join todas las instancias en una sola mesh (la primera seleccionada)
    if len(instances) > 1:
        bpy.ops.object.join()
    petals_merged = bpy.context.active_object
    petals_merged.name = "PetalsMerged"

    # Quitar el template original (no escalado/posicionado)
    bpy.data.objects.remove(petal_template, do_unlink=True)

    # Mergear petals_merged dentro de rock_obj como segundo material slot.
    # Importante: usar placeholder Materials NOMBRADOS distintos en cada slot.
    # Si dejamos None en ambos, el join de Blender los dedupea en 1 slot y
    # pierde el material_index, mezclando rock y petals en un solo submesh.
    rock_mat_name = "RockSlot_Placeholder"
    petals_mat_name = "PetalsSlot_Placeholder"
    rock_placeholder = bpy.data.materials.get(rock_mat_name) or bpy.data.materials.new(rock_mat_name)
    petals_placeholder = bpy.data.materials.get(petals_mat_name) or bpy.data.materials.new(petals_mat_name)

    rock_obj.data.materials.clear()
    rock_obj.data.materials.append(rock_placeholder)   # slot 0 → rock
    rock_obj.data.materials.append(petals_placeholder) # slot 1 → petals (Unity asigna M_BluePetals aquí)
    for p in rock_obj.data.polygons:
        p.material_index = 0

    petals_merged.data.materials.clear()
    petals_merged.data.materials.append(rock_placeholder)
    petals_merged.data.materials.append(petals_placeholder)
    for p in petals_merged.data.polygons:
        p.material_index = 1

    bpy.ops.object.select_all(action='DESELECT')
    petals_merged.select_set(True)
    rock_obj.select_set(True)
    bpy.context.view_layer.objects.active = rock_obj
    bpy.ops.object.join()
    return len(placed)


def _make_preview_material(name, texture_path=None, tint=(1, 1, 1, 1), luminance_tint=False, alpha_cutout=False, cutoff=0.5):
    """Material para Blender Material Preview que reproduce los 3 modos del
    shader Aline/Standard:
      - Plain texture (rock):   luminance_tint=False, alpha_cutout=False
      - Multiplied tint:        luminance_tint=False con tint != (1,1,1,1)
      - Luminance tint + alpha: luminance_tint=True, alpha_cutout=True (ivy/petals)

    Reemplaza los placeholders sin shading. Permite iterar visualmente en
    Blender (cambiar viewport a 'Material Preview') sin round-trip a BS."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')

    if not (texture_path and _os.path.exists(texture_path)):
        # Sin textura: solo emission del tint
        emission = nt.nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = tint
        nt.links.new(emission.outputs['Emission'], out.inputs['Surface'])
        return mat

    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(texture_path, check_existing=True)

    # Color path: optional luminance conversion + tint multiply
    if luminance_tint:
        bw = nt.nodes.new('ShaderNodeRGBToBW')
        nt.links.new(tex.outputs['Color'], bw.inputs['Color'])
        tint_node = nt.nodes.new('ShaderNodeRGB')
        tint_node.outputs[0].default_value = tint
        mix = nt.nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Fac'].default_value = 1.0
        nt.links.new(bw.outputs['Val'], mix.inputs['Color1'])
        nt.links.new(tint_node.outputs[0], mix.inputs['Color2'])
        color_out = mix.outputs[0]
    elif tint != (1, 1, 1, 1):
        tint_node = nt.nodes.new('ShaderNodeRGB')
        tint_node.outputs[0].default_value = tint
        mix = nt.nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Fac'].default_value = 1.0
        nt.links.new(tex.outputs['Color'], mix.inputs['Color1'])
        nt.links.new(tint_node.outputs[0], mix.inputs['Color2'])
        color_out = mix.outputs[0]
    else:
        color_out = tex.outputs['Color']

    emission = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(color_out, emission.inputs['Color'])

    if alpha_cutout:
        transparent = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix_shader = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(tex.outputs['Alpha'], mix_shader.inputs['Fac'])
        nt.links.new(transparent.outputs['BSDF'], mix_shader.inputs[1])
        nt.links.new(emission.outputs['Emission'], mix_shader.inputs[2])
        nt.links.new(mix_shader.outputs['Shader'], out.inputs['Surface'])
        mat.blend_method = 'CLIP'
        mat.alpha_threshold = cutoff
        mat.shadow_method = 'CLIP'
    else:
        nt.links.new(emission.outputs['Emission'], out.inputs['Surface'])
    return mat


def build_ivy_scatter(rock_obj):
    """Scatter de N copias del IvyFloorDense en grid 2x2 sobre el top del rock,
    rotación Y aleatoria por instancia + scale variation, merged en rock_obj
    como segundo material slot (M_BlueIvy en Unity).

    Cada instancia es un parche denso pre-construido — el scatter solo
    necesita 4-5 copias para cubrir el platform completo, y la rotación
    aleatoria oculta cualquier borde de tile."""
    import random
    rng = random.Random(IVY_SCATTER_SEED)

    pre_names = {o.name for o in bpy.data.objects}
    bpy.ops.import_scene.fbx(filepath=IVY_SOURCE_FBX)
    new_names = [o.name for o in bpy.data.objects if o.name not in pre_names]
    template = next((bpy.data.objects[n] for n in new_names if bpy.data.objects[n].type == 'MESH'), None)
    if template is None:
        for n in new_names:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
        raise RuntimeError("Ivy FBX no contenía mesh importable")

    # Apply transform (mismo fix que en build_petals — el FBX viene con object
    # scale != 1, hay que hornearlo en verts antes de duplicar)
    bpy.ops.object.select_all(action='DESELECT')
    template.select_set(True)
    bpy.context.view_layer.objects.active = template
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Decimate al template ANTES de duplicar — divide tris al ratio configurado
    # en TODAS las copias resultantes. ratio=0.5 reduce a ~half tris,
    # visualmente indistinguible a distancia BS.
    if IVY_DECIMATE_RATIO < 1.0:
        dec_mod = template.modifiers.new(name="DecimateIvy", type='DECIMATE')
        dec_mod.ratio = IVY_DECIMATE_RATIO
        dec_mod.decimate_type = 'COLLAPSE'
        bpy.ops.object.modifier_apply(modifier=dec_mod.name)

    instances = []
    for i, (px, py, pscale) in enumerate(IVY_PATCHES):
        new_obj = template.copy()
        new_obj.data = template.data.copy()
        new_obj.name = f"IvyScatter_{i:02d}"
        bpy.context.collection.objects.link(new_obj)

        new_obj.location = (px, py, IVY_LIFT)
        # Rotación aleatoria solo en Z (yaw) — el mesh es flat, tilt no aporta.
        # El seed deterministico mantiene la layout reproducible entre re-builds.
        yaw_deg = rng.uniform(0, IVY_YAW_JITTER_DEG)
        new_obj.rotation_euler = (0, 0, math.radians(yaw_deg))
        # Scale no-uniforme: XY mantiene cobertura del patch, Z aplasta height
        # para que las leaves tumben planas contra el suelo (petals look).
        new_obj.scale = (pscale, pscale, pscale * IVY_HEIGHT_SCALE)
        instances.append(new_obj)

    # Apply transforms en batch
    bpy.ops.object.select_all(action='DESELECT')
    for inst in instances:
        inst.select_set(True)
    bpy.context.view_layer.objects.active = instances[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Join todas en una sola mesh
    if len(instances) > 1:
        bpy.ops.object.join()
    ivy_merged = bpy.context.active_object
    ivy_merged.name = "IvyMerged"

    bpy.data.objects.remove(template, do_unlink=True)

    # Setup material slots con preview materials (texturas reales + EEVEE
    # nodes que reproducen el shader Aline/Standard). Los nombres siguen el
    # convention "_Placeholder" porque Unity los reasigna al material real
    # del prefab — esto es solo para que Blender Material Preview tenga look.
    rock_placeholder = _make_preview_material(
        "RockSlot_Placeholder",
        texture_path=PREVIEW_ROCK_TEXTURE,
        tint=(1, 1, 1, 1),
        luminance_tint=False,
        alpha_cutout=False,
    )
    ivy_placeholder = _make_preview_material(
        "IvySlot_Placeholder",
        texture_path=PREVIEW_IVY_TEXTURE,
        tint=PREVIEW_IVY_TINT,
        luminance_tint=True,
        alpha_cutout=True,
    )

    rock_obj.data.materials.clear()
    rock_obj.data.materials.append(rock_placeholder)
    rock_obj.data.materials.append(ivy_placeholder)
    for p in rock_obj.data.polygons:
        p.material_index = 0

    ivy_merged.data.materials.clear()
    ivy_merged.data.materials.append(rock_placeholder)
    ivy_merged.data.materials.append(ivy_placeholder)
    for p in ivy_merged.data.polygons:
        p.material_index = 1

    # Join ivy_merged dentro de rock_obj
    bpy.ops.object.select_all(action='DESELECT')
    ivy_merged.select_set(True)
    rock_obj.select_set(True)
    bpy.context.view_layer.objects.active = rock_obj
    bpy.ops.object.join()
    return len(instances)


def build_bush_scatter(rock_obj):
    """Scatter de N bushes pequeños rosa como tercer submesh sobre el rock.
    Mesh source SM_ground_foliage_03 (~64 tris, ~67cm wide × 23cm tall),
    extremadamente ligero. Aporta toques de color y pequeñas protrusiones de
    altura sobre el ivy carpet. Permite overlap con el ivy (los bushes se
    asoman por encima → contraste cromático).

    Posiciones aleatorias deterministas con seed BUSH_SCATTER_SEED, evita
    amontonamiento via min spacing. Asume que rock_obj YA tiene 2 material
    slots (Rock + Ivy) creados por build_ivy_scatter — appende el tercer
    slot (Bush) sin tocar los anteriores."""
    import random
    rng = random.Random(BUSH_SCATTER_SEED)

    pre_names = {o.name for o in bpy.data.objects}
    bpy.ops.import_scene.fbx(filepath=BUSH_SOURCE_FBX)
    new_names = [o.name for o in bpy.data.objects if o.name not in pre_names]
    template = next((bpy.data.objects[n] for n in new_names if bpy.data.objects[n].type == 'MESH'), None)
    if template is None:
        for n in new_names:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
        raise RuntimeError("Bush FBX no contenía mesh importable")

    # Apply transform (mismo fix que ivy/petals — bake scale en verts)
    bpy.ops.object.select_all(action='DESELECT')
    template.select_set(True)
    bpy.context.view_layer.objects.active = template
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Scatter aleatorio dentro del platform (con margen al borde)
    rim_buffer = 1.0
    placed_xy = []
    instances = []
    attempts = 0
    while len(placed_xy) < BUSH_COUNT and attempts < 500:
        attempts += 1
        x = rng.uniform(-(HALF_X - rim_buffer), HALF_X - rim_buffer)
        y = rng.uniform(BUSH_Y_MIN, HALF_Y - rim_buffer)
        too_close = False
        for px, py in placed_xy:
            if (px - x) ** 2 + (py - y) ** 2 < BUSH_MIN_SPACING ** 2:
                too_close = True
                break
        if too_close:
            continue

        z_surface = _sample_top_z(x, y)

        new_obj = template.copy()
        new_obj.data = template.data.copy()
        new_obj.name = f"BushScatter_{len(placed_xy):02d}"
        bpy.context.collection.objects.link(new_obj)

        new_obj.location = (x, y, z_surface + BUSH_LIFT)
        s = rng.uniform(BUSH_SCALE_MIN, BUSH_SCALE_MAX)
        new_obj.scale = (s, s, s)
        yaw = rng.uniform(0, 360)
        tx = rng.uniform(-BUSH_TILT_MAX_DEG, BUSH_TILT_MAX_DEG)
        ty = rng.uniform(-BUSH_TILT_MAX_DEG, BUSH_TILT_MAX_DEG)
        new_obj.rotation_euler = (math.radians(tx), math.radians(ty), math.radians(yaw))
        instances.append(new_obj)
        placed_xy.append((x, y))

    bpy.ops.object.select_all(action='DESELECT')
    for inst in instances:
        inst.select_set(True)
    bpy.context.view_layer.objects.active = instances[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    if len(instances) > 1:
        bpy.ops.object.join()
    bushes_merged = bpy.context.active_object
    bushes_merged.name = "BushesMerged"
    bpy.data.objects.remove(template, do_unlink=True)

    # Append tercer slot al rock_obj (mantener slots 0/1 del ivy intactos).
    bush_mat_name = "BushSlot_Placeholder"
    bush_placeholder = _make_preview_material(
        bush_mat_name,
        texture_path=PREVIEW_BUSH_TEXTURE,
        tint=PREVIEW_BUSH_TINT,
        luminance_tint=True,
        alpha_cutout=True,
    )
    rock_obj.data.materials.append(bush_placeholder)
    bush_slot_idx = len(rock_obj.data.materials) - 1

    # bushes_merged: copiar todos los slots de rock_obj para que el join no
    # cree nuevos slots
    bushes_merged.data.materials.clear()
    for m in rock_obj.data.materials:
        bushes_merged.data.materials.append(m)
    for p in bushes_merged.data.polygons:
        p.material_index = bush_slot_idx

    bpy.ops.object.select_all(action='DESELECT')
    bushes_merged.select_set(True)
    rock_obj.select_set(True)
    bpy.context.view_layer.objects.active = rock_obj
    bpy.ops.object.join()
    return len(instances)


def build_petal_carpet(rock_obj):
    """Duplicar las caras top del rock_obj, levantarlas 1.5cm, y asignarlas
    al material slot 1 (M_BluePetals) con UVs por proyección XY-planar a
    1 UV/metro. La carpet sigue exactamente el relief del rock (incluida la
    parte plana del corredor) y el tiling fino se controla via _MainTex_ST
    en el material — así iteramos densidad sin re-exportar mesh.

    Reemplaza el approach de scatter de clusters discretos: ~5K polys de
    carpet vs ~21K polys que generaban 22 clusters, y produce cobertura
    visual continua tipo E33 en lugar de "puntitos esparcidos"."""
    import bmesh as _bmesh

    # rock_obj viene de build() y aún no tiene material slots asignados.
    # Crear los placeholders nombrados aquí (mismo patrón que build_petals).
    rock_mat_name = "RockSlot_Placeholder"
    petals_mat_name = "PetalsSlot_Placeholder"
    rock_placeholder = bpy.data.materials.get(rock_mat_name) or bpy.data.materials.new(rock_mat_name)
    petals_placeholder = bpy.data.materials.get(petals_mat_name) or bpy.data.materials.new(petals_mat_name)
    rock_obj.data.materials.clear()
    rock_obj.data.materials.append(rock_placeholder)
    rock_obj.data.materials.append(petals_placeholder)
    for p in rock_obj.data.polygons:
        p.material_index = 0

    bm = _bmesh.new()
    bm.from_mesh(rock_obj.data)

    # Caras top: normal apuntando hacia arriba (Z+ en Blender). Threshold 0.5
    # captura la zona superior incluyendo perimetro inclinado, pero excluye
    # paredes verticales del borde.
    top_faces = [f for f in bm.faces if f.normal.z > 0.5]

    duplicated = _bmesh.ops.duplicate(bm, geom=top_faces)
    new_faces = [g for g in duplicated['geom'] if isinstance(g, _bmesh.types.BMFace)]
    new_verts = {g for g in duplicated['geom'] if isinstance(g, _bmesh.types.BMVert)}

    CARPET_LIFT = 0.015  # 1.5cm sobre el rock para evitar z-fight
    for v in new_verts:
        v.co.z += CARPET_LIFT

    # Asignar al slot 1 (petals)
    for f in new_faces:
        f.material_index = 1

    # UVs: proyección XY-planar a 1 UV/metro. El _MainTex_ST del material
    # controla cuántas veces tilea el atlas por metro.
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        uv_layer = bm.loops.layers.uv.new()
    for f in new_faces:
        for loop in f.loops:
            loop[uv_layer].uv = (loop.vert.co.x, loop.vert.co.y)

    bm.to_mesh(rock_obj.data)
    bm.free()

    return len(new_faces)


def finalize(obj):
    """Espejo en Y al final del pipeline. La build construye el corredor sobre
    +Y en Blender, pero el combo de export (bake_space_transform=True +
    axis_forward='-Z') mapea Blender +Y a Unity -Z (espalda del jugador).
    Negar Y aquí garantiza que el corredor caiga en Unity +Z (hacia Aline)."""
    import bmesh as _bmesh
    bm = _bmesh.new()
    bm.from_mesh(obj.data)
    for v in bm.verts:
        v.co.y = -v.co.y
    _bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def export(obj):
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    prev_hidden = {}
    for ob in bpy.context.scene.objects:
        if ob.name != obj.name:
            prev_hidden[ob.name] = (ob.hide_viewport, ob.hide_select)
            ob.hide_viewport = True

    # No backup .bak — el build es reproducible deterministicamente desde
    # este script y los archivos .bak ensucian el AssetDatabase de Unity
    # creando .meta orfans.

    bpy.ops.export_scene.fbx(
        filepath=EXPORT_PATH,
        use_selection=True,
        object_types={'MESH'},
        use_mesh_modifiers=True,
        mesh_smooth_type='OFF',
        apply_scale_options='FBX_SCALE_NONE',
        # bake_space_transform=True hornea la conversión Blender Z-up → Unity Y-up
        # en los vértices. Sin esto, Unity 2019.4 importa la mesh como pared
        # vertical (Y-extent grande) en vez de como suelo (Z-extent grande).
        bake_space_transform=True,
        axis_forward='-Z',
        axis_up='Y',
        apply_unit_scale=True,
        use_space_transform=True,
        use_custom_props=False,
    )

    for name, (hv, hs) in prev_hidden.items():
        ob = bpy.data.objects.get(name)
        if ob:
            ob.hide_viewport = hv
            ob.hide_select = hs


if __name__ == "__main__":
    o = build()
    ivy_count = build_ivy_scatter(o)
    bush_count = build_bush_scatter(o)
    # build_petals y build_petal_carpet quedan definidos pero NO se llaman:
    # build_petals → futuro scatter discreto si lo necesitamos
    # build_petal_carpet → approach abandonado de duplicate-rock-top + tile-shader
    finalize(o)
    export(o)
    me = o.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    print(f"[build_rock_platform] verts={len(me.vertices)} polys={len(me.polygons)} ivy={ivy_count} bushes={bush_count} mat_slots={len(me.materials)}")
    print(f"[build_rock_platform] X {min(xs):.2f}..{max(xs):.2f}  Y {min(ys):.2f}..{max(ys):.2f}  Z {min(zs):.2f}..{max(zs):.2f}")
    print(f"[build_rock_platform] exported {EXPORT_PATH}")
