; installer.iss
; 2026-10-10
; Version: v1.2.0
;
; PURPOSE:
; Inno Setup script for the Windows installer of the packaged app (built
; first with packaging/screencap.spec). Installs for all users in
; C:\Program Files\ILHS\Screencap-Documentation-Tool (the default; needs admin
; rights) or, when chosen, for the current user only in
; %LOCALAPPDATA%\Programs\ILHS\Screencap-Documentation-Tool (no admin rights).
; A copy installed earlier in another folder (versions before 1.19.0 used
; ...\Screencap Documentation Tool) is removed first. When a copy is already
; installed, setup runs as an update: it skips the license, folder, and
; (when FFmpeg is found) options pages, and says which version it updates. Adds a Start Menu shortcut
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
; Every app from this organization installs under an ILHS folder
DefaultDirName={autopf}\ILHS\Screencap-Documentation-Tool
; Upgrades move older copies to the folder above (see PrepareToInstall)
UsePreviousAppDir=no
; No "folder already exists" question: an existing copy is updated (see [Code])
DirExistsWarning=no
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; All users by default (Program Files); the first page offers "Install for
; me only" (no admin rights). /ALLUSERS or /CURRENTUSER on the command line.
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog commandline
UsePreviousPrivileges=no
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

[UninstallDelete]
; The shared ILHS folder, once no other app from this organization is in it
Type: dirifempty; Name: "{autopf}\ILHS"

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

const
  UninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{39ABD99E-CAC0-48C0-B602-EF8172627F70}_is1';

{ Silently uninstall a copy registered under RootKey when it lives in
  another folder than the one being installed to. Returns an error message,
  or '' when there was nothing to do or it worked. }
function RemoveOldCopy(RootKey: Integer; const NewDir: String): String;
var
  OldDir, Uninstaller: String;
  ResultCode, I: Integer;
begin
  Result := '';
  if not RegQueryStringValue(RootKey, UninstallKey, 'InstallLocation', OldDir) then
    Exit;
  OldDir := RemoveBackslashUnlessRoot(OldDir);
  if CompareText(OldDir, RemoveBackslashUnlessRoot(NewDir)) = 0 then
    Exit;
  if not RegQueryStringValue(RootKey, UninstallKey, 'UninstallString', Uninstaller) then
    Exit;
  Uninstaller := RemoveQuotes(Uninstaller);
  if not FileExists(Uninstaller) then
    Exit;
  Log('Removing the copy installed earlier in ' + OldDir);
  if not Exec(Uninstaller, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '', SW_HIDE,
              ewWaitUntilTerminated, ResultCode) then
  begin
    Result := 'Could not remove the copy installed earlier in ' + OldDir +
              '. Uninstall it from Settings > Apps, then run this setup again.';
    Exit;
  end;
  { The uninstaller finishes from a copy of itself: wait for the files to go }
  for I := 1 to 60 do
  begin
    if not FileExists(Uninstaller) then
      Break;
    Sleep(500);
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := RemoveOldCopy(HKCU, WizardDirValue);
  if (Result = '') and IsAdminInstallMode then
    Result := RemoveOldCopy(HKLM, WizardDirValue);
end;

var
  UpdateMode: Boolean;     { a copy is already installed: this run updates it }
  OldVersion, OldDir: String;

function FindInstalled(RootKey: Integer): Boolean;
begin
  Result := RegQueryStringValue(RootKey, UninstallKey, 'InstallLocation', OldDir);
  if Result then
  begin
    OldDir := RemoveBackslashUnlessRoot(OldDir);
    if not RegQueryStringValue(RootKey, UninstallKey, 'DisplayVersion', OldVersion) then
      OldVersion := '';
  end;
end;

procedure InitializeWizard;
begin
  { All users: a copy for all users, or one for this user only (moved by
    PrepareToInstall). Only me: a copy for this user. }
  if IsAdminInstallMode then
    UpdateMode := FindInstalled(HKLM) or FindInstalled(HKCU)
  else
    UpdateMode := FindInstalled(HKCU);
  if UpdateMode then
    Log('Update mode: v' + OldVersion + ' is installed in ' + OldDir)
  else
    Log('New installation');
end;

{ An update keeps the license (already accepted), the folder (always the
  standard one), and the options chosen last time. The options page is still
  shown when FFmpeg is missing, so it can be installed. }
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := UpdateMode and ((PageID = wpLicense) or (PageID = wpSelectDir) or
            ((PageID = wpSelectTasks) and FfmpegFound));
end;

procedure CurPageChanged(CurPageID: Integer);
var
  Action: String;
begin
  if not UpdateMode then
    Exit;
  if CompareText(OldVersion, '{#AppVersion}') = 0 then
    Action := 'reinstall v{#AppVersion} of {#AppName}'
  else if OldVersion <> '' then
    Action := 'update {#AppName} from v' + OldVersion + ' to v{#AppVersion}'
  else
    Action := 'update {#AppName} to v{#AppVersion}';
  if CurPageID = wpReady then
  begin
    WizardForm.PageNameLabel.Caption := 'Ready to Update';
    WizardForm.PageDescriptionLabel.Caption := 'Setup is ready to ' + Action + '.';
    WizardForm.ReadyLabel.Caption := '{#AppName} is already installed in ' + OldDir +
      '. Click Update to replace it with this version. Your recordings, output, ' +
      'settings, and presets are kept.';
    WizardForm.NextButton.Caption := 'Update';
  end
  else if CurPageID = wpFinished then
    WizardForm.FinishedLabel.Caption := '{#AppName} has been updated to v{#AppVersion}.';
end;

function WingetScope(Param: String): String;
begin
  if IsAdminInstallMode then
    Result := 'machine'
  else
    Result := 'user';
end;
