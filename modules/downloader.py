"""Descarga de archivos con callback de progreso."""
import os
import requests

_CABECERAS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def descargar(url: str, carpeta: str, progreso=None, nombre: str = "") -> str:
    """Descarga `url` en `carpeta`.

    progreso: callback(recibidos, total) opcional. Devuelve la ruta del archivo.
    nombre: nombre con el que se guarda. Si no se indica, se usa el de la URL
            (varios paquetes comparten nombre en la URL: hay que renombrarlos).
    """
    os.makedirs(carpeta, exist_ok=True)
    if not nombre:
        nombre = url.split("/")[-1].split("?")[0] or "driver.cab"
    destino = os.path.join(carpeta, nombre)

    with requests.get(url, headers=_CABECERAS, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length") or 0)
        recibidos = 0
        with open(destino, "wb") as f:
            for bloque in resp.iter_content(chunk_size=256 * 1024):
                if not bloque:
                    continue
                f.write(bloque)
                recibidos += len(bloque)
                if progreso:
                    progreso(recibidos, total)
    return destino
