// AlineLighting.cginc — modelo de iluminación compartido para los shaders
// custom de Aline. Sustituye el "fake light hardcoded" que cada shader tenía
// por separado.
//
// Vivify bundles no reciben luces dinámicas (no hay forward pass real,
// no hay key light de BS) NI environment probes precomputados (`ShadeSH9`
// devuelve 0 sin GI baking — verificado en BS 2026-05-03). Pero SÍ reciben
// `RenderSettings.ambientMode/ambientLight/ambientSkyColor/...` que Unity
// expone directamente como uniforms `unity_AmbientSky/Equator/Ground`,
// poblados sin GI ni baking.
//
// Sampleamos esos uniforms con un blend Trilight (sky cuando la normal mira
// arriba, equator a horizonte, ground hacia abajo). En modo Flat los uniforms
// Equator/Ground vienen a 0 → caemos a Sky color flat para que la superficie
// no se vaya a negro en sus lados/abajo.
//
// Dos modos de mezcla:
//   AlineShade(N, base, floor, strength)
//      Modulativo: base * (floor + ambient·strength).
//      Para superficies con BaseColor visible (piel, ropa) — el ambient
//      module la luminosidad, manteniendo el color del material.
//
//   AlineRimTint(N, base, fillStrength)
//      Aditivo: base + ambient · fillStrength.
//      Para superficies con BaseColor muy oscuro/negro (BlackPart, void,
//      energy fabric) donde queremos que el ambient les dé un tinte de
//      borde sin volver a la silueta gris/blanca.

#ifndef ALINE_LIGHTING_INCLUDED
#define ALINE_LIGHTING_INCLUDED

float3 AlineSampleAmbient(float3 worldN)
{
    // Trilight blend basado en world.y de la normal.
    float upWeight = saturate(worldN.y);
    float downWeight = saturate(-worldN.y);
    float horizWeight = 1.0 - upWeight - downWeight;

    float3 sky = unity_AmbientSky.rgb;
    // Fallback: si Equator/Ground están a ~0 (modo Flat), reusamos Sky para
    // que el shading no oscurezca lados/abajo a negro.
    float3 equator = unity_AmbientEquator.rgb;
    float3 ground = unity_AmbientGround.rgb;
    float trilightActive = step(0.001, dot(equator + ground, float3(1, 1, 1)));
    equator = lerp(sky, equator, trilightActive);
    ground = lerp(sky, ground, trilightActive);

    return sky * upWeight + equator * horizWeight + ground * downWeight;
}

float3 AlineShade(float3 worldN, float3 base, float ambientFloor, float ambientStrength)
{
    float3 sh = AlineSampleAmbient(worldN) * ambientStrength;
    float3 lighting = ambientFloor + sh;
    return base * lighting;
}

float3 AlineRimTint(float3 worldN, float3 base, float fillStrength)
{
    float3 sh = AlineSampleAmbient(worldN) * fillStrength;
    return base + sh;
}

#endif // ALINE_LIGHTING_INCLUDED
