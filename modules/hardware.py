"""Deteccion de hardware esencial usando PowerShell CIM (sin dependencias externas)."""
import json
import subprocess

from modules import i18n

CATEGORIAS = ("Red", "Video", "Audio", "Chipset", "Otro")


def nombre_categoria(clave: str) -> str:
    """Texto visible de la categoria (CATEGORIAS sigue siendo la clave interna)."""
    return i18n.t("cat_" + clave.lower())

_PALABRAS_AUDIO = ("audio", "sound", "high definition audio", "realtek")
_PALABRAS_CHIPSET = (
    "chipset", "smbus", "lpc", "pci standard", "host bridge",
    "isa bridge", "memory controller", "subsystem",
)
_EXCLUIR = (
    "wan miniport", "wi-fi direct", "kernel debug", "remote ndis",
    "virtual", "bluetooth", "cpu to pcie", "pci express root",
    "botón", "boton", "contenedor de procesador", "compatible con acpi",
    "interfaz de administración para acpi", "interfaz de administracion para acpi",
)


def _excluido(nombre: str) -> bool:
    return any(p in nombre for p in _EXCLUIR)


def _consultar_sistema() -> tuple[list[dict], str]:
    """Lee los dispositivos PnP y el procesador en UNA sola llamada a PowerShell.

    Cada proceso de PowerShell tarda en arrancar; unir las dos consultas
    ahorra ese arranque. Se piden solo las columnas que usa la app en vez
    de todas las propiedades de cada dispositivo.
    """
    comando = (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        "ConvertTo-Json -Depth 4 -Compress -InputObject @{ "
        "dispositivos = @(Get-CimInstance Win32_PnPEntity | "
        "Select-Object Name, PNPClass, ConfigManagerErrorCode, PNPDeviceID, "
        "DeviceID, Manufacturer); "
        "procesador = @(Get-CimInstance Win32_Processor | "
        "Select-Object -First 1 -ExpandProperty Name) }"
    )
    resultado = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
        capture_output=True, timeout=60,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    salida = resultado.stdout.decode("utf-8", errors="replace").strip()
    if not salida:
        return [], ""
    datos = json.loads(salida)
    dispositivos = datos.get("dispositivos") or []
    if isinstance(dispositivos, dict):
        dispositivos = [dispositivos]
    procesador = datos.get("procesador") or ""
    if isinstance(procesador, list):
        procesador = procesador[0] if procesador else ""
    return dispositivos, str(procesador).strip()


def _limpiar_nombre(nombre: str) -> str:
    """Quita ruido tipico de los nombres PnP para buscar mejor en el catalogo."""
    for ruido in ("(R)", "(TM)", "(C)", "Corporation", "Technologies", "Inc."):
        nombre = nombre.replace(ruido, "")
    return " ".join(nombre.split())


def _clasificar(dispositivo: dict) -> str:
    clase = (dispositivo.get("PNPClass") or "").strip()
    nombre = (dispositivo.get("Name") or "").lower()

    if clase == "Net":
        return "Red"
    if clase == "Display":
        return "Video"
    if clase == "Media" or any(p in nombre for p in _PALABRAS_AUDIO):
        return "Audio"
    if clase == "System" and any(p in nombre for p in _PALABRAS_CHIPSET):
        return "Chipset"
    return "Otro"


_EXCLUIR_CLASES = ("AudioEndpoint", "SoftwareComponent", "Volume")


def _extraer_ids(pnp_id: str) -> tuple[str, str]:
    """Devuelve (VEN/VID_xxxx, DEV/PID_xxxx) desde un PNPDeviceID. Vacio si no aplica."""
    ven, dev = "", ""
    for parte in (pnp_id or "").upper().split("\\"):
        for token in parte.split("&"):
            if token.startswith(("VEN_", "VID_")):
                ven = token
            elif token.startswith(("DEV_", "PID_")):
                dev = token
    return ven, dev


def detectar_hardware() -> dict:
    """Detecta dispositivos y devuelve dict con 'dispositivos' y 'procesador'."""
    brutos, procesador = _consultar_sistema()

    dispositivos = []
    vistos = set()
    for d in brutos:
        nombre = (d.get("Name") or "").strip()
        if not nombre:
            continue
        categoria = _clasificar(d)
        nombre_min = nombre.lower()
        if (d.get("PNPClass") or "") in _EXCLUIR_CLASES or _excluido(nombre_min):
            continue
        if categoria == "Otro" and not d.get("ConfigManagerErrorCode"):
            continue  # solo esenciales o con error
        pnp_id = d.get("PNPDeviceID") or d.get("DeviceID") or ""
        clave = (nombre, pnp_id)
        if clave in vistos:
            continue
        vistos.add(clave)
        ven, dev = _extraer_ids(pnp_id)
        dispositivos.append({
            "nombre": nombre,
            "categoria": categoria,
            "fabricante": (d.get("Manufacturer") or "").strip(),
            "pnp_id": pnp_id,
            "ven": ven,
            "dev": dev,
            "error": bool(d.get("ConfigManagerErrorCode")),
            "consulta": _limpiar_nombre(nombre),
        })

    orden = {c: i for i, c in enumerate(CATEGORIAS)}
    dispositivos.sort(key=lambda x: (orden.get(x["categoria"], 99), x["nombre"]))
    return {"procesador": procesador, "dispositivos": dispositivos}
