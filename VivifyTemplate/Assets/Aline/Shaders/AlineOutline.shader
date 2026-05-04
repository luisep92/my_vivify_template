// Aline/Outline — inverted-hull outline shader para los proyectiles (notes).
// Dos passes: cuerpo opaco (_BodyColor) + casco extruido en back-face (outline).
// SPI-compatible (BS 1.34.2 usa Single Pass Instanced).
//
// Adaptado del tutorial "020 Inverted Hull Unlit" de Ronja (CC-BY 4.0):
// https://www.ronja-tutorials.com/post/020-inverted-hull/
//
// Diferencias vs. el original:
//   - Offset del outline en WORLD space (independiente del scale del transform).
//   - Macros SPI en ambas passes.
//   - Sin _MainTex: la mesh del Default Base no trae UVs.
//   - GPU instancing en ambas passes para que Vivify pase props per-instance
//     automáticamente vía AssignObjectPrefab. Doc heckdocs:
//     "Sets properties _Color, _Cutout, and _CutoutTexOffset" en
//     colorNotes.{asset, anyDirectionAsset, debrisAsset}.
//
// Properties pasadas por Vivify per-instance:
//   _Color   → saber color (rojo si c=0, azul si c=1).
//   _Cutout  → declarado pero sin discard activo. Vivify lo pasa en función de
//              proximidad al player (no de animation.dissolve), lo cual oculta
//              los notes al dispararse — no deseable. Queda como hook para
//              parry / debris futuros.
//
// "Dissolve trick" para ocultar la fase de jump-in:
//   NO se hace en el shader. Se hace en el .dat via animation.scale per-note
//   con primer punto scale=0. Doc Heck: durante el NJS jump-in los objetos
//   "strictly use the first point in the point definition", así que primer
//   punto a (0,0,0) deja el cube invisible durante todo el viaje desde far Z.
//   El pop a scale=1 ocurre just after landing (t≈0.05..0.1 en el note
//   timeline donde t=0=landing, t=0.5=hit, t=1=despawn).
//
// Tuning local:
//   _BodyColor       → cuerpo. Azul muy profundo casi-negro por defecto.
//   _OutlineIntensity → multiplicador HDR. 2.0 ≈ neón punzante con bloom de BS.
//   _OutlineThickness → metros en world space.
Shader "Aline/Outline"
{
    Properties
    {
        _BodyColor ("Body Tint", Color) = (0.005, 0.005, 0.025, 1)
        [HDR] _Color ("Outline Color (per-instance, Vivify)", Color) = (1, 1, 1, 1)
        _OutlineIntensity ("Outline Intensity (HDR mult)", Range(0, 5)) = 2.0
        _OutlineThickness ("Outline Thickness (world m)", Range(0, 0.1)) = 0.02
        _Cutout ("Cutout (per-instance, Vivify)", Range(0, 1)) = 1.0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }

        // ───────── Pass 1: cuerpo ─────────
        Pass
        {
            Cull Back
            ZWrite On

            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2f
            {
                float4 position : SV_POSITION;
                UNITY_VERTEX_OUTPUT_STEREO
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            UNITY_INSTANCING_BUFFER_START(Props)
                UNITY_DEFINE_INSTANCED_PROP(float, _Cutout)
            UNITY_INSTANCING_BUFFER_END(Props)

            fixed4 _BodyColor;

            v2f vert(appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                UNITY_INITIALIZE_OUTPUT(v2f, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);

                o.position = UnityObjectToClipPos(v.vertex);
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                return _BodyColor;
            }
            ENDCG
        }

        // ───────── Pass 2: outline (back-face del casco extruido) ─────────
        Pass
        {
            Cull Front
            ZWrite On

            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2f
            {
                float4 position : SV_POSITION;
                UNITY_VERTEX_OUTPUT_STEREO
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            UNITY_INSTANCING_BUFFER_START(Props)
                UNITY_DEFINE_INSTANCED_PROP(fixed4, _Color)
                UNITY_DEFINE_INSTANCED_PROP(float, _Cutout)
            UNITY_INSTANCING_BUFFER_END(Props)

            float _OutlineIntensity;
            float _OutlineThickness;

            v2f vert(appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                UNITY_INITIALIZE_OUTPUT(v2f, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);

                float3 worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                float3 worldNormal = normalize(UnityObjectToWorldNormal(v.normal));
                worldPos += worldNormal * _OutlineThickness;
                o.position = mul(UNITY_MATRIX_VP, float4(worldPos, 1));
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                fixed4 c = UNITY_ACCESS_INSTANCED_PROP(Props, _Color);
                return c * _OutlineIntensity;
            }
            ENDCG
        }
    }
}
