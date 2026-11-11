; installer.iss
; 2026-11-11
; Version: v1.9.0
;
; PURPOSE:
; Inno Setup script for the Windows installer of ScreenCap Docs, the packaged
; app (built first with packaging/screencap.spec). Until v1.34.1 the app was
; called Screencap Documentation Tool: the program file, the install folder,
; the registry key, and the AppId keep that name so updates, taskbar pins,
; and application allow-lists keep working; only the shown name changed. Installs for all users in
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
; and, optionally, Tesseract OCR and Pandoc with winget. The program folder
; is added to the PATH (the system PATH for all users, the user's own PATH
; for "only for me") so the screencap command works in any terminal; this is
; on by default, /MERGETASKS="!addtopath" leaves it out, and uninstalling
; takes it out again. Recordings, output, and settings are never touched by
; uninstalling.
; Setup speaks English, Spanish, French, German, or Portuguese (Brazil),
; whichever matches Windows (asked only when none does; /LANG=german and so
; on choose one). Inno Setup's own pages use its translations; the text
; this script adds is in [CustomMessages], just before [Code].
;
; Build from the repository root, after the PyInstaller build:
;   iscc /DAppVersion=1.16.0 packaging\installer.iss                (x64 PCs)
;   iscc /DAppVersion=1.16.0 /DArch=arm64 packaging\installer.iss   (Windows on ARM,
;        from a PyInstaller build made with ARM64 Python)
; Output: release\Screencap-Documentation-Tool-v<version>-windows-<x64|arm64>-setup.exe
; The x64 installer also runs on Windows 11 on ARM (x64 emulation); both use
; the same AppId, so either one updates a copy installed by the other.

#define AppName "ScreenCap Docs"
#define OldAppName "Screencap Documentation Tool"
#define AppExe "Screencap Documentation Tool.exe"
#define AppUserModelId "ILHS.ScreencapDocumentationTool.GUI"
#ifndef Arch
  #define Arch "x64"
#endif
#if Arch != "x64" && Arch != "arm64"
  #error Arch must be x64 or arm64
#endif
#ifndef AppVersion
  #error Pass the version: iscc /DAppVersion=X.Y.Z packaging\installer.iss
#endif

