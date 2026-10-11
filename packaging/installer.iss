; installer.iss
; 2026-10-11
; Version: v1.3.0
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
; (when FFmpeg is found) options pages, and says which version it updates.
; A page asks where recordings (source) and screenshots (output) should go:
; the defaults are the source and output folders inside the install folder
; (for an all-users install they are made writable for all users), or any
; folders the user picks. The choice is stored under
; HKLM or HKCU\Software\ILHS\Screencap Documentation Tool, where the app
; reads it (apppaths.py). Silent installs take /SOURCEDIR="..." and
; /OUTPUTDIR="..."; an update keeps the folders chosen before.
; Adds a Start Menu shortcut with the app's taskbar identity, an optional
; desktop shortcut, and an uninstaller; and can install FFmpeg (required)
; and, optionally, Tesseract OCR and Pandoc with winget. Recordings, output,
; and settings are never touched by uninstalling.
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

[Dirs]
; The recordings and output folders. Inside the install folder (the
; defaults) an empty one is removed on uninstall; folders the user picked
; elsewhere are never removed. Files in them are never deleted.
Name: "{code:GetSourceDir}"; Permissions: users-modify; Check: FoldersInApp and IsAdminInstallMode
Name: "{code:GetOutputDir}"; Permissions: users-modify; Check: FoldersInApp and IsAdminInstallMode
Name: "{code:GetSourceDir}"; Check: FoldersInApp and not IsAdminInstallMode
Name: "{code:GetOutputDir}"; Check: FoldersInApp and not IsAdminInstallMode
Name: "{code:GetSourceDir}"; Flags: uninsneveruninstall; Check: not FoldersInApp
Name: "{code:GetOutputDir}"; Flags: uninsneveruninstall; Check: not FoldersInApp

[Registry]
; HKA: HKLM for an all-users install, HKCU for "only for me"
Root: HKA; Subkey: "Software\ILHS"; Flags: uninsdeletekeyifempty
Root: HKA; Subkey: "Software\ILHS\Screencap Documentation Tool"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\ILHS\Screencap Documentation Tool"; ValueType: string; ValueName: "SourceDir"; ValueData: "{code:GetSourceDir}"
Root: HKA; Subkey: "Software\ILHS\Screencap Documentation Tool"; ValueType: string; ValueName: "OutputDir"; ValueData: "{code:GetOutputDir}"
Root: HKA; Subkey: "Software\ILHS\Screencap Documentation Tool"; ValueType: string; ValueName: "FolderMode"; ValueData: "{code:GetFolderMode}"
Root: HKA; Subkey: "Software\ILHS\Screencap Documentation Tool"; ValueType: string; ValueName: "FoldersStamp"; ValueData: "{code:GetFoldersStamp}"

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

const
  FoldersKey = 'Software\ILHS\Screencap Documentation Tool';

var
  UpdateMode: Boolean;     { a copy is already installed: this run updates it }
  OldVersion, OldDir: String;
  FolderModePage: TInputOptionWizardPage;
  FolderDirPage: TInputDirWizardPage;
  HavePrevFolders: Boolean;          { an earlier install recorded its folders }
  PrevSource, PrevOutput, PrevMode, PrevStamp: String;
  FoldersDecided: Boolean;
  FinalSource, FinalOutput, FinalMode, FinalStamp: String;

function FoldersRoot: Integer;
begin
  if IsAdminInstallMode then
    Result := HKLM
  else
    Result := HKCU;
end;

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

  HavePrevFolders := RegQueryStringValue(FoldersRoot, FoldersKey, 'SourceDir', PrevSource) and
                     RegQueryStringValue(FoldersRoot, FoldersKey, 'OutputDir', PrevOutput) and
                     (PrevSource <> '') and (PrevOutput <> '');
  if not RegQueryStringValue(FoldersRoot, FoldersKey, 'FolderMode', PrevMode) then
    PrevMode := '';
  if not RegQueryStringValue(FoldersRoot, FoldersKey, 'FoldersStamp', PrevStamp) then
    PrevStamp := '';

  FolderModePage := CreateInputOptionPage(wpSelectDir,
    'Recordings and Output Folders',
    'Where should your recordings and screenshots be kept?',
    'The source folder holds the screen recordings to process. The output folder ' +
    'gets the screenshots and documents made from them. Both can be changed later ' +
    'in the app.', True, False);
  FolderModePage.Add('Use the default folders (source and output in the install folder)');
  FolderModePage.Add('Choose my own folders');
  if HavePrevFolders and (PrevMode = 'custom') then
    FolderModePage.SelectedValueIndex := 1
  else
    FolderModePage.SelectedValueIndex := 0;

  FolderDirPage := CreateInputDirPage(FolderModePage.ID,
    'Choose Folders', 'Pick the source and output folders.',
    'Setup creates the folders if they do not exist yet. Files already in them are kept.',
    False, '');
  FolderDirPage.Add('Source folder (screen recordings):');
  FolderDirPage.Add('Output folder (screenshots and documents):');
  if HavePrevFolders then
  begin
    FolderDirPage.Values[0] := PrevSource;
    FolderDirPage.Values[1] := PrevOutput;
  end
  else
  begin
    FolderDirPage.Values[0] := ExpandConstant('{userdocs}\Screencap Documentation Tool\source');
    FolderDirPage.Values[1] := ExpandConstant('{userdocs}\Screencap Documentation Tool\output');
  end;
