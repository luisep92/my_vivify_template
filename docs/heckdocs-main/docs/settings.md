# Settings Setter

Annoyed by that one streamer who always play with static lights? Recommend they play your map with the correct settings using **Settings Setter™**!

Additionally, other mod developers can add compatibility to have their mod integrate with settings setter as well. If the appropriate mod for which your setting comes from is not installed, Heck will skip over your setting.

!!! warning
    Although all settings are included for posterity's sake, it is *HIGHLY* recommended to only list settings you *NEED*, e.g. your map uses a lot of text and left handed mode needs to be disabled to not mirror your text. Keep it to the bare minimum!

## Adding recommended settings

* `"_customData"` -> `"_settings"`
    * `category`: The category your setting belongs to. See below for category names.
        * `setting name`: The name of your setting. See below for setting names.

Custom data for settable settings is set in the info.dat.
!!! example
    ```json
    {
      "_version": "2.0.0",
      "_songName": "NULCTRL MEISO FLIP",
      ...
      "_difficultyBeatmapSets": [
        {
          "_beatmapCharacteristicName": "Standard",
          "_difficultyBeatmaps": [
            {
              "_difficulty": "ExpertPlus",
              "_difficultyRank": 9,
              "_beatmapFilename": "ExpertPlusStandard.dat",
              "_noteJumpMovementSpeed": 19,
              "_customData": {
                "_settings": {
                  "_playerOptions":{
                    "_leftHanded": true,
                    "_hideNoteSpawnEffect": false
                  },
                  "_graphics": {
                    "_mirrorGraphicsSettings": 0
                  },
                  "_chroma": {
                    "_disableEnvironmentEnhancements": true
                  }
                }
              }
            }
          ]
        }
      ]
    }
    ```

## Categories

### Vanilla

These settings are implemented by default.

* `#!json "_playerOptions"`
    * `#!json "_leftHanded": bool`
    * `#!json "_playerHeight": float`
    * `#!json "_automaticPlayerHeight": bool`
    * `#!json "_sfxVolume": float`
    * `#!json "_reduceDebris": bool`
    * `#!json "_noTextsAndHuds": bool`
    * `#!json "_noFailEffects": bool` Hidden setting: *This will hide "Miss" text.*
    * `#!json "_advancedHud": bool`
    * `#!json "_autoRestart": bool`
    * `#!json "_saberTrailIntensity": float`
    * `#!json "_noteJumpDurationTypeSettings": "Dynamic"/"Static"`
    * `#!json "_noteJumpFixedDuration": float` *Only available w/ "Static"*
    * `#!json "_noteJumpStartBeatOffset": float` *Only available w/ "Dynamic"*,
        * Close: `-0.5`
        * Closer: `-0.25`
        * Default: `0`
        * Further: `0.25`
        * Far: `0.5`
    * `#!json "_hideNoteSpawnEffect": bool`
    * `#!json "_adaptiveSfx": bool`
    * `#!json "_environmentEffectsFilterDefaultPreset": "AllEffects"/"StrobeFilter"/"NoEffects"`
    * `#!json "_environmentEffectsFilterExpertPlusPreset": "AllEffects"/"StrobeFilter"/"NoEffects"`
* `#!json "_modifiers"`
    * `#!json "_energyType": Bar, Battery`
    * `#!json "_noFailOn0Energy": bool`
    * `#!json "_instaFail": bool`
    * `#!json "_failOnSaberClash": bool` Hidden setting: *Instantly fails player when sabers clash.*
    * `#!json "_enabledObstacleType": "All"/"FullHeightOnly"/"NoObstacles"` *The `"FullHeightOnly"` option is a hidden setting and disables crouch walls.*
    * `#!json "_fastNotes": bool` Hidden setting: *Forces NJS to 20.*
    * `#!json "_strictAngles": bool`
    * `#!json "_disappearingArrows": bool`
    * `#!json "_ghostNotes": bool`
    * `#!json "_noBombs": bool`
    * `#!json "_songSpeed": "Normal"/"Faster"/"Slower"/"SuperFast"`
    * `#!json "_noArrows": bool`
    * `#!json "_proMode": bool`
    * `#!json "_zenMode": bool`
    * `#!json "_smallCubes": bool`
