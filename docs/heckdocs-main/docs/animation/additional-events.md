# Additional Events

These are additional custom events that use tracks and point definitions.

## Noodle Extensions

### AssignTrackParent

```json
{
  "b": float, // Time in beats.
  "t": "AssignTrackParent",
  "d": {
    "childrenTracks": string[], // Array of tracks to parent to _parentTrack.
    "parentTrack": string, // The track you want to animate.
    "worldPositionStays": bool // Defaults to false if not set. See https://docs.unity3d.com/ScriptReference/Transform.SetParent.html
  }
}
```

**`AssignTrackParent`** will create an new GameObject with a [TransformController](../environment/environment.md#transformcontroller) and parent any number of children tracks to it.

### AssignPlayerToTrack

```json
{
  "b": float, // Time in beats.
  "t": "AssignPlayerToTrack",
  "d": {
    "track": string, // The track you wish to assign the player to.
    "target": string // (optional) The specific player object you wish to target.
  }
}
```

**`AssignPlayerToTrack`** will assign the player a [TransformController](../environment/environment.md#transformcontroller).
Available targets are `Root`, `Head`, `LeftHand`, and `RightHand`.

!!! warning
    It is recommended to have a track dedicated to the player, and not use easings in movement.
    This is VR, non-linear movement or any form of rotation can easily cause motion sickness.
    To clarify, it is very easy to make people motion sick with player tracks, please use them carefully and sparingly.

## Chroma

### AnimateComponent

```json
{
  "b": float, // Time in beats.
  "t": "AnimateComponent",
  "d": {
    "track": string, // The track you want to animate.
    "duration": float, // The length of the event in beats (defaults to 0).
    "easing": string, // An easing for the animation to follow (defaults to easeLinear).
    "component name": { // name of component
      "field name": point definition // name of field on component
    }
  }
}
```

**`AnimateComponent`** allows for animating [components](../environment/environment.md#components). Animating fog [demo](https://streamable.com/d1ztwq).

!!! example
    Lights start off extremely bright and then quickly dim.
    ```json
    {
      "b": 15,
      "t": "AnimateComponent",
      "d": {
        "track": "lights",
        "duration": 5,
        "TubeBloomPrePassLight":
          {
              "colorAlphaMultiplier": [[10, 0], [0, 1, "easeInExpo"]],
              "bloomFogIntensityMultiplier": [[10, 0], [0, 1, "easeInExpo"]]
          }
      }
    },
    ```
