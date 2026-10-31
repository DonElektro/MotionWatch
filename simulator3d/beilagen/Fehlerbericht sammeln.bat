<# : Batch-Teil
@echo off
rem (Die erste Zeile ist Absicht: cmd liest nur bis "exit /b", PowerShell sieht den Batch-Teil als Kommentar.)
rem MoveEye Sim 3D - Fehlerbericht sammeln: packt die Protokolle des Simulators in eine ZIP-Datei auf dem Desktop.
rem Geht auch, wenn der Simulator gar nicht startet. Braucht keine Adminrechte und kein Internet.
rem Kommt mit: Godot-Protokolle (logs\*.log), Absturz-Merker, einige Einstellungen ohne Codes, Liste der
rem Programmdateien, Grafikkarte und Windows-Version, Absturzmeldungen von Windows zum Simulator.
rem Kommt NICHT mit: Passwoerter und Hashes, Tunnel-Code, ntfy-Themen, Schluessel, "MoveEye auf diesem PC",
rem Spielstaende, Bilder. Zeilen, die nach Zugangsdaten aussehen, werden entfernt.
setlocal
set "MESIM_BAT=%~f0"
set "MESIM_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%MESIM_PS%" set "MESIM_PS=powershell.exe"
"%MESIM_PS%" -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Expression ((Get-Content -LiteralPath $env:MESIM_BAT -Raw))"
echo.
pause
exit /b
#>

$ErrorActionPreference = 'Continue'
$jetzt = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$prog = Split-Path -Parent $env:MESIM_BAT
$ud = Join-Path $env:APPDATA 'Godot\app_userdata\MoveEye Sim 3D'
$desk = ''
try { $desk = [Environment]::GetFolderPath('Desktop') } catch { }
if (-not $desk -or -not (Test-Path -LiteralPath $desk)) { $desk = Join-Path $env:USERPROFILE 'Desktop' }
if (-not (Test-Path -LiteralPath $desk)) { $desk = $env:USERPROFILE }
$ziel = Join-Path $desk ('MoveEyeSim3D_Fehlerbericht_' + $jetzt + '.zip')
$stage = Join-Path $env:TEMP ('MoveEyeSim3D_Fehlerbericht_' + $jetzt)
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$notiz = New-Object System.Collections.ArrayList

Write-Host 'MoveEye Sim 3D - Fehlerbericht wird gesammelt ...'

# geheime Werte, die nie in den Bericht duerfen (nur gelesen, nie kopiert)
$geheim = New-Object System.Collections.ArrayList
$einst = Join-Path $ud 'simulator_settings.json'
if (Test-Path -LiteralPath $einst) {
    try {
        $j = Get-Content -LiteralPath $einst -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($p in $j.PSObject.Properties) {
            if ($p.Name -match '(?i)code|pass|token|secret|key|hash|salt|ntfy|topic') {
                $v = [string]$p.Value
                if ($v.Length -ge 4 -and $v -ne 'True' -and $v -ne 'False') { [void]$geheim.Add($v) }
            }
        }
    } catch { }
}
$schl = Join-Path $ud 'pruefstand\schluessel.txt'
if (Test-Path -LiteralPath $schl) {
    try { $v = (Get-Content -LiteralPath $schl -Raw).Trim(); if ($v.Length -ge 4) { [void]$geheim.Add($v) } } catch { }
}

$zeileWeg = '(?i)(passw|kennwort|tunnel_code|token|secret|schluessel|ntfy|topic|authorization|cookie|ghp_|github_pat_)'
$schluesselWeg = '(?i)(code|pass|pw$|token|secret|schluessel|key|hash|salt|ntfy|topic|host|user|mail|ssid|psk|auth|cookie)'

function Weg-Geheim([string]$t) {
    foreach ($g in $geheim) { $t = $t.Replace($g, '<entfernt>') }
    $t = $t -replace '://[^/\s:@]+:[^/\s@]+@', '://<entfernt>@'
    return ($t -replace '\b[0-9a-fA-F]{40,}\b', '<lange Hex-Zahl entfernt>')
}

