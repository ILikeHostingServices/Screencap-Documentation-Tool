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
    Version: v1.1.0
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
$AppUserModelId = 'ILHS.ScreencapDocumentationTool.GUI'  # must match APP_USER_MODEL_ID in screencap_gui.pyw

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

    # Pick up PATH changes from the prerequisite install without a new window
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')

    # Point shortcuts at the Python launcher (pyw.exe) rather than the .bat:
    # Windows will not pin a .bat shortcut to the taskbar, and pyw.exe keeps
    # working when Python is upgraded. Fall back to the .bat if pyw is missing.
    $pyw = Get-Command pyw.exe -ErrorAction SilentlyContinue
    $gui = Join-Path $InstallDir 'screencap_gui.pyw'
    $icon = Join-Path $InstallDir 'assets\icon.ico'

    # Give each shortcut the same AppUserModelID the GUI window sets, so the
    # running window and a pinned shortcut share one taskbar button and icon.
    $appIdSupported = $false
    try {
        if (-not ('ScreencapInstall.ShortcutAppId' -as [type])) {
            Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace ScreencapInstall {
    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    public struct PropertyKey { public Guid fmtid; public uint pid; }

    [StructLayout(LayoutKind.Explicit, Size = 24)]
    public struct PropVariant {
        [FieldOffset(0)] public ushort vt;
        [FieldOffset(8)] public IntPtr pointer;
    }

    [ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IPropertyStore {
        [PreserveSig] int GetCount(out uint count);
        [PreserveSig] int GetAt(uint index, out PropertyKey key);
        [PreserveSig] int GetValue(ref PropertyKey key, out PropVariant value);
        [PreserveSig] int SetValue(ref PropertyKey key, ref PropVariant value);
        [PreserveSig] int Commit();
    }

    [ComImport, Guid("0000010b-0000-0000-C000-000000000046"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IPersistFile {
        void GetClassID(out Guid classId);
        [PreserveSig] int IsDirty();
        void Load([MarshalAs(UnmanagedType.LPWStr)] string fileName, uint mode);
        void Save([MarshalAs(UnmanagedType.LPWStr)] string fileName, [MarshalAs(UnmanagedType.Bool)] bool remember);
        void SaveCompleted([MarshalAs(UnmanagedType.LPWStr)] string fileName);
        void GetCurFile([MarshalAs(UnmanagedType.LPWStr)] out string fileName);
    }

    [ComImport, Guid("00021401-0000-0000-C000-000000000046")]
    class CShellLink { }

    public static class ShortcutAppId {
        public static void Set(string lnkPath, string appId) {
            object link = new CShellLink();
            IPersistFile file = (IPersistFile)link;
            file.Load(lnkPath, 2); // STGM_READWRITE
            IPropertyStore store = (IPropertyStore)link;
            PropertyKey key = new PropertyKey();
            key.fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"); // PKEY_AppUserModel_ID
            key.pid = 5;
            PropVariant value = new PropVariant();
            value.vt = 31; // VT_LPWSTR
            value.pointer = Marshal.StringToCoTaskMemUni(appId);
            try {
                Marshal.ThrowExceptionForHR(store.SetValue(ref key, ref value));
                Marshal.ThrowExceptionForHR(store.Commit());
            } finally {
                Marshal.FreeCoTaskMem(value.pointer);
            }
            file.Save(lnkPath, true);
            Marshal.ReleaseComObject(link);
        }
    }
}
'@
        }
        $appIdSupported = $true
    } catch {
        Write-Host "    Taskbar grouping setup skipped: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    $shell = New-Object -ComObject WScript.Shell
    $targets = @(
        (Join-Path ([Environment]::GetFolderPath('Programs')) "$AppName.lnk"),
        (Join-Path ([Environment]::GetFolderPath('Desktop')) "$AppName.lnk")
    )
    foreach ($lnkPath in $targets) {
        try {
            $lnk = $shell.CreateShortcut($lnkPath)
            if ($pyw) {
                $lnk.TargetPath = $pyw.Source
                $lnk.Arguments = "-3 `"$gui`""
            } else {
                $lnk.TargetPath = Join-Path $InstallDir 'Run-Screencap-GUI.bat'
                $lnk.WindowStyle = 7  # minimized, so the launcher console does not flash up
            }
            $lnk.WorkingDirectory = $InstallDir
            $lnk.Description = 'Capture a screenshot of every step in screen recordings'
            $lnk.IconLocation = if (Test-Path $icon) { "$icon,0" } else { "$env:SystemRoot\System32\imageres.dll,67" }
            $lnk.Save()
            if ($appIdSupported) {
                try {
                    [ScreencapInstall.ShortcutAppId]::Set($lnkPath, $AppUserModelId)
                } catch {
                    Write-Host "    Shortcut created, but taskbar grouping could not be set: $($_.Exception.Message)" -ForegroundColor Yellow
                }
            }
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
