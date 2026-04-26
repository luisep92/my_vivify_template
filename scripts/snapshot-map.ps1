<#
.SYNOPSIS
    Snapshot de los .dat del mapa actual a docs/map-snapshots/.

.DESCRIPTION
    Dos modos:

    -Label <X>   : snapshot manual con etiqueta. NUNCA se rota. Se queda hasta
                   que el usuario lo borre a mano. Para marcar momentos
                   importantes ("before-textures", "v1-jugable").

    -Auto        : snapshot automático (sin etiqueta). Ring buffer de 5
                   últimos. Si el contenido es idéntico al último auto
                   (mismo hash SHA-256 de los archivos), NO se crea un
                   duplicado.

    Solo se copian los archivos versionables: .dat (Info, ExpertPlusStandard,
    BPMInfo, otras dificultades) y bundleinfo.json. NO se copia .ogg ni
    *.vivify (audio y bundles regenerables, no aportan al historial).

.PARAMETER Label
    Etiqueta corta del snapshot manual. Sin espacios. Excluye -Auto.

.PARAMETER Auto
    Modo automático con ring buffer de 5. Excluye -Label.

.PARAMETER MaxAuto
    Tamaño del ring buffer en modo -Auto. Default: 5.

.EXAMPLE
    .\scripts\snapshot-map.ps1 -Label "before-textures"

.EXAMPLE
    .\scripts\snapshot-map.ps1 -Auto
    # Crea docs/map-snapshots/2026-04-26_1734-auto/ y rota los antiguos.

.EXAMPLE
    # Si tu ExecutionPolicy bloquea scripts locales:
    powershell -ExecutionPolicy Bypass -File .\scripts\snapshot-map.ps1 -Auto
    # O permite scripts locales una sola vez (recomendado):
    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

.NOTES
    Si el junction beatsaber-map/ no existe, el script termina con exit 0
    (no error). Esto permite que el git pre-commit hook lo invoque sin
    romper commits en máquinas donde Beat Saber no esté instalado.
    Crear el junction con:
        cmd /c 'mklink /J beatsaber-map "C:\...\CustomWIPLevels\Test"'
#>

[CmdletBinding(DefaultParameterSetName = 'Manual')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Manual')]
    [ValidatePattern('^[a-zA-Z0-9_-]+$')]
    [string]$Label,

    [Parameter(Mandatory = $true, ParameterSetName = 'Auto')]
    [switch]$Auto,

    [Parameter(ParameterSetName = 'Auto')]
    [int]$MaxAuto = 5
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$MapPath = Join-Path $RepoRoot 'beatsaber-map'
$SnapshotsRoot = Join-Path $RepoRoot 'docs\map-snapshots'

if (-not (Test-Path $MapPath)) {
    if ($Auto) {
        # Modo auto = invocado por hook. No bloquear el commit por esto.
        Write-Host "snapshot-map: beatsaber-map/ no existe, skip auto-snapshot."
        exit 0
    }
    Write-Error "No existe '$MapPath'. Crea el junction con: cmd /c 'mklink /J beatsaber-map `"<ruta a CustomWIPLevels\Test>`"'"
    exit 1
}

$Patterns = @('*.dat', 'bundleinfo.json')

# Hash combinado del contenido actual del mapa, para dedup en modo -Auto.
function Get-MapStateHash {
    param([string]$Path)
    $files = foreach ($p in $Patterns) {
        Get-ChildItem -Path $Path -Filter $p -File -ErrorAction SilentlyContinue
    }
    $files = $files | Sort-Object Name
    if (-not $files) { return $null }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $combined = ''
    foreach ($f in $files) {
        $h = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash
        $combined += "$($f.Name):$h;"
    }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($combined)
    return [System.BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-', '')
}

$Timestamp = Get-Date -Format 'yyyy-MM-dd_HHmm'

if ($Auto) {
    if (-not (Test-Path $SnapshotsRoot)) {
        New-Item -ItemType Directory -Path $SnapshotsRoot | Out-Null
    }

    $currentHash = Get-MapStateHash -Path $MapPath
    if (-not $currentHash) {
        Write-Host "snapshot-map: no hay .dat en beatsaber-map/, skip."
        exit 0
    }

    # Comparar con último auto-snapshot. Si idéntico, skip.
    $lastAuto = Get-ChildItem -Path $SnapshotsRoot -Directory -Filter '*-auto' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        Select-Object -First 1

    if ($lastAuto) {
        $lastHash = Get-MapStateHash -Path $lastAuto.FullName
        if ($lastHash -eq $currentHash) {
            Write-Host "snapshot-map: contenido idéntico a $($lastAuto.Name), skip."
            exit 0
        }
    }

    $SnapshotName = "$Timestamp-auto"
}
else {
    $SnapshotName = "$Timestamp-$Label"
}

$SnapshotPath = Join-Path $SnapshotsRoot $SnapshotName

if (Test-Path $SnapshotPath) {
    Write-Error "Ya existe '$SnapshotPath'. Espera al siguiente minuto o usa otro label."
    exit 1
}

New-Item -ItemType Directory -Path $SnapshotPath | Out-Null

$Copied = @()
foreach ($Pattern in $Patterns) {
    Get-ChildItem -Path $MapPath -Filter $Pattern -File | ForEach-Object {
        $Dest = Join-Path $SnapshotPath $_.Name
        Copy-Item -Path $_.FullName -Destination $Dest
        $Copied += $_.Name
    }
}

if ($Copied.Count -eq 0) {
    Write-Warning "No se copio nada. Revisa que '$MapPath' contenga .dat / bundleinfo.json."
    Remove-Item $SnapshotPath
    exit 1
}

# Ring buffer en modo -Auto: dejar solo los últimos $MaxAuto.
if ($Auto) {
    $autos = Get-ChildItem -Path $SnapshotsRoot -Directory -Filter '*-auto' |
        Sort-Object Name -Descending
    if ($autos.Count -gt $MaxAuto) {
        $autos | Select-Object -Skip $MaxAuto | ForEach-Object {
            Remove-Item -Path $_.FullName -Recurse -Force
            Write-Host "snapshot-map: rotado $($_.Name)"
        }
    }
}

Write-Host "Snapshot creado: $SnapshotPath"
Write-Host "Archivos:"
$Copied | ForEach-Object { Write-Host "  - $_" }
