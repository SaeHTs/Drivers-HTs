"""Diccionario de textos de la interfaz (espanol / ingles).

Las claves van en ingles tecnico; los valores son el texto visible.
Los textos en espanol conservan el estilo del proyecto (mayusculas en etiquetas,
sin tildes en la mayoria de literales historicos).
"""

TEXTOS = {
    "es": {
        # --- cabecera y ventana ---
        "app_titulo": "Drivers HTs  v{version}",
        "marca_edicion": "CYBERDARK EDITION  //  CATALOGO MICROSOFT UPDATE",
        "chip_listo": "● LISTO",
        "chip_error": "● ERROR",
        "chip_activo": "● ACTIVO",
        "chip_trabajando": "● TRABAJANDO",

        # --- botones y fila de carpeta ---
        "btn_detectar": "1 · DETECTAR HARDWARE",
        "btn_buscar": "2 · BUSCAR DRIVER",
        "btn_descargar": "3 · DESCARGAR",
        "btn_vcpp": "VISUAL C++",
        "btn_kit": "★ KIT COMPLETO",
        "lbl_carpeta": "CARPETA DE DESCARGA",

        # --- paneles y tablas ---
        "panel_hw": "HARDWARE DETECTADO",
        "panel_hw_sub": "Equipos esenciales del sistema",
        "panel_dr": "DRIVERS ENCONTRADOS",
        "panel_dr_sub": "Catalogo de Microsoft Update",
        "col_categoria": "CATEGORIA",
        "col_dispositivo": "DISPOSITIVO",
        "col_titulo": "TITULO DEL DRIVER",
        "col_windows": "WINDOWS",
        "col_fecha": "FECHA",

        # --- progreso y estado ---
        "lbl_progreso": "PROGRESO",
        "chk_instalar": "Instalar tras descargar (requiere administrador)",
        "estado_listo": "Listo. Pulsa 'Detectar hardware' para empezar.",

        # --- categorias ---
        "cat_red": "Red",
        "cat_video": "Video",
        "cat_audio": "Audio",
        "cat_chipset": "Chipset",
        "cat_otro": "Otro",

        # --- estados dinamicos ---
        "log_instalando": "Instalando {nombre}...",
        "log_detectando": "Detectando hardware...",
        "log_hardware": "{n} dispositivos esenciales. CPU: {cpu}",
        "log_buscando": "Buscando: {consulta}...",
        "log_con_aviso": "{n} drivers encontrados. AVISO: {aviso}",
        "log_resultados": "{n} drivers encontrados. Selecciona uno y pulsa Descargar.",
        "log_sin_resultados": "Sin resultados en el catalogo.",
        "log_kit_detectando": "Detectando hardware para el kit...",
        "log_obteniendo_enlace": "Obteniendo enlace de descarga...",
        "log_descargando": "Descargando {titulo}...",
        "log_guardado": "Guardado en: {datos}{extra}",
        "log_guardado_extra": " -> {resultado}",
        "log_error": "{motivo}",
        "err_conexion": ("No se pudo conectar con el Catalogo de Microsoft Update. "
                         "Revisa la conexion a internet."),
        "err_servidor": ("El Catalogo de Microsoft Update respondio con un error. "
                         "Intentalo de nuevo en un momento."),
        "err_generico": "Error: {msg}",
        "desconocido": "desconocido",

        # --- kit ---
        "kit_buscando": "[{n}/{total}] Buscando driver de {nombre}...",
        "kit_sin_resultados": "[{n}/{total}] Sin resultados para {nombre}",
        "kit_sin_enlace": "[{n}/{total}] Sin enlace para {nombre}",
        "kit_descargando": "[{n}/{total}] Descargando {nombre}...",
        "kit_error": "[{n}/{total}] {motivo}",
        "kit_instalado": "[{n}/{total}] {nombre} -> {resultado}",
        "kit_terminado_fallos": ("Kit terminado con {n} fallo(s) y {omitidos} sin driver "
                                 "en el catalogo. Revisa los marcados arriba."),
        "kit_terminado_ok": "Kit terminado: {instalados} driver(s) instalado(s).",
        "kit_terminado_descarga": "Kit terminado: {descargados} driver(s) descargado(s) en {carpeta}.",
        "kit_terminado_ok_sin": ("Kit terminado: {instalados} driver(s) instalado(s). "
                                 "{omitidos} dispositivo(s) no tienen driver en el catalogo."),
        "kit_sin_deteccion": ("No se pudo detectar el hardware. Pulsa 'Detectar hardware' "
                              "para intentarlo de nuevo."),

        # --- marcas y sufijos ---
        "marca_recomendado": "★ RECOMENDADO - ",
        "marca_antiguo": "  ⚠ ANTIGUO",
        "inst_ok": "OK: {msg}",
        "inst_fallo": "FALLO: {msg}",
        "err_sin_enlace": "No se encontro enlace directo para este driver.",

        # --- dialogos ---
        "msg_admin_titulo": "Instalar tras descargar",
        "msg_admin_cuerpo": ("Instalar drivers requiere administrador.\n\n"
                             "¿Reiniciar la app como administrador ahora?"),
        "msg_buscar_titulo": "Buscar driver",
        "msg_buscar_cuerpo": "Selecciona un dispositivo de la lista izquierda.",
        "msg_kit_titulo": "Kit completo",
        "msg_kit_cuerpo": ("Se descargara el driver recomendado de cada esencial "
                           "({n}) + Visual C++:\n\n{resumen}\n\n¿Continuar?"),
        "msg_kit_instalar_cuerpo": ("Se instalaran los drivers uno a uno al descargarse.\n"
                                    "Se recomienda crear un punto de restauracion antes. ¿Continuar?"),
        "msg_descargar_titulo": "Descargar",
        "msg_descargar_cuerpo": "Selecciona un driver de la lista derecha.",
        "msg_vcpp_titulo": "Instalacion silenciosa",
        "msg_vcpp_cuerpo": ("Instalar requiere administrador. Cierra esta ventana, activa la\n"
                            "casilla en la ventana principal (te pedira reiniciar como admin)\n"
                            "y vuelve a abrir Visual C++."),

        # --- ventana Visual C++ ---
        "vcpp_ventana": "Visual C++ Redistributables",
        "vcpp_titulo": "VISUAL C++",
        "vcpp_subtitulo": "REDISTRIBUTABLES OFICIALES DE MICROSOFT",
        "vcpp_selecciona": "SELECCIONA LAS VERSIONES A DESCARGAR",
        "vcpp_todas": "TODAS",
        "vcpp_ninguna": "NINGUNA",
        "vcpp_descargar": "DESCARGAR SELECCIONADOS",
        "vcpp_chk_instalar": "Instalar silencioso al descargar (requiere administrador)",
        "vcpp_nada_seleccionado": "No hay nada seleccionado.",
        "vcpp_progreso": "[{n}/{total}] {nombre}...",
        "vcpp_instalando": "[{n}/{total}] Instalando {nombre}...",
        "vcpp_fallo_instalar": "Fallo al instalar {nombre}: {msg}",
        "vcpp_error": "Error en {nombre}: {motivo}",
        "vcpp_completado": "Completado{extra}. Guardado en: {carpeta}",
        "vcpp_instalados": " | {n} instalado(s)",

        # --- modulos ---
        "aviso_catalogo_antiguo": ("catalogo sin versiones recientes ({antiguedad} anos); "
                                   "puede requerir el driver del fabricante"),
        "inst_req_admin": "requiere administrador",
        "inst_sin_inf": "no se pudieron extraer .inf del paquete",
        "inst_zip_invalido": "no se pudo descomprimir el paquete .zip",
        "inst_pnputil_error": "{motivo}\nDetalle: {detalle}",
        "inst_error_admin": "No se pudo instalar: hace falta ejecutar como administrador.",
        "inst_error_ya_existe": "No se pudo instalar: el paquete ya estaba instalado.",
        "inst_error_sin_hardware": "No se pudo instalar: no hay hardware compatible con ese driver.",
        "inst_error_invalido": "No se pudo instalar: el paquete de drivers no es valido o esta incompleto.",
        "inst_error_otro": "No se pudo instalar con pnputil.",
        "inst_ok_texto": "instalado",
        "inst_ok_reinicio": "instalado (reinicio pendiente)",
        "inst_ya_existente": "ya estaba instalado",
        "inst_ya_instalado": "ya habia una version mas nueva instalada",
        "inst_no_instalable": ("{nombre} no se puede instalar automaticamente: "
                               "abre el archivo a mano para instalarlo."),
        "inst_codigo_salida": "codigo de salida {codigo}",
    },
    "en": {
        # --- header and window ---
        "app_titulo": "Drivers HTs  v{version}",
        "marca_edicion": "CYBERDARK EDITION  //  MICROSOFT UPDATE CATALOG",
        "chip_listo": "● READY",
        "chip_error": "● ERROR",
        "chip_activo": "● ACTIVE",
        "chip_trabajando": "● WORKING",

        # --- buttons and folder row ---
        "btn_detectar": "1 · DETECT HARDWARE",
        "btn_buscar": "2 · FIND DRIVER",
        "btn_descargar": "3 · DOWNLOAD",
        "btn_vcpp": "VISUAL C++",
        "btn_kit": "★ FULL KIT",
        "lbl_carpeta": "DOWNLOAD FOLDER",

        # --- panels and tables ---
        "panel_hw": "HARDWARE DETECTED",
        "panel_hw_sub": "Essential system devices",
        "panel_dr": "DRIVERS FOUND",
        "panel_dr_sub": "Microsoft Update Catalog",
        "col_categoria": "CATEGORY",
        "col_dispositivo": "DEVICE",
        "col_titulo": "DRIVER TITLE",
        "col_windows": "WINDOWS",
        "col_fecha": "DATE",

        # --- progress and status ---
        "lbl_progreso": "PROGRESS",
        "chk_instalar": "Install after downloading (requires administrator)",
        "estado_listo": "Ready. Press 'Detect hardware' to start.",

        # --- categories ---
        "cat_red": "Network",
        "cat_video": "Video",
        "cat_audio": "Audio",
        "cat_chipset": "Chipset",
        "cat_otro": "Other",

        # --- dynamic states ---
        "log_instalando": "Installing {nombre}...",
        "log_detectando": "Detecting hardware...",
        "log_hardware": "{n} essential devices. CPU: {cpu}",
        "log_buscando": "Searching: {consulta}...",
        "log_con_aviso": "{n} drivers found. WARNING: {aviso}",
        "log_resultados": "{n} drivers found. Select one and press Download.",
        "log_sin_resultados": "No results in the catalog.",
        "log_kit_detectando": "Detecting hardware for the kit...",
        "log_obteniendo_enlace": "Getting download link...",
        "log_descargando": "Downloading {titulo}...",
        "log_guardado": "Saved to: {datos}{extra}",
        "log_guardado_extra": " -> {resultado}",
        "log_error": "{motivo}",
        "err_conexion": ("Could not connect to the Microsoft Update Catalog. "
                         "Check your internet connection."),
        "err_servidor": ("The Microsoft Update Catalog returned an error. "
                         "Try again in a moment."),
        "err_generico": "Error: {msg}",
        "desconocido": "unknown",

        # --- kit ---
        "kit_buscando": "[{n}/{total}] Searching driver for {nombre}...",
        "kit_sin_resultados": "[{n}/{total}] No results for {nombre}",
        "kit_sin_enlace": "[{n}/{total}] No link for {nombre}",
        "kit_descargando": "[{n}/{total}] Downloading {nombre}...",
        "kit_error": "[{n}/{total}] {motivo}",
        "kit_instalado": "[{n}/{total}] {nombre} -> {resultado}",
        "kit_terminado_fallos": ("Kit finished with {n} failure(s) and {omitidos} with no "
                                 "driver in the catalog. Check the ones marked above."),
        "kit_terminado_ok": "Kit finished: {instalados} driver(s) installed.",
        "kit_terminado_descarga": "Kit finished: {descargados} driver(s) downloaded to {carpeta}.",
        "kit_terminado_ok_sin": ("Kit finished: {instalados} driver(s) installed. "
                                 "{omitidos} device(s) have no driver in the catalog."),
        "kit_sin_deteccion": ("Could not detect the hardware. Press 'Detect hardware' "
                              "to try again."),

        # --- marks and suffixes ---
        "marca_recomendado": "★ RECOMMENDED - ",
        "marca_antiguo": "  ⚠ OLD",
        "inst_ok": "OK: {msg}",
        "inst_fallo": "FAILED: {msg}",
        "err_sin_enlace": "No direct link found for this driver.",

        # --- dialogs ---
        "msg_admin_titulo": "Install after downloading",
        "msg_admin_cuerpo": ("Installing drivers requires administrator.\n\n"
                             "Restart the app as administrator now?"),
        "msg_buscar_titulo": "Find driver",
        "msg_buscar_cuerpo": "Select a device from the left list.",
        "msg_kit_titulo": "Full kit",
        "msg_kit_cuerpo": ("The recommended driver of each essential device "
                           "({n}) + Visual C++ will be downloaded:\n\n{resumen}\n\nContinue?"),
        "msg_kit_instalar_cuerpo": ("Drivers will be installed one by one as they download.\n"
                                    "Creating a restore point first is recommended. Continue?"),
        "msg_descargar_titulo": "Download",
        "msg_descargar_cuerpo": "Select a driver from the right list.",
        "msg_vcpp_titulo": "Silent install",
        "msg_vcpp_cuerpo": ("Installing requires administrator. Close this window, check the\n"
                            "box in the main window (it will offer to restart as admin)\n"
                            "and open Visual C++ again."),

        # --- Visual C++ window ---
        "vcpp_ventana": "Visual C++ Redistributables",
        "vcpp_titulo": "VISUAL C++",
        "vcpp_subtitulo": "OFFICIAL MICROSOFT REDISTRIBUTABLES",
        "vcpp_selecciona": "SELECT THE VERSIONS TO DOWNLOAD",
        "vcpp_todas": "ALL",
        "vcpp_ninguna": "NONE",
        "vcpp_descargar": "DOWNLOAD SELECTED",
        "vcpp_chk_instalar": "Silent install after downloading (requires administrator)",
        "vcpp_nada_seleccionado": "Nothing selected.",
        "vcpp_progreso": "[{n}/{total}] {nombre}...",
        "vcpp_instalando": "[{n}/{total}] Installing {nombre}...",
        "vcpp_fallo_instalar": "Failed to install {nombre}: {msg}",
        "vcpp_error": "Error in {nombre}: {motivo}",
        "vcpp_completado": "Completed{extra}. Saved to: {carpeta}",
        "vcpp_instalados": " | {n} installed",

        # --- modules ---
        "aviso_catalogo_antiguo": ("catalog has no recent versions ({antiguedad} years); "
                                   "the manufacturer driver may be needed"),
        "inst_req_admin": "requires administrator",
        "inst_sin_inf": "could not extract .inf from the package",
        "inst_zip_invalido": "could not unzip the driver package",
        "inst_pnputil_error": "{motivo}\nDetail: {detalle}",
        "inst_error_admin": "Could not install: administrator rights are required.",
        "inst_error_ya_existe": "Could not install: the package was already installed.",
        "inst_error_sin_hardware": "Could not install: no hardware matches that driver.",
        "inst_error_invalido": "Could not install: the driver package is invalid or incomplete.",
        "inst_error_otro": "Could not install with pnputil.",
        "inst_ok_texto": "installed",
        "inst_ok_reinicio": "installed (restart pending)",
        "inst_ya_existente": "was already installed",
        "inst_ya_instalado": "a newer version was already installed",
        "inst_no_instalable": ("{nombre} cannot be installed automatically: "
                               "open the file manually to install it."),
        "inst_codigo_salida": "exit code {codigo}",
    },
}


def claves_faltantes() -> list:
    """Claves presentes en espanol y ausentes en ingles."""
    return sorted(set(TEXTOS["es"]) - set(TEXTOS["en"]))
