# Getting Started

It is recommended when mapping, to use the launch argument `--verbose` in order to open the console with the game. If there are any errors with your map, they will display here along with the beat of the erroneous object. SERIOUSLY IF YOU RELEASE A MAP WITH ANY ERRORS, I WILL FIND YOU.

## Capabilities

In order to use **Chroma**, **Noodle Extensions**, or **Vivify**, you *MUST* add the appropriate capability to your map, otherwise the mod will not activate. You can go [here](https://github.com/Kylemc1413/SongCore/#infodat-explanation) to see how adding requirements to the info.dat works.

Currently these capabilities are:

- `"Chroma"`: Suggestion or Requirement
- `"Noodle Extensions"`: Requirement Only
- `"Vivify"`: Requirement Only

!!! info
    `"AudioLink"` may also be added as either a suggestion or requirement, however that mod will always run regardless of if the map has the capability set.

## CustomJSONData

All the extra JSON fields are powered by **[CustomJSONData](https://github.com/Aeroluna/CustomJSONData)**, which adds the `customData` field and `customEvents` array.

### Custom Data

`customData` fields allow adding additional arbitrary data to any existing objects, like notes/walls/lighting events.
!!! example
    ```json
    "colorNotes":[
      {
        "b": 8.0,
        "x": 2,
        "y": 0,
        "c": 1,
        "d": 1,
        "customData": {
          "foo": 3,
          "bar": "Hello, BSMG!"
        }
      }
    ]
    ```

### Custom Events

**Custom events** are stored inside the `customEvents` field of your difficulty's `customData`. Not to be confused with vanilla lighting events with custom data added, these are entirely new events.
!!! example
    ```json
    {
      "version": "3.0.0",
      "customData": {
        "customEvents": [
          {
            "b": float,
            "t": string,
            "d": {
              "foo": 1.0,
              "message": "Hello from a custom event!"
            }
          }
        ]
      },
      "colorNotes": [],
      "obstacles": []
    }
    ```

## ReLoader

Need to quickly prototype your map? Tired of having to exit the song and reload? Well **Reloader** is for you! Originally starting as a [mod developed by Kyle1413](https://github.com/Kylemc1413/ReLoader) before being integrated into Heck, ReLoader allows hot reloading beatmaps and scrubbing through time without ever opening a menu.

### Enabling

In order to activate ReLoader, you must be in **Debug Mode**, which is activated with the launch parameter `-aerolunaisthebestmodder` (yes really). Afterwards, entering any song in practice mode will activate ReLoader.

### Keybinds

These key binds are configurable from `UserData/Heck.json`.

- **Left Control** - Save current time.
- **Space** - Jump to saved time/hot reload beatmap.
- **Left Arrow** - Scrub backwards 5 seconds.
- **Right Arrow** - Scrub forwards 5 seconds.

Additionally, pressing your reload key while in the practice menu where you select your start time and song speed will also hot reload the map you currently have selected.

### ReLoad on Restart

Unfortunately, environments changes through Chroma cannot be hot ReLoaded™ while in-game, so to help with that, there is an additional `"ReloadOnRestart"` option with in the config that will automatically reload the JSON whenever you restart the map.

=== ":octicons-file-code-16: `UserData/Heck.json`"

  ```json hl_lines="5"
  {
    "ReLoader": {
      "JumpToSavedTime": "Space",
      "Reload": "Space",
      "ReloadOnRestart": true,
      "SaveTime": "LeftControl",
      "ScrubBackwards": "LeftArrow",
      "ScrubForwards": "RightArrow",
      "ScrubIncrement": 5.0
    }
  }
  ```

!!! tip
    You can quickly restart by pressing `F4` (SiraUtil), or by navigating the pause menu using `P` to pause and `R` to restart (vanilla).
