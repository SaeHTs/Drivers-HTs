"""Instalacion de drivers (.cab/.inf via pnputil) y redistribuibles (.exe silencioso).

Todo requiere privilegios de administrador.
"""
import ctypes
import os
import subprocess
import sys

from modules import i18n

_SIN_VENTANA = subprocess.CREATE_NO_WINDOW


def _texto(clave: str, **kwargs) -> str:
    """Traduce un mensaje devuelto al usuario."""
    return i18n.t(clave, **kwargs)


# Palabras clave de los errores de pnputil, en ingles y en espanol
# (pnputil escribe en el idioma del sistema: hay que reconocer ambos).
_ERRORES_PNPUTIL = (
    ("inst_error_admin", ("access is denied", "requires elevation",
                          "requiere privilegios", "acceso denegado",
                          "se requiere privilegios de administrador")),
    ("inst_error_ya_existe", ("already exists", "already installed",
                               "ya esta instalado", "ya existe")),
    ("inst_error_sin_hardware", ("no applicable hardware", "no matching hardware",
                                 "no se encontro hardware", "no hay hardware",
                                 "hardware aplicable")),
    ("inst_error_invalido", ("missing or invalid", "falta o no es valido",
                             "no es valido", "invalid")),
)


def _sin_tildes(texto: str) -> str:
    """Quita acentos y pasa a minusculas, para comparar sin sorpresas."""
    import unicodedata
    plano = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in plano if not unicodedata.combining(c)).lower()


# Lineas de pnputil que son RESUMEN, no error: nunca deben mostrarse como error
_RESUMEN_PNPUTIL = ("paquetes de controladores totales",
                    "paquetes de controladores agregados",
                    "nombre publicado:",
                    "agregando paquete de controladores:")

# pnputil avisa asi cuando el driver ya estaba en el sistema
_YA_EXISTE = ("ya existe en el sistema", "already exists", "ya esta instalado")


def _linea_error_pnputil(lineas) -> str:
    """Extrae la linea de error real de la salida de pnputil.

    pnputil imprime un resumen al final ("Paquetes de controladores totales: 0"),
    asi que la ultima linea NO es el error: hay que buscar la que lo dice.
    Las lineas de resumen se descartan siempre.
    """
    texto = [l.strip() for l in lineas if l and l.strip()]
    informativas = []
    for linea in texto:
        bajo = _sin_tildes(linea)
        if any(bajo.startswith(r) for r in _RESUMEN_PNPUTIL):
            continue
        if bajo.startswith(("error", "failed", "advertencia", "warning")):
            return linea
        informativas.append(linea)
    # sin linea de error: se devuelve la ultima linea que no sea resumen
    return informativas[-1] if informativas else ""


def _ya_instalado(lineas) -> bool:
    """True si pnputil dice que el driver ya estaba instalado.

    Importante: en ese caso pnputil devuelve un codigo de salida != 0 aunque
    todo este bien, asi que el codigo por si solo NO significa fallo.
    """
    for linea in lineas:
        bajo = _sin_tildes(linea)
        if any(marca in bajo for marca in _YA_EXISTE):
            return True
    return False


def _clasificar_error_pnputil(detalle: str) -> str:
    """Devuelve la clave de traduccion del motivo del error de pnputil."""
    bajo = _sin_tildes(detalle)
    for clave, marcas in _ERRORES_PNPUTIL:
        if any(marca in bajo for marca in marcas):
            return clave
    return "inst_error_otro"


def es_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def reiniciar_como_admin() -> None:
    """Relanza la app actual con UAC (administrador)."""
    exe = sys.executable
    params = "" if getattr(sys, "frozen", False) else f'"{os.path.abspath(sys.argv[0])}"'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)