* `#!json "_environments"`
    * `#!json "_overrideEnvironments": bool` *Enable or disable user environment. If you are using chroma environment enhancement, this setting is redundant.*
* `#!json "_colors"`
    * `#!json "_overrideDefaultColors": bool` *Enable or disable user color scheme.*
* `#!json "_graphics"`
    * `#!json "_mirrorGraphicsSettings": int (0 - 3)` *Off/Low (0/1) will not create cameras. "Low" duplicates base game notes to create a "fake" mirror.*
    * `#!json "_mainEffectGraphicsSettings": int (0 - 1)` "Bloom Post Process" *Disabling will switch to baked/fake "Quest style" bloom*
    * `#!json "_smokeGraphicsSettings": int (0 - 1)` *Also enables depth texture/"Soft Particles" when used.*
    * `#!json "_burnMarkTrailsEnabled": bool` Hidden setting: *Hides burn trails left by sabers.*
    * `#!json "_screenDisplacementEffectsEnabled": bool`
    * `#!json "_maxShockwaveParticles": int (0 - 2)`

### Chroma

* `#!json "_chroma"`
    * `#!json "_disableChromaEvents": bool`
    * `#!json "_disableEnvironmentEnhancements": bool`
    * `#!json "_disableNoteColoring": bool`
    * `#!json "_forceZenModeWalls": bool`

### Other Mods

There are a handful of other mods with support for Settings Setter as well.
Main properties for these will be provided here, and the full list of available settings will be linked alongside if required.

#### Counters+

Full property list with things like HUD offsets, size, colors, etc can be found on the [Counters+ Wiki](https://github.com/NuggoDEV/CountersPlus/wiki/For-Developers#heck-integration).

* `#!json "_countersPlus"`
    * `#!json "_mainEnabled": bool`
    * `#!json "_mainParentedToBaseGameHUD": bool`
    * `#!json "_missedEnabled": bool`
    * `#!json "_progressEnabled": bool`
    * `#!json "_scoreEnabled": bool`
    * `#!json "_personalBestEnabled": bool`
    * `#!json "_speedEnabled": bool`
    * `#!json "_cutEnabled": bool`
    * `#!json "_spinometerEnabled": bool`
    * `#!json "_notesLeftEnabled": bool`
    * `#!json "_failEnabled": bool`

#### UITweaks

[UITweaks Wiki](https://github.com/Exomanz/UITweaks/wiki/IV.-Heck-Integration-(Mapping))

* `#!json "_uiTweaks"`
    * `#!json "_multiplierEnabled": bool`
    * `#!json "_energyEnabled": bool`
    * `#!json "_comboEnabled": bool`
    * `#!json "_positionEnabled": bool`
    * `#!json "_progressEnabled": bool`

#### NoteTweaks

Significantly more settings and all default values can be found at the [NoteTweaks Wiki](https://github.com/TheBlackParrot/NoteTweaks/wiki/Settings-Setter).

* `#!json "_noteTweaks"`
    * `#!json "_enabled": bool`
    * `#!json "_enableBombOutlines": bool`
    * `#!json "_enableNoteOutlines": bool`
    * `#!json "_enableAccDot": bool`
    * `#!json "_enableDots": bool`
    * `#!json "_enableChainDots": bool`
    * `#!json "_fixDotsIfNoodle": bool`
    * `#!json "_enableFog": bool`
    * `#!json "_enableHeightFog": bool`
    * `#!json "_noteScaleX": float`
    * `#!json "_noteScaleY": float`
    * `#!json "_noteScaleZ": float`
    * `#!json "_arrowScaleX": float`
    * `#!json "_arrowScaleY": float`
    * `#!json "_dotScaleX": float`
    * `#!json "_dotScaleY": float`
    * `#!json "_linkScale": float`
    * `#!json "_bombScale": float`

!!! tip
    Noodle will override any scaling options set by NoteTweaks or BS+.
    If you don't want any random "big note jumpscares", it's a good idea to assign all notes a scale value of `[1,1,1]` using Noodle directly.
