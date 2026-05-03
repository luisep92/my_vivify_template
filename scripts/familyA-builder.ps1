# familyA-builder.ps1 — helper para construir ataques de familia A
# (proyectiles "hold-then-launch": telegraph Vivify + nota BS con definitePosition).
#
# Resuelve dos pegas que aparecieron iterando con Skill4:
#   1) Vivify InstantiatePrefab usa world meters; NoodleExtensions definitePosition
#      usa lane units (1 = 0.6m) ANCLADAS al lane grid (Y=0 ≈ 1m world).
#   2) Cálculo de launch_norm / cut_norm normalizado a la lifetime de la nota
#      (depende de NJS y noteJumpStartBeatOffset).
#
# El helper toma posiciones en METROS (consistencia con Vivify) y convierte
# internamente a lane units. Devuelve los fragments a mergear en el .dat:
#   .customEvents: telegraph spawn/destroy + AssignPathAnimation per proyectil
#   .colorNotes: notas con track + spawnEffect off
#   .pointDefinitions: paths nombrados + dissolve compartido
#
# Uso típico (ver scripts/build-skill4.ps1 para ejemplo completo):
#   # Si tienes execution policy restrictiva, dot-source via Invoke-Expression:
#   $helper = Get-Content '.\scripts\familyA-builder.ps1' -Raw; iex $helper
#   # O bien permitir scripts: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#   $proj = @(
#       @{ position_m=@(-3,3,8); spawn_beat=14.67; launch_beat=24.67; cut_beat=25.67; color=0 },
#       ... 7 proyectiles ...
#   )
#   $frag = New-FamilyAAttack -Name "skill4" -TelegraphAsset "assets/aline/prefabs/projectiles/telegraphsphere.prefab" -Projectiles $proj
#   # Mergear $frag.customEvents, $frag.colorNotes, $frag.pointDefinitions en el .dat de la dificultad.

# ---- Constantes BS / NoodleExtensions ----
$script:LU = 0.6                    # 1 lane unit = 0.6m
$script:LANE_Y_ZERO_WORLD = 1.0     # lane Y=0 ≈ 1m world (hand-reach height)
$script:DEFAULT_NJS = 10.0
$script:DEFAULT_HJD_BEATS = 4.0     # half-jump duration default a NJS=10

# ---- Conversión de coords ----
function ConvertTo-LaneUnits {
    param([double]$x_m, [double]$y_m, [double]$z_m)
    return @(
        [Math]::Round($x_m / $script:LU, 3),
        [Math]::Round(($y_m - $script:LANE_Y_ZERO_WORLD) / $script:LU, 3),
        [Math]::Round($z_m / $script:LU, 3)
    )
}

# ---- Builder de un solo proyectil ----
function New-FamilyAProjectile {
    param(
        [string]$AttackName,
        [int]$Index,
        [string]$TelegraphAsset,
        [double[]]$PositionMeters,
        [double]$SpawnBeat,
        [double]$LaunchBeat,
        [double]$CutBeat,
        [int]$Color = 0,
        [double]$NJS = $script:DEFAULT_NJS,
        [double]$NoteJumpStartBeatOffset = 0.0
    )

    # Path en lane units. cut_norm/launch_norm calculadas según NJS/HJD para
    # alinear el "hold ends" del path con el launch beat.
    $laneStart = ConvertTo-LaneUnits $PositionMeters[0] $PositionMeters[1] $PositionMeters[2]
    $playerEnd = ConvertTo-LaneUnits 0.0 1.0 0.0      # cut moment a hand-reach
    $pastPlayer = ConvertTo-LaneUnits 0.0 1.0 -3.0    # past player at despawn

    # Lifetime (beats): HJD adjustado + cola de despawn. Aproximación que ha
    # funcionado en Skill4: lifetime ≈ HJD + 1 beat.
    $hjd = $script:DEFAULT_HJD_BEATS + $NoteJumpStartBeatOffset
    $spawnBeatOfNote = $CutBeat - $hjd
    $lifetime = $hjd + 1.0
    $launchNorm = [Math]::Round(($LaunchBeat - $spawnBeatOfNote) / $lifetime, 3)
    $cutNorm = [Math]::Round(($CutBeat - $spawnBeatOfNote) / $lifetime, 3)

    $trackId = "${AttackName}_proj_$Index"
    $pathName = "${AttackName}_path_$Index"
    $prefabId = "${AttackName}_telegraph_$Index"

    $pathPoints = @(
        @($laneStart[0], $laneStart[1], $laneStart[2], 0.0),
        @($laneStart[0], $laneStart[1], $laneStart[2], $launchNorm),
        @($playerEnd[0], $playerEnd[1], $playerEnd[2], $cutNorm),
        @($pastPlayer[0], $pastPlayer[1], $pastPlayer[2], 1.0)
    )

    $events = @(
        # Telegraph spawn (Vivify, world meters)
        [ordered]@{
            b = $SpawnBeat; t = 'InstantiatePrefab'
            d = [ordered]@{
                asset = $TelegraphAsset; id = $prefabId; track = "${AttackName}_telegraph_track_$Index"
                position = $PositionMeters; rotation = @(0,0,0); scale = @(1,1,1)
            }
        },
        # Telegraph destroy en el launch beat
        [ordered]@{
            b = $LaunchBeat; t = 'DestroyPrefab'; d = [ordered]@{ id = $prefabId }
        },
        # Bind del path al track de la nota
        [ordered]@{
            b = 0; t = 'AssignPathAnimation'
            d = [ordered]@{
                track = $trackId; duration = 0
                definitePosition = $pathName
                dissolve = "${AttackName}_dissolve"
                dissolveArrow = "${AttackName}_dissolve"
            }
        }
    )

    $note = [ordered]@{
        b = $CutBeat; x = 0; y = 0; c = $Color; d = 8
        customData = [ordered]@{
            track = $trackId; spawnEffect = $false
        }
    }
    if ($NJS -ne $script:DEFAULT_NJS) {
        $note.customData.noteJumpMovementSpeed = $NJS
    }
    if ($NoteJumpStartBeatOffset -ne 0.0) {
        $note.customData.noteJumpStartBeatOffset = $NoteJumpStartBeatOffset
    }

    return [PSCustomObject]@{
        Events = $events
        Note = $note
        PathName = $pathName
        PathPoints = $pathPoints
    }
}

