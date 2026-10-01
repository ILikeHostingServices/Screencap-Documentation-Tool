<#
.SYNOPSIS
    Install-Prerequisites.ps1

.DESCRIPTION
    Checks for Python 3 and FFmpeg on Windows 11 and installs any that are
    missing using winget (built into Windows 11). Safe to run more than once.

.NOTES
    Version: v1.0.0
    Last Edit Date: 2026-10-01

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Install-Prerequisites.ps1
#>

[CmdletBinding()]
param()

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

if (-not (Test-Command 'winget')) {
    Write-Error 'winget was not found. Install "App Installer" from the Microsoft Store, then run this script again.'
    exit 2
}

$packages = @(
    @{ Name = 'Python 3'; Check = { (Test-Command 'py') -or ((Test-Command 'python') -and ((& python --version 2>&1) -match 'Python 3')) }; Id = 'Python.Python.3.12' },
    @{ Name = 'FFmpeg'; Check = { (Test-Command 'ffmpeg') -and (Test-Command 'ffprobe') }; Id = 'Gyan.FFmpeg' }
)

$failed = $false
foreach ($pkg in $packages) {
    if (& $pkg.Check) {
        Write-Host "[OK]      $($pkg.Name) is already installed." -ForegroundColor Green
        continue
    }
    Write-Host "[INSTALL] $($pkg.Name) ($($pkg.Id)) via winget..." -ForegroundColor Yellow
    & winget install --id $pkg.Id -e --accept-source-agreements --accept-package-agreements
    Update-SessionPath
    if (& $pkg.Check) {
        Write-Host "[OK]      $($pkg.Name) installed." -ForegroundColor Green
    } else {
        Write-Host "[WARN]    $($pkg.Name) not detected yet. Close this window, open a new one, and run this script again." -ForegroundColor Red
        $failed = $true
    }
}

if ($failed) { exit 1 }
Write-Host ''
Write-Host 'All prerequisites are installed. Put recordings in the "source" folder and run Run-Screencap.bat.' -ForegroundColor Cyan
exit 0
