; installer.iss
; 2026-10-04
; Version: v1.0.0
;
; PURPOSE:
; Inno Setup script for the Windows installer of the packaged app (built
; first with packaging/screencap.spec). Installs for the current user (no
; admin rights) or, when chosen, for all users; adds a Start Menu shortcut
; with the app's taskbar identity, an optional desktop shortcut, and an
; uninstaller; and can install FFmpeg (required) and, optionally, Tesseract
; OCR and Pandoc with winget. Recordings, output, and settings are never
; touched by uninstalling.
;
; Build from the repository root, after the PyInstaller build:
;   iscc /DAppVersion=1.16.0 packaging\installer.iss
; Output: release\Screencap-Documentation-Tool-v<version>-windows-x64-setup.exe

#define AppName "Screencap Documentation Tool"
#define AppExe "Screencap Documentation Tool.exe"
#define AppUserModelId "ILHS.ScreencapDocumentationTool.GUI"
#ifndef AppVersion
  #error Pass the version: iscc /DAppVersion=X.Y.Z packaging\installer.iss
#endif

[Setup]
; Never change AppId: Windows uses it to recognize upgrades and to uninstall
AppId={{39ABD99E-CAC0-48C0-B602-EF8172627F70}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher=ILikeHostingServices
AppPublisherURL=https://github.com/ILikeHostingServices/Screencap-Documentation-Tool
AppSupportURL=https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/issues
AppUpdatesURL=https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Just me by default (no admin rights); the user can choose all users
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=..\LICENSE
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
OutputDir=..\release
OutputBaseFilename=Screencap-Documentation-Tool-v{#AppVersion}-windows-x64-setup
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany=ILikeHostingServices
VersionInfoDescription={#AppName} Setup
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
VersionInfoCopyright=Copyright (c) 2026 ILikeHostingServices. MIT License.
; Close a running copy before replacing its files
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
Name: "ffmpeg"; Description: "Install FFmpeg with winget (required; not found on this PC)"; Check: not FfmpegFound
Name: "extras"; Description: "Also install Tesseract OCR (automatic blurring) and Pandoc (Word export) with winget"; Flags: unchecked

[Files]
Source: "..\dist\Screencap-Documentation-Tool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; An upgrade replaces the bundled runtime completely
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; AppUserModelID: "{#AppUserModelId}"; Comment: "Capture a screenshot of every step in screen recordings"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; AppUserModelID: "{#AppUserModelId}"; Tasks: desktopicon

[Run]
Filename: "{cmd}"; Parameters: "/c winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements --scope {code:WingetScope}"; StatusMsg: "Installing FFmpeg with winget..."; Flags: runhidden waituntilterminated; Tasks: ffmpeg
Filename: "{cmd}"; Parameters: "/c winget install --id UB-Mannheim.TesseractOCR -e --accept-source-agreements --accept-package-agreements"; StatusMsg: "Installing Tesseract OCR with winget..."; Flags: runhidden waituntilterminated; Tasks: extras
Filename: "{cmd}"; Parameters: "/c winget install --id JohnMacFarlane.Pandoc -e --accept-source-agreements --accept-package-agreements --scope {code:WingetScope}"; StatusMsg: "Installing Pandoc with winget..."; Flags: runhidden waituntilterminated; Tasks: extras
Filename: "{app}\{#AppExe}"; Description: "Start {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
function FfmpegFound: Boolean;
begin
  Result := (FileSearch('ffmpeg.exe', GetEnv('PATH')) <> '') or
            FileExists(AddBackslash(WizardDirValue) + 'tools\ffmpeg\bin\ffmpeg.exe');
end;

function WingetScope(Param: String): String;
begin
  if IsAdminInstallMode then
    Result := 'machine'
  else
    Result := 'user';
end;