function Text-Kopie($von, $nach) {
    try {
        $zeilen = Get-Content -LiteralPath $von -Encoding UTF8 -ErrorAction Stop
        $aus = foreach ($z in $zeilen) {
            if ($z -match $zeileWeg) { '[Zeile entfernt: koennte Zugangsdaten enthalten]' } else { Weg-Geheim $z }
        }
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $nach) | Out-Null
        Set-Content -LiteralPath $nach -Value @($aus) -Encoding UTF8
    } catch { [void]$notiz.Add('nicht lesbar: ' + $von + ' (' + $_.Exception.Message + ')') }
}

function Ohne-Geheim($o) {
    if ($o -is [System.Management.Automation.PSCustomObject]) {
        $neu = [ordered]@{}
        foreach ($p in $o.PSObject.Properties) {
            if ($p.Name -match $schluesselWeg) { $neu[$p.Name] = '<entfernt>' } else { $neu[$p.Name] = Ohne-Geheim $p.Value }
        }
        return [pscustomobject]$neu
    }
    if ($o -is [System.Array]) { return @($o | ForEach-Object { Ohne-Geheim $_ }) }
    if ($o -is [string]) { return (Weg-Geheim $o) }
    return $o
}

function Json-Kopie($von, $nach) {
    try {
        $j = Get-Content -LiteralPath $von -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $nach) | Out-Null
        Set-Content -LiteralPath $nach -Value ((Ohne-Geheim $j) | ConvertTo-Json -Depth 12) -Encoding UTF8
    } catch { [void]$notiz.Add('nicht lesbar oder kein JSON (weggelassen): ' + $von) }
}

