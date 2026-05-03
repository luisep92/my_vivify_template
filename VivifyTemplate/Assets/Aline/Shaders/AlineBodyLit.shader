// Aline/BodyLit — extensión del Aline/Standard con normal map + AO + fake
// directional shading. Pensado para los slots Curator_Body / Curator_Body_001
// del SK_Curator_Aline (MIs Body_1 y Body_2 en UE: BaseColor + Normal + ORM).
//
// Sigue siendo unlit cutout — los bundles Vivify no reciben luz de la escena
// de BS, así que un shader lit "real" se vería plano. En su lugar fakeamos
// un keylight fijo en world-space; el normal map perturba la normal de la
// malla y el dot(N, L) module el color base. El canal AO del ORM oscurece
// recesos. Roughness/Metallic del ORM se ignoran (sin lighting real no
// significan nada).
//
// Mapping desde MaterialInstanceConstant (UE) a properties (Unity):
//   Base Color Map     → _MainTex
//   Normal Map         → _BumpMap
//   ORM (R=AO,G=R,B=M) → _OcclusionMap (sólo .R se lee)
//   Normal/Bump Mult.  → _BumpScale
Shader "Aline/BodyLit"
{
    Properties
    {
        _MainTex ("Base Color", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _AlphaCutoff ("Alpha Cutoff", Range(0,1)) = 0.333

        _BumpMap ("Normal Map", 2D) = "bump" {}
        _BumpScale ("Normal Scale (UE: Normal/Bump Multiplier)", Range(0, 4)) = 1.5

        _OcclusionMap ("ORM (R=AO)", 2D) = "white" {}
        _OcclusionStrength ("AO Strength", Range(0, 1)) = 1.0

        // Fake key light in world space + ambient floor para no apagar las
        // zonas en sombra. Tweakable per-material para ajustar el "look"
        // por personaje sin tocar shader.
        _LightDir ("Fake Light Dir (world)", Vector) = (0.3, 0.7, -0.6, 0)
        _LightStrength ("Fake Light Strength", Range(0, 1)) = 0.5
        _Ambient ("Ambient Floor", Range(0, 1)) = 0.5
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
                float4 worldTangent : TEXCOORD2;
                float4 vertex : SV_POSITION;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            sampler2D _MainTex;       float4 _MainTex_ST;
            sampler2D _BumpMap;
            sampler2D _OcclusionMap;
            fixed4 _Color;
            float _AlphaCutoff;
            float _BumpScale;
            float _OcclusionStrength;
            float4 _LightDir;
            float _LightStrength;
            float _Ambient;

            v2f vert (appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_OUTPUT(v2f, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);

                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                float3 wTangent = UnityObjectToWorldDir(v.tangent.xyz);
                o.worldTangent = float4(wTangent, v.tangent.w * unity_WorldTransformParams.w);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 base = tex2D(_MainTex, i.uv) * _Color;
                clip(base.a - _AlphaCutoff);

                // Reconstruir normal en world-space desde tangente + normal map.
                float3 N = normalize(i.worldNormal);
                float3 T = normalize(i.worldTangent.xyz);
                float3 B = normalize(cross(N, T) * i.worldTangent.w);
                float3 nTan = UnpackNormal(tex2D(_BumpMap, i.uv));
                nTan.xy *= _BumpScale;
                float3 worldN = normalize(nTan.x * T + nTan.y * B + nTan.z * N);

                // Fake directional light (no real lighting in Vivify bundles).
                // Half-Lambert para que las zonas en sombra no se apaguen del todo.
                float3 L = normalize(_LightDir.xyz);
                float ndotl = saturate(dot(worldN, L));
                float lambert = lerp(_Ambient, 1.0, ndotl);
                float shading = lerp(1.0, lambert, _LightStrength);

                // AO del ORM (R channel).
                float ao = lerp(1.0, tex2D(_OcclusionMap, i.uv).r, _OcclusionStrength);

                fixed3 color = base.rgb * shading * ao;
                return fixed4(color, base.a);
            }
            ENDCG
        }
    }
}
