<#
.SYNOPSIS
    install.ps1

.DESCRIPTION
    One-step Windows installer for the Screencap Documentation Tool. Downloads
    the latest version from GitHub into the install folder, installs Python 3
    and FFmpeg with winget if they are missing, and adds Start Menu and Desktop
    shortcuts for the GUI. Safe to re-run to update; your source and output
    folders are kept.

    Install scope is picked automatically:
      - Normal PowerShell window        -> just the current user (no admin needed)
      - Administrator PowerShell window -> all users (system-wide)
    Override with -UserOnly or -SystemWide.

    Add -WithWhisper to also install the optional speech recognition used by
    Captions From Narration (about 450 MB, in a whisper-env folder inside the
    install folder).

.NOTES
    Version: v1.3.1
    Last Edit Date: 2026-10-03

.EXAMPLE
    & ([scriptblock]::Create((irm https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.ps1)))

.EXAMPLE
    .\install.ps1 -InstallDir 'D:\Tools\Screencap-Documentation-Tool' -NoShortcuts

.EXAMPLE
    .\install.ps1 -SystemWide    # from an Administrator PowerShell window

.EXAMPLE
    & ([scriptblock]::Create((irm https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.ps1))) -WithWhisper
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
    [switch]$SkipPrerequisites,
    # Install Python, FFmpeg, and shortcuts for all users (needs Administrator)
    [switch]$SystemWide,
    # Install for the current user only, even from an Administrator window
    [switch]$UserOnly,
    # Also install speech recognition (faster-whisper) for Captions From Narration
    [switch]$WithWhisper
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'  # Invoke-WebRequest is far faster without the progress bar in PowerShell 5.1
$Repo = 'ILikeHostingServices/Screencap-Documentation-Tool'
$AppName = 'Screencap Documentation Tool'
$AppUserModelId = 'ILikeHostingServices.ScreencapDocumentationTool.GUI'  # must match APP_USER_MODEL_ID in screencap_gui.pyw

function Write-Step([string]$Text) { Write-Host "==> $Text" -ForegroundColor Cyan }

# 0. Decide the install scope. Errors use 'throw', never 'exit', because the
#    Quick Start runs this as a script block and 'exit' would close the window.
if ($SystemWide -and $UserOnly) { throw 'Use either -SystemWide or -UserOnly, not both.' }
$isAdmin = $false
if ($env:OS -eq 'Windows_NT') {
    $principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
if ($SystemWide) {
    if (-not $isAdmin) {
        throw 'A system-wide install needs an Administrator PowerShell window. Right-click Start > "Terminal (Admin)" and paste the command again.'
    }
    $scope = 'machine'
} elseif ($UserOnly) {
    $scope = 'user'
} else {
    $scope = if ($isAdmin) { 'machine' } else { 'user' }
}
if ($scope -eq 'machine') {
    Write-Step 'Install scope: ALL USERS (running as Administrator). Use -UserOnly to install just for you.'
} else {
    Write-Step 'Install scope: CURRENT USER ONLY. Run from an Administrator window (or add -SystemWide) to install for everyone.'
}

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
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallDir 'Install-Prerequisites.ps1') -Scope $scope
    $prereqOk = ($LASTEXITCODE -eq 0)
}

# 3b. System-wide: make sure every user can save recordings and screenshots in
#     the default folders. S-1-5-32-545 is the built-in Users group (the SID
#     works on any Windows language, unlike the name "Users").
if ($scope -eq 'machine') {
    foreach ($folder in 'source', 'output') {
        $path = Join-Path $InstallDir $folder
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        & icacls.exe $path /grant '*S-1-5-32-545:(OI)(CI)M' /Q | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host "    Could not grant Users write access to $path" -ForegroundColor Yellow }
    }
}