def _instalar_con_pnputil(inf_o_carpeta: str) -> tuple[bool, str, dict]:
    """Ejecuta pnputil sobre un .inf (o una carpeta) y traduce el resultado."""
    if os.path.isdir(inf_o_carpeta):
        objetivo = os.path.join(inf_o_carpeta, "*.inf")
    else:
        objetivo = inf_o_carpeta
    r = subprocess.run(["pnputil", "/add-driver", objetivo, "/subdirs", "/install"],
                       capture_output=True, text=True, creationflags=_SIN_VENTANA)
    salida = (r.stdout + r.stderr).strip().splitlines()
    if _ya_instalado(salida):
        # el driver ya estaba en el sistema: pnputil devuelve un codigo != 0
        # aunque todo este bien, asi que NO es un fallo
        return True, "inst_ya_existente", {}
    if r.returncode in (0, 3010):
        clave = "inst_ok_reinicio" if r.returncode == 3010 else "inst_ok_texto"
        return True, clave, {}
    detalle = _linea_error_pnputil(salida)
    if detalle:
        # el motivo va traducido; el detalle tecnico se conserva tal cual
        return False, "inst_pnputil_error", {
            "motivo": (_clasificar_error_pnputil(detalle), {}),
            "detalle": detalle,
        }
    return False, "inst_codigo_salida", {"codigo": r.returncode}


def instalar_driver_zip(ruta_zip: str) -> tuple[bool, str, dict]:
    """Instala un paquete de driver en .zip.

    Un .zip de drivers trae el .inf y sus archivos: se extrae en una carpeta
    junto al .zip y se instala con pnputil, igual que un .cab.
    """
    if not es_admin():
        return False, "inst_req_admin", {}
    base = ruta_zip[:-4] if ruta_zip.lower().endswith(".zip") else ruta_zip
    destino = base + "_extraido"
    try:
        import zipfile
        with zipfile.ZipFile(ruta_zip) as z:
            z.extractall(destino)
    except Exception:
        # zip corrupto o con formato inesperado: se avisa, no se reventa
        return False, "inst_zip_invalido", {"nombre": os.path.basename(ruta_zip)}
    if not any(f.lower().endswith(".inf")
               for _, _, files in os.walk(destino) for f in files):
        return False, "inst_sin_inf", {}
    return _instalar_con_pnputil(destino)


def instalar_driver_cab(ruta_cab: str) -> tuple[bool, str, dict]:
    """Extrae el .cab y lo instala con pnputil.

    Devuelve (ok, clave_tradaccion, kwargs). Se devuelve la CLAVE y no el texto
    para que la interfaz pueda re-traducir el mensaje al cambiar de idioma.
    """
    if not es_admin():
        return False, "inst_req_admin", {}
    destino = ruta_cab.rsplit(".", 1)[0] + "_extraido"
    os.makedirs(destino, exist_ok=True)

    r = subprocess.run(["expand", "-F:*", ruta_cab, destino],
                       capture_output=True, text=True, creationflags=_SIN_VENTANA)
    if r.returncode != 0 or not any(f.lower().endswith(".inf")
                                    for _, _, files in os.walk(destino)
                                    for f in files):
        return False, "inst_sin_inf", {}

    return _instalar_con_pnputil(destino)


def instalar_driver_msu(ruta_msu: str) -> tuple[bool, str, dict]:
    """Instala un paquete .msu (Microsoft Update Standalone) con wusa.exe.

    Un .msu no es un ejecutable: si se intenta ejecutar directamente, falla.
    """
    if not es_admin():
        return False, "inst_req_admin", {}
    r = subprocess.run(["wusa.exe", ruta_msu, "/quiet", "/norestart"],
                       capture_output=True, creationflags=_SIN_VENTANA)
    if r.returncode in (0, 3010):
        clave = "inst_ok_reinicio" if r.returncode == 3010 else "inst_ok_texto"
        return True, clave, {}
    if r.returncode == 1638:
        return True, "inst_ya_instalado", {}
    return False, "inst_codigo_salida", {"codigo": r.returncode}


def instalar_redistribuible(ruta_exe: str,
                            switches=("/install", "/quiet", "/norestart")) -> tuple[bool, str, dict]:
    """Instala un Visual C++ Redistributable en modo silencioso.

    `switches` debe ser el que acepta ESE instalador: los de 2005 y 2008 solo
    entienden "/q" y con "/install" muestran un error de sintaxis.
    """
    if not es_admin():
        return False, "inst_req_admin", {}
    r = subprocess.run([ruta_exe] + list(switches),
                       capture_output=True, creationflags=_SIN_VENTANA)
    if r.returncode in (0, 3010):  # 3010 = exito, requiere reinicio
        clave = "inst_ok_reinicio" if r.returncode == 3010 else "inst_ok_texto"
        return True, clave, {}
    if r.returncode == 1638:
        # 1638 = ya hay una version mas nueva instalada: no es un fallo
        return True, "inst_ya_instalado", {}
    return False, "inst_codigo_salida", {"codigo": r.returncode}
