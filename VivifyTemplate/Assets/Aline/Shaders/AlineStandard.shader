Shader "Aline/Standard"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _AlphaCutoff ("Alpha Cutoff", Range(0,1)) = 0
        [Toggle(LUMINANCE_TINT)] _UseLumTint ("Tinte por luminancia (recolor real, no multiply)", Float) = 0
        // Crop a una subregión del _MainTex (útil para tilear UNA hoja de un atlas).
        // xy = offset, zw = size. Default (0,0,1,1) = sin crop (atlas entero).
        _AtlasRegion ("Atlas Region (xy=offset, zw=size)", Vector) = (0,0,1,1)
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
            #pragma multi_compile_local _ LUMINANCE_TINT

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

            sampler2D _MainTex;
            float4 _MainTex_ST;
            fixed4 _Color;
            float _AlphaCutoff;
            float4 _AtlasRegion;

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
                // Crop el atlas: frac(uv) wrapea el tile a [0,1], luego mapeamos
                // a la región (offset, size). Con _AtlasRegion=(0,0,1,1) es
                // identity y no afecta a materiales que usan textura entera.
                float2 atlas_uv = frac(i.uv) * _AtlasRegion.zw + _AtlasRegion.xy;
                fixed4 src = tex2D(_MainTex, atlas_uv);
                clip(src.a - _AlphaCutoff);
                #ifdef LUMINANCE_TINT
                    // Modo recolor: usa el brillo del pixel original como factor,
                    // y _Color como hue final. Permite tintear texturas warmtone
                    // (verdes, marrones) a colores radicalmente distintos sin
                    // perder la variación de brillo del atlas. Coeficientes Rec. 709.
                    half lum = dot(src.rgb, half3(0.2126, 0.7152, 0.0722));
                    return fixed4(lum * _Color.rgb, src.a);
                #else
                    return src * _Color;
                #endif
            }
            ENDCG
        }
    }
}