# 3c. Optional speech recognition. It goes into its own Python environment
#     (whisper-env) so its packages never touch the system Python, and an
#     update without -WithWhisper leaves an existing one in place.
$whisperOk = $true
if ($WithWhisper) {
    Write-Step 'Installing speech recognition (faster-whisper, about 450 MB; this takes a few minutes)'
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $env:Path
    $envDir = Join-Path $InstallDir 'whisper-env'
    $envPy = Join-Path $envDir 'Scripts\python.exe'
    try {
        if (-not (Test-Path $envPy)) {
            # Prefer Python 3.12 (what the prerequisites install), then any Python 3
            $py = Get-Command py.exe -ErrorAction SilentlyContinue
            if ($py) {
                & $py.Source -3.12 -m venv $envDir
                if ($LASTEXITCODE -ne 0) { & $py.Source -3 -m venv $envDir }
            } else {
                & python.exe -m venv $envDir
            }
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path $envPy)) { throw 'Could not create the whisper-env Python environment.' }
        }
        & $envPy -m pip install --disable-pip-version-check --quiet --upgrade faster-whisper
        if ($LASTEXITCODE -ne 0) { throw 'pip could not install faster-whisper (check the internet connection or proxy).' }
        & $envPy -c 'import faster_whisper'
        if ($LASTEXITCODE -ne 0) { throw 'faster-whisper was installed but does not load.' }
        Write-Host '[OK]      Speech recognition installed. The speech model is downloaded the first time it is used.' -ForegroundColor Green
    } catch {
        $whisperOk = $false
        Write-Host "[WARN]    Speech recognition was not installed: $($_.Exception.Message) Everything else works; run the command again with -WithWhisper to retry." -ForegroundColor Yellow
    }
}

# 4. Shortcuts. User scope: your Start Menu and Desktop (no admin needed).
#    System-wide: the All Users Start Menu and Public Desktop.
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
    $userLinks = @(
        (Join-Path ([Environment]::GetFolderPath('Programs')) "$AppName.lnk"),
        (Join-Path ([Environment]::GetFolderPath('Desktop')) "$AppName.lnk")
    )
    if ($scope -eq 'machine') {
        $targets = @(
            (Join-Path ([Environment]::GetFolderPath('CommonPrograms')) "$AppName.lnk"),
            (Join-Path ([Environment]::GetFolderPath('CommonDesktopDirectory')) "$AppName.lnk")
        )
        # Remove this account's per-user shortcuts from an earlier just-me
        # install so the app does not show up twice
        foreach ($old in $userLinks) { Remove-Item -Path $old -Force -ErrorAction SilentlyContinue }
    } else {
        $targets = $userLinks
    }
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

    # A shortcut pinned to the taskbar is a separate copy. Give copies that
    # start this tool the current taskbar identity too, so an update does not
    # leave a second taskbar button. Other pinned shortcuts are not touched.
    $pinned = Join-Path $env:APPDATA 'Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar'
    if ($appIdSupported -and (Test-Path $pinned)) {
        foreach ($pin in Get-ChildItem -Path $pinned -Filter '*.lnk' -ErrorAction SilentlyContinue) {
            try {
                $link = $shell.CreateShortcut($pin.FullName)
                if ("$($link.TargetPath) $($link.Arguments)" -like "*$([WildcardPattern]::Escape($gui))*") {
                    [ScreencapInstall.ShortcutAppId]::Set($pin.FullName, $AppUserModelId)
                }
            } catch {
                Write-Host "    Could not update the pinned taskbar shortcut $($pin.Name): $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host ''
if ($prereqOk) {
    $who = if ($scope -eq 'machine') { 'for all users' } else { 'for the current user' }
    Write-Host "$AppName is installed $who in $InstallDir" -ForegroundColor Green
    if (-not $NoShortcuts) { Write-Host "Start it from the '$AppName' Start Menu or Desktop shortcut." }
    Write-Host "Or run: $InstallDir\Run-Screencap-GUI.bat"
    Write-Host "Put recordings in $InstallDir\source (or choose any folder in the GUI)."
    if ($WithWhisper -and -not $whisperOk) { Write-Host 'Speech recognition (Captions From Narration) is not installed; see the warning above.' -ForegroundColor Yellow }
} else {
    Write-Host "$AppName was downloaded to $InstallDir, but a prerequisite still needs attention (see the messages above)." -ForegroundColor Yellow
    Write-Host 'Close this window, open a new PowerShell window, and paste the install command again.'
}
