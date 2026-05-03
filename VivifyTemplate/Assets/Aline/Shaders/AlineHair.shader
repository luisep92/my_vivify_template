// Aline/Hair — cards-based hair, cutout doble-cara.
//
// Hair UE típico se renderiza con cards (planos rectangulares texturizados
// con un atlas de mechones). Aquí: sample atlas Color + sample atlas Mask
// para el alpha test. La mask es separada del color (no es el alpha del PNG)
// porque el ripeo de FModel da la mask como textura R/G/B grayscale aparte.
//
// Usa Cull Off porque las cards son planos sin volumen — la otra cara debe
// verse o se nota el "hueco". Sin keywords (Toggle no sincroniza por API).
//
// Ambient: las cards no tienen normales útiles para el trilight gradient,
// así que sampleamos `unity_AmbientSky.rgb` flat. Mismos parámetros
// `_AmbientFloor`/`_AmbientStrength` que el resto de shaders Aline para
// mantener alineación de comportamiento — un fade out global apaga el
// pelo igual que apaga la skin.
//
// Mapping desde MaterialInstanceConstant (UE → MI_Hair_Aline → padre
// MI_Hair_HighlightsVariation):
//   Diffuse  → _MainTex
//   Alpha    → _AlphaMap
//   (Color Down/Top, Highlights, Rim, etc) → no replicados (PBR shader-only)
Shader "Aline/Hair"
{
    Properties
    {
        _MainTex ("Color (Diffuse)", 2D) = "white" {}
        _AlphaMap ("Alpha Mask", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _AlphaCutoff ("Alpha Cutoff", Range(0,1)) = 0.333
        _AmbientFloor ("Ambient Floor", Range(0, 2)) = 0.0
        _AmbientStrength ("Ambient Strength", Range(0, 4)) = 1.0
    }
    SubShader
    {
        Tags {
            "RenderType"="TransparentCutout"
            "Queue"="AlphaTest"
        }

        Cull Off

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "UnityCG.cginc"
            #include "AlineLighting.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                float4 vertex : SV_POSITION;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            sampler2D _MainTex;  float4 _MainTex_ST;
            sampler2D _AlphaMap;
            fixed4 _Color;
            float _AlphaCutoff;
            float _AmbientFloor;
            float _AmbientStrength;

            v2f vert (appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_OUTPUT(v2f, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed alpha = tex2D(_AlphaMap, i.uv).r;
                clip(alpha - _AlphaCutoff);

                fixed3 base = tex2D(_MainTex, i.uv).rgb * _Color.rgb;
                // Ambient flat (sin normal — cards no tienen orientación útil).
                float3 ambient = unity_AmbientSky.rgb * _AmbientStrength;
                fixed3 color = base * (_AmbientFloor + ambient);
                return fixed4(color, alpha);
            }
        ENDCG
        }
    }
}
