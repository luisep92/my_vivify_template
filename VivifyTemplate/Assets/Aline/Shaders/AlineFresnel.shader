// Aline/Fresnel — masked cutout cuya MÁSCARA es un fresnel (rim opaco en
// silueta, transparente al frente). Aproxima el M_Curator_BlackPart de UE
// usado por MI_Curator_Aline_BlackPart (vestido) y _BlackPart1 (cuerpo negro).
//
// El shader es unlit — BS no manda luces a los bundles de Vivify, así que
// la "iluminación" del rim viene 100% del fresnel angular (NdotV).
// `_BumpMap` se sample para perturbar la normal y dar variación al rim
// (de otra forma sería un anillo perfectamente liso). `_OpacityMask` es
// opcional: el slot Curator_Dress lo usa, el Curator_Black_Body no.
//
// Mapping desde MaterialInstanceConstant (UE) a properties (Unity):
//   Alpha              → _Alpha
//   Fresnel            → _FresnelExponent
//   |FresnelR|         → _RimBoost   (UE usa negativos para potenciar el rim)
//   Normal             → _BumpMap
//   Opacity_Mask       → _OpacityMask + USE_OPACITY_MASK keyword
Shader "Aline/Fresnel"
{
    Properties
    {
        _Color ("Tint (UE BlackPart = negro)", Color) = (0,0,0,1)
        _BumpMap ("Normal Map", 2D) = "bump" {}
        _OpacityMask ("Opacity Mask (optional)", 2D) = "white" {}
        [Toggle(USE_OPACITY_MASK)] _UseOpacityMask ("Use Opacity Mask", Float) = 0
        _Alpha ("Alpha (UE: Alpha)", Range(0,2)) = 0.35
        _FresnelExponent ("Fresnel Exponent (UE: Fresnel)", Range(0.05, 8)) = 0.5
        _RimBoost ("Rim Boost (UE: |FresnelR|)", Range(0.1, 8)) = 2.0
        _AlphaCutoff ("Alpha Cutoff", Range(0,1)) = 0.333
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
            #pragma multi_compile_local _ USE_OPACITY_MASK

            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float4 tangent : TANGENT;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                float3 worldNormal : TEXCOORD1;
                float4 worldTangent : TEXCOORD2; // w = bitangent sign
                float3 worldPos : TEXCOORD3;
                float4 vertex : SV_POSITION;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            sampler2D _BumpMap;  float4 _BumpMap_ST;
            sampler2D _OpacityMask;
            fixed4 _Color;
            float _Alpha;
            float _FresnelExponent;
            float _RimBoost;
            float _AlphaCutoff;

            v2f vert (appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_OUTPUT(v2f, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);

                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _BumpMap);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                float3 wTangent = UnityObjectToWorldDir(v.tangent.xyz);
                o.worldTangent = float4(wTangent, v.tangent.w * unity_WorldTransformParams.w);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                // Reconstruir normal en world space desde tangent + normal map.
                float3 N = normalize(i.worldNormal);
                float3 T = normalize(i.worldTangent.xyz);
                float3 B = normalize(cross(N, T) * i.worldTangent.w);
                float3 nTan = UnpackNormal(tex2D(_BumpMap, i.uv));
                float3 worldN = normalize(nTan.x * T + nTan.y * B + nTan.z * N);

                float3 V = normalize(_WorldSpaceCameraPos - i.worldPos);
                float NdotV = saturate(dot(worldN, V));

                // Edge-fresnel: 1 en silueta, 0 en frente. Exponente bajo (<1)
                // ensancha el rim hacia el centro; exponente alto (>1) lo
                // estrecha contra el contorno.
                float fresnel = pow(1.0 - NdotV, _FresnelExponent);

                // RimBoost actúa como ganancia: amplifica el rim para que pase
                // el AlphaCutoff incluso con _Alpha bajo.
                float alpha = saturate(fresnel * _RimBoost * _Alpha);

                #ifdef USE_OPACITY_MASK
                    fixed mask = tex2D(_OpacityMask, i.uv).r;
                    alpha *= mask;
                #endif

                clip(alpha - _AlphaCutoff);
                return fixed4(_Color.rgb, alpha);
            }
            ENDCG
        }
    }
}
