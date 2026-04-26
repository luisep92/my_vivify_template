# Environment Enhancements

From simply removing a logo to creating completely hand modelled scenes, Chroma does it all with its environment tools.

!!! tip
    Set `#!json "PrintEnvironmentEnhancementDebug": true` in the `Chroma.json` config file to print extra environment enhancement information to your console.

## Adding Commands

Environments are modified by a list of "commands" in the `"environment"` array. The commands are ran sequentially at the beginning of the map, and each one will find an object(s) using the id and lookup method, and then set the properties on them.

* `#!json "customData"` -> `#!json "environment"` (array)
    * `#!json "id": string` The ID to use when looking up the GameObject.
    * `#!json "lookupMethod": "Regex"/"Exact"/"Contains"/"StartsWith"/"EndsWith"` How to use the ID to search. Regex allows for the greatest control, such as future-proofing by using wildcards.
    * `#!json "duplicate": int` How many instances of this GameObject to duplicate. This changes the scope of the command and all the following properties will affect the duplicated objects instead.
    * `#!json "active": bool` When false, disables the GameObject.
    * `#!json "scale": [x, y, z]` (floats) Sets scale of GameObject.
    * `#!json "position": [x, y, z]` (floats) Sets position of GameObject.
    * `#!json "localPosition": [x, y, z]` (floats) Sets localPosition of GameObject.
    * `#!json "rotation": [x, y, z]` (floats) Sets rotation of GameObject.
    * `#!json "localRotation": [x, y, z]` (floats) Sets localRotation of GameObject.
    * `#!json "track": string/string[]` Adds the object to a track, allowing you to animate it. See [TransformController](#transformcontroller)
    * `#!json "components": object`: See below.

All of the custom data is stored in the difficulty's json.
!!! example
    ```json
    "version": "3.0.0",
    "customData": {
      "environment": [
        {
          "id": "^.*\\[\\d*[13579]\\]BigTrackLaneRing\\(Clone\\)$",
          "lookupMethod": "Regex",
          "scale": [0.1, 0.1, 0.1]
        }
      ]
    }
    ```

### Components

Allows you to change fields of components found on game objects.

* `#!json "environment"` -> `#!json "components"`
    * `component name`: The name of the component to look for.
        * `field`: The field of the component to affect.

Available components:

* `#!json "ILightWithId"`
    * `#!json "lightID": int`: Which ID to assign. For use with the `lightID` tag for lighting events (Cannot be animated)
    * `#!json "type": int`: Which event type to active on. (Cannot be animated)
* `#!json "BloomFogEnvironment"`: Will always be found on the `[0]Environment` object.
    * `#!json "attenuation": float`: attenuation is the fog density. logarithmic
    * `#!json "offset": float`: offset I have no idea
    * `#!json "startY": float`: startY is starting Y of the gradient thing
    * `#!json "height": float`: height is the gradient length of the dissolving plane fog
* `#!json "TubeBloomPrePassLight"`
    * `#!json "colorAlphaMultiplier": float`
    * `#!json "bloomFogIntensityMultiplier": float`

!!! example
    ```json
    {
      "id": "DragonsEnvironment.[0]Environment",
      "lookupMethod": "Exact",
      "components": {
        "BloomFogEnvironment": {
          "attenuation": 0.2
        }
      }
    },
    ```

Additionally, components can be animated using the [`AnimateComponent`](../animation/additional-events.md#animatecomponent) custom event.

### TransformController

Any GameObject assigned a track will automatically be assigned a `TransformController`. This is a standard Component which will follow `position`, `localPosition`, `rotation`, `localRotation`, and `scale` properties on a Track. These are the standard Unity properties on a Transform.

!!! note
    Because `position` and `localPosition` both control position (and similarly for rotation), only one of them can be set. If you attempt to set both at the same time, only `localPosition` will be set.

## Geometry

*Tired of only being able to move existing objects?* **Geometry** allows you to create your own primitive shapes. Instead of defining `"id"` and `"lookupMethod"`, use `"geometry"`.

```json
"version": "3.0.0",
"customData": {
  "environment": [
    {
      "geometry": {
        "type": "Cylinder",
        "material": {
          "color": [0, 1, 0, 0],
          "shader": "Standard",
        }
      },
      "scale": [0.1, 0.1, 0.1],
      "track": "cylindertrack"
    }
  ]
}
```

* `#!json "environment"` -> `#!json "geometry"`
    * `#!json "type": string` What kind of primitive to create. (Sphere, Capsule, Cylinder, Cube, Plane, Quad, Triangle)
    * `#!json "material": string/object` What material to assign the object. Can be referred to by name to reuse, or defined here.
    * `#!json "collision": bool` Whether or not the object has a collider. Useful if you want note debris to bounce off.

### Material

* `#!json "color": [r, g, b, a]` (floats)
* `#!json "shader": "Standard"/"OpaqueLight"/"TransparentLight"/"Glowing"/"BaseWater"/"BTSPillar"/"BillieWater"/"WaterfallMirror"/"InterscopeConcrete"/"InterscopeCar"` What shader to use. OpaqueLight and TransparentLight will create a TubeBloomPrePassLightWithId and TubeBloomPrePassLight and can be controlled by standard lighting events. TransparentLight will be invisible when the light is turned off.
* `#!json "track": string` Assign the material to a track, allowing you to animate the `color`.
* `#!json "shaderKeywords": string[]` By default, each shader has its default keywords. This allows overwriting the keywords of the shader.
!!! danger
    The Standard/BTSPillar shader has changed in BS v1.38, setting it to empty shaderKeywords no longer makes it appear full bright. Chroma will automatically change these to Glowing and set the color alpha to 0 when using an empty array to attempt to replicate the previous behavior on old maps.
![Keyword difference](../assets/environment/shaderKeyword.png)

!!! tip
    Every object needs a material, however creating materials can be laggy! The best way to assign materials is to create one initially, and then reuse it whenever you need one. It is recommended you reuse materials whenever possible as it is the most performant way of creating many geometry objects.
      ```json hl_lines="12 19"
      "customData": {
        "materials": {
          "green standard": {
            "color": [0, 1, 0, 0],
            "shader": "Standard"
          }
        },
        "environment": [
          {
            "geometry": {
              "type": "Cylinder",
              "material": "green standard"
            },
            "scale": [0.1, 0.1, 0.1],
          },
          {
            "geometry": {
              "type": "Sphere",
              "material": "green standard"
            },
            "position": [1, 1, 1]
          }
        ]
      }
      ```
