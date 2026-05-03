# familyA-builder.ps1 — helper para ataques de familia A (proyectiles secuenciales).
#
# Patrón v2 (2026-05-04): el VISUAL es un prefab Vivify (full control); la NOTA
# es solo hitbox invisible (dissolve permanente). NO comparten track:
#   - AnimateTrack position en Vivify tracks = world meters absolute.
#   - AnimateTrack position en NE notes = offset relativo al lane default.
#   No son equivalentes. Coordinamos por TIMING en lugar de por track:
#   ambos "llegan al jugador" en el mismo beat (cut_beat).
#
# Lifecycle por proyectil:
#   spawn_beat:    InstantiatePrefab del visual en world position semicircle.
#                  Visual stays static hasta launch_beat (sin animación).
#   launch_beat:   AnimateTrack mueve el visual de semicircle → player (durante
#                  travel_beats = cut_beat - launch_beat). Nota BS spawn standard
#                  con _time = cut_beat, invisible vía dissolve=0 throughout.
#   cut_beat:      visual prefab Y nota llegan al player simultáneamente.
#                  Player ve solo el prefab; cut detection sobre la nota invisible.
#   cut_beat+δ:    DestroyPrefab del visual.
#
# Beneficios vs versión previa:
#   - Cero fight con conversiones lane units / lineIndex offsets.
#   - Visual = cualquier prefab Unity (sphere, spike, paint stroke, etc).
#   - Nota standard, sin definitePosition; cualquier mod respeta dissolve.
#   - Patrón reusable para mele (sólo cambia la trayectoria de AnimateTrack).
#
# Uso típico:
#   $helper = Get-Content '.\scripts\familyA-builder.ps1' -Raw; iex $helper
#   $proj = @(@{position_m=@(-3,3,8); spawn_beat=14.67; launch_beat=24.67; cut_beat=26.67}, ...)
#   $frag = New-FamilyAAttack -Name "skill4" -PrefabAsset "assets/.../sphere.prefab" -Projectiles $proj
#   # Mergear $frag.CustomEvents y $frag.ColorNotes en el .dat de la dificultad.

$script:DEFAULT_NJS = 10.0

# Construye los eventos + nota para un único proyectil.
function New-FamilyAProjectile {
    param(
        [string]$AttackName,
        [int]$Index,
        [string]$PrefabAsset,
        [double[]]$PositionMeters,        # spawn world position (matches Vivify)
        [double[]]$PlayerEndMeters = @(0, 1, 0),  # donde llega al jugador (default: hand-reach center)
        [double]$SpawnBeat,
        [double]$LaunchBeat,
        [double]$CutBeat,
        [int]$Color = 0,
        [double]$NJS = $script:DEFAULT_NJS,
        [double]$PrefabScale = 1.0,
        [double]$PrefabDespawnDelayBeats = 0.1   # cuánto tras cut_beat se destroy
    )

    $trackId = "${AttackName}_proj_$Index"
    $prefabId = "${AttackName}_visual_$Index"
    $travelBeats = $CutBeat - $LaunchBeat

    $events = @(
        # Spawn del visual en posición semicircle
        [ordered]@{
            b = $SpawnBeat; t = 'InstantiatePrefab'
            d = [ordered]@{
                asset = $PrefabAsset; id = $prefabId; track = $trackId
                position = $PositionMeters; rotation = @(0,0,0); scale = @($PrefabScale, $PrefabScale, $PrefabScale)
            }
        },
        # AnimateTrack en launch_beat: mueve semicircle → jugador en travel_beats.
        # Tanto prefab como nota están en este track; ambos siguen el position.
        [ordered]@{
            b = $LaunchBeat; t = 'AnimateTrack'
            d = [ordered]@{
                track = $trackId; duration = $travelBeats
                position = @(
                    @($PositionMeters[0], $PositionMeters[1], $PositionMeters[2], 0.0),
                    @($PlayerEndMeters[0], $PlayerEndMeters[1], $PlayerEndMeters[2], 1.0)
                )
            }
        },
        # Destroy del prefab tras el cut
        [ordered]@{
            b = $CutBeat + $PrefabDespawnDelayBeats; t = 'DestroyObject'; d = [ordered]@{ id = $prefabId }
        }
    )

    # Nota: invisible (dissolve=0 throughout) pero cuttable. Standard BS jump-in,
    # _time = cut_beat → llega a player default position a cut_beat. Coincide
    # temporalmente con la llegada del prefab visual al jugador (vía AnimateTrack).
    # Player ve solo el prefab; cut detection se registra sobre la nota invisible.
    # NO comparte track con el prefab: AnimateTrack position tiene semánticas
    # distintas (absolute en Vivify, offset-from-lane en NE).
    $note = [ordered]@{
        b = $CutBeat; x = 1; y = 1; c = $Color; d = 8
        customData = [ordered]@{
            spawnEffect = $false
            animation = [ordered]@{
                dissolve = @(@(0.0, 0.0), @(0.0, 1.0))
                dissolveArrow = @(@(0.0, 0.0), @(0.0, 1.0))
            }
        }
    }
    if ($NJS -ne $script:DEFAULT_NJS) {
        $note.customData.noteJumpMovementSpeed = $NJS
    }

    return [PSCustomObject]@{ Events = $events; Note = $note }
}

# Construye el ataque completo (N proyectiles).
function New-FamilyAAttack {
    param(
        [string]$Name,
        [string]$PrefabAsset,
        [object[]]$Projectiles,
        [double[]]$PlayerEndMeters = @(0, 1, 0),
        [double]$PrefabScale = 1.0
    )
    $allEvents = New-Object System.Collections.ArrayList
    $allNotes = New-Object System.Collections.ArrayList

    for ($i = 0; $i -lt $Projectiles.Length; $i++) {
        $p = $Projectiles[$i]
        $proj = New-FamilyAProjectile `
            -AttackName $Name -Index $i -PrefabAsset $PrefabAsset `
            -PositionMeters $p.position_m `
            -PlayerEndMeters $PlayerEndMeters `
            -SpawnBeat $p.spawn_beat -LaunchBeat $p.launch_beat -CutBeat $p.cut_beat `
            -Color $(if ($p.PSObject.Properties.Name -contains 'color') { $p.color } else { ($i % 2) }) `
            -NJS $(if ($p.PSObject.Properties.Name -contains 'njs') { $p.njs } else { $script:DEFAULT_NJS }) `
            -PrefabScale $PrefabScale

        foreach ($ev in $proj.Events) { [void]$allEvents.Add($ev) }
        [void]$allNotes.Add($proj.Note)
    }

    return [PSCustomObject]@{
        CustomEvents = $allEvents.ToArray()
        ColorNotes = $allNotes.ToArray()
    }
}

# Helper: posiciones en arc semicircular (vertical o horizontal) sobre un centro.
function Get-SemicircleArc {
    param(
        [int]$Count,
        [double[]]$Center,
        [double]$Radius,
        [double]$StartAngleDeg = 180,
        [double]$EndAngleDeg = 0
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
