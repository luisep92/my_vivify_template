// Aline/ParticleSmoke — billboard particle alpha-blend para humo oscuro
// que se ve contra el skybox. Soft circle procedural con gradient de
// alpha hacia el borde. Para "humillo negro" rodeando los rayitos del
// despawn (estilo E33). SPI macros para BS 1.34.2.
Shader "Aline/ParticleSmoke"
{
    Properties
    {
        _TintColor ("Tint Color", Color) = (0.05, 0.05, 0.08, 1)
        _SoftEdge ("Soft Edge", Range(0.01, 1)) = 0.5
        _CoreOpacity ("Core Opacity", Range(0, 1)) = 0.7
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "IgnoreProjector"="True" "PreviewType"="Plane" }
        Cull Off
        ZWrite Off
        Blend SrcAlpha OneMinusSrcAlpha

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
            float _CoreOpacity;

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
                float2 d = i.uv - 0.5;
                float r = length(d) * 2.0;
                // Soft circle: 1 at center, 0 at edge with smooth falloff.
                float mask = 1.0 - smoothstep(1.0 - _SoftEdge, 1.0, r);
                fixed4 col = _TintColor * i.color;
                col.a *= mask * _CoreOpacity;
                return col;
            }
            ENDCG
        }
    }
}