if (Test-Path -LiteralPath $ud) {
    # Godot-Protokolle (das laufende und die aelteren)
    $logs = Join-Path $ud 'logs'
    if (Test-Path -LiteralPath $logs) {
        Get-ChildItem -LiteralPath $logs -Filter '*.log' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 8 |
            ForEach-Object { Text-Kopie $_.FullName (Join-Path $stage ('logs\' + $_.Name)) }
    } else { [void]$notiz.Add('kein Ordner logs (der Simulator hat noch kein Protokoll geschrieben)') }
    # Absturz-Merker und Einstellungen (nur diese Dateien; Codes und Passwoerter entfernt)
    foreach ($f in @('inhalte_merker.json', 'grafik_stufe.json', 'werk_reset.json', 'inhalte.json', 'fenster.json',
                     'simulator_sprache.json', 'simulator_settings.json')) {
        $p = Join-Path $ud $f
        if (Test-Path -LiteralPath $p) { Json-Kopie $p (Join-Path $stage ('daten\' + $f)) }
    }
    foreach ($f in @('maggie\vorfuehrung_protokoll.txt', 'orte\3d_gebaeude_bericht.txt')) {
        $p = Join-Path $ud $f
        if (Test-Path -LiteralPath $p) { Text-Kopie $p (Join-Path $stage ('daten\' + $f)) }
    }
} else { [void]$notiz.Add('Benutzerordner fehlt: ' + $ud + ' (der Simulator lief auf diesem Konto noch nie)') }

# Uebersicht: Programmordner, Benutzerordner, Windows, Grafikkarte, Absturzmeldungen
$info = New-Object System.Collections.ArrayList
[void]$info.Add('MoveEye Sim 3D - Fehlerbericht ' + $jetzt)
[void]$info.Add('Programmordner: ' + $prog)
[void]$info.Add('')
[void]$info.Add('== Dateien im Programmordner ==')
Get-ChildItem -LiteralPath $prog -File -ErrorAction SilentlyContinue | ForEach-Object {
    $ver = ''
    if ($_.Extension -eq '.exe') { try { $ver = ' - ' + $_.VersionInfo.FileVersion } catch { } }
    [void]$info.Add(('{0}  {1:N0} Bytes  {2:yyyy-MM-dd HH:mm}{3}' -f $_.Name, $_.Length, $_.LastWriteTime, $ver))
}
[void]$info.Add('')
[void]$info.Add('== Dateien im Benutzerordner (nur Namen) ==')
if (Test-Path -LiteralPath $ud) {
    Get-ChildItem -LiteralPath $ud -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.PSIsContainer) { [void]$info.Add($_.Name + '\') }
        else { [void]$info.Add(('{0}  {1:N0} Bytes  {2:yyyy-MM-dd HH:mm}' -f $_.Name, $_.Length, $_.LastWriteTime)) }
    }
}
[void]$info.Add('')
[void]$info.Add('== Windows und Grafik ==')
try {
    $os = Get-CimInstance Win32_OperatingSystem
    [void]$info.Add('Windows: ' + $os.Caption + ' ' + $os.Version + ' - RAM ' + [math]::Round($os.TotalVisibleMemorySize / 1MB, 1) + ' GB')
} catch { [void]$info.Add('Windows: unbekannt') }
try {
    Get-CimInstance Win32_VideoController | ForEach-Object {
        [void]$info.Add('Grafik: ' + $_.Name + ' - Treiber ' + $_.DriverVersion + ' (' + $_.DriverDate + ') - ' + $_.CurrentHorizontalResolution + ' x ' + $_.CurrentVerticalResolution)
    }
} catch { [void]$info.Add('Grafik: unbekannt') }
try {
    $pr = Get-Process -Name 'MoveEyeSim3D' -ErrorAction SilentlyContinue
    [void]$info.Add('Simulator laeuft gerade: ' + $(if ($pr) { 'ja' } else { 'nein' }))
} catch { }
[void]$info.Add('')
[void]$info.Add('== Absturzmeldungen von Windows (14 Tage) ==')
try {
    $ev = Get-WinEvent -FilterHashtable @{ LogName = 'Application'; Id = 1000, 1001, 1002; StartTime = (Get-Date).AddDays(-14) } -MaxEvents 400 -ErrorAction Stop |
        Where-Object { $_.Message -match '(?i)MoveEyeSim3D|MotionWatch3D' } | Select-Object -First 10
    if ($ev) { foreach ($e in $ev) { [void]$info.Add(('{0:yyyy-MM-dd HH:mm}  ID {1}' -f $e.TimeCreated, $e.Id)); [void]$info.Add((Weg-Geheim $e.Message)); [void]$info.Add('') } }
    else { [void]$info.Add('keine') }
} catch { [void]$info.Add('keine (oder nicht lesbar)') }
if ($notiz.Count -gt 0) { [void]$info.Add(''); [void]$info.Add('== Hinweise =='); foreach ($n in $notiz) { [void]$info.Add($n) } }
$info2 = foreach ($z in $info) { if ([string]$z -match $zeileWeg) { '[Zeile entfernt: koennte Zugangsdaten enthalten]' } else { $z } }
Set-Content -LiteralPath (Join-Path $stage 'info.txt') -Value @($info2) -Encoding UTF8

# Schlusspruefung: kein geheimer Wert und keine Zeile mit Zugangsdaten im Bericht, sonst die Datei weglassen
foreach ($d in (Get-ChildItem -LiteralPath $stage -Recurse -File)) {
    $t = Get-Content -LiteralPath $d.FullName -Raw -Encoding UTF8
    $schlecht = $false
    foreach ($g in $geheim) { if ($t -and $t.Contains($g)) { $schlecht = $true } }
    if ($d.Extension -ne '.json' -and $t -and ($t -split "`n" | Where-Object { $_ -match $zeileWeg -and $_ -notmatch '^\[Zeile entfernt' })) { $schlecht = $true }
    if ($schlecht) { Remove-Item -LiteralPath $d.FullName -Force; Write-Host ('weggelassen (Zugangsdaten?): ' + $d.Name) }
}

try {
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $ziel -Force -ErrorAction Stop
    Write-Host ''
    Write-Host 'Fertig. Die Datei liegt auf dem Desktop:'
    Write-Host $ziel
    Write-Host 'Diese ZIP-Datei zusammen mit einer kurzen Beschreibung des Fehlers schicken.'
    try { Start-Process explorer.exe ('/select,"' + $ziel + '"') } catch { }
} catch {
    Write-Host ('Die ZIP-Datei liess sich nicht erstellen: ' + $_.Exception.Message)
    Write-Host ('Die Dateien liegen hier: ' + $stage)
    exit
}
Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
