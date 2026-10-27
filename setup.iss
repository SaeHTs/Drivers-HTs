; ============================================================
;  Instalador de Drivers HTs — Axiios_HTs
;  Compilar: ISCC.exe setup.iss
;
;  Instalación POR USUARIO (sin permisos de Administrador):
;  evita el error 740. El ejecutable se eleva solo con UAC
;  cuando hace falta (instalar drivers).
;
;  OJO: este fichero debe guardarse en UTF-8 CON BOM (la
;  sección [Code] lo necesita).
; ============================================================

#define AppVersion "1.1.8"

[Setup]
AppName=Drivers HTs
AppVersion={#AppVersion}
AppVerName=Drivers HTs v{#AppVersion}
AppPublisher=Axiios_HTs
AppPublisherURL=https://github.com/SaeHTs/Drivers-HTs
AppSupportURL=https://github.com/SaeHTs/Drivers-HTs
DefaultDirName={localappdata}\Programs\DriversHTs
DefaultGroupName=Drivers HTs
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=DriversHTs-Setup
SetupIconFile=docs\icono_axiios_glow.ico
UninstallDisplayIcon={app}\DriversHTs.exe
Compression=lzma2/max
SolidCompression=yes
; Cierra la app si esta abierta al instalar (si no, el .exe esta en uso y
; la instalacion falla con "Omitir este archivo"). Inno 6.2+ lo hace solo.
CloseApplications=yes
RestartApplications=yes
; Por usuario: NO requiere elevacion (soluciona el error 740)
PrivilegesRequired=none
PrivilegesRequiredOverridesAllowed=commandline
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
SetupLogging=yes
; Metadatos del instalador
VersionInfoVersion={#AppVersion}
VersionInfoCompany=Axiios_HTs
VersionInfoDescription=Instalador de Drivers HTs v{#AppVersion}
VersionInfoCopyright=Axiios_HTs

[Languages]
; Instalador bilingue: los textos propios vienen de instalador\mensajes_*.isl
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl,instalador\mensajes_es.isl"
Name: "english"; MessagesFile: "compiler:Default.isl,instalador\mensajes_en.isl"

[Files]
Source: "dist\DriversHTs.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{cm:Icon_Acceso}"; Filename: "{app}\DriversHTs.exe"
Name: "{group}\{cm:Icon_Desinstalar}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{cm:Icon_Acceso}"; Filename: "{app}\DriversHTs.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:Tarea_Escritorio}"; GroupDescription: "{cm:Tarea_Grupo}"; Flags: unchecked

[Run]
; El .exe va con --uac-admin (exige elevacion), asi que hay que lanzarlo con
; ShellExecute ("shellexec"): con CreateProcess, Inno falla al final de la
; instalacion con "CreateProcess fallo; codigo 740". ShellExecute si dispara
; el aviso de UAC.
Filename: "{app}\DriversHTs.exe"; Description: "{cm:EjecutarAhora}"; Flags: nowait postinstall skipifsilent shellexec

[Code]
// El ejecutable va con --uac-admin: si la aplicacion esta abierta, su
// fichero esta en uso y la instalacion falla con "Omitir este archivo".
// Inno no puede cerrar una app elevada desde un instalador sin elevate,
// asi que se avisa antes de empezar.
function ProcesoCorriendo(Nombre: String): Boolean;
var
  Resultado: Integer;
  Comando: String;
begin
  Resultado := 1;
  Comando := '/C tasklist /FI "IMAGENAME eq ' + Nombre + '" /NH ' +
            '| find /I "' + Nombre + '" >NUL';
  Exec(ExpandConstant('{cmd}'), Comando, '', SW_HIDE, ewWaitUntilTerminated, Resultado);
  Result := Resultado = 0;
end;

function AppEstaAbierta: Boolean;
begin
  Result := ProcesoCorriendo('DriversHTs.exe');
end;

// La comprobacion va en PrepareToInstall, NO en InitializeSetup:
// InitializeSetup se ejecuta ANTES de la pagina de idioma, asi que el aviso
// saldria siempre en el idioma por defecto. En PrepareToInstall el usuario
// ya ha elegido el idioma y todavia no se ha copiado nada.
// Devolver un texto != '' cancela la instalacion con ese motivo.
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if AppEstaAbierta then
    Result := CustomMessage('AppEnUso');
end;
