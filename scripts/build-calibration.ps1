# build-calibration.ps1 — test empírico de coordenadas lane-units ↔ world-meters.
#
# Spawnea 5 marcadores Vivify (esferas en world meters conocidos) + 5 notas con
# `definitePosition` apuntando a las mismas coords (convertidas a lane units).
# Si overlap perfecto en BS → conversión correcta. Si descuadran → ajustar las
# constantes LANE_*_ZERO_WORLD/LANE_UNIT_M.
#
# Constantes calibradas (resultado validado del test, también en
# `.claude/skills/vivify-mapping/SKILL.md` sección "Conversión lane units ↔ world meters"):
#   LANE_UNIT_M       = 0.6
#   LANE_X_ZERO_WORLD = -0.9
#   LANE_Y_ZERO_WORLD =  1.0
#
# Sobreescribe NormalStandard.dat con el test. Backup automático a NormalStandard.dat.bak.

$root = Split-Path -Parent $PSScriptRoot
$datPath = Join-Path $root 'beatsaber-map\NormalStandard.dat'
$easyPath = Join-Path $root 'beatsaber-map\EasyStandard.dat'
$bakPath = "${datPath}.bak"
if (Test-Path $datPath) { Copy-Item $datPath $bakPath -Force; "Backed up current NormalStandard.dat to $bakPath" }

$LANE_UNIT_M = 0.6
$LANE_X_ZERO_WORLD = -0.9
$LANE_Y_ZERO_WORLD = 1.0

function Convert-MetersToLanes {
    param([double]$WorldX, [double]$WorldY, [double]$WorldZ)
    $lx = ($WorldX - $LANE_X_ZERO_WORLD) / $LANE_UNIT_M
    $ly = ($WorldY - $LANE_Y_ZERO_WORLD) / $LANE_UNIT_M
    $lz = $WorldZ / $LANE_UNIT_M
    return @([Math]::Round($lx, 3), [Math]::Round($ly, 3), [Math]::Round($lz, 3))
}

function Empty-Array { return ,@() }

# ---- Configuración del test ----
# 5 marcadores en línea horizontal a hand-reach (y=1m), 4m en frente (z=4)
$TestPositions_m = @(
    @(-2.0, 1.0, 4.0),
    @(-1.0, 1.0, 4.0),
    @( 0.0, 1.0, 4.0),
    @( 1.0, 1.0, 4.0),
    @( 2.0, 1.0, 4.0)
)
$SpawnBeat = 4.0
$LaunchBeat = 8.0
$TravelBeats = 3.0   # lentos para tener tiempo de inspeccionar

# ---- Build markers (Vivify) + notas (NE) ----
$easy = Get-Content $easyPath -Raw | ConvertFrom-Json
$boilerplate = @($easy.customData.customEvents | Where-Object { $_.b -le 0.001 })

$customEvents = New-Object System.Collections.ArrayList
foreach ($ev in $boilerplate) { [void]$customEvents.Add($ev) }

$colorNotes = New-Object System.Collections.ArrayList
$pointDefs = [ordered]@{}

for ($i=0; $i -lt $TestPositions_m.Length; $i++) {
    $pos = $TestPositions_m[$i]
    $launchT = [Math]::Round($LaunchBeat + $i * 1.0, 3)
    $cutT = [Math]::Round($launchT + $TravelBeats, 3)

    # Marker prefab in Vivify world meters
    [void]$customEvents.Add([ordered]@{
        b = $SpawnBeat; t = 'InstantiatePrefab'
        d = [ordered]@{
            asset = 'assets/aline/prefabs/projectiles/telegraphsphere.prefab'
            id = "calib_marker_$i"; track = "calib_track_$i"
            position = $pos; rotation = @(0,0,0); scale = @(2,2,2)  # x2 escala para visibilidad
        }
    })
    # Marker stays visible after launch beat too (no destroy) so we can compare overlap

    # Note path: starts and stays at marker position the entire lifetime
    $laneStart = Convert-MetersToLanes $pos[0] $pos[1] $pos[2]
    $pointDefs["calib_path_$i"] = @(
        @($laneStart[0], $laneStart[1], $laneStart[2], 0.0),
        @($laneStart[0], $laneStart[1], $laneStart[2], 1.0)
    )
    [void]$customEvents.Add([ordered]@{
        b = 0; t = 'AssignPathAnimation'
        d = [ordered]@{
            track = "calib_proj_$i"; duration = 0
            definitePosition = "calib_path_$i"
        }
    })
    [void]$colorNotes.Add([ordered]@{
        b = $cutT; x = 0; y = 0; c = ($i % 2); d = 8
        customData = [ordered]@{
            track = "calib_proj_$i"
            spawnEffect = $false
        }
    })
}

$normal = [ordered]@{
    version='3.3.0'
    bpmEvents=(Empty-Array); rotationEvents=(Empty-Array)
    colorNotes = $colorNotes.ToArray()
    bombNotes=(Empty-Array); obstacles=(Empty-Array); sliders=(Empty-Array); burstSliders=(Empty-Array); waypoints=(Empty-Array)
    basicBeatmapEvents=(Empty-Array); colorBoostBeatmapEvents=(Empty-Array)
    lightColorEventBoxGroups=(Empty-Array); lightRotationEventBoxGroups=(Empty-Array); lightTranslationEventBoxGroups=(Empty-Array)
    basicEventTypesWithKeywords=[ordered]@{ d=(Empty-Array) }
    useNormalEventsAsCompatibleEvents=$false
    customData=[ordered]@{
        customEvents = $customEvents.ToArray()
        environment = $easy.customData.environment
        pointDefinitions = $pointDefs
    }
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$json = $normal | ConvertTo-Json -Depth 32 -Compress
[IO.File]::WriteAllText($datPath, $json, $utf8NoBom)
"Wrote calibration test to ${datPath}"
"5 marcadores en (x={-2,-1,0,1,2}, y=1, z=4)m world."
"Notas con definitePosition apuntando a las MISMAS coords."
"En BS Normal: si las notas overlap perfecto con las esferas → conversion ok. Si descuadran → reporta delta y ajustamos LANE_X_ZERO_WORLD/LANE_Y_ZERO_WORLD."
"Para restaurar el NormalStandard.dat anterior: copia ${bakPath} a ${datPath}."
