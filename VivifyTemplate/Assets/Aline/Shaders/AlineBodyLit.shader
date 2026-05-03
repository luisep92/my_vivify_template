// Aline/BodyLit — slots Curator_Body / Curator_Body_001 (skin/cuerpo
// principal). BaseColor + Normal map + AO opcional + iluminación SH ambient
// vía AlineLighting.cginc.
//
// La normal map perturba la normal de la malla y la SH ambient (alimentada
// por RenderSettings.ambientLight + skybox del juego) module la luminosidad.
// `SetRenderingSettings` cambia el shading sin tocar el material.
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

        // Iluminación: ambientFloor evita negro absoluto cuando SH=0;
        // ambientStrength escala la SH ambient antes del shading.
        _AmbientFloor ("Ambient Floor", Range(0, 2)) = 0.6
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
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                float3 wTangent = UnityObjectToWorldDir(v.tangent.xyz);
                o.worldTangent = float4(wTangent, v.tangent.w * unity_WorldTransformParams.w);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 base = tex2D(_MainTex, i.uv) * _Color;
                clip(base.a - _AlphaCutoff);

                float3 N = normalize(i.worldNormal);
                float3 T = normalize(i.worldTangent.xyz);
                float3 B = normalize(cross(N, T) * i.worldTangent.w);
                float3 nTan = UnpackNormal(tex2D(_BumpMap, i.uv));
                nTan.xy *= _BumpScale;
                float3 worldN = normalize(nTan.x * T + nTan.y * B + nTan.z * N);

                float ao = lerp(1.0, tex2D(_OcclusionMap, i.uv).r, _OcclusionStrength);

                fixed3 color = AlineShade(worldN, base.rgb, _AmbientFloor, _AmbientStrength) * ao;
                return fixed4(color, base.a);
            }
            ENDCG
        }
    }
}
