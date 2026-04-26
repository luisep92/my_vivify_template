# User Shared Environments

After creating a custom environment, they can be turned into a shareable standalone JSON that can be used on any map like the override environment option. These JSONs must be placed in `UserData/Chroma../environments/` and must have the file extension `.dat`. These files will be loaded when you launch Beat Saber and will produce errors in your log when any fail to load.

!!! tip
    You can also manually reload the files without restarting Beat Saber if you are in Debug Mode (launch parameter `-aerolunaisthebestmodder`) by pressing `Ctrl+E`.

## Finding Custom Chroma Environments

Other user's environments can be found in the heck Discord in the #environments channel, feel free to share your own in there as well!

## Structure

``` { .json .copy }
{
  "version": "1.0.0", // must be 1.0.0 to work
  "name": "my environment!",
  "author": "Aeroluna",
  "environmentVersion": "0.0.1", // the version of your custom environment
  "environmentName": "DragonsEnvironment", // the name of the base environment to load
  "description": "check out my cool environment", // unused for now, but still required
  "features": { // activates certain features for your environment, see below
    "forceEffectsFilter": "NoEffects"
  },
  "environment": [ // your environment!
    {
      "id": "^.*\\[\\d*[13579]\\]BigTrackLaneRing\\(Clone\\)$",
      "lookupMethod": "Regex",
      "scale": [0.1, 0.1, 0.1]
    }
  ],
  "materials": { // optional field if you want materials!
    "green standard": {
      "color": [0, 1, 0, 0],
      "shader": "Standard"
    }
  }
}
```

### Features

* `#!json "useChromaEvents": true` Forces Chroma to load its features such as rgb lights and light ids.
* `#!json "forceEffectsFilter": "AllEffects"/"StrobeFilter"/"NoEffects"` Forces the effects filter option to a specific preset.
* `#!json "basicBeatmapEvents": []` Loads basic lighting events into the map.