end;

function DefaultFolder(const Name: String): String;
begin
  Result := AddBackslash(WizardDirValue) + Name;
end;

{ The folders to record, decided once when they are first needed:
  /SOURCEDIR and /OUTPUTDIR win; an update keeps the earlier choice; else the
  page's choice (silent: the defaults). The stamp changes only when the
  folders were chosen in this run, so the app applies a choice once. An update
  from a version without this page, run silently (for example by winget),
  records the folders with an empty stamp: the app keeps its own settings. }
procedure DecideFolders;
var
  ParamSource, ParamOutput: String;
  Chosen: Boolean;
begin
  if FoldersDecided then
    Exit;
  FoldersDecided := True;
  ParamSource := ExpandConstant('{param:SOURCEDIR|}');
  ParamOutput := ExpandConstant('{param:OUTPUTDIR|}');
  Chosen := True;
  if (ParamSource <> '') or (ParamOutput <> '') then
  begin
    FinalMode := 'custom';
    FinalSource := ParamSource;
    FinalOutput := ParamOutput;
    if FinalSource = '' then FinalSource := DefaultFolder('source');
    if FinalOutput = '' then FinalOutput := DefaultFolder('output');
  end
  else if UpdateMode and HavePrevFolders then
  begin
    FinalMode := PrevMode;
    FinalSource := PrevSource;
    FinalOutput := PrevOutput;
    Chosen := False;
  end
  else if (not WizardSilent) and (FolderModePage.SelectedValueIndex = 1) then
  begin
    FinalMode := 'custom';
    FinalSource := RemoveBackslashUnlessRoot(FolderDirPage.Values[0]);
    FinalOutput := RemoveBackslashUnlessRoot(FolderDirPage.Values[1]);
  end
  else
  begin
    FinalMode := 'default';
    FinalSource := DefaultFolder('source');
    FinalOutput := DefaultFolder('output');
    Chosen := not (UpdateMode and WizardSilent);
  end;
  if Chosen then
    FinalStamp := GetDateTimeString('yyyymmddhhnnss', #0, #0)
  else if UpdateMode and HavePrevFolders then
    FinalStamp := PrevStamp
  else
    FinalStamp := '';
  Log('Folders (' + FinalMode + '): source ' + FinalSource + ', output ' + FinalOutput +
      ', stamp "' + FinalStamp + '"');
end;

function GetSourceDir(Param: String): String;
begin
  DecideFolders;
  Result := FinalSource;
end;

function GetOutputDir(Param: String): String;
begin
  DecideFolders;
  Result := FinalOutput;
end;

function GetFolderMode(Param: String): String;
begin
  DecideFolders;
  Result := FinalMode;
end;

function GetFoldersStamp(Param: String): String;
begin
  DecideFolders;
  Result := FinalStamp;
end;

{ True when both folders are inside the install folder (the defaults) }
function FoldersInApp: Boolean;
var
  App: String;
begin
  DecideFolders;
  App := Lowercase(AddBackslash(WizardDirValue));
  Result := (Pos(App, Lowercase(AddBackslash(FinalSource))) = 1) and
            (Pos(App, Lowercase(AddBackslash(FinalOutput))) = 1);
end;

{ An update keeps the license (already accepted), the folder (always the
  standard one), and the options chosen last time. The options page is still
  shown when FFmpeg is missing, so it can be installed. }
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  if PageID = FolderModePage.ID then
    { asked again only when an earlier version never recorded the folders }
    Result := UpdateMode and HavePrevFolders
  else if PageID = FolderDirPage.ID then
    Result := (UpdateMode and HavePrevFolders) or (FolderModePage.SelectedValueIndex = 0)
  else
    Result := UpdateMode and ((PageID = wpLicense) or (PageID = wpSelectDir) or
              ((PageID = wpSelectTasks) and FfmpegFound));
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = FolderDirPage.ID) and
     ((Trim(FolderDirPage.Values[0]) = '') or (Trim(FolderDirPage.Values[1]) = '')) then
  begin
    MsgBox('Choose both a source folder and an output folder.', mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
var
  Action: String;
begin
  if CurPageID = FolderModePage.ID then
    FolderModePage.CheckListBox.ItemCaption[0] := 'Use the default folders: ' +
      DefaultFolder('source') + ' and ' + DefaultFolder('output');
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

{ The shared ILHS folder, once empty. [UninstallDelete] does this too, but
  after setup ran twice over one copy it can run before the program folder
  is gone; at this point everything else has been removed. }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    if RemoveDir(ExpandConstant('{autopf}\ILHS')) then
      Log('Removed the empty ILHS folder');
end;

function WingetScope(Param: String): String;
begin
  if IsAdminInstallMode then
    Result := 'machine'
  else
    Result := 'user';
end;
