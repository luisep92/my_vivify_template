# Events

Custom events added by Vivify.

## Materials

### Property Types

- **Texture**: Must be a string that is a direct path file to a texture.
- **Float**: May either be a direct value (`#!json "value": 10.4`) or a point definition (`#!json "value": [[0,0], [10, 1]]`).
- **Color**: May either be an RGBA array (`#!json "value": [0, 1, 0, (optional) 1]`) or a point definition (`#!json "value": [1, 0, 0, 0, 0.2], [0, 0, 1, 0, 0.6]`).
- **Vector**: May either be an array (`#!json "value": [0, 1, 0, 1]`) or a point definition (`#!json "value": [1, 0, 0, 0, 0.2], [0, 0, 1, 0, 0.6]`).
- **Keyword**: May either be a direct value (`#!json "value": true`) or a point definition (`#!json "value": [[0,0], [1, 1]]`) where values equal to or greater than 1 will enable the keyword.

!!! example
    ```json
    {
      "b": 3.0,
      "t": "SetMaterialProperty",
      "d": {
        "asset": "assets/screens/glitchmat.mat",
        "duration": 8,
        "properties": [{
          "id": "_Juice",
          "type": "Float",
          "value": [
            [0.02, 0],
            [0.04, 0.1875, "easeStep"],
            [0.06, 0.375, "easeStep"],
            [0.08, 0.5, "easeStep"],
            [0.1, 0.625, "easeStep"],
            [0.12, 0.75, "easeStep"]
          ]
        }]
      }
    }
    ```

### SetMaterialProperty

```json
{
  "b": float, // Time in beats.
  "t": "SetMaterialProperty",
  "d": {
    "asset": string, // File path to the desired material.
    "duration": float, // The length of the event in beats. Defaults to 0.
    "easing": string, // An easing for the animation to follow. Defaults to "easeLinear".
    "properties": [{
      "id": string, // Name of the property on the material.
      "type": string, // Type of the property (Texture, Float, Color, Vector, Keyword).
      "value": value/point definition // What to set the property to, type varies depending on property type.
    }]
  }
}
```

Allows setting material properties, e.g. Texture, Float, Color, Vector, Keyword.

### SetGlobalProperty

```json
{
  "b": float, // Time in beats.
  "t": "SetGlobalProperty",
  "d": {
    "duration": float, // The length of the event in beats. Defaults to 0.
    "easing": string, // An easing for the animation to follow. Defaults to "easeLinear".
    "properties": [{
      "id": string, // Name of the property.
      "type": string, // Type of the property (Texture, Float, Color, Vector, Keyword).
      "value": value/point definition // What to set the property to, type varies depending on property type.
    }]
  }
}
```

Allows setting global shader properties, e.g. Texture, Float, Color, Vector, Keyword.

### Blit

```json
{
  "b": float, // Time in beats.
  "t": "Blit",
  "d": {
    "asset": string, // (Optional) File path to the desired material. If missing, will just copy from source to destination without anything special.
    "priority": int, // (Optional) Which order to run current active post processing effects. Higher priority will run first. Default = 0
    "pass": int, // (Optional) Which pass in the shader to use. Will use all passes if not defined.
    "order": string, // (Optional) BeforeMainEffect, AfterMainEffect. Whether to activate before the main bloom effect or after. Defaults fo AfterMainEffect
    "source": string, // (Optional) Which texture to pass to the shader as "_MainTex". "_Main" is reserved for the camera. Default = "_Main"
    "destination": string, // (Optional) Which render texture to save to. Can be an array. "_Main" is reserved for the camera. Default = "_Main"
    "duration": float, // (Optional) How long will this material be applied. Defaults to 0
    "easing": string, // (Optional) See SetMaterialProperty.
    "properties": ? // (Optional) See SetMaterialProperty.
  }
}
```

Blit a texture to another texture using a material. A duration of 0 will run for exactly one frame. If a destination is the same as
source, a temporary render texture will be created as a buffer.

