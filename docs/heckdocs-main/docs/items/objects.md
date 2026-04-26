# Notes/Walls

Noodle Extensions and Chroma provide simple data you can add to any note or wall to change its properties.

!!! example
    ```json
    "colorNotes": [
      {
        "b": 8.0,
        "x": 2,
        "y": 0,
        "c": 1,
        "d": 1,
        "customData": {
          "coordinates": [5.2, -1.3]
        }
      }
    ]
    ```

!!! info
    Internally, bombs are treated **nearly identically to notes**, and as such, bombs will be considered notes henceforth.

## Heck

### All Objects

* `#!json "track": string/string[]` A single track or list of tracks that an object belongs to. Commonly used for animating groups of objects. Does nothing by itself. See [Tracks and Points](../animation/tracks-and-points.md).

## Noodle Extensions

### Fake Objects

If you wish to create **fake notes** (notes that do not show up in the note count and not count towards score in any way), you must place them in a separate array within `customData`. These arrays are called `fakeColorNotes`, `fakeBombNotes`, `fakeObstacles` and `fakeBurstSliders`.

!!! example
    ```json
    "customData":{
      "fakeColorNotes": [
        {
          "b": 15,
          "x": 0,
          "y": 1,
          "c": 0,
          "d": 0
        }
      ]
    }
    ```

### All Objects

* `#!json "coordinates": [x, y]` (floats) Should be self explanatory. Will override `x` and `y` NOTE: All positions are based off the [Beatwalls system](../assets/items/beatwallsgrid.png).
!!! note
    When sorting your notes, e.g. in a map parsing script, sort by `coordinates`, not `x` (line index) and `y` (line layer).
* `#!json "worldRotation": [x, y, z]` (floats) Also known as "world rotation". Think the 360Degree Characteristic but way more options. This field can also be just a single float (`#!json "worldRotation": 90`) and it will be interpreted as [0, x, 0] (`#!json "worldRotation": [0, 90, 0]`). [0, 0, 0] will always be the initial position the player is facing at the beginning of the song.
* `#!json "localRotation": [x, y, z]` (floats) Allows you to [rotate the object](../assets/items/rotatedwall.png). This won't affect the direction it spawns from or the path it takes. The origin for walls is the front bottom center, [as illustrated by spooky](../assets/items/frontcenter.png).
* `#!json "scale": [x, y, z]` (floats) Sets the scale of the object. This will affect the hitboxes. Because this directly sets the object's transform's scale, it will not correctly scale an obstacle's frame.
* `#!json "noteJumpMovementSpeed": float` Set the NJS of an individual object.
* `#!json "noteJumpStartBeatOffset": float` Set the spawn offset of an individual object.
* `#!json "uninteractable": bool` When true, the note/wall cannot be interacted with. This means notes cannot be cut and walls will not interact with sabers/putting your head in the wall. Notes will still count towards your score.

### Notes

* `#!json "flip": [flip line index, flip jump]` (floats) Flip notes from an initial spawn position to its true position. [PREVIEW](https://streamable.com/9o2puz) (Map by AaltopahWi). Flip line index is the initial `x` the note will spawn at and flip jump is how high (or low) the note will jump up (or down) when flipping to its true position. Base game behavior will set one note's flip jump to -1 and the other to 1.
* `#!json "disableNoteGravity": bool` When true, notes will no longer do [their animation where they float up](https://streamable.com/28rqhy).
* `#!json "disableNoteLook": bool` When true, notes will no longer rotate towards the player.
* `#!json "disableBadCutDirection": bool` When true, the note cannot be cut from wrong direction.
* `#!json "disableBadCutSpeed": bool` When true, the note cannot be cut with insufficient speed.
* `#!json "disableBadCutSaberType": bool` When true, the note cannot be cut with the wrong saber.
* `#!json "link": string` When cut, all notes with the same link string will also be cut.

### Obstacles

* `#!json "size": [w, h, l]` (floats) Width, height and length of the wall. `#!json "size": [1, 1, 1]` will be perfectly square. While `d` (duration) will still control the lifetime, the length of the wall will be controlled by `size` instead.

### Sliders

* `#!json "disableNoteGravity": bool` See above.
* `#!json "tailCoordinates": [x, y]` (floats) `coordinates`, but for the tail.

!!! tip
    `coordinate`, `scale`, `flip`, `size`, and `tailCoordinates` do not require all values to be set, and will use default values if null or missing.

    === ""null" value"
        ```json5
        "coordinates": [null, 0] // will use the vanilla "x" instead
        ```

    === "Missing value"
        ```json5 hl_lines="9"
        "coordinates": [2] // will use the vanilla "y" instead
        ```

## Chroma

### All Objects

* `#!json "color": [r, g, b, a]` (floats) Array of RGB values (Alpha is optional and will default to 1 if not specified).
!!! note
    All RGBA values are on a 0-1 scale, not a 0-255 scale.

### Notes

* `#!json "spawnEffect": bool` Set to false and the note spawn effect will be hidden. True and the note spawn effect will spawn regardless of player setting.
* `#!json "disableDebris": bool` When true, cutting the note spawns will not debris.
