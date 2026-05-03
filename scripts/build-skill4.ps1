# build-skill4.ps1 — regenera NormalStandard.dat con el ataque Skill4
# usando familyA-builder.ps1.
#
# Sirve también como plantilla para skills de la misma familia (Skill3, etc).
# Edita las constantes (positions, beats, NJS) y re-ejecuta.
#
# Si execution policy bloquea: pwsh -ExecutionPolicy Bypass -File .\scripts\build-skill4.ps1

$root = Split-Path -Parent $PSScriptRoot
$helperPath = Join-Path $PSScriptRoot 'familyA-builder.ps1'
$datPath = Join-Path $root 'beatsaber-map\NormalStandard.dat'
$easyPath = Join-Path $root 'beatsaber-map\EasyStandard.dat'

# Load helper (Invoke-Expression to bypass dot-source policy si aplica)
$helperContent = Get-Content $helperPath -Raw
Invoke-Expression $helperContent

function Empty-Array { return ,@() }

# ---- Configuración del ataque Skill4 ----
$AttackName = 'skill4'
$TelegraphAsset = 'assets/aline/prefabs/projectiles/telegraphsphere.prefab'
$TriggerBeat = 8.0           # Skill4 animator trigger
$ProjectileCount = 7
$ArcCenter_m = @(0, 3, 8)    # Aline approx position
$ArcRadius_m = 3.0
$SpawnFirstBeat = 14.67      # ≈4s tras trigger (matchea anim)
$SpawnStepBeats = 1.333      # 0.8s entre spawns
$LaunchFirstBeat = 24.67     # ≈10s tras trigger (matchea anim)
$LaunchStepBeats = 1.667     # 1s entre launches
$TravelBeats = 1.0           # tiempo desde launch al cut

# ---- Build ----
$positions = Get-SemicircleArc -Count $ProjectileCount -Center $ArcCenter_m -Radius $ArcRadius_m -StartAngleDeg 180 -EndAngleDeg 0
$projectiles = @()
for ($i=0; $i -lt $ProjectileCount; $i++) {
    $projectiles += @{
        position_m = $positions[$i]
        spawn_beat = [Math]::Round($SpawnFirstBeat + $i * $SpawnStepBeats, 3)
        launch_beat = [Math]::Round($LaunchFirstBeat + $i * $LaunchStepBeats, 3)
        cut_beat = [Math]::Round($LaunchFirstBeat + $i * $LaunchStepBeats + $TravelBeats, 3)
    }
}
$attack = New-FamilyAAttack -Name $AttackName -TelegraphAsset $TelegraphAsset -Projectiles $projectiles

# ---- Compose .dat (boilerplate from Easy + animator trigger + attack fragments) ----
$easy = Get-Content $easyPath -Raw | ConvertFrom-Json
$boilerplate = @($easy.customData.customEvents | Where-Object { $_.b -le 0.001 })

$customEvents = New-Object System.Collections.ArrayList
foreach ($ev in $boilerplate) { [void]$customEvents.Add($ev) }
[void]$customEvents.Add([ordered]@{
    b = $TriggerBeat; t = 'SetAnimatorProperty'
    d = [ordered]@{ id='alineMain'; properties=@([ordered]@{ id=($AttackName.Substring(0,1).ToUpper() + $AttackName.Substring(1)); type='Trigger'; value=$true }) }
})
foreach ($ev in $attack.CustomEvents) { [void]$customEvents.Add($ev) }

$normal = [ordered]@{
    version='3.3.0'
    bpmEvents=(Empty-Array); rotationEvents=(Empty-Array)
    colorNotes = $attack.ColorNotes
    bombNotes=(Empty-Array); obstacles=(Empty-Array); sliders=(Empty-Array); burstSliders=(Empty-Array); waypoints=(Empty-Array)
    basicBeatmapEvents=(Empty-Array); colorBoostBeatmapEvents=(Empty-Array)
    lightColorEventBoxGroups=(Empty-Array); lightRotationEventBoxGroups=(Empty-Array); lightTranslationEventBoxGroups=(Empty-Array)
    basicEventTypesWithKeywords=[ordered]@{ d=(Empty-Array) }
    useNormalEventsAsCompatibleEvents=$false
    customData=[ordered]@{
        customEvents = $customEvents.ToArray()
        environment = $easy.customData.environment
        pointDefinitions = $attack.PointDefinitions
    }
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$json = $normal | ConvertTo-Json -Depth 32 -Compress
[IO.File]::WriteAllText($datPath, $json, $utf8NoBom)
"Wrote ${datPath}: $($attack.ColorNotes.Count) notes, $($customEvents.Count) custom events"
