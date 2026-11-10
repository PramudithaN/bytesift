; Inno Setup Script for ByteSift
; Builds a professional, user-friendly Windows setup installer (ByteSift-Setup-x64.exe)
; Installs cleanly to Local AppData (no administrator privileges required) to avoid permission issues and EDR blocks.

#ifndef MyAppVersion
#define MyAppVersion "0.1.8"
#endif
#define MyAppName "ByteSift"
#define MyAppPublisher "ByteSift Open Source"
#define MyAppURL "https://pramudithan.github.io/bytesift/"
#define MyAppExeName "ByteSift.exe"

[Setup]
; Unique application GUID
AppId={{D37F8E44-9B8A-4F8C-9B3E-7281D9E74A62}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
; Install into user-level AppData by default (No UAC admin prompt required)
DefaultDirName={userpf}\{#MyAppName}
UsePreviousAppDir=yes
CloseApplications=yes
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=ByteSift-Setup-x64
SetupIconFile=..\bytesift\assets\icon_light.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=ByteSift Desktop Installer
VersionInfoCopyright=Copyright (C) 2026 Pramuditha. MIT License.
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Distribute all files from the PyInstaller onedir output
Source: "..\dist\ByteSift\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\bytesift\assets\*"; DestDir: "{app}\bytesift\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\bytesift\assets\icon_light.ico"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\bytesift\assets\icon_light.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]

function ParseNextVersionPart(var S: String): Integer;
var
  DotPos: Integer;
  PartStr: String;
begin
  DotPos := Pos('.', S);
  if DotPos > 0 then
  begin
    PartStr := Copy(S, 1, DotPos - 1);
    S := Copy(S, DotPos + 1, Length(S));
  end
  else
  begin
    PartStr := S;
    S := '';
  end;
  Result := StrToIntDef(PartStr, 0);
end;

function CompareVersionStrings(V1, V2: String): Integer;
var
  Clean1, Clean2: String;
  P1, P2: Integer;
begin
  Clean1 := Trim(V1);
  if (Length(Clean1) > 0) and ((Clean1[1] = 'v') or (Clean1[1] = 'V')) then
    Clean1 := Copy(Clean1, 2, Length(Clean1));

  Clean2 := Trim(V2);
  if (Length(Clean2) > 0) and ((Clean2[1] = 'v') or (Clean2[1] = 'V')) then
    Clean2 := Copy(Clean2, 2, Length(Clean2));

  while (Length(Clean1) > 0) or (Length(Clean2) > 0) do
  begin
    P1 := ParseNextVersionPart(Clean1);
    P2 := ParseNextVersionPart(Clean2);
    if P1 > P2 then
    begin
      Result := 1;
      Exit;
    end
    else if P1 < P2 then
    begin
      Result := -1;
      Exit;
    end;
  end;
  Result := 0;
end;

function GetInstalledVersion(var InstalledVer: String): Boolean;
var
  RegPath: String;
begin
  Result := False;
  InstalledVer := '';
  RegPath := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{D37F8E44-9B8A-4F8C-9B3E-7281D9E74A62}_is1';

  // Check Current User (standard install path with PrivilegesRequired=lowest)
  if RegKeyExists(HKCU, RegPath) then
  begin
    Result := True;
    RegQueryStringValue(HKCU, RegPath, 'DisplayVersion', InstalledVer);
    Exit;
  end;

  // Check Local Machine (in case installed with elevated privileges)
  if RegKeyExists(HKLM, RegPath) then
  begin
    Result := True;
    RegQueryStringValue(HKLM, RegPath, 'DisplayVersion', InstalledVer);
    Exit;
  end;
end;

function InitializeSetup(): Boolean;
var
  InstalledVer: String;
  CurrentVer: String;
  Cmp: Integer;
  Msg: String;
begin
  Result := True;
  CurrentVer := '{#MyAppVersion}';

  if GetInstalledVersion(InstalledVer) then
  begin
    if InstalledVer = '' then
      InstalledVer := 'Existing';

    Cmp := CompareVersionStrings(CurrentVer, InstalledVer);

    if (Cmp = 0) or (InstalledVer = 'Existing') then
    begin
      // Same version is already installed - prevent reinstall
      Msg := 'ByteSift (version ' + InstalledVer + ') is already installed on your system.' + #13#10#13#10 +
             'Reinstallation of the same version is not allowed.' + #13#10#13#10 +
             '• If ByteSift is already installed and working, you do not need to reinstall it.' + #13#10 +
             '• When a new update is released, run the newer installer to upgrade.' + #13#10 +
             '• If you want to perform a clean reinstallation, please uninstall the current version first from Windows Settings > Installed apps.';
      MsgBox(Msg, mbInformation, MB_OK);
      Result := False;
      Exit;
    end
    else if Cmp < 0 then
    begin
      // Newer version is already installed - prevent downgrade
      Msg := 'A newer version of ByteSift (version ' + InstalledVer + ') is already installed on your system.' + #13#10#13#10 +
             'Downgrading to version ' + CurrentVer + ' is not supported.' + #13#10#13#10 +
             'Please keep your current version, or uninstall it first if you specifically wish to install this build.';
      MsgBox(Msg, mbError, MB_OK);
      Result := False;
      Exit;
    end
    else
    begin
      // Older version is installed -> notify and prompt to update
      Msg := 'An existing installation of ByteSift (version ' + InstalledVer + ') was detected.' + #13#10#13#10 +
             'Setup will update ByteSift to version ' + CurrentVer + '.' + #13#10#13#10 +
             'Click OK to proceed with updating ByteSift, or Cancel to exit.';
      if MsgBox(Msg, mbConfirmation, MB_OKCANCEL) <> IDOK then
      begin
        Result := False;
        Exit;
      end;
    end;
  end;
end;
