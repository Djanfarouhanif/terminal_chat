; Installeur Windows pour Relay.
; Compile : ISCC.exe installer\relay.iss  (depuis le dossier client/)
; Produit  : client/installer/Output/Relay-Setup.exe
;
; - Installe relay.exe (par utilisateur, sans droits admin)
; - Ajoute le dossier au PATH -> la commande `relay` marche dans tout terminal
; - Raccourcis menu Démarrer + bureau (optionnel)

#define AppName "Relay"
#define AppVersion "0.2.0"
#define AppPublisher "Hanif Code"
#define AppExe "relay.exe"

[Setup]
AppId={{8F3A1C4E-9B27-4D6A-A1F2-0A1B2C3D4E5F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\Relay
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=Relay-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=relay.ico
UninstallDisplayIcon={app}\{#AppExe}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le bureau"; GroupDescription: "Raccourcis :"

[Files]
Source: "..\dist\relay.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{group}\Désinstaller {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
; Ajoute {app} au PATH utilisateur (seulement s'il n'y est pas déjà).
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; \
  ValueData: "{olddata};{app}"; Check: NeedsAddPath('{app}')

[Run]
Filename: "{app}\{#AppExe}"; Parameters: "version"; Description: "Vérifier l'installation"; \
  Flags: nowait postinstall skipifsilent runhidden

[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + ExpandConstant(Param) + ';', ';' + OrigPath + ';') = 0;
end;

procedure RemoveFromPath();
var
  OrigPath, AppDir, NewPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
    exit;
  AppDir := ExpandConstant('{app}');
  NewPath := ';' + OrigPath + ';';
  StringChangeEx(NewPath, ';' + AppDir + ';', ';', True);
  { retire les points-virgules ajoutés en début/fin }
  if (Length(NewPath) > 0) and (NewPath[1] = ';') then
    Delete(NewPath, 1, 1);
  if (Length(NewPath) > 0) and (NewPath[Length(NewPath)] = ';') then
    Delete(NewPath, Length(NewPath), 1);
  RegWriteExpandStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', NewPath);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    RemoveFromPath();
end;
