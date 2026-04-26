<#
.SYNOPSIS
    Sincroniza los CRCs de bundleinfo.json en Info.dat tras un build de Unity.

.DESCRIPTION
    Tras pulsar F5 en Unity (Vivify > Build > Build Working Version Uncompressed),
    Unity escribe en beatsaber-map/:
      - bundleWindows2021.vivify (y/o bundleWindows2019, bundleAndroid2021)
      - bundleinfo.json (con los CRCs nuevos en bundleCRCs)

    Beat Saber valida los CRCs leyendo Info.dat -> _customData._assetBundle.
    Si no matchean: el bundle no carga (error "Checksum not defined" en logs)
    o los prefabs de Vivify aparecen como rectangulos magenta.

    Este script:
      1. Lee bundleCRCs de bundleinfo.json.
      2. Para cada CRC, hace replace surgical (regex) en Info.dat para
         actualizar el numero sin reformatear el JSON ni tocar otros campos.
      3. Solo escribe Info.dat si algun CRC ha cambiado (evita churn de
         hash en snapshots automaticos).

    Las claves CRC (_windows2021, etc.) tienen que ya existir en
    Info.dat._customData._assetBundle. La primera vez se anaden a mano.

.PARAMETER MapDir
    Ruta al mapa. Por defecto: junction beatsaber-map/ relativo al repo.

.EXAMPLE
    .\scripts\sync-crcs.ps1
    # Lee beatsaber-map\bundleinfo.json y patcha beatsaber-map\Info.dat.

.EXAMPLE
    .\scripts\sync-crcs.ps1 -MapDir "C:\otra\ruta\Test"
    # Para mapas fuera del junction.

.NOTES
    Si el junction beatsaber-map/ no existe, exit 0 (sin error). Permite
    invocarlo desde hooks sin romper en maquinas sin BS instalado, igual
    que snapshot-map.ps1.
#>

[CmdletBinding()]
param(
    [string]$MapDir
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $MapDir) {
    $MapDir = Join-Path $RepoRoot 'beatsaber-map'
}

if (-not (Test-Path $MapDir)) {
    Write-Host "sync-crcs: '$MapDir' no existe, skip."
    exit 0
}

$BundleInfoPath = Join-Path $MapDir 'bundleinfo.json'
$InfoDatPath    = Join-Path $MapDir 'Info.dat'

if (-not (Test-Path $BundleInfoPath)) {
    Write-Error "No existe '$BundleInfoPath'. Ejecuta F5 en Unity primero."
    exit 1
}
if (-not (Test-Path $InfoDatPath)) {
    Write-Error "No existe '$InfoDatPath'."
    exit 1
}

$bundleInfo = Get-Content -Path $BundleInfoPath -Raw | ConvertFrom-Json
$crcs = $bundleInfo.bundleCRCs

if (-not $crcs -or -not $crcs.PSObject.Properties.Count) {
    Write-Error "bundleinfo.json no contiene 'bundleCRCs'. Build incompleto?"
    exit 1
}

# Leer Info.dat como UTF-8 raw para preservar CRLF y formato exacto.
$infoDatText = [System.IO.File]::ReadAllText($InfoDatPath, [System.Text.Encoding]::UTF8)

$missingKeys = @()
$changes     = @()

foreach ($prop in $crcs.PSObject.Properties) {
    $key   = $prop.Name
    $value = $prop.Value

    # Captura la pareja "key" : <numero>. Preserva espacios alrededor del colon.
    $pattern = '("' + [regex]::Escape($key) + '"\s*:\s*)(\d+)'
    $match   = [regex]::Match($infoDatText, $pattern)

    if (-not $match.Success) {
        $missingKeys += $key
        continue
    }

    $oldValue = $match.Groups[2].Value
    if ($oldValue -ne "$value") {
        $infoDatText = [regex]::Replace($infoDatText, $pattern, "`${1}$value")
        $changes += "  $key  $oldValue -> $value"
    }
}

if ($missingKeys.Count -gt 0) {
    Write-Warning "Claves no encontradas en Info.dat._customData._assetBundle: $($missingKeys -join ', ')"
    Write-Warning "Anadelas a mano la primera vez. Skipped sin tocar el resto."
}

if ($changes.Count -eq 0) {
    Write-Host "sync-crcs: CRCs ya sincronizados, no hay cambios."
    exit 0
}

# Escribir UTF-8 sin BOM (formato que usa ChroMapper). Preserva CRLF del raw.
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($InfoDatPath, $infoDatText, $utf8NoBom)

Write-Host "sync-crcs: actualizado Info.dat"
$changes | ForEach-Object { Write-Host $_ }
