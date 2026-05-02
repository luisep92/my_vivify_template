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

    # Espejo en Y. La build coloca el corredor sobre +Y en Blender, pero el
    # combo de export (bake_space_transform=True + axis_forward='-Z') mapea
    # Blender +Y a Unity -Z (espalda del jugador). Negar Y aquí garantiza que
    # el corredor caiga en Unity +Z (hacia Aline) sin tocar opciones de export.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for v in bm.verts:
        v.co.y = -v.co.y
    # Voltear la orientación de las caras para mantener normales correctas tras el flip
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()

    obj.location = (0, 0, 0)
    return obj


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

    if os.path.exists(EXPORT_PATH):
        shutil.copy2(EXPORT_PATH, EXPORT_PATH + ".bak")

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
    export(o)
    me = o.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    print(f"[build_rock_platform] verts={len(me.vertices)} polys={len(me.polygons)}")
    print(f"[build_rock_platform] X {min(xs):.2f}..{max(xs):.2f}  Y {min(ys):.2f}..{max(ys):.2f}  Z {min(zs):.2f}..{max(zs):.2f}")
    print(f"[build_rock_platform] exported {EXPORT_PATH}")
