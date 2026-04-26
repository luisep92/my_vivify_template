# Lighting Events

Not to be confused with custom events, these are *vanilla lighting events* that have extra data added to them.

!!! example
    ```json
    "basicBeatmapEvents":[
      {
        "b": 8.0,
        "et": 2,
        "i": 1,
        "f": 1,
        "customData": {
          "color": [1, 0, 1],
        }
      }
    ]
    ```

## Chroma

### Standard Lights

* `#!json "lightID": int` Causes event to only affect specified [ID](https://streamable.com/dhs31). Can be an array.
* `#!json "color": [r, g, b, a]` (floats) Array of RGB values (Alpha is optional and will default to 1 if not specified).
* `#!json "easing": string` Any easing from [easings.net](https://easings.net) (with the addition of easeLinear and easeStep).
* `#!json "lerpType": string` Lerp as `HSV` or `RGB`.![color lerp](../assets/items/ColorLerp.png) (Courtesy of [The Secrets of Colour Interpolation](https://www.alanzucconi.com/2016/01/06/colour-interpolation/)).

### Laser Speed

* `#!json "lockRotation": bool` Set to true and the event it is attached to will not reset laser rotations.
* `#!json "speed": float` Identical to just setting value, but allows for decimals. Will overwrite value (Because the game will randomize laser position on anything other than value 0, a small trick you can do is set value to 1 and _preciseSpeed to 0, creating 0 speed lasers with a randomized position).
* `#!json "direction": int` Set the spin direction (0 left lasers spin CCW, 1 left lasers spin CW).

### Ring Rotation

* `#!json "nameFilter": string` Causes event to only affect rings with a listed name (e.g. SmallTrackLaneRings, BigTrackLaneRings).
* `#!json "rotation": float` Dictates how far the first ring will spin.
* `#!json "step": float` Dictates how much rotation is added between each ring.
* `#!json "prop": float` Dictates the rate at which rings behind the first one have physics applied to them.  High value makes all rings move simultaneously, low value gives them [significant delay](https://streamable.com/vsdr9).
* `#!json "speed": float` Dictates the [speed multiplier of the rings](https://streamable.com/fxlse).
* `#!json "direction": int` Direction to spin the rings (1 spins clockwise, 0 spins counter-clockwise).

### Ring Zoom

* `#!json "step": float` Dictates how much position offset is added between each ring.
* `#!json "speed": float` Dictates how quickly it will move to its new position.
