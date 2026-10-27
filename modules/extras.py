"""Paquetes extra utiles tras formatear: Visual C++ Redistributables (enlaces oficiales MS).

OJO: cada familia de instalador tiene SU PROPIA sintaxis de linea de comandos.
Los de 2010 en adelante aceptan "/install /quiet /norestart", pero los de 2008
y 2005 solo entienden "/q": con los switches equivocados el de 2005 abre un
dialogo "Command line option syntax error" y el de 2008 falla en silencio.
"""

# (version, arquitectura, url, nombre de archivo, switches de instalacion)
_VISUAL_CPP = [
    ("2015-2022", "x64", "https://aka.ms/vs/17/release/vc_redist.x64.exe",
     "vc_redist_2015-2022_x64.exe", ("/install", "/quiet", "/norestart")),
    ("2015-2022", "x86", "https://aka.ms/vs/17/release/vc_redist.x86.exe",
     "vc_redist_2015-2022_x86.exe", ("/install", "/quiet", "/norestart")),
    ("2013", "x64", "https://download.microsoft.com/download/2/E/6/2E61CFA4-993B-4DD4-91DA-3737CD5CD6E3/vcredist_x64.exe",
     "vcredist_2013_x64.exe", ("/install", "/quiet", "/norestart")),
    ("2013", "x86", "https://download.microsoft.com/download/2/E/6/2E61CFA4-993B-4DD4-91DA-3737CD5CD6E3/vcredist_x86.exe",
     "vcredist_2013_x86.exe", ("/install", "/quiet", "/norestart")),
    ("2012", "x64", "https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe",
     "vcredist_2012_x64.exe", ("/install", "/quiet", "/norestart")),
    ("2012", "x86", "https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x86.exe",
     "vcredist_2012_x86.exe", ("/install", "/quiet", "/norestart")),
    ("2010", "x64", "https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x64.exe",
     "vcredist_2010_x64.exe", ("/install", "/quiet", "/norestart")),
    ("2010", "x86", "https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x86.exe",
     "vcredist_2010_x86.exe", ("/install", "/quiet", "/norestart")),
    ("2008", "x64", "https://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x64.exe",
     "vcredist_2008_x64.exe", ("/q",)),
    ("2008", "x86", "https://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x86.exe",
     "vcredist_2008_x86.exe", ("/q",)),
    ("2005", "x64", "https://download.microsoft.com/download/8/B/4/8B42259F-5D70-43F4-AC2E-4B208FD8D66A/vcredist_x64.EXE",
     "vcredist_2005_x64.exe", ("/q",)),
    ("2005", "x86", "https://download.microsoft.com/download/8/B/4/8B42259F-5D70-43F4-AC2E-4B208FD8D66A/vcredist_x86.EXE",
     "vcredist_2005_x86.exe", ("/q",)),
]


def listar_visual_cpp() -> list[dict]:
    """Devuelve los redistribuibles disponibles.

    Cada dict lleva: nombre (visible), version, arch, url, archivo (nombre unico
    para la descarga) y switches (los que acepta ese instalador).
    """
    return [
        {"nombre": f"Visual C++ {ver} ({arch})",
         "version": ver, "arch": arch, "url": url,
         "archivo": archivo, "switches": switches}
        for ver, arch, url, archivo, switches in _VISUAL_CPP
    ]
