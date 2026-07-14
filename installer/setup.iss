; ─────────────────────────────────────────────────────────────────────────────
; PDF Accesible — Script de Inno Setup 6
;
; Antes de compilar:
;   1. Coloca el instalador de Tesseract en  installer\deps\tesseract-setup.exe
;      Descárgalo de https://github.com/UB-Mannheim/tesseract/releases
;      (usa la versión w64 con los paquetes de idioma spa + eng incluidos)
;   2. Coloca el instalador de Ghostscript en  installer\deps\gs-setup.exe
;      Descárgalo de https://www.ghostscript.com/releases/gsdnld.html
;   3. Ejecuta  installer\build_installer.bat  (corre PyInstaller e Inno Setup)
; ─────────────────────────────────────────────────────────────────────────────

#define AppName      "PDF Accesible"
#define AppVersion   "1.0.0"
#define AppPublisher "República Dominicana"
#define AppExeName   "PDF Accesible.exe"
#define DistDir      "..\dist\PDF Accesible"

[Setup]
AppId={{A7F2C3D8-4E1B-4F9A-B2C3-1D8E7F6A5B4C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://ogtic.gob.do
AppSupportURL=https://ogtic.gob.do
AppUpdatesURL=https://ogtic.gob.do
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
; Carpeta de salida del instalador
OutputDir=Output
OutputBaseFilename=PDF_Accesible_Instalador_v{#AppVersion}
; Compresión máxima (lzma2 multi-núcleo)
Compression=lzma2/ultra64
SolidCompression=yes
LZMANumBlockThreads=4
; Apariencia
WizardStyle=modern
WizardResizable=yes
; Requiere 64 bits
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Requiere Windows 10 o superior
MinVersion=10.0
; Muestra avance de instalación en la barra de tareas
ShowTasksTreeLines=yes
; No necesita ser administrador (instala en AppData si no hay permisos)
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el &Escritorio"; GroupDescription: "Iconos adicionales:"
Name: "startupicon"; Description: "Iniciar {#AppName} al arrancar Windows"; GroupDescription: "Inicio automático:"; Flags: unchecked

[Files]
; ── App (salida de PyInstaller) ──────────────────────────────────────────────
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs; Excludes: "*.pdb"

; ── Dependencias externas (se instalan si no están presentes) ────────────────
Source: "deps\tesseract-setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: NecesitaTesseract
Source: "deps\gs-setup.exe";        DestDir: "{tmp}"; Flags: deleteafterinstall; Check: NecesitaGhostscript

[Icons]
; Menú Inicio
Name: "{group}\{#AppName}";          Filename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
; Escritorio (opcional)
Name: "{commondesktop}\{#AppName}";  Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
; Inicio automático
Name: "{userstartup}\{#AppName}";    Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Run]
; Tesseract (silencioso, con paquetes de idioma español e inglés)
Filename: "{tmp}\tesseract-setup.exe"; \
  Parameters: "/S /COMPONENTS=""tesseract,tesseract_language_spa,tesseract_language_eng"""; \
  StatusMsg: "Instalando Tesseract OCR (puede tardar un minuto)…"; \
  Flags: waituntilterminated; \
  Check: NecesitaTesseract

; Ghostscript (silencioso)
Filename: "{tmp}\gs-setup.exe"; \
  Parameters: "/S"; \
  StatusMsg: "Instalando Ghostscript…"; \
  Flags: waituntilterminated; \
  Check: NecesitaGhostscript

; Ofrece abrir la app al terminar
Filename: "{app}\{#AppExeName}"; \
  Description: "Abrir {#AppName} ahora"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

; ─────────────────────────────────────────────────────────────────────────────
; Código de detección de dependencias
; ─────────────────────────────────────────────────────────────────────────────
[Code]
function TesseractExe: String;
begin
  Result := ExpandConstant('{pf64}\Tesseract-OCR\tesseract.exe');
  if FileExists(Result) then Exit;
  Result := ExpandConstant('{pf}\Tesseract-OCR\tesseract.exe');
  if FileExists(Result) then Exit;
  Result := 'C:\Program Files\Tesseract-OCR\tesseract.exe';
  if FileExists(Result) then Exit;
  Result := '';
end;

function GhostscriptExe: String;
var
  Path: String;
begin
  // Ghostscript instala en C:\Program Files\gs\gsX.XX\bin\gswin64c.exe
  if RegQueryStringValue(HKLM64,
      'SOFTWARE\Artifex\GPL Ghostscript',
      'GS_DLL', Path) then
  begin
    Result := ExtractFilePath(Path);
    Exit;
  end;
  Result := '';
end;

function NecesitaTesseract: Boolean;
begin
  Result := (TesseractExe = '');
end;

function NecesitaGhostscript: Boolean;
begin
  Result := (GhostscriptExe = '');
end;

// Avisa si faltan los instaladores de las dependencias pero deja continuar.
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  FaltaTess, FaltaGs: Boolean;
  Msg: String;
begin
  FaltaTess := NecesitaTesseract and not FileExists(ExpandConstant('{tmp}\tesseract-setup.exe'));
  FaltaGs   := NecesitaGhostscript and not FileExists(ExpandConstant('{tmp}\gs-setup.exe'));
  if FaltaTess or FaltaGs then
  begin
    Msg := 'Atención: falta(n) los siguientes instaladores en la carpeta deps\:' + #13#10;
    if FaltaTess then Msg := Msg + '  • tesseract-setup.exe' + #13#10;
    if FaltaGs   then Msg := Msg + '  • gs-setup.exe' + #13#10;
    Msg := Msg + #13#10 +
      'La aplicación se instalará igualmente, pero Tesseract y/o Ghostscript' + #13#10 +
      'deberán instalarse manualmente para que la conversión OCR funcione.';
    MsgBox(Msg, mbInformation, MB_OK);
  end;
  Result := '';
end;
