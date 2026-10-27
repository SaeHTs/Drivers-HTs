"""Busqueda y descarga en el Catalogo de Microsoft Update (catalog.update.microsoft.com)."""
import datetime
import re
import json
import sys
import requests

from modules import i18n

_URL_BUSQUEDA = "https://www.catalog.update.microsoft.com/Search.aspx"
_URL_DIALOGO = "https://www.catalog.update.microsoft.com/DownloadDialog.aspx"

_CABECERAS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/x-www-form-urlencoded",
}

# Cada resultado es una fila <tr id="{guid}_R{n}"> con celdas:
# [icono, titulo, productos, clasificacion, fecha, version, tamano, boton]
_RE_FILA = re.compile(r'<tr id="([\w-]{36})_R\d+"[^>]*>(.*?)</tr>',
                      re.DOTALL | re.IGNORECASE)
_RE_CELDA = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL | re.IGNORECASE)
_RE_TAGS = re.compile(r"<[^>]+>")
_RE_CEROS = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_RE_VERSION = re.compile(r"(\d+(?:\.\d+)+)")
_RE_BUILD_WIN = re.compile(r"version\s+(\d{2})h(\d)", re.IGNORECASE)


def _version_tupla(texto: str) -> tuple:
    """'32.0.16.1060' -> (32,0,16,1060). (0,) si no hay version."""
    m = _RE_VERSION.search(texto or "")
    return tuple(int(x) for x in m.group(1).split(".")) if m else (0,)


def _recencia(fecha: str) -> int:
    """Antiguedad en anos desde hoy (0 = de este ano). 99 si no hay fecha."""
    anio, mes, dia = _fecha_tupla(fecha)
    if not anio:
        return 99
    hoy = datetime.date.today()
    return hoy.year - anio - (1 if (hoy.month, hoy.day) < (mes, dia) else 0)


def buscar_drivers(consulta: str, limite: int = 15) -> list[dict]:
    """Busca en el catalogo y devuelve [{'guid','titulo','productos','fecha','version'}]."""
    resp = requests.get(
        _URL_BUSQUEDA,
        params={"q": consulta},
        headers=_CABECERAS,
        timeout=30,
    )
    resp.raise_for_status()
    html = resp.text

    resultados = []
    vistos = set()
    for guid, cuerpo in _RE_FILA.findall(html):
        if guid in vistos:
            continue
        celdas = [_RE_TAGS.sub("", c).strip() for c in _RE_CELDA.findall(cuerpo)]
        if len(celdas) < 6 or not celdas[1]:
            continue
        vistos.add(guid)
        resultados.append({
            "guid": guid,
            "titulo": celdas[1],
            "productos": celdas[2],
            "clasificacion": celdas[3],
            "fecha": celdas[4],
            "version": celdas[5],
            "antiguo": False,
            "aviso": "",
        })
    return resultados[:limite]


def _fecha_tupla(fecha: str) -> tuple:
    """'10/6/2016' -> (2016, 10, 6). (0,0,0) si no hay fecha."""
    m = _RE_CEROS.search(fecha or "")
    return (int(m.group(3)), int(m.group(1)), int(m.group(2))) if m else (0, 0, 0)


def _windows_actual() -> int:
    """10 u 11 segun el equipo local (11 empieza en build 22000)."""
    try:
        return 11 if sys.getwindowsversion().build >= 22000 else 10
    except Exception:
        return 10


def _puntuar(resultado: dict, consulta: str, win: int) -> tuple:
    """Orden de preferencia: Windows correcto > version > fecha > coincidencia de nombre."""
    productos = (resultado.get("productos") or "").lower()
    coincide_os = f"windows {win}" in productos
    build = _RE_BUILD_WIN.search(productos)
    # Se prefiere la etiqueta de build mas nueva (24H2 > 22H2 > sin build)
    build_val = (int(build.group(1)), int(build.group(2))) if build else (0, 0)
    palabras = {p.lower() for p in consulta.split() if len(p) > 2}
    titulo_min = resultado["titulo"].lower()
    coincidencias = sum(1 for p in palabras if p in titulo_min)
    return (
        coincide_os,
        _version_tupla(resultado.get("version")),
        build_val,
        _fecha_tupla(resultado.get("fecha")),
        coincidencias,
    )


def marcar_recomendado(resultados: list[dict], consulta: str,
                       windows: int | None = None) -> list[dict]:
    """Marca 'recomendado'=True en la mejor opcion y avisa de las antiguas.

    Elige la version mas nueva para el Windows actual. Si el mejor resultado
    tiene 3+ anos, lo marca como 'antiguo' (puede no haber nada reciente en el
    catalogo para ese dispositivo).
    """
    if not resultados:
        return resultados
    win = windows or _windows_actual()
    mejor = max(resultados, key=lambda r: _puntuar(r, consulta, win))
    mejor["recomendado"] = True
    antiguedad = _recencia(mejor.get("fecha"))
    if antiguedad >= 3:
        mejor["antiguo"] = True
        # se guarda la antiguedad (no el texto) para poder re-traducir el aviso
        mejor["antiguedad"] = antiguedad
        mejor["aviso"] = _texto_aviso(antiguedad)
    return resultados


def _texto_aviso(antiguedad: int) -> str:
    """Aviso visible cuando el catalogo no tiene versiones recientes."""
    return i18n.t("aviso_catalogo_antiguo", antiguedad=antiguedad)


def obtener_enlace_descarga(guid: str) -> str | None:
    """Pide el dialogo de descarga del catalogo y extrae la URL directa del .cab/.msu."""
    payload = [{
        "size": 0,
        "languages": "",
        "uidInfo": guid,
        "updateID": guid,
    }]
    resp = requests.post(
        _URL_DIALOGO,
        data={"updateIDs": json.dumps(payload)},
        headers=_CABECERAS,
        timeout=30,
    )
    resp.raise_for_status()
    m = re.search(r"(https?://[^\s\"'<>]*?\.(?:cab|msu|exe|zip))", resp.text, re.IGNORECASE)
    return m.group(1) if m else None
