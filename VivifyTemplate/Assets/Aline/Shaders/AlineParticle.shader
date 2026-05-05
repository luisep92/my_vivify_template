// Aline/Particle — billboard particle shader, additive HDR.
// Para ParticleSystemRenderer en Billboard mode. Maneja vertex color
// per-particle (modulado por StartColor del PS) + máscara circular
// procedural desde UV (sin texture). SPI macros para BS 1.34.2.
Shader "Aline/Particle"
{
    Properties
    {
        [HDR] _TintColor ("Tint Color (HDR)", Color) = (1, 1, 1, 1)
        _SoftEdge ("Soft Edge", Range(0.01, 0.5)) = 0.2
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "IgnoreProjector"="True" "PreviewType"="Plane" }
        Cull Off
        ZWrite Off
        Blend SrcAlpha One

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float4 color : COLOR;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2f
            {
                float4 position : SV_POSITION;
                float4 color : COLOR;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            fixed4 _TintColor;
            float _SoftEdge;

            v2f vert(appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_OUTPUT(v2f, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.position = UnityObjectToClipPos(v.vertex);
                o.color = v.color;
                o.uv = v.uv;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                // Procedural circular mask from UV (centered at 0.5, 0.5).
                float2 d = i.uv - 0.5;
                float r = length(d) * 2.0; // 0 at center, 1 at edge of unit quad
                // Smooth falloff at the edge using _SoftEdge as the inner radius of the falloff band.
                float alpha = 1.0 - smoothstep(1.0 - _SoftEdge, 1.0, r);
                fixed4 col = _TintColor * i.color;
                col.a *= alpha;
                return col;
            }
            ENDCG
        }
    }
}