[Setup]
; Never change AppId: Windows uses it to recognize upgrades and to uninstall
AppId={{39ABD99E-CAC0-48C0-B602-EF8172627F70}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher=ILHS Software, LLC
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
; me only" (no admin rights). An update keeps the choice of the installed
; copy without asking again. /ALLUSERS or /CURRENTUSER on the command line
; override both.
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog commandline
UsePreviousPrivileges=yes
#if Arch == "arm64"
ArchitecturesAllowed=arm64
ArchitecturesInstallIn64BitMode=arm64
#else
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
#endif
LicenseFile=..\LICENSE
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
OutputDir=..\release
OutputBaseFilename=Screencap-Documentation-Tool-v{#AppVersion}-windows-{#Arch}-setup
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany=ILHS Software, LLC
VersionInfoDescription={#AppName} Setup
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
VersionInfoCopyright=(c) 2026 ILHS Software, LLC. MIT License.
; Close a running copy before replacing its files
CloseApplications=yes
; Tell open programs (Explorer, new terminals) that the PATH changed
ChangesEnvironment=yes
; The language of Windows, without asking, when setup has it
ShowLanguageDialog=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked
Name: "addtopath"; Description: "{cm:TaskPath}"
Name: "ffmpeg"; Description: "{cm:TaskFfmpeg}"; Check: not FfmpegFound
; Offered only while one of them is missing, so an update never runs winget again for nothing
Name: "extras"; Description: "{cm:TaskExtras}"; Flags: unchecked; Check: not ExtrasFound

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
; Shortcuts with the name used before v1.35.0 (new ones are made below)
Type: files; Name: "{autoprograms}\{#OldAppName}.lnk"
Type: files; Name: "{autodesktop}\{#OldAppName}.lnk"

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; AppUserModelID: "{#AppUserModelId}"; Comment: "{cm:ShortcutComment}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; AppUserModelID: "{#AppUserModelId}"; Tasks: desktopicon

[Run]
Filename: "{cmd}"; Parameters: "/c winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements --scope {code:WingetScope}"; StatusMsg: "{cm:InstallingWith,FFmpeg}"; Flags: runhidden waituntilterminated; Tasks: ffmpeg
Filename: "{cmd}"; Parameters: "/c winget install --id UB-Mannheim.TesseractOCR -e --accept-source-agreements --accept-package-agreements"; StatusMsg: "{cm:InstallingWith,Tesseract OCR}"; Flags: runhidden waituntilterminated; Tasks: extras
Filename: "{cmd}"; Parameters: "/c winget install --id JohnMacFarlane.Pandoc -e --accept-source-agreements --accept-package-agreements --scope {code:WingetScope}"; StatusMsg: "{cm:InstallingWith,Pandoc}"; Flags: runhidden waituntilterminated; Tasks: extras
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; Update Now in the app runs setup silently with /RELAUNCH=1: open the app
; again afterwards, as the signed-in user (not as administrator)
Filename: "{app}\{#AppExe}"; Flags: nowait runasoriginaluser; Check: RelaunchAfterUpdate

[CustomMessages]
; The text this script adds, in each language of [Languages]. %1, %2, %3
; are filled in by the code (FmtMessage) or by {cm:Name,value}.

english.TaskPath=Add the screencap command to the PATH (use it in any terminal)
english.TaskFfmpeg=Install FFmpeg with winget (required, and not found on this PC)
english.TaskExtras=Also install Tesseract OCR (automatic blurring) and Pandoc (Word export) with winget
english.ShortcutComment=Capture a screenshot of every step in screen recordings
english.InstallingWith=Installing %1 with winget...
english.RemoveOldFailed=Setup could not remove the copy installed earlier in %1. Uninstall it from Settings > Apps, then run this setup again.
english.FoldersTitle=Recordings and Output Folders
english.FoldersQuestion=Where should your recordings and screenshots be kept?
english.FoldersInfo=The source folder holds the screen recordings to process. The output folder receives the screenshots and documents made from them. You can change both later in the app.
english.FoldersDefault=Use the default folders (recommended)
english.FoldersOwn=Choose my own folders
english.ChooseTitle=Choose Folders
english.ChooseQuestion=Where should the source and output folders be?
english.ChooseInfo=Setup creates any folder that does not exist yet. Files already in a folder are kept.
english.SourcePrompt=Source folder (screen recordings):
english.OutputPrompt=Output folder (screenshots and documents):
english.BothFolders=Choose both a source folder and an output folder.
english.DefaultFolders=The default folders are:
english.SourceLabel=Source:
english.OutputLabel=Output:
english.FinishedInstalled=%1 v%2 is installed. Start it from the Start Menu.
english.ClickFinish=Click Finish to close Setup.
english.ReadyReinstallText=Setup is ready to reinstall %1 v%2.
english.ReadyUpdateFromText=Setup is ready to update %1 from v%2 to v%3.
english.ReadyUpdateText=Setup is ready to update %1 to v%2.
english.ReadyReinstallTitle=Ready to Reinstall
english.ReinstallButton=Reinstall
english.ReadyUpdateTitle=Ready to Update
english.UpdateButton=Update
english.ReadyReplace=Click %1 to replace the installed copy with this version. Your recordings, output, settings, and presets are kept.
english.FinishedReinstalled=%1 v%2 has been reinstalled.
english.FinishedUpdated=%1 has been updated to v%2.
english.MemoFolders=Recordings and output folders:
english.MemoKept=Kept from the current installation:
english.MemoStartMenu=Start Menu shortcut
english.MemoDesktop=Desktop shortcut
english.MemoPath=The screencap command on the PATH
english.MemoSettings=Settings and saved presets
english.MemoFfmpeg=FFmpeg (not found on this PC)
english.MemoExtras=Tesseract OCR and Pandoc (not both found on this PC)
english.MemoWinget=Also installed with winget:

spanish.TaskPath=Añadir el comando screencap al PATH (usarlo en cualquier terminal)
spanish.TaskFfmpeg=Instalar FFmpeg con winget (necesario y no encontrado en este equipo)
spanish.TaskExtras=Instalar también Tesseract OCR (difuminado automático) y Pandoc (exportar a Word) con winget
spanish.ShortcutComment=Captura cada paso de las grabaciones de pantalla
spanish.InstallingWith=Instalando %1 con winget...
spanish.RemoveOldFailed=El instalador no pudo quitar la copia instalada antes en %1. Desinstálela desde Configuración > Aplicaciones y vuelva a ejecutar este instalador.
spanish.FoldersTitle=Carpetas de grabaciones y de salida
spanish.FoldersQuestion=¿Dónde se guardan sus grabaciones y capturas?
spanish.FoldersInfo=La carpeta de origen contiene las grabaciones que se van a procesar. La carpeta de salida recibe las capturas y los documentos creados a partir de ellas. Puede cambiar ambas más tarde en la aplicación.
spanish.FoldersDefault=Usar las carpetas predeterminadas (recomendado)
spanish.FoldersOwn=Elegir mis propias carpetas
spanish.ChooseTitle=Elegir carpetas
spanish.ChooseQuestion=¿Dónde deben estar las carpetas de origen y de salida?
spanish.ChooseInfo=El instalador crea las carpetas que aún no existan. Los archivos que ya haya en una carpeta se conservan.
spanish.SourcePrompt=Carpeta de origen (grabaciones de pantalla):
spanish.OutputPrompt=Carpeta de salida (capturas y documentos):
spanish.BothFolders=Elija una carpeta de origen y una de salida.
spanish.DefaultFolders=Las carpetas predeterminadas son:
spanish.SourceLabel=Origen:
spanish.OutputLabel=Salida:
spanish.FinishedInstalled=%1 v%2 está instalado. Inícielo desde el menú Inicio.
spanish.ClickFinish=Haga clic en Finalizar para cerrar el instalador.
spanish.ReadyReinstallText=El instalador está listo para reinstalar %1 v%2.
spanish.ReadyUpdateFromText=El instalador está listo para actualizar %1 de v%2 a v%3.
spanish.ReadyUpdateText=El instalador está listo para actualizar %1 a v%2.
spanish.ReadyReinstallTitle=Listo para reinstalar
spanish.ReinstallButton=Reinstalar
spanish.ReadyUpdateTitle=Listo para actualizar
spanish.UpdateButton=Actualizar
spanish.ReadyReplace=Haga clic en %1 para sustituir la copia instalada por esta versión. Se conservan sus grabaciones, salida, ajustes y ajustes predefinidos.
spanish.FinishedReinstalled=%1 v%2 se ha reinstalado.
spanish.FinishedUpdated=%1 se ha actualizado a v%2.
spanish.MemoFolders=Carpetas de grabaciones y de salida:
spanish.MemoKept=Se conserva de la instalación actual:
spanish.MemoStartMenu=Acceso directo en el menú Inicio
spanish.MemoDesktop=Acceso directo en el escritorio
spanish.MemoPath=El comando screencap en el PATH
spanish.MemoSettings=Ajustes y ajustes predefinidos guardados
spanish.MemoFfmpeg=FFmpeg (no encontrado en este equipo)
spanish.MemoExtras=Tesseract OCR y Pandoc (no se encontraron ambos en este equipo)
spanish.MemoWinget=También se instala con winget:

french.TaskPath=Ajouter la commande screencap au PATH (l'utiliser dans tout terminal)
french.TaskFfmpeg=Installer FFmpeg avec winget (requis, introuvable sur ce PC)
french.TaskExtras=Installer aussi Tesseract OCR (floutage automatique) et Pandoc (export Word) avec winget
french.ShortcutComment=Capture chaque étape des enregistrements d'écran
french.InstallingWith=Installation de %1 avec winget...
french.RemoveOldFailed=Le programme d'installation n'a pas pu supprimer la copie installée auparavant dans %1. Désinstallez-la depuis Paramètres > Applications, puis relancez cette installation.
french.FoldersTitle=Dossiers des enregistrements et de sortie
french.FoldersQuestion=Où conserver vos enregistrements et captures ?
french.FoldersInfo=Le dossier source contient les enregistrements à traiter. Le dossier de sortie reçoit les captures et documents créés à partir d'eux. Vous pourrez changer les deux plus tard dans l'application.
french.FoldersDefault=Utiliser les dossiers par défaut (recommandé)
french.FoldersOwn=Choisir mes propres dossiers
french.ChooseTitle=Choisir les dossiers
french.ChooseQuestion=Où placer les dossiers source et de sortie ?
french.ChooseInfo=L'installation crée les dossiers qui n'existent pas encore. Les fichiers déjà présents sont conservés.
french.SourcePrompt=Dossier source (enregistrements d'écran) :
french.OutputPrompt=Dossier de sortie (captures et documents) :
french.BothFolders=Choisissez un dossier source et un dossier de sortie.
french.DefaultFolders=Les dossiers par défaut sont :
french.SourceLabel=Source :
french.OutputLabel=Sortie :
french.FinishedInstalled=%1 v%2 est installé. Lancez-le depuis le menu Démarrer.
french.ClickFinish=Cliquez sur Terminer pour fermer l'installation.
french.ReadyReinstallText=L'installation est prête à réinstaller %1 v%2.
french.ReadyUpdateFromText=L'installation est prête à mettre à jour %1 de v%2 vers v%3.
french.ReadyUpdateText=L'installation est prête à mettre à jour %1 vers v%2.
french.ReadyReinstallTitle=Prêt à réinstaller
french.ReinstallButton=Réinstaller
french.ReadyUpdateTitle=Prêt à mettre à jour
french.UpdateButton=Mettre à jour
french.ReadyReplace=Cliquez sur %1 pour remplacer la copie installée. Vos enregistrements, sorties, paramètres et préréglages sont conservés.
french.FinishedReinstalled=%1 v%2 a été réinstallé.
french.FinishedUpdated=%1 a été mis à jour vers v%2.
french.MemoFolders=Dossiers des enregistrements et de sortie :
french.MemoKept=Conservé de l'installation actuelle :
french.MemoStartMenu=Raccourci du menu Démarrer
french.MemoDesktop=Raccourci sur le bureau
french.MemoPath=La commande screencap dans le PATH
french.MemoSettings=Paramètres et préréglages enregistrés
french.MemoFfmpeg=FFmpeg (introuvable sur ce PC)
french.MemoExtras=Tesseract OCR et Pandoc (pas tous deux trouvés sur ce PC)
french.MemoWinget=Également installé avec winget :

german.TaskPath=Den Befehl screencap zum PATH hinzufügen (in jedem Terminal nutzbar)
german.TaskFfmpeg=FFmpeg mit winget installieren (erforderlich, auf diesem PC nicht gefunden)
german.TaskExtras=Auch Tesseract OCR (automatisches Unkenntlichmachen) und Pandoc (Word-Export) mit winget installieren
german.ShortcutComment=Ein Screenshot für jeden Schritt in Bildschirmaufnahmen
german.InstallingWith=%1 wird mit winget installiert...
german.RemoveOldFailed=Setup konnte die früher in %1 installierte Kopie nicht entfernen. Deinstallieren Sie sie unter Einstellungen > Apps und starten Sie dieses Setup erneut.
german.FoldersTitle=Aufnahme- und Ausgabeordner
german.FoldersQuestion=Wo sollen Ihre Aufnahmen und Screenshots liegen?
german.FoldersInfo=Der Quellordner enthält die zu verarbeitenden Bildschirmaufnahmen. Der Ausgabeordner erhält die daraus erstellten Screenshots und Dokumente. Beides können Sie später in der App ändern.
german.FoldersDefault=Standardordner verwenden (empfohlen)
german.FoldersOwn=Eigene Ordner wählen
german.ChooseTitle=Ordner wählen
german.ChooseQuestion=Wo sollen Quell- und Ausgabeordner liegen?
german.ChooseInfo=Setup legt fehlende Ordner an. Vorhandene Dateien in einem Ordner bleiben erhalten.
german.SourcePrompt=Quellordner (Bildschirmaufnahmen):
german.OutputPrompt=Ausgabeordner (Screenshots und Dokumente):
german.BothFolders=Wählen Sie einen Quell- und einen Ausgabeordner.
german.DefaultFolders=Die Standardordner sind:
german.SourceLabel=Quelle:
german.OutputLabel=Ausgabe:
german.FinishedInstalled=%1 v%2 ist installiert. Starten Sie es über das Startmenü.
german.ClickFinish=Klicken Sie auf Fertigstellen, um Setup zu beenden.
german.ReadyReinstallText=Setup ist bereit, %1 v%2 neu zu installieren.
german.ReadyUpdateFromText=Setup ist bereit, %1 von v%2 auf v%3 zu aktualisieren.
german.ReadyUpdateText=Setup ist bereit, %1 auf v%2 zu aktualisieren.
german.ReadyReinstallTitle=Bereit zur Neuinstallation
german.ReinstallButton=Neu installieren
german.ReadyUpdateTitle=Bereit zum Aktualisieren
german.UpdateButton=Aktualisieren
german.ReadyReplace=Klicken Sie auf %1, um die installierte Kopie zu ersetzen. Aufnahmen, Ausgaben, Einstellungen und Voreinstellungen bleiben erhalten.
german.FinishedReinstalled=%1 v%2 wurde neu installiert.
german.FinishedUpdated=%1 wurde auf v%2 aktualisiert.
german.MemoFolders=Aufnahme- und Ausgabeordner:
german.MemoKept=Aus der aktuellen Installation übernommen:
german.MemoStartMenu=Verknüpfung im Startmenü
german.MemoDesktop=Desktopverknüpfung
german.MemoPath=Der Befehl screencap im PATH
german.MemoSettings=Einstellungen und gespeicherte Voreinstellungen
german.MemoFfmpeg=FFmpeg (auf diesem PC nicht gefunden)
german.MemoExtras=Tesseract OCR und Pandoc (nicht beide auf diesem PC gefunden)
german.MemoWinget=Außerdem mit winget installiert:

brazilianportuguese.TaskPath=Adicionar o comando screencap ao PATH (usar em qualquer terminal)
brazilianportuguese.TaskFfmpeg=Instalar o FFmpeg com o winget (necessário e não encontrado neste PC)
brazilianportuguese.TaskExtras=Instalar também o Tesseract OCR (desfoque automático) e o Pandoc (exportação para Word) com o winget
brazilianportuguese.ShortcutComment=Captura cada etapa das gravações de tela
brazilianportuguese.InstallingWith=Instalando %1 com o winget...
brazilianportuguese.RemoveOldFailed=O instalador não conseguiu remover a cópia instalada antes em %1. Desinstale-a em Configurações > Aplicativos e execute este instalador novamente.
brazilianportuguese.FoldersTitle=Pastas de gravações e de saída
brazilianportuguese.FoldersQuestion=Onde suas gravações e capturas devem ficar?
brazilianportuguese.FoldersInfo=A pasta de origem guarda as gravações de tela a processar. A pasta de saída recebe as capturas e os documentos criados a partir delas. Você pode mudar as duas depois no aplicativo.
brazilianportuguese.FoldersDefault=Usar as pastas padrão (recomendado)
brazilianportuguese.FoldersOwn=Escolher minhas próprias pastas
brazilianportuguese.ChooseTitle=Escolher pastas
brazilianportuguese.ChooseQuestion=Onde devem ficar as pastas de origem e de saída?
brazilianportuguese.ChooseInfo=O instalador cria as pastas que ainda não existem. Os arquivos já presentes em uma pasta são mantidos.
brazilianportuguese.SourcePrompt=Pasta de origem (gravações de tela):
brazilianportuguese.OutputPrompt=Pasta de saída (capturas e documentos):
brazilianportuguese.BothFolders=Escolha uma pasta de origem e uma de saída.
brazilianportuguese.DefaultFolders=As pastas padrão são:
brazilianportuguese.SourceLabel=Origem:
brazilianportuguese.OutputLabel=Saída:
brazilianportuguese.FinishedInstalled=O %1 v%2 está instalado. Abra-o pelo menu Iniciar.
brazilianportuguese.ClickFinish=Clique em Concluir para fechar o instalador.
brazilianportuguese.ReadyReinstallText=O instalador está pronto para reinstalar o %1 v%2.
brazilianportuguese.ReadyUpdateFromText=O instalador está pronto para atualizar o %1 da v%2 para a v%3.
brazilianportuguese.ReadyUpdateText=O instalador está pronto para atualizar o %1 para a v%2.
brazilianportuguese.ReadyReinstallTitle=Pronto para reinstalar
brazilianportuguese.ReinstallButton=Reinstalar
brazilianportuguese.ReadyUpdateTitle=Pronto para atualizar
brazilianportuguese.UpdateButton=Atualizar
brazilianportuguese.ReadyReplace=Clique em %1 para substituir a cópia instalada por esta versão. Gravações, saídas, configurações e predefinições são mantidas.
brazilianportuguese.FinishedReinstalled=O %1 v%2 foi reinstalado.
brazilianportuguese.FinishedUpdated=O %1 foi atualizado para a v%2.
brazilianportuguese.MemoFolders=Pastas de gravações e de saída:
brazilianportuguese.MemoKept=Mantido da instalação atual:
brazilianportuguese.MemoStartMenu=Atalho no menu Iniciar
brazilianportuguese.MemoDesktop=Atalho na área de trabalho
brazilianportuguese.MemoPath=O comando screencap no PATH
brazilianportuguese.MemoSettings=Configurações e predefinições salvas
brazilianportuguese.MemoFfmpeg=FFmpeg (não encontrado neste PC)
brazilianportuguese.MemoExtras=Tesseract OCR e Pandoc (os dois não foram encontrados neste PC)
brazilianportuguese.MemoWinget=Também instalado com o winget:

[Code]
function FfmpegFound: Boolean;
begin
  Result := (FileSearch('ffmpeg.exe', GetEnv('PATH')) <> '') or
            FileExists(AddBackslash(WizardDirValue) + 'tools\ffmpeg\bin\ffmpeg.exe');
end;

{ Where the app itself looks for them (redact.py and export.py): the PATH,
  then the folders their installers use }
function TesseractFound: Boolean;
begin
  Result := (FileSearch('tesseract.exe', GetEnv('PATH')) <> '') or
            FileExists(ExpandConstant('{commonpf64}\Tesseract-OCR\tesseract.exe')) or
            FileExists(ExpandConstant('{commonpf32}\Tesseract-OCR\tesseract.exe')) or
            FileExists(ExpandConstant('{localappdata}\Programs\Tesseract-OCR\tesseract.exe'));
end;

function PandocFound: Boolean;
begin
  Result := (FileSearch('pandoc.exe', GetEnv('PATH')) <> '') or
            FileExists(ExpandConstant('{localappdata}\Pandoc\pandoc.exe')) or
            FileExists(ExpandConstant('{commonpf64}\Pandoc\pandoc.exe'));
end;

function ExtrasFound: Boolean;
begin
  Result := TesseractFound and PandocFound;
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
    Result := FmtMessage(CustomMessage('RemoveOldFailed'), [OldDir]);
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
  DefaultFoldersLabel: TNewStaticText;  { the default paths, under the choices }
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
var
  DocsName: String;
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
    CustomMessage('FoldersTitle'), CustomMessage('FoldersQuestion'),
    CustomMessage('FoldersInfo'), True, False);
  FolderModePage.Add(CustomMessage('FoldersDefault'));
  FolderModePage.Add(CustomMessage('FoldersOwn'));
  { Two short choices, then the default paths on lines of their own, so long
    paths never wrap in the middle of a choice }
  FolderModePage.CheckListBox.Height := ScaleY(46);
  DefaultFoldersLabel := TNewStaticText.Create(FolderModePage);
  DefaultFoldersLabel.Parent := FolderModePage.Surface;
  DefaultFoldersLabel.Left := ScaleX(18);
  DefaultFoldersLabel.Top := FolderModePage.CheckListBox.Top + FolderModePage.CheckListBox.Height + ScaleY(10);
  DefaultFoldersLabel.Width := FolderModePage.SurfaceWidth - ScaleX(18);
  DefaultFoldersLabel.AutoSize := False;
  DefaultFoldersLabel.WordWrap := True;
  DefaultFoldersLabel.Height := ScaleY(80);
  if HavePrevFolders and (PrevMode = 'custom') then
    FolderModePage.SelectedValueIndex := 1
  else
    FolderModePage.SelectedValueIndex := 0;

  FolderDirPage := CreateInputDirPage(FolderModePage.ID,
    CustomMessage('ChooseTitle'), CustomMessage('ChooseQuestion'),
    CustomMessage('ChooseInfo'), False, '');
  FolderDirPage.Add(CustomMessage('SourcePrompt'));
  FolderDirPage.Add(CustomMessage('OutputPrompt'));
  if HavePrevFolders then
  begin
    FolderDirPage.Values[0] := PrevSource;
    FolderDirPage.Values[1] := PrevOutput;
  end
  else
  begin
    { A Documents folder with the name used before v1.35.0 is kept }
    if DirExists(ExpandConstant('{userdocs}\{#OldAppName}')) then
      DocsName := '{#OldAppName}'
    else
      DocsName := '{#AppName}';
    FolderDirPage.Values[0] := ExpandConstant('{userdocs}\') + DocsName + '\source';
    FolderDirPage.Values[1] := ExpandConstant('{userdocs}\') + DocsName + '\output';
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

{ Update Now in the app (silent setup with /RELAUNCH=1) }
function RelaunchAfterUpdate: Boolean;
begin
  Result := WizardSilent and (ExpandConstant('{param:RELAUNCH|0}') = '1');
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
    MsgBox(CustomMessage('BothFolders'), mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
var
  Action: String;
  Reinstall: Boolean;
begin
  if CurPageID = FolderModePage.ID then
    DefaultFoldersLabel.Caption := CustomMessage('DefaultFolders') + #13#10 +
      CustomMessage('SourceLabel') + '  ' + DefaultFolder('source') + #13#10 +
      CustomMessage('OutputLabel') + '  ' + DefaultFolder('output');
  { A first install: Inno Setup's own text is one line too long for the label }
  if (CurPageID = wpFinished) and not UpdateMode then
    WizardForm.FinishedLabel.Caption :=
      FmtMessage(CustomMessage('FinishedInstalled'), ['{#AppName}', '{#AppVersion}']) +
      #13#10#13#10 + CustomMessage('ClickFinish');
  if not UpdateMode then
    Exit;
  Reinstall := CompareText(OldVersion, '{#AppVersion}') = 0;
  if Reinstall then
    Action := FmtMessage(CustomMessage('ReadyReinstallText'), ['{#AppName}', '{#AppVersion}'])
  else if OldVersion <> '' then
    Action := FmtMessage(CustomMessage('ReadyUpdateFromText'),
                         ['{#AppName}', OldVersion, '{#AppVersion}'])
  else
    Action := FmtMessage(CustomMessage('ReadyUpdateText'), ['{#AppName}', '{#AppVersion}']);
  if CurPageID = wpReady then
  begin
    if Reinstall then
    begin
      WizardForm.PageNameLabel.Caption := CustomMessage('ReadyReinstallTitle');
      WizardForm.NextButton.Caption := CustomMessage('ReinstallButton');
    end
    else
    begin
      WizardForm.PageNameLabel.Caption := CustomMessage('ReadyUpdateTitle');
      WizardForm.NextButton.Caption := CustomMessage('UpdateButton');
    end;
    WizardForm.PageDescriptionLabel.Caption := Action;
    { Two lines at most: the label has no room for a third (checked by the
      layout dump in build-windows.yml). The folder is in the memo below. }
    WizardForm.ReadyLabel.Caption := FmtMessage(CustomMessage('ReadyReplace'),
                                                [WizardForm.NextButton.Caption]);
  end
  else if CurPageID = wpFinished then
  begin
    if Reinstall then
      WizardForm.FinishedLabel.Caption :=
        FmtMessage(CustomMessage('FinishedReinstalled'), ['{#AppName}', '{#AppVersion}'])
    else
      WizardForm.FinishedLabel.Caption :=
        FmtMessage(CustomMessage('FinishedUpdated'), ['{#AppName}', '{#AppVersion}']);
    WizardForm.FinishedLabel.Caption := WizardForm.FinishedLabel.Caption + #13#10#13#10 +
      CustomMessage('ClickFinish');
  end;
end;

{ The Ready page summary. On an update the options page is skipped and the
  choices made last time are applied again, so say what is kept rather than
  "Create a desktop shortcut", and list only what will really be installed. }
function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  Winget: String;
begin
  { Worked out afresh here and again when installing, in case the user goes
    back and picks other folders }
  FoldersDecided := False;
  Result := MemoDirInfo + NewLine + NewLine +
    CustomMessage('MemoFolders') + NewLine +
    Space + CustomMessage('SourceLabel') + ' ' + GetSourceDir('') + NewLine +
    Space + CustomMessage('OutputLabel') + ' ' + GetOutputDir('');
  FoldersDecided := False;
  if not UpdateMode then
  begin
    if MemoTasksInfo <> '' then
      Result := Result + NewLine + NewLine + MemoTasksInfo;
    Exit;
  end;
  Result := Result + NewLine + NewLine + CustomMessage('MemoKept') + NewLine +
    Space + CustomMessage('MemoStartMenu');
  if WizardIsTaskSelected('desktopicon') then
    Result := Result + NewLine + Space + CustomMessage('MemoDesktop');
  if WizardIsTaskSelected('addtopath') then
    Result := Result + NewLine + Space + CustomMessage('MemoPath');
  Result := Result + NewLine + Space + CustomMessage('MemoSettings');
  Winget := '';
  if WizardIsTaskSelected('ffmpeg') then
    Winget := Winget + NewLine + Space + CustomMessage('MemoFfmpeg');
  if WizardIsTaskSelected('extras') then
    Winget := Winget + NewLine + Space + CustomMessage('MemoExtras');
  if Winget <> '' then
    Result := Result + NewLine + NewLine + CustomMessage('MemoWinget') + Winget;
end;

{ The screencap command on the PATH: the program folder is added to the
  system PATH (all users) or the user's PATH (only for me). Done in code
  rather than in [Registry] so an entry is never added twice, an empty PATH
  does not get a stray ';', and uninstalling removes only this entry. }
const
  MachineEnvKey = 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment';
  UserEnvKey = 'Environment';

procedure GetEnvKey(var RootKey: Integer; var SubKey: String);
begin
  if IsAdminInstallMode then
  begin
    RootKey := HKLM;
    SubKey := MachineEnvKey;
  end
  else
  begin
    RootKey := HKCU;
    SubKey := UserEnvKey;
  end;
end;

{ Paths with or without a trailing backslash count as the same folder }
function SamePath(const A, B: String): Boolean;
begin
  Result := CompareText(RemoveBackslashUnlessRoot(Trim(A)),
                        RemoveBackslashUnlessRoot(Trim(B))) = 0;
end;

{ Adds Dir to the PATH (Add) or removes every entry for it (not Add) }
procedure SetOnPath(const Dir: String; Add: Boolean);
var
  RootKey, P: Integer;
  SubKey, OldPath, NewPath, Rest, Item: String;
  Found: Boolean;
begin
  GetEnvKey(RootKey, SubKey);
  if not RegQueryStringValue(RootKey, SubKey, 'Path', OldPath) then
    OldPath := '';
  NewPath := '';
  Found := False;
  Rest := OldPath;
  while Rest <> '' do
  begin
    P := Pos(';', Rest);
    if P = 0 then
    begin
      Item := Rest;
      Rest := '';
    end
    else
    begin
      Item := Copy(Rest, 1, P - 1);
      Delete(Rest, 1, P);
    end;
    if Trim(Item) = '' then
      Continue;
    if SamePath(Item, Dir) then
    begin
      Found := True;
      if not Add then
        Continue;
    end;
    if NewPath <> '' then
      NewPath := NewPath + ';';
    NewPath := NewPath + Item;
  end;
  if Add and Found then
    Exit;
  if not Add and not Found then
    Exit;
  if Add then
  begin
    if NewPath <> '' then
      NewPath := NewPath + ';';
    NewPath := NewPath + Dir;
  end;
  if RegWriteExpandStringValue(RootKey, SubKey, 'Path', NewPath) then
  begin
    if Add then
      Log('Added to the PATH: ' + Dir)
    else
      Log('Removed from the PATH: ' + Dir);
  end
  else
    Log('Could not update the PATH in ' + SubKey);
end;

{ Applied on every run, so unticking the option on a later run takes the
  entry out again }
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    SetOnPath(ExpandConstant('{app}'), WizardIsTaskSelected('addtopath'));
end;

{ The shared ILHS folder, once empty. [UninstallDelete] does this too, but
  after setup ran twice over one copy it can run before the program folder
  is gone; at this point everything else has been removed. }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    SetOnPath(ExpandConstant('{app}'), False);
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