# ---- Builder del ataque completo (N proyectiles) ----
function New-FamilyAAttack {
    param(
        [string]$Name,
        [string]$TelegraphAsset,
        [object[]]$Projectiles,        # array de hashtables con position_m, spawn_beat, launch_beat, cut_beat, color, etc
        [double[]]$DissolveCurve = @(0.0, 0.0, 0.0, 0.59, 1.0, 0.6, 1.0, 1.0)  # 4 keyframes [v,t,v,t,...]
    )

    $allEvents = New-Object System.Collections.ArrayList
    $allNotes = New-Object System.Collections.ArrayList
    $pathDefs = [ordered]@{}

    # Dissolve compartido (curve flat por design del patrón)
    $dissolvePoints = @()
    for ($i = 0; $i -lt $DissolveCurve.Length; $i += 2) {
        $dissolvePoints += ,@($DissolveCurve[$i], $DissolveCurve[$i+1])
    }
    $pathDefs["${Name}_dissolve"] = $dissolvePoints

    for ($i = 0; $i -lt $Projectiles.Length; $i++) {
        $p = $Projectiles[$i]
        $proj = New-FamilyAProjectile `
            -AttackName $Name -Index $i -TelegraphAsset $TelegraphAsset `
            -PositionMeters $p.position_m `
            -SpawnBeat $p.spawn_beat -LaunchBeat $p.launch_beat -CutBeat $p.cut_beat `
            -Color $(if ($p.PSObject.Properties.Name -contains 'color') { $p.color } else { ($i % 2) }) `
            -NJS $(if ($p.PSObject.Properties.Name -contains 'njs') { $p.njs } else { $script:DEFAULT_NJS }) `
            -NoteJumpStartBeatOffset $(if ($p.PSObject.Properties.Name -contains 'offset') { $p.offset } else { 0.0 })

        foreach ($ev in $proj.Events) { [void]$allEvents.Add($ev) }
        [void]$allNotes.Add($proj.Note)
        $pathDefs[$proj.PathName] = $proj.PathPoints
    }

    return [PSCustomObject]@{
        CustomEvents = $allEvents.ToArray()
        ColorNotes = $allNotes.ToArray()
        PointDefinitions = $pathDefs
    }
}

# ---- Helper para generar posiciones en semicírculo (atajo común) ----
function Get-SemicircleArc {
    param(
        [int]$Count,
        [double[]]$Center,        # @(x_m, y_m, z_m)
        [double]$Radius,
        [double]$StartAngleDeg = 180,   # left
        [double]$EndAngleDeg = 0        # right
    )
    $positions = @()
    for ($i = 0; $i -lt $Count; $i++) {
        $t = if ($Count -eq 1) { 0.5 } else { $i / [double]($Count - 1) }
        $angle = $StartAngleDeg + ($EndAngleDeg - $StartAngleDeg) * $t
        $rad = $angle * [Math]::PI / 180
        $positions += ,@(
            [Math]::Round($Center[0] + $Radius * [Math]::Cos($rad), 3),
            [Math]::Round($Center[1] + $Radius * [Math]::Sin($rad), 3),
            $Center[2]
        )
    }
    return $positions
}