This event allows you to call a [SetMaterialProperty](#setmaterialproperty) from within.
!!! example
    ```json
    {
      "b": 73.0,
      "t": "Blit",
      "d": {
        "asset": "assets/shaders/tvdistortmat.mat",
        "duration": 32,
        "properties": [
          {
            "id": "_Juice",
            "type": "Float",
            "value": 0.2
          }
        ]
      }
    }
    ```

## Camera

### CreateCamera

```json
{
  "b": float, // Time in beats.
  "t": "CreateCamera",
  "d": {
    "id": string, // Id of the camera.
    "texture": string, // (Optional) Will render to a new texture set to this key.
    "depthTexture": string, // (Optional) Renders just the depth to this texture.
    "properties": ? // (Optional) See SetCameraProperty
  }
}
```

Creates an additional camera that will render to the desired texture. Useful for creating a secondary texture where a certain track is culled.

!!! danger
    `CreateCamera` has a significant performance increase as each camera must render your scene again. Be careful about using this event and use `DestroyObject` to destroy the cameras after using them.

!!! example
    Example where notes are not rendered on the right side of the screen.
    === "JSON"
        ```json
        {
          "b": 0.0,
          "t": "CreateCamera",
          "d": {
            "id": "NotesCam",
            "texture": "_Notes",
            "depthTexture": "_Notes_Depth",
            "properties": {
              "culling": {
                "track": "allnotes",
                "whitelist": true,
              },
              "depthTextureMode": ["Depth"]
            }
          }
        }
        ```
    === "Shader"
        ```csharp
        UNITY_DECLARE_SCREENSPACE_TEXTURE(_Notes);

        fixed4 frag(v2f i) : SV_Target
        {
          UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
          if (i.uv.x > 0.5)
          {
            return UNITY_SAMPLE_SCREENSPACE_TEXTURE(_Notes, UnityStereoTransformScreenSpaceTex(i.uv));
          }
          else {
            return UNITY_SAMPLE_SCREENSPACE_TEXTURE(_MainTex, UnityStereoTransformScreenSpaceTex(i.uv));
          }
        }
        ```

### SetCameraProperty

```json
{
  "b": float, // Time in beats.
  "t": "SetCameraProperty",
  "d": {
    "id": string, // (Optional) Id of camera to affect. Default to "_Main".
    "properties": {
      "depthTextureMode": [], // (Optional) Sets the depth texture mode on the camera. Can be [Depth, DepthNormals, MotionVectors].
      "clearFlags": string, // (Optional) Can be [Skybox, SolidColor, Depth, Nothing]. See https://docs.unity3d.com/ScriptReference/CameraClearFlags.html
      "backgroundColor": [], // (Optional) [R, G, B, (Optional) A] Color to clear screen with. Only used with SolidColor clear flag.
      "culling": { // (Optional) Sets a culling mask where the selected tracks are culled
          "track": string/string[], // Name(s) of your track(s). Everything on the track(s) will be added to this mask.
          "whitelist": bool // (Optional) When true, will cull everything but the selected tracks. Defaults to false.
      },
      "bloomPrePass": bool, // (Optional) Enable or disable the bloom pre pass effect.
      "mainEffect": bool // (Optional) Enable or disable the main bloom effect.
    }
  }
}
```

Used to set properties on the main camera or cameras created through `CreateCamera`
Setting any field to `null` will return it to its default. Remember to clear the `depthTextureMode` to `null` after you are done using it as rendering a depth texture can impact performance. See [Output a depth texture from a camera](https://docs.unity3d.com/Manual/SL-CameraDepthTexture.html) for more info.
!!! note
    If the player has the Smoke option enabled, the `depthTextureMode` will always have `Depth`.

## CreateScreenTexture

```json
{
  "b": float, // Time in beats.
  "t": "CreateScreenTexture",
  "d": {
    "id": string, // Name of the texture
    "xRatio": float, // (Optional) Number to divide width by, i.e. on a 1920x1080 screen, an xRatio of 2 will give you a 960x1080 texture.
    "yRatio": float, // (Optional) Number to divide height by.
    "width": int, // (Optional) Exact width for the texture.
    "height": int, // (Optional) Exact height for the texture.
    "colorFormat": string, // (Optional) https://docs.unity3d.com/ScriptReference/RenderTextureFormat.html
    "filterMode": string // (Optional) https://docs.unity3d.com/ScriptReference/FilterMode.html
  }
}
```

Declares a RenderTexture to be used anywhere. They are set as a global variable and can be accessed by declaring a
sampler named what you put in "id".

!!! example
    Here we declare a texture called "snapshot", capture a single frame at 78.0, then store it in our new render texture.
    Lastly we destroy the texture (See DestroyObject) after we are done with it to free up any memory it was taking.
    (Realistically, won't provide noticeable boost to performance, but it can't hurt.)
    ```json
    {
      "b": 70.0,
      "t": "CreateScreenTexture",
      "d": {
        "id": "snapshot"
      }
    },
    {
      "b": 78.0,
      "t": "Blit",
      "d": {
        "destination": "snapshot"
      }
    },
    {
      "b": 120.0,
      "t": "DestroyObject",
      "d": {
        "id": "snapshot"
      }
    }
    ```

## InstantiatePrefab

```json
{
  "b": float, // Time in beats.
  "t": "InstantiatePrefab",
  "d": {
    "asset": string, // File path to the desired prefab.
    "id": string, // (Optional) Unique id for referencing prefab later. Random id will be given by default.
    "track": string, // (Optional) Track to animate prefab transform.
    "position": vector3, // (Optional) Set position.
    "localPosition": vector3, // (Optional) Set localPosition.
    "rotation": vector3, // (Optional) Set rotation (in euler angles).
    "localRotation": vector3, // (Optional) Set localRotation (in euler angles).
    "scale": vector3 //(Optional) Set scale.
  }
}
```

Instantiates a prefab in the scene. If left-handed option is enabled, then the position, rotation, and scale will be
mirrored.

## DestroyObject

```json
{
  "b": float, // Time in beats.
  "t": "DestroyObject",
  "d": {
    "id": string/string[], // Id(s) of object to destroy.
  }
}
```

Destroys an object in the scene. Can be a prefab, camera, or texture id.

It is important to destroy any cameras created through `CreateCamera` because the scene
will have to be rendered again for each active camera.

## SetAnimatorProperty

```json
{
  "b": float, // Time in beats.
  "t": "SetAnimatorProperty",
  "d": {
    "id": string, // Id assigned to prefab.
    "duration": float, // (Optional) The length of the event in beats. Defaults to 0.
    "easing": string, // (Optional) An easing for the animation to follow. Defaults to "easeLinear".
    "properties": [{
      "id": string, // Name of the property.
      "type": string, // Type of the property (Bool, Float, Trigger).
      "value": value/point definition // What to set the property to, type varies depending on property type.
    }]
  }
}
```

Allows setting animator properties. This will search the prefab for all Animator components.

Property types:

- **Bool**: May either be a direct value (`#!json "value": true`) or a point definition (`#!json "value": [[0,0], [1, 1]]`). Any value greater than or equal to 1 is true.
- **Float**: May either be a direct value (`#!json "value": 10.4`) or a point definition (`#!json "value": [[0,0], [10, 1]]`).
- **Integer**: May either be a direct value (`#!json "value": 10`) or a point definition (`#!json "value": [[0,0], [10, 1]]`). Value will be rounded.
- **Trigger**: Must be `true` to set trigger or `false` to reset trigger. Can not be a point definition.

## AssignObjectPrefab

```json
{
  "b": float, // Time in beats.
  "t": "AssignObjectPrefab",
  "d": {
    "loadMode": string, // (Optional) How to load the asset (Single, Additive).
    "object": {} // See below
  }
}
```

Assigns prefabs to a specific object. Setting any asset to `null` is equivalent to resetting to the default model. Most
objects will have their per-instance properties set automatically (See section "Adding per-instance properties to GPU
instancing shaders" at [Creating shaders that support GPU instancing](https://docs.unity3d.com/2021.3/Documentation/Manual/gpu-instancing-shader.html)).

- `#!json "loadMode": Single/Additive`
    - `Single`: Clears all loaded prefabs on the object and adds a prefab
    - `Additive`: Adds a prefab to the currently loaded prefabs.
- `#!json "colorNotes"`:
    - `#!json "track": string` Only notes on this track(s) will be affected.
    - `#!json "asset": string` (Optional) File path to the desired prefab. Only applies to directional notes. Sets properties `_Color`, `_Cutout`, and `_CutoutTexOffset`.
    - `#!json "anyDirectionAsset": string` (Optional) Only applies to dot notes. Sets same properties as directional notes.
    - `#!json "debrisAsset": string` (Optional) Applies to cut debris. Sets properties `_Color`, `_Cutout`, `_CutPlane`, and `_CutoutTexOffset`.
- `#!json "burstSliders"`:
    - `#!json "track": string` See above.
    - `#!json "asset": string` (Optional) See above.
    - `#!json "debrisAsset": string` (Optional) See above.
- `#!json "burstSliderElements"`:
    - `#!json "track": string` See above.
    - `#!json "asset": string` (Optional) See above.
    - `#!json "debrisAsset": string` (Optional) See above.
- `#!json "bombNotes"`:
    - `#!json "track": string` See above.
    - `#!json "asset": string` (Optional) See above.
- `#!json "saber"`:
    - `#!json "type": string` Which saber to affect. `Left`, `Right` or `Both`.
    - `#!json "asset": string` (Optional) File path to the desired prefab. Sets property `_Color`.
    - `#!json "trailAsset": string` (Optional) File path to the material to replace the trail. Sets property `_Color` and sets vertex colors for a gradient.
    - `#!json "trailTopPos": vector3` (Optional) Vector3 position of the top of the trail. Defaults to [0, 0, 1]
    - `#!json "trailBottomPos": vector3` (Optional) Vector3 position of the bottom of the trail. Defaults to [0, 0, 0]
    - `#!json "trailDuration": float` (Optional) Age of most distant segment of trail. Defaults to 0.4
    - `#!json "trailSamplingFrequency": int` (Optional) Saber position snapshots taken per second. Defaults to 50
    - `#!json "trailGranularity": int` (Optional) Segments count in final trail mesh. Defaults to 60

!!! example
    Adds a cool particle system to your sabers!
    ```json
    {
      "b": 70.0,
      "t": "AssignObjectPrefab",
      "d": {
        "loadMode": "Additive",
        "saber": {
          "type": "Both",
          "asset": "assets/path/to/cool/particlesystem.prefab"
        }
      }
    }
    ```

## SetRenderingSettings

```json
{
  "b": float, // Time in beats.
  "t": "SetRenderingSettings",
  "d": {
    "duration": float, // (Optional) The length of the event in beats. Defaults to 0.
    "easing": string, // (Optional) An easing for the animation to follow. Defaults to "easeLinear".
    "category": {
        "property": value/point definition // The setting to set
    }
  }
}
```

Allows changing most Unity rendering or quality settings.

Property does not have to be a point definition. When enabling a render setting with a performance cost, remember to disable it after you no longer need it to gain performance back.

Current provided settings:

- `#!json "renderSettings"` [RenderSettings](https://docs.unity3d.com/ScriptReference/RenderSettings.html)
    - `#!json "ambientEquatorColor": color`
    - `#!json "ambientGroundColor": color`
    - `#!json "ambientIntensity": float`
    - `#!json "ambientLight": color`
    - `#!json "ambientMode": 0/1/3/4` Skybox, Trilight, Flat, Custom
    - `#!json "ambientSkyColor": color`
    - `#!json "defaultReflectionMode": 0/1` Skybox, Custom
    - `#!json "defaultReflectionResolution": int`
    - `#!json "flareFadeSpeed": float`
    - `#!json "flareStrength": float`
    - `#!json "fog": 0/1` Bool
    - `#!json "fogColor": color`
    - `#!json "fogDensity": float`
    - `#!json "fogEndDistance": float`
    - `#!json "fogMode": 1/2/3` Linear, Exponential, ExponentialSquared
    - `#!json "fogEndDistance": float`
    - `#!json "haloStrength": float`
    - `#!json "reflectionBounces": int`
    - `#!json "reflectionIntensity": float`
    - `#!json "skybox": string` File path to a material
    - `#!json "subtractiveShadowColor": color`
    - `#!json "sun": string` Id from InstantiatePrefab event, will find the first directional light on the top level GameObject

- `#!json "qualitySettings"`: [QualitySettings](https://docs.unity3d.com/ScriptReference/QualitySettings.html)
    - `#!json "anisotropicFiltering": 0/1/2` Disable, Enable, ForceEnable.
    - `#!json "antiAliasing": 0/2/4/8`
    - `#!json "pixelLightCount": int`
    - `#!json "realtimeReflectionProbes": 0/1` Bool
    - `#!json "shadowCascades": 0/2/4`
    - `#!json "shadowDistance": float`
    - `#!json "shadowmaskMode": 0/1` Shadowmask, DistanceShadowmask
    - `#!json "shadowNearPlaneOffset": float`
    - `#!json "shadowProjection": 0/1` CloseFit, StableFit
    - `#!json "shadowResolution": 0/1/2/3` Low, Medium, High, VeryHigh.
    - `#!json "shadows": 0/1/2` Disable, HardOnly, All.
    - `#!json "softParticles": 0/1` Bool

- `#!json "xrSettings"`: [XRSettings](https://docs.unity3d.com/ScriptReference/XR.XRSettings.html) WARNING: Only works on 2019 versions.
    - `#!json "useOcclusionMesh": 0/1` Bool

!!! example
    ```json
    {
      "b": 70.0,
      "t": "SetRenderingSettings",
      "d": {
        "qualitySettings": {
          "ambientLight": [0, 0, 0, 0]
        }
      }
    }
    ```
