# install-windows-tools.ps1
# 2026-11-04
# Version: v1.0.1
#
# PURPOSE:
# Installs the helper programs the Windows CI jobs need (FFmpeg, Tesseract,
# Pandoc, VLC, Inno Setup) and checks that each one really is installed:
# Chocolatey can report success while a package failed to download (it did
# for VLC on 2026-11-04, a 504 from its feed).
#
# Source (the -Source parameter, or the WINDOWS_TOOLS_SOURCE variable):
#   chocolatey (default)  Chocolatey, tried up to three times over about
#                         five minutes, installing only what is still missing.
#   scoop                 THE LAST RESORT, chosen by a person when Chocolatey
#                         has been down for hours or a release cannot wait:
#                         Scoop downloads each tool from its project's own
#                         site and checks the SHA-256 in its manifest. The run
#                         is marked with a warning; once Chocolatey is back,
#                         run the workflow again with chocolatey to confirm
#                         (see "When Chocolatey is down" in CONTRIBUTING.md).
#
# Usage: .github/scripts/install-windows-tools.ps1 -Tools ffmpeg,tesseract,pandoc,vlc

param(
    [Parameter(Mandatory)][string[]]$Tools,
    [string]$Source = $(if ($env:WINDOWS_TOOLS_SOURCE) { $env:WINDOWS_TOOLS_SOURCE } else { 'chocolatey' })
)
$ErrorActionPreference = 'Stop'
$Tools = @($Tools | ForEach-Object { $_ -split ',' } | Where-Object { $_ })

# Where each tool lands, so "installed" means "the program is there"
function Test-Tool([string]$name) {
    $pf, $pf86 = $env:ProgramFiles, ${env:ProgramFiles(x86)}
    switch ($name) {
        'ffmpeg'    { return [bool](Get-Command ffmpeg -ErrorAction SilentlyContinue) }
        'tesseract' { return [bool](Get-Command tesseract -ErrorAction SilentlyContinue) -or
                             (Test-Path "$pf\Tesseract-OCR\tesseract.exe") }
        'pandoc'    { return [bool](Get-Command pandoc -ErrorAction SilentlyContinue) -or
                             (Test-Path "$pf\Pandoc\pandoc.exe") }
        'vlc'       { return [bool](Get-Command vlc -ErrorAction SilentlyContinue) -or
                             (Test-Path "$pf\VideoLAN\VLC\vlc.exe") -or (Test-Path "$pf86\VideoLAN\VLC\vlc.exe") }
        'innosetup' { return [bool](Get-Command iscc -ErrorAction SilentlyContinue) -or
                             (Test-Path "$pf86\Inno Setup 6\ISCC.exe") -or (Test-Path "$pf\Inno Setup 6\ISCC.exe") }
        default     { throw "Unknown tool: $name" }
    }
}

function Get-Missing { @($Tools | Where-Object { -not (Test-Tool $_) }) }

if ($Source -eq 'chocolatey') {
    $waits = @(0, 60, 180)       # seconds before each try
    foreach ($wait in $waits) {
        $missing = @(Get-Missing)
        if (-not $missing) { break }
        if ($wait) {
            Write-Host "Still missing: $($missing -join ', '). Trying Chocolatey again in $wait s."
            Start-Sleep -Seconds $wait
        }
        # An array argument passes each name separately (splatting a single
        # name would pass it letter by letter)
        choco install $missing -y --no-progress
        # Programs installed to Program Files are found by full path; PATH
        # changes from Chocolatey's shims apply to the next steps
        Import-Module "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1" -ErrorAction SilentlyContinue
        if (Get-Command refreshenv -ErrorAction SilentlyContinue) { refreshenv | Out-Null }
    }
    $missing = @(Get-Missing)
    if ($missing) {
        Write-Host "::error::Chocolatey could not install $($missing -join ', ') after 3 tries (its feed is probably down; see https://status.chocolatey.org). Re-run later. If it stays down for hours, or a release cannot wait, use the Scoop fallback: see 'When Chocolatey is down' in CONTRIBUTING.md."
        exit 1
    }
    Write-Host "Installed with Chocolatey: $($Tools -join ', ')"
    exit 0
}

if ($Source -ne 'scoop') { throw "Unknown source '$Source' (use chocolatey or scoop)" }

Write-Host "::warning::Tools for this run come from Scoop, the fallback for when Chocolatey is down. Once Chocolatey is back, run this workflow again with the chocolatey source to confirm the result."
"### Built with the Scoop fallback`n`nChocolatey was not used for $($Tools -join ', ') in this run. Run the workflow again with the **chocolatey** tool source once Chocolatey is back up, and check that it passes too." >> $env:GITHUB_STEP_SUMMARY

if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    $installer = Join-Path $env:RUNNER_TEMP 'install-scoop.ps1'
    Invoke-RestMethod 'https://get.scoop.sh' -OutFile $installer
    & $installer -RunAsAdmin                     # CI runners are administrators
    $shims = Join-Path $env:USERPROFILE 'scoop\shims'
    $env:PATH = "$shims;$env:PATH"
    $shims >> $env:GITHUB_PATH                   # and for the steps after this one
}
scoop bucket add extras 2>$null
$names = @{ ffmpeg = 'main/ffmpeg'; tesseract = 'main/tesseract'; pandoc = 'main/pandoc'
            vlc = 'extras/vlc'; innosetup = 'extras/inno-setup' }
foreach ($tool in @(Get-Missing)) {
    scoop install $names[$tool]
}
$missing = @(Get-Missing)
if ($missing) {
    Write-Host "::error::Scoop could not install $($missing -join ', ') either."
    exit 1
}
Write-Host "Installed with Scoop: $($Tools -join ', ')"
