<#
.SYNOPSIS
    install.ps1

.DESCRIPTION
    One-step Windows installer for the Screencap Documentation Tool. Downloads
    the latest version from GitHub into the install folder, installs Python 3
    and FFmpeg with winget if they are missing, and adds Start Menu and Desktop
    shortcuts for the GUI. Safe to re-run to update; your source and output
    folders are kept.

.NOTES
    Version: v1.0.0
    Last Edit Date: 2026-10-01

.EXAMPLE
    & ([scriptblock]::Create((irm https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.ps1)))

.EXAMPLE
    .\install.ps1 -InstallDir 'D:\Tools\Screencap-Documentation-Tool' -NoShortcuts
#>

[CmdletBinding()]
param(
    # Where the tool is installed
    [string]$InstallDir = 'C:\DATA\Tools\Screencap-Documentation-Tool',
    # Branch, tag, or commit to install. HEAD = the repository's default branch.
    [string]$Ref = 'HEAD',
    # Skip creating Start Menu and Desktop shortcuts
    [switch]$NoShortcuts,
    # Only download the program; do not install Python or FFmpeg
    [switch]$SkipPrerequisites
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'  # Invoke-WebRequest is far faster without the progress bar in PowerShell 5.1
$Repo = 'ILikeHostingServices/Screencap-Documentation-Tool'
$AppName = 'Screencap Documentation Tool'

function Write-Step([string]$Text) { Write-Host "==> $Text" -ForegroundColor Cyan }

# GitHub requires TLS 1.2; older PowerShell 5.1 defaults may not include it
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$tmp = Join-Path ([IO.Path]::GetTempPath()) ("screencap-install-" + [guid]::NewGuid().ToString('N'))
try {
    # 1. Download and unpack
    Write-Step "Downloading $AppName ($Ref) from GitHub"
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    $zip = Join-Path $tmp 'source.zip'
    Invoke-WebRequest -Uri "https://github.com/$Repo/archive/$Ref.zip" -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath (Join-Path $tmp 'x') -Force
    $top = Get-ChildItem -Path (Join-Path $tmp 'x') -Directory | Select-Object -First 1
    if (-not $top -or -not (Test-Path (Join-Path $top.FullName 'screencap.py'))) {
        throw 'The downloaded archive does not look like the Screencap Documentation Tool (screencap.py missing).'
    }

    # 2. Copy into place. Nothing is deleted, so recordings and screenshots
    #    already in source\ and output\ survive an update.
    Write-Step "Installing to $InstallDir"
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Copy-Item -Path (Join-Path $top.FullName '*') -Destination $InstallDir -Recurse -Force
    if ($env:OS -eq 'Windows_NT') {
        # Clear the "downloaded from the internet" flag so scripts run without prompts
        Get-ChildItem -Path $InstallDir -Recurse -File | Unblock-File
    }
    foreach ($required in 'screencap.py', 'screencap_gui.pyw', 'Run-Screencap-GUI.bat') {
        if (-not (Test-Path (Join-Path $InstallDir $required))) { throw "Install incomplete: $required is missing from $InstallDir" }
    }
}
finally {
    Remove-Item -Path $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

# 3. Prerequisites. Run in a child process with -ExecutionPolicy Bypass so the
#    default "Restricted" policy on Windows 11 does not block the script file.
$prereqOk = $true
if (-not $SkipPrerequisites) {
    Write-Step 'Checking prerequisites (Python 3, FFmpeg)'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallDir 'Install-Prerequisites.ps1')
    $prereqOk = ($LASTEXITCODE -eq 0)
}

# 4. Shortcuts (per user, no admin rights needed)
if (-not $NoShortcuts) {
    Write-Step 'Creating Start Menu and Desktop shortcuts'
    $shell = New-Object -ComObject WScript.Shell
    $targets = @(
        (Join-Path ([Environment]::GetFolderPath('Programs')) "$AppName.lnk"),
        (Join-Path ([Environment]::GetFolderPath('Desktop')) "$AppName.lnk")
    )
    foreach ($lnkPath in $targets) {
        try {
            $lnk = $shell.CreateShortcut($lnkPath)
            $lnk.TargetPath = Join-Path $InstallDir 'Run-Screencap-GUI.bat'
            $lnk.WorkingDirectory = $InstallDir
            $lnk.WindowStyle = 7  # minimized, so the launcher console does not flash up
            $lnk.Description = 'Capture a screenshot of every step in screen recordings'
            $lnk.IconLocation = "$env:SystemRoot\System32\imageres.dll,67"
            $lnk.Save()
        } catch {
            Write-Host "    Could not create $lnkPath : $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

Write-Host ''
if ($prereqOk) {
    Write-Host "$AppName is installed in $InstallDir" -ForegroundColor Green
    if (-not $NoShortcuts) { Write-Host "Start it from the '$AppName' Start Menu or Desktop shortcut." }
    Write-Host "Or run: $InstallDir\Run-Screencap-GUI.bat"
    Write-Host "Put recordings in $InstallDir\source (or choose any folder in the GUI)."
} else {
    Write-Host "$AppName was downloaded to $InstallDir, but a prerequisite still needs attention (see the messages above)." -ForegroundColor Yellow
    Write-Host 'Close this window, open a new PowerShell window, and paste the install command again.'
}
