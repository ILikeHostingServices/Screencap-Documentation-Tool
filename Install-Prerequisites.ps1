<#
.SYNOPSIS
    Install-Prerequisites.ps1

.DESCRIPTION
    Checks for Python 3 and FFmpeg on Windows 11 and installs any that are
    missing using winget (built into Windows 11). Safe to run more than once.
    -Scope user (default) installs for the current user only, no admin needed.
    -Scope machine installs for all users and must be run as Administrator.

.NOTES
    Version: v1.2.0
    Last Edit Date: 2026-10-01

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Install-Prerequisites.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Install-Prerequisites.ps1 -Scope machine
#>

[CmdletBinding()]
param(
    [ValidateSet('user', 'machine')]
    [string]$Scope = 'user'
)

$ErrorActionPreference = 'Stop'

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Update-SessionPath {
    # Pick up PATH changes made by winget without opening a new window
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Test-MachinePath([string]$Name) {
    # True only if the program is on the machine-wide PATH, i.e. usable by
    # every account, not just the one running this script
    foreach ($dir in ([Environment]::GetEnvironmentVariable('Path', 'Machine') -split ';')) {
        if ($dir -and (Test-Path (Join-Path ([Environment]::ExpandEnvironmentVariables($dir)) $Name))) { return $true }
    }
    return $false
}

function Test-MachinePython {
    # winget's machine-scope Python lands in C:\Program Files\Python3xx, and the
    # all-users py launcher lives in C:\Windows
    $installed = @(Get-ChildItem -Path $env:ProgramFiles -Filter 'Python3*' -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName 'pythonw.exe') })
    return ($installed.Count -gt 0) -and (Test-Path (Join-Path $env:SystemRoot 'py.exe'))
}

if ($Scope -eq 'machine') {
    $principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Host 'ERROR: A system-wide (-Scope machine) install must be run from an Administrator PowerShell window.' -ForegroundColor Red
        exit 2
    }
}

if (-not (Test-Command 'winget')) {
    # Write-Host, not Write-Error: with ErrorActionPreference Stop, Write-Error would end the script before 'exit 2'
    Write-Host 'ERROR: winget was not found. Install "App Installer" from the Microsoft Store, then run this script again.' -ForegroundColor Red
    exit 2
}

if ($Scope -eq 'machine') {
    # A copy installed only in someone's user profile does not count here,
    # because other accounts on this PC cannot use it
    $packages = @(
        @{ Name = 'Python 3 (all users)'; Check = { Test-MachinePython }; Id = 'Python.Python.3.12' },
        @{ Name = 'FFmpeg (all users)'; Check = { (Test-MachinePath 'ffmpeg.exe') -and (Test-MachinePath 'ffprobe.exe') }; Id = 'Gyan.FFmpeg' }
    )
    $scopeArgs = @('--scope', 'machine')
} else {
    $packages = @(
        @{ Name = 'Python 3'; Check = { (Test-Command 'py') -or ((Test-Command 'python') -and ((& python --version 2>&1) -match 'Python 3')) }; Id = 'Python.Python.3.12' },
        @{ Name = 'FFmpeg'; Check = { (Test-Command 'ffmpeg') -and (Test-Command 'ffprobe') }; Id = 'Gyan.FFmpeg' }
    )
    $scopeArgs = @()  # winget's default for these packages is the current user
}

$failed = $false
foreach ($pkg in $packages) {
    if (& $pkg.Check) {
        Write-Host "[OK]      $($pkg.Name) is already installed." -ForegroundColor Green
        continue
    }
    Write-Host "[INSTALL] $($pkg.Name) ($($pkg.Id)) via winget..." -ForegroundColor Yellow
    & winget install --id $pkg.Id -e --accept-source-agreements --accept-package-agreements @scopeArgs
    Update-SessionPath
    if (& $pkg.Check) {
        Write-Host "[OK]      $($pkg.Name) installed." -ForegroundColor Green
    } else {
        Write-Host "[WARN]    $($pkg.Name) not detected yet. Close this window, open a new one, and run this script again." -ForegroundColor Red
        $failed = $true
    }
}

# The GUI needs Tkinter, which the python.org / winget installer includes by default
if ((-not $failed) -and (Test-Command 'py')) {
    & py -3 -c "import tkinter" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host '[OK]      Tkinter (needed for the GUI) is available.' -ForegroundColor Green
    } else {
        Write-Host '[WARN]    Tkinter is missing, so the GUI will not start. Re-run the Python installer, choose Modify, and tick "tcl/tk and IDLE". The command line version still works.' -ForegroundColor Red
    }
}

if ($failed) { exit 1 }
Write-Host ''
Write-Host 'All prerequisites are installed. Put recordings in the "source" folder and run Run-Screencap-GUI.bat.' -ForegroundColor Cyan
exit 0
