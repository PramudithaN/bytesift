; Inno Setup Script for ByteSift
; Builds a professional, user-friendly Windows setup installer (ByteSift-Setup-x64.exe)
; Installs cleanly to Local AppData (no administrator privileges required) to avoid permission issues and EDR blocks.

#define MyAppName "ByteSift"
#define MyAppVersion "0.1.0"
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
VersionInfoVersion=0.1.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=ByteSift Desktop Installer
VersionInfoCopyright=Copyright (C) 2026 Pramuditha. MIT License.
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=0.1.0.0

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
