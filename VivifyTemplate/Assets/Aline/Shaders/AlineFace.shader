// Aline/Face — translucent + opacity mask para el slot Curator_Aline_Hole.
//
// Aproxima el M_CuratorFace de UE: una capa translucent sobre la zona
// de la cara que usa una mask (Mask_Curator_Aline) para definir el
// "agujero de void" característico del personaje.
//
// El original tiene un graph con RadialGradient + HueShift + rotaciones;
// aquí simplificamos a `tint × mask.r × alpha` y sumamos un radial fade
// opcional (Radius/Hardness) que aproxima el efecto "void" sin recrear
// el grafo entero. Aún hay margen para sumar offset+rotation de UV si
// la mask aparece descentrada respecto a la malla de la cara.
Shader "Aline/Face"
{
    Properties
    {
        _Color ("Tint (UE: BaseColor)", Color) = (0,0,0,1)
        _MainTex ("Mask Face (sample R)", 2D) = "white" {}
        _Alpha ("Alpha (UE: Alpha)", Range(0, 3)) = 1.5
        // UV transform — el original UE reposiciona+escala el mask sample
        // antes de aplicarlo (Offset, ScaleUVsByCenter, EasyRotate). Sin
        // esto la malla de la cara muestrea solo el centro brillante y
        // queda full opaque. Mapping a UE: _UVOffset = -Offset.
        _UVScale ("UV Scale (zoom out >1)", Range(0.1, 8)) = 2.0
        _UVOffset ("UV Offset (UE: -Offset)", Vector) = (0,0,0,0)
        _UVAngleDeg ("UV Angle (deg)", Range(-180, 180)) = 0
        [Toggle(USE_RADIAL_FADE)] _UseRadialFade ("Use Radial Fade", Float) = 0
        _Radius ("Radial Radius (UE: Radius)", Range(0.05, 1)) = 0.42
        _Hardness ("Radial Hardness", Range(0.01, 1)) = 0.25
    }
    SubShader
    {
        Tags {
            "RenderType"="Transparent"
            "Queue"="Transparent"
        }

        Cull Off
        ZWrite Off
        Blend SrcAlpha OneMinusSrcAlpha

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_local _ USE_RADIAL_FADE

            #include "UnityCG.cginc"

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
            fixed4 _Color;
            float _Alpha;
            float _UVScale;
            float4 _UVOffset;
            float _UVAngleDeg;
            float _Radius;
            float _Hardness;

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
                // Recentrar UV alrededor de (0.5, 0.5), aplicar rotación,
                // escala (zoom-out >1) y offset, luego volver a UV-space.
                // _UVScale > 1 → muestreamos un área MAYOR del texture
                // (el mesh ve también el negro alrededor del blob central
                // de la mask). Multiplicar la UV centrada, no dividir.
                float2 uv = i.uv - 0.5;
                float a = radians(_UVAngleDeg);
                float ca = cos(a), sa = sin(a);
                uv = float2(uv.x * ca - uv.y * sa, uv.x * sa + uv.y * ca);
                uv *= _UVScale;
                uv += 0.5 + _UVOffset.xy;

                fixed4 sample = tex2D(_MainTex, uv);
                // UE masks vary on which channel carries data; usamos R
                // por defecto pero alpha también es plausible.
                float mask = max(sample.r, sample.a);

                float alpha = saturate(mask * _Alpha);

                #ifdef USE_RADIAL_FADE
                    float2 c = i.uv - 0.5;
                    float dist = length(c);
                    float radial = 1.0 - smoothstep(_Radius - _Hardness, _Radius, dist);
                    alpha *= radial;
                #endif

                return fixed4(_Color.rgb, alpha);
            }
            ENDCG
        }
    }
}
