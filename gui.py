"""Descargar-Drivers - GUI principal.

Detecta el hardware esencial (red, video, audio, chipset) y descarga
drivers desde el Catalogo de Microsoft Update.
"""
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from modules import catalog, downloader, extras, hardware, i18n, installer

# Version de la app: una sola fuente de verdad (titulo de la ventana).
VERSION = "1.1.8"


def ruta_recurso(nombre: str) -> str:
    """Resuelve un recurso empaquetado (compatible con PyInstaller --onefile)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    candidatos = [os.path.join(base, nombre), os.path.join(base, "docs", nombre)]
    for ruta in candidatos:
        if os.path.exists(ruta):
            return ruta
    return candidatos[0]

COLOR_FONDO = "#05080f"
COLOR_FONDO_ALT = "#070d18"
COLOR_PANEL = "#0a1422"
COLOR_PANEL_ALT = "#0d1b2e"
COLOR_BORDE = "#1b5570"
COLOR_TEXTO = "#dbeafe"
COLOR_TEXTO_TENUE = "#7c93b5"
COLOR_ACENTO = "#22d3ee"
COLOR_ACENTO_HOVER = "#67e8f9"
COLOR_ACENTO_2 = "#1e5bff"
COLOR_OK = "#34d399"
COLOR_ERROR = "#fb7185"
COLOR_AVISO = "#fbbf24"

FUENTE = "Segoe UI"
FUENTE_MONO = "Consolas"


def mezclar_color(c1: str, c2: str, t: float) -> str:
    """Interpola dos colores hex (#rrggbb) con t entre 0 y 1."""
    a = tuple(int(c1[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(c2[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def linea_degradado(padre) -> tk.Canvas:
    """Linea neon de 2 px con degradado cian -> azul."""
    lienzo = tk.Canvas(padre, height=2, bg=COLOR_FONDO, highlightthickness=0, bd=0)

    def dibujar(event):
        lienzo.delete("all")
        ancho = max(1, event.width)
        for x in range(0, ancho, 4):
            color = mezclar_color(COLOR_ACENTO, COLOR_ACENTO_2, x / ancho)
            lienzo.create_rectangle(x, 0, x + 4, 2, fill=color, outline=color)

    lienzo.bind("<Configure>", dibujar)
    return lienzo


def _png_escalado(ruta_png: str, alto: int, ancho: int = None) -> str:
    """Devuelve la ruta de un PNG escalado EXACTAMENTE a `ancho` x `alto` px.

    Tkinter solo reduce por factores enteros (subsample), lo que dejaba la
    marca en 37px dentro de un canvas de 58px. Aqui se escala con muestreo por
    caja (promedio ponderado por alfa) a cualquier tamano.

    Si `ancho` es None se recorta a un cuadrado ajustado a la marca (uso del
    logo). Si se pasa `ancho`, se respeta la imagen completa con esa proporcion
    (uso de la portada apaisada) y no se recorta a cuadrado.

    No modifica el original: lee `ruta_png` y escribe un PNG temporal con tamano
    exacto. Devuelve la ruta original si algo falla (respaldo seguro).
    """
    cuadrado = ancho is None
    tam = alto
    try:
        import struct as _struct

        with open(ruta_png, "rb") as fh:
            data = fh.read()
        p = 8
        idat = b""
        ihdr = None
        while p < len(data):
            ln = _struct.unpack_from(">I", data, p)[0]
            tipo = data[p + 4:p + 8]
            pay = data[p + 8:p + 8 + ln]
            if tipo == b"IHDR":
                ihdr = _struct.unpack(">IIBBBBB", pay)
            elif tipo == b"IDAT":
                idat += pay
            p += 12 + ln
        w, h, bits, ct = ihdr[0], ihdr[1], ihdr[2], ihdr[3]
        if ct != 6 or bits != 8:
            return ruta_png  # solo RGBA8 (los recursos del proyecto lo son)

        import zlib
        raw = zlib.decompress(idat)
        bpp = 4
        stride = w * bpp

        def paeth(a, b, c):
            pp = a + b - c
            pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
            return a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)

        prev = bytearray(stride)
        filas = []
        q = 0
        for _y in range(h):
            ft = raw[q]; q += 1
            fila = bytearray(raw[q:q + stride]); q += stride
            if ft == 1:
                for i in range(bpp, stride):
                    fila[i] = (fila[i] + fila[i - bpp]) & 255
            elif ft == 2:
                for i in range(stride):
                    fila[i] = (fila[i] + prev[i]) & 255
            elif ft == 3:
                for i in range(stride):
                    a = fila[i - bpp] if i >= bpp else 0
                    fila[i] = (fila[i] + ((a + prev[i]) >> 1)) & 255
            elif ft == 4:
                for i in range(stride):
                    a = fila[i - bpp] if i >= bpp else 0
                    b = prev[i]
                    c = prev[i - bpp] if i >= bpp else 0
                    fila[i] = (fila[i] + paeth(a, b, c)) & 255
            filas.append(fila); prev = fila

        # si es para el logo: recortar la marca a un cuadrado ajustado
        if cuadrado:
            ys = [y for y in range(h) if any(filas[y][x * 4 + 3] > 20 for x in range(w))]
            xs = [x for x in range(w) if any(filas[y][x * 4 + 3] > 20 for y in range(h))]
            x0, x1 = min(xs), max(xs) + 1
            y0, y1 = min(ys), max(ys) + 1
            lado = max(x1 - x0, y1 - y0) + 2
            ccx, ccy = (x0 + x1) / 2, (y0 + y1) / 2
            nx0, ny0 = int(ccx - lado / 2), int(ccy - lado / 2)
            nw = nh = lado
        else:
            nx0, ny0, nw, nh = 0, 0, w, h

        def pixel(x, y):
            if 0 <= y < h and 0 <= x < w:
                o = x * 4
                return filas[y][o], filas[y][o + 1], filas[y][o + 2], filas[y][o + 3]
            return 0, 0, 0, 0

        # muestreo por caja al tamano exacto (ancho x alto independientes)
        fxn = nw / ancho if not cuadrado else nw / tam
        fyn = nh / alto
        sal_ancho = tam if cuadrado else ancho
        sal_alto = tam
        crudo = bytearray()
        for y in range(sal_alto):
            crudo.append(0)
            for x in range(sal_ancho):
                xa = nx0 + int(x * fxn); xb = nx0 + max(int(x * fxn) + 1, int((x + 1) * fxn))
                ya = ny0 + int(y * fyn); yb = ny0 + max(int(y * fyn) + 1, int((y + 1) * fyn))
                rs = gs = bs = as_ = n = 0
                for yy in range(ya, yb):
                    for xx in range(xa, xb):
                        r, g, b, a = pixel(xx, yy)
                        rs += r * a; gs += g * a; bs += b * a; as_ += a; n += 1
                if as_ > 0:
                    crudo += bytes((rs // as_, gs // as_, bs // as_, as_ // max(1, n)))
                else:
                    crudo += b"\x00\x00\x00\x00"

        def chunk(tipo, datos):
            return (_struct.pack(">I", len(datos)) + tipo + datos
                    + _struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF))

        png = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", _struct.pack(">IIBBBBB", sal_ancho, sal_alto, 8, 6, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(bytes(crudo), 9))
               + chunk(b"IEND", b""))
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        destino = os.path.join(base, "png_%dx%d.png" % (sal_ancho, sal_alto))
        try:
            with open(destino, "wb") as fh:
                fh.write(png)
        except OSError:
            import tempfile
            destino = os.path.join(tempfile.gettempdir(), "png_%dx%d.png" % (sal_ancho, sal_alto))
            with open(destino, "wb") as fh:
                fh.write(png)
        return destino
    except Exception:
        return ruta_png  # respaldo: usar el PNG original (subsample como antes)


def portada_cabecera(padre, alto: int = 54):
    """Portada apaisada de la cabecera, escalada a la altura pedida.

    Usa `docs/portada_limpia.png` (recorte de la imagen del usuario, sin la
    periferia que contenia la marca de agua). No modifica ningun original:
    escala con muestreo por caja a un PNG temporal del tamano exacto.

    Devuelve el Label con la imagen (None si la portada no esta disponible).
    """
    # dimensiones del original para calcular el ancho proporcional
    ancho_px, alto_px = 960, 560
    try:
        foto = tk.PhotoImage(file=ruta_recurso("portada_limpia.png"))
        ancho_px, alto_px = foto.width(), foto.height()
    except tk.TclError:
        return None
    ancho = max(1, round(ancho_px * alto / alto_px))
    ruta = _png_escalado(ruta_recurso("portada_limpia.png"), alto, ancho)
    try:
        imagen = tk.PhotoImage(file=ruta)
    except tk.TclError:
        return None
    etiqueta = tk.Label(padre, image=imagen, bg=COLOR_FONDO_ALT, bd=0,
                        highlightthickness=0)
    etiqueta.imagen = imagen  # referencia viva
    return etiqueta


def logo_con_halo(padre, tamano: int = 58):
    """Logo transparente dentro de un canvas con halo radial cian -> azul.

    No modifica el PNG original: lo escala a tamano exacto (Tkinter solo reduce
    por factores enteros, lo que dejaba la marca diminuta) y lo dibuja sobre un
    halo tenue, para que la marca sea la protagonista y no el fondo.
    Devuelve el canvas (None si el logo no esta disponible).
    """
    margen = 6
    objetivo = tamano - margen * 2
    ruta = _png_escalado(ruta_recurso("portada.png"), objetivo)
    try:
        imagen = tk.PhotoImage(file=ruta)
    except tk.TclError:
        return None
    lienzo = tk.Canvas(padre, width=tamano, height=tamano,
                       bg=COLOR_FONDO_ALT, highlightthickness=0, bd=0)
    centro = tamano / 2
    # Halo radial tenue: anillos del cian (centro) al azul (borde)
    pasos = int(centro * 0.75)
    for i in range(pasos, 0, -1):
        radio = i
        color = mezclar_color(COLOR_ACENTO_2, COLOR_ACENTO, i / pasos)
        debil = mezclar_color(COLOR_PANEL, color, 0.42)
        lienzo.create_oval(centro - radio, centro - radio, centro + radio, centro + radio,
                           fill=debil, outline="")
    # Anillo neon exterior
    lienzo.create_oval(0.5, 0.5, tamano - 0.5, tamano - 0.5,
                       outline=COLOR_ACENTO, width=1)
    # El logo encima, ya escalado a tamano exacto (sin alterar el archivo)
    lienzo.imagen = imagen  # referencia viva
    lienzo.create_image(centro, centro, image=imagen)
    return lienzo


def boton_con_halo(padre, texto, estilo, comando, color_halo=COLOR_ACENTO, **opciones):
    """Boton envuelto en un marco de 2 px que se ilumina al pasar el mouse."""
    halo = tk.Frame(padre, bg=COLOR_PANEL, padx=2, pady=2)
    boton = ttk.Button(halo, text=texto, style=estilo, command=comando, **opciones)
    boton.pack()
    boton.bind("<Enter>", lambda _e: halo.configure(bg=color_halo))
    boton.bind("<Leave>", lambda _e: halo.configure(bg=COLOR_PANEL))
    halo.boton = boton
    return halo

CARPETA_DESCARGAS = os.path.join(os.path.expanduser("~"), "Downloads", "Drivers")

# Excepciones de red: no hay que enseñar el volcado de requests al usuario
_ERRORES_RED = ("ConnectionError", "ConnectTimeout", "ReadTimeout", "Timeout",
                "SSLError", "ProxyError", "ChunkedEncodingError")


def _error_traducido(excepcion) -> tuple[str, dict]:
    """Convierte una excepcion en (clave, kwargs) con un mensaje entendible."""
    nombre = type(excepcion).__name__
    if nombre in _ERRORES_RED:
        return "err_conexion", {}
    if nombre == "HTTPError":
        return "err_servidor", {}
    return "err_generico", {"msg": str(excepcion)[:80]}


class DriverGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(i18n.t("app_titulo", version=VERSION))
        self.root.geometry("1040x680")
        self.root.minsize(920, 620)
        self.root.configure(bg=COLOR_FONDO)
        try:
            self.root.iconbitmap(ruta_recurso("icono_axiios_glow.ico"))
        except tk.TclError:
            try:
                self.root.iconbitmap(ruta_recurso("icono_axiios.ico"))
            except tk.TclError:
                pass  # icono no disponible: se usa el de Tk por defecto

        self.cola = queue.Queue(maxsize=200)
        self.dispositivos: list[dict] = []
        self.resultados: list[dict] = []
        self.carpeta = tk.StringVar(value=CARPETA_DESCARGAS)

        # Idioma: la preferencia guardada (si el usuario la eligio) o la del sistema
        self._textos_registrados: list = []
        i18n.fijar_idioma(i18n.cargar_preferencia())
        self._estado_clave = "estado_listo"
        self._estado_kwargs: dict = {}
        self._estado_texto = i18n.t("estado_listo")
        self._estado_color = COLOR_TEXTO
        self._chip_clave = "chip_listo"
        self._chip_color = COLOR_TEXTO
        self._detectando = False
        self._intentos_kit = 0

        self._configurar_estilos()
        self._crear_widgets()
        self._after_id = self.root.after(100, self._procesar_cola)

    def cerrar(self):
        """Cierra la app de forma limpia (cancela el temporizador de la cola)."""
        try:
            self.root.after_cancel(self._after_id)
        except Exception:
            pass
        for hijo in self.root.winfo_children():
            try:
                hijo.destroy()
            except tk.TclError:
                pass

    # ------------------------------------------------------------- interfaz
    def _configurar_estilos(self):
        estilo = ttk.Style(self.root)
        estilo.theme_use("clam")
        estilo.configure(".", background=COLOR_FONDO, foreground=COLOR_TEXTO,
                         fieldbackground=COLOR_PANEL, borderwidth=0,
                         font=(FUENTE, 9))
        estilo.configure("TFrame", background=COLOR_FONDO)
        estilo.configure("Card.TFrame", background=COLOR_PANEL)
        estilo.configure("TLabel", background=COLOR_FONDO, foreground=COLOR_TEXTO)
        estilo.configure("Card.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXTO)

        estilo.configure("TButton", background=COLOR_PANEL_ALT, foreground=COLOR_TEXTO,
                         bordercolor=COLOR_BORDE, lightcolor=COLOR_PANEL_ALT,
                         darkcolor=COLOR_PANEL_ALT, padding=(14, 8),
                         font=(FUENTE, 9, "bold"), relief="flat")
        estilo.map("TButton",
                   background=[("disabled", COLOR_PANEL), ("active", "#12314a")],
                   foreground=[("disabled", "#4b5f78")])
        estilo.configure("Accent.TButton", background=COLOR_ACENTO, foreground="#04121a",
                         bordercolor=COLOR_ACENTO, lightcolor=COLOR_ACENTO,
                         darkcolor=COLOR_ACENTO, padding=(14, 8),
                         font=(FUENTE, 9, "bold"), relief="flat")
        estilo.map("Accent.TButton",
                   background=[("pressed", "#06b6d4"), ("active", COLOR_ACENTO_HOVER)],
                   foreground=[("active", "#04121a")])
        estilo.configure("Blue.TButton", background=COLOR_ACENTO_2, foreground="#f5f9ff",
                         bordercolor=COLOR_ACENTO_2, lightcolor=COLOR_ACENTO_2,
                         darkcolor=COLOR_ACENTO_2, padding=(14, 8),
                         font=(FUENTE, 9, "bold"), relief="flat")
        estilo.map("Blue.TButton",
                   background=[("pressed", "#133fc4"), ("active", "#7aa8ff")],
                   foreground=[("active", "#ffffff")])
        estilo.configure("Ghost.TButton", background=COLOR_FONDO_ALT, foreground=COLOR_ACENTO,
                         bordercolor=COLOR_BORDE, lightcolor=COLOR_BORDE,
                         darkcolor=COLOR_BORDE, padding=(12, 8),
                         font=(FUENTE, 9, "bold"), relief="flat")
        estilo.map("Ghost.TButton",
                   background=[("active", "#0f2233")],
                   foreground=[("active", COLOR_ACENTO_HOVER)])

        estilo.configure("Treeview", background=COLOR_PANEL, fieldbackground=COLOR_PANEL,
                         foreground=COLOR_TEXTO, rowheight=26,
                         bordercolor=COLOR_BORDE, lightcolor=COLOR_BORDE,
                         darkcolor=COLOR_BORDE)
        estilo.map("Treeview",
                   background=[("selected", "#0e4a63")],
                   foreground=[("selected", "#ffffff")])
        estilo.configure("Treeview.Heading", background="#0e2a40", foreground=COLOR_ACENTO,
                         font=(FUENTE, 9, "bold"), relief="flat", padding=(6, 6))
        estilo.map("Treeview.Heading", background=[("active", "#154866")])

        estilo.configure("Horizontal.TProgressbar", background=COLOR_ACENTO,
                         troughcolor="#08111d", bordercolor="#08111d",
                         lightcolor=COLOR_ACENTO, darkcolor=COLOR_ACENTO,
                         thickness=12)
        estilo.configure("TEntry", fieldbackground="#08111d", foreground=COLOR_TEXTO,
                         insertcolor=COLOR_ACENTO, bordercolor=COLOR_BORDE,
                         lightcolor=COLOR_BORDE, darkcolor=COLOR_BORDE, padding=(8, 6))
        estilo.map("TEntry", bordercolor=[("focus", COLOR_ACENTO)])

    def _crear_widgets(self):
        raiz = tk.Frame(self.root, bg=COLOR_FONDO)
        raiz.pack(fill="both", expand=True)

        # Cabecera
        cabecera = tk.Frame(raiz, bg=COLOR_FONDO_ALT, height=78)
        cabecera.pack(fill="x")
        cabecera.pack_propagate(False)

        # Bloque de texto a la IZQUIERDA (como estaba)
        marca = tk.Frame(cabecera, bg=COLOR_FONDO_ALT)
        marca.pack(side="left", padx=18, pady=10)
        fila = tk.Frame(marca, bg=COLOR_FONDO_ALT)
        fila.pack(anchor="w")
        tk.Label(fila, text="DRIVERS", bg=COLOR_FONDO_ALT, fg=COLOR_TEXTO,
                 font=(FUENTE, 17, "bold")).pack(side="left")
        tk.Label(fila, text="HTS", bg=COLOR_FONDO_ALT, fg=COLOR_ACENTO_2,
                 font=(FUENTE, 17, "bold")).pack(side="left", padx=(6, 0))
        self._registrar_texto(
            tk.Label(marca, bg=COLOR_FONDO_ALT, fg=COLOR_TEXTO_TENUE,
                     font=(FUENTE_MONO, 8)),
            "marca_edicion").pack(anchor="w")

        self.chip = tk.Label(cabecera, bg="#04222e",
                             fg=COLOR_ACENTO, font=(FUENTE_MONO, 8, "bold"),
                             padx=12, pady=6, highlightbackground=COLOR_ACENTO,
                             highlightthickness=1)
        self.chip.pack(side="right", padx=18)
        self._chip_por_color(COLOR_TEXTO, "chip_listo")

        # Selector de idioma (a la derecha del todo; el chip queda a su izquierda)
        selector = tk.Frame(cabecera, bg=COLOR_FONDO_ALT)
        selector.pack(side="right", padx=(0, 6), pady=23)
        self._lbl_idioma = {}
        tk.Label(selector, text="|", bg=COLOR_FONDO_ALT, fg=COLOR_BORDE,
                 font=(FUENTE_MONO, 8, "bold")).pack(side="right", padx=4)
        for codigo in reversed(i18n.IDIOMAS):
            lbl = tk.Label(selector, text=codigo.upper(), bg=COLOR_FONDO_ALT,
                           fg=COLOR_TEXTO_TENUE, font=(FUENTE_MONO, 8, "bold"),
                           padx=5, cursor="hand2")
            lbl.pack(side="right")
            lbl.bind("<Button-1>", lambda _e, c=codigo: self._aplicar_idioma(c))
            self._lbl_idioma[codigo] = lbl

        # SOLO la portada va centrada, sin mover el resto
        portada = portada_cabecera(cabecera, 62)
        if portada is None:
            portada = logo_con_halo(cabecera, 62)  # respaldo si falta la portada
        if portada is not None:
            portada.place(relx=0.5, rely=0.5, anchor="center")

        # Linea neon degradada bajo la cabecera
        linea_degradado(raiz).pack(fill="x")

        cuerpo = tk.Canvas(raiz, bg=COLOR_FONDO, highlightthickness=0, bd=0)
        cuerpo.pack(fill="both", expand=True)
        self.lienzo = cuerpo

        # Acciones
        acciones = tk.Frame(cuerpo, bg=COLOR_PANEL, highlightbackground=COLOR_ACENTO,
                            highlightthickness=1, padx=12, pady=10)

        fila_botones = tk.Frame(acciones, bg=COLOR_PANEL)
        fila_botones.pack(fill="x")
        self.boton_detectar = boton_con_halo(fila_botones, i18n.t("btn_detectar"),
                                             "Accent.TButton", self._accion_detectar)
        self.boton_detectar.pack(side="left")
        self.boton_buscar = boton_con_halo(fila_botones, i18n.t("btn_buscar"),
                                           "Accent.TButton", self._accion_buscar)
        self.boton_buscar.pack(side="left", padx=(8, 0))
        self.boton_descargar = boton_con_halo(fila_botones, i18n.t("btn_descargar"),
                                              "Accent.TButton", self._accion_descargar)
        self.boton_descargar.pack(side="left", padx=(8, 0))
        self.boton_vcpp = boton_con_halo(fila_botones, i18n.t("btn_vcpp"),
                                         "Ghost.TButton", self._abrir_visual_cpp)
        self.boton_vcpp.pack(side="left", padx=(16, 0))
        self.boton_kit = boton_con_halo(fila_botones, i18n.t("btn_kit"), "Blue.TButton",
                                        self._accion_kit, "#7aa8ff")
        self.boton_kit.pack(side="right")
        for halo, clave in ((self.boton_detectar, "btn_detectar"),
                            (self.boton_buscar, "btn_buscar"),
                            (self.boton_descargar, "btn_descargar"),
                            (self.boton_vcpp, "btn_vcpp"),
                            (self.boton_kit, "btn_kit")):
            self._registrar_texto(halo.boton, clave)

        fila_carpeta = tk.Frame(acciones, bg=COLOR_PANEL)
        fila_carpeta.pack(fill="x", pady=(10, 0))
        self.etiqueta_carpeta = tk.Label(fila_carpeta, bg=COLOR_PANEL,
                                        fg=COLOR_TEXTO_TENUE, font=(FUENTE_MONO, 8, "bold"))
        self.etiqueta_carpeta.configure(text=i18n.t("lbl_carpeta"))
        self.etiqueta_carpeta.pack(side="left", padx=(0, 10))
        self._textos_registrados.append((self.etiqueta_carpeta, "lbl_carpeta"))
        ttk.Entry(fila_carpeta, textvariable=self.carpeta).pack(side="left", fill="x", expand=True)
        boton_con_halo(fila_carpeta, "...", "Ghost.TButton",
                       self._elegir_carpeta, width=4).pack(side="left", padx=(8, 0))

        # Listas lado a lado (tarjetas directas sobre el lienzo con rejilla)
        borde_izq, izq = self._panel_lista(cuerpo, "panel_hw", "panel_hw_sub")
        self.arbol_hw = ttk.Treeview(izq, columns=("categoria", "nombre"),
                                     show="headings", selectmode="browse")
        self.arbol_hw.heading("categoria", text=i18n.t("col_categoria"))
        self.arbol_hw.heading("nombre", text=i18n.t("col_dispositivo"))
        self.arbol_hw.column("categoria", width=90, anchor="center")
        self.arbol_hw.column("nombre", width=330)
        self.arbol_hw.pack(fill="both", expand=True)

        borde_der, der = self._panel_lista(cuerpo, "panel_dr", "panel_dr_sub")
        self.arbol_dr = ttk.Treeview(der, columns=("titulo", "productos", "fecha"),
                                     show="headings", selectmode="browse")
        self.arbol_dr.heading("titulo", text=i18n.t("col_titulo"))
        self.arbol_dr.heading("productos", text=i18n.t("col_windows"))
        self.arbol_dr.heading("fecha", text=i18n.t("col_fecha"))
        self.arbol_dr.column("titulo", width=200)
        self.arbol_dr.column("productos", width=120)
        self.arbol_dr.column("fecha", width=70, anchor="center")
        self.arbol_dr.pack(fill="both", expand=True)

        # Panel inferior: progreso y estado
        inferior = tk.Frame(cuerpo, bg=COLOR_PANEL, highlightbackground=COLOR_BORDE,
                            highlightthickness=1, padx=12, pady=10)

        fila_progreso = tk.Frame(inferior, bg=COLOR_PANEL)
        fila_progreso.pack(fill="x")
        self._registrar_texto(
            tk.Label(fila_progreso, bg=COLOR_PANEL, fg=COLOR_TEXTO_TENUE,
                     font=(FUENTE_MONO, 8, "bold")),
            "lbl_progreso").pack(side="left", padx=(0, 10))
        self.barra = ttk.Progressbar(fila_progreso, mode="determinate")
        self.barra.pack(side="left", fill="x", expand=True)

        self.instalar_var = tk.BooleanVar(value=False)
        self.chk_instalar = tk.Checkbutton(
            inferior, variable=self.instalar_var, command=self._toggle_instalar,
            bg=COLOR_PANEL, fg=COLOR_TEXTO_TENUE, selectcolor=COLOR_FONDO,
            activebackground=COLOR_PANEL, activeforeground=COLOR_TEXTO,
            highlightthickness=0, bd=0, anchor="w", font=(FUENTE, 9))
        self.chk_instalar.pack(anchor="w", pady=(8, 0))
        self._textos_registrados.append((self.chk_instalar, "chk_instalar"))
        self.etiqueta_estado = ttk.Label(inferior, style="Card.TLabel")
        self.etiqueta_estado.pack(anchor="w", pady=(6, 0))
        self._etiqueta_estado_actual()

        # Tarjetas como ventanas del lienzo (dejan ver la rejilla de fondo)
        self.acciones = acciones
        self.inferior = inferior
        self._win_acciones = cuerpo.create_window(14, 12, window=acciones, anchor="nw")
        self._win_izq = cuerpo.create_window(14, 140, window=borde_izq, anchor="nw")
        self._win_der = cuerpo.create_window(520, 140, window=borde_der, anchor="nw")
        self._win_inferior = cuerpo.create_window(14, 560, window=inferior, anchor="nw")
        cuerpo.bind("<Configure>", self._layout_cuerpo)

    def _layout_cuerpo(self, event):
        ancho, alto = event.width, event.height
        self._dibujar_rejilla(ancho, alto)
        alto_acciones = self.acciones.winfo_reqheight()
        alto_inferior = self.inferior.winfo_reqheight()
        margen, separacion = 14, 12
        ancho_util = max(200, ancho - margen * 2)
        y_listas = margen + alto_acciones + separacion
        alto_listas = max(120, alto - margen - alto_inferior - separacion - y_listas)
        ancho_izq = max(120, (ancho_util - 16) // 2)
        ancho_der = max(120, ancho_util - ancho_izq - 16)
        self.lienzo.itemconfigure(self._win_acciones, width=ancho_util, height=alto_acciones)
        self.lienzo.coords(self._win_acciones, margen, margen)
        self.lienzo.itemconfigure(self._win_izq, width=ancho_izq, height=alto_listas)
        self.lienzo.coords(self._win_izq, margen, y_listas)
        self.lienzo.itemconfigure(self._win_der, width=ancho_der, height=alto_listas)
        self.lienzo.coords(self._win_der, margen + ancho_izq + 16, y_listas)
        self.lienzo.itemconfigure(self._win_inferior, width=ancho_util, height=alto_inferior)
        self.lienzo.coords(self._win_inferior, margen, alto - margen - alto_inferior)

    def _dibujar_rejilla(self, ancho: int, alto: int):
        self.lienzo.delete("rejilla")
        paso = 28
        for x in range(0, ancho, paso):
            color = "#0e2a40" if x % (paso * 4) == 0 else "#0a1a2a"
            self.lienzo.create_line(x, 0, x, alto, fill=color, tags="rejilla")
        for y in range(0, alto, paso):
            color = "#0e2a40" if y % (paso * 4) == 0 else "#0a1a2a"
            self.lienzo.create_line(0, y, ancho, y, fill=color, tags="rejilla")
        self.lienzo.tag_lower("rejilla")

    def _panel_lista(self, padre, clave_titulo: str, clave_subtitulo: str):
        """Tarjeta con borde neon, cabecera y cuerpo para una lista."""
        borde = tk.Frame(padre, bg=COLOR_PANEL, highlightbackground=COLOR_BORDE,
                         highlightthickness=1)
        cab = tk.Frame(borde, bg=COLOR_PANEL)
        cab.pack(fill="x", padx=12, pady=(10, 0))
        tk.Frame(cab, bg=COLOR_ACENTO, width=3, height=16).pack(side="left", padx=(0, 8))
        textos = tk.Frame(cab, bg=COLOR_PANEL)
        textos.pack(side="left")
        lbl_titulo = tk.Label(textos, bg=COLOR_PANEL, fg=COLOR_TEXTO,
                              font=(FUENTE, 9, "bold"))
        lbl_titulo.pack(anchor="w")
        lbl_sub = tk.Label(textos, bg=COLOR_PANEL, fg=COLOR_TEXTO_TENUE,
                           font=(FUENTE_MONO, 7))
        lbl_sub.pack(anchor="w")
        self._textos_registrados.append((lbl_titulo, clave_titulo))
        self._textos_registrados.append((lbl_sub, clave_subtitulo))
        lbl_titulo.configure(text=i18n.t(clave_titulo))
        lbl_sub.configure(text=i18n.t(clave_subtitulo))
        cuerpo = tk.Frame(borde, bg=COLOR_PANEL)
        cuerpo.pack(fill="both", expand=True, padx=10, pady=(8, 10))
        return borde, cuerpo

    # ------------------------------------------------------------- idioma
    @property
    def idioma_actual(self) -> str:
        """Idioma vigente de la interfaz."""
        return i18n.idioma()

    def _registrar_texto(self, widget, clave: str):
        """Guarda el widget y su clave para poder re-traducirlo al cambiar idioma."""
        widget.configure(text=i18n.t(clave))
        self._textos_registrados.append((widget, clave))
        return widget

    def _aplicar_idioma(self, codigo: str):
        """Cambia el idioma y reescribe TODO el texto visible (estatico y dinamico)."""
        # guardar=True: el usuario eligio el idioma, se recuerda entre sesiones
        i18n.fijar_idioma(codigo, guardar=True)
        for c, lbl in self._lbl_idioma.items():
            lbl.configure(fg=COLOR_ACENTO if c == self.idioma_actual else COLOR_TEXTO_TENUE)
        for widget, clave in self._textos_registrados:
            widget.configure(text=i18n.t(clave))
        self.arbol_hw.heading("categoria", text=i18n.t("col_categoria"))
        self.arbol_hw.heading("nombre", text=i18n.t("col_dispositivo"))
        self.arbol_dr.heading("titulo", text=i18n.t("col_titulo"))
        self.arbol_dr.heading("productos", text=i18n.t("col_windows"))
        self.arbol_dr.heading("fecha", text=i18n.t("col_fecha"))
        self.root.title(i18n.t("app_titulo", version=VERSION))
        self._chip_por_color(self._chip_color, self._chip_clave)
        self._etiqueta_estado_actual()
        self._redibujar_tablas()
        vc = getattr(self, "_ventana_vcpp", None)
        if vc is not None and vc.ventana.winfo_exists():
            vc.aplicar_idioma()

    def _redibujar_tablas(self):
        """Vuelve a poblar las tablas desde los datos en memoria, traducidos.

        Conserva la seleccion del usuario (si la habia).
        """
        sel_hw = self.arbol_hw.selection()
        sel_dr = self.arbol_dr.selection()
        self.arbol_hw.delete(*self.arbol_hw.get_children())
        for i, d in enumerate(self.dispositivos):
            marca = " ⚠" if d.get("error") else ""
            self.arbol_hw.insert("", "end", iid=str(i),
                                 values=(hardware.nombre_categoria(d["categoria"]),
                                         d["nombre"] + marca))
        self.arbol_dr.delete(*self.arbol_dr.get_children())
        self.arbol_dr.tag_configure("recomendado", foreground=COLOR_OK)
        self.arbol_dr.tag_configure("antiguo", foreground=COLOR_AVISO)
        for i, r in enumerate(self.resultados):
            self.arbol_dr.insert("", "end", iid=str(i),
                                 values=self._valores_resultado(r),
                                 tags=self._tags_resultado(r))
        for arbol, sel in ((self.arbol_hw, sel_hw), (self.arbol_dr, sel_dr)):
            for iid in sel:
                if arbol.exists(iid):
                    arbol.selection_add(iid)

    # ------------------------------------------------------------- utilidad
    def _log(self, texto: str, color: str = COLOR_TEXTO):
        self._estado_texto = texto
        self._estado_color = color
        self._estado_clave = None
        self._estado_kwargs = {}
        self.etiqueta_estado.configure(text=texto, foreground=color)
        self._chip_por_color(color, None)

    def _log_t(self, clave: str, color: str = COLOR_TEXTO, **kwargs):
        """Log traducible: guarda la clave para re-renderizar al cambiar idioma."""
        self._log(i18n.t(clave, **kwargs), color)
        self._estado_clave = clave
        self._estado_kwargs = kwargs

    def _cola_estado(self, clave: str, color: str = COLOR_TEXTO, **kwargs):
        """Encola un estado traducible (lo consume el hilo principal)."""
        self.cola.put(("estado_clave", (clave, color, kwargs)))

    def _etiqueta_estado_actual(self):
        """Reescribe la etiqueta de estado con el idioma vigente."""
        clave = getattr(self, "_estado_clave", None)
        if clave:
            texto = i18n.t(clave, **getattr(self, "_estado_kwargs", {}))
        else:
            texto = getattr(self, "_estado_texto", "")
        self.etiqueta_estado.configure(
            text=texto, foreground=getattr(self, "_estado_color", COLOR_TEXTO))

    _CHIP_POR_COLOR = {COLOR_ERROR: "chip_error", COLOR_OK: "chip_activo"}

    def _chip_por_color(self, color, clave=None):
        """Pinta el chip segun su estado real (la clave se guarda para traducir)."""
        if clave is None:
            clave = self._CHIP_POR_COLOR.get(color, "chip_trabajando")
        self._chip_clave = clave
        self._chip_color = color
        fg = color if color in (COLOR_OK, COLOR_ERROR) else COLOR_ACENTO
        self.chip.configure(text=i18n.t(clave), fg=fg, highlightbackground=fg)

    def _ejecutar_hilo(self, funcion, *args):
        threading.Thread(target=funcion, args=args, daemon=True).start()

    def _valores_resultado(self, r: dict) -> tuple:
        """Valores de una fila de resultados, con marcas traducidas."""
        titulo = r["titulo"]
        if r.get("recomendado"):
            titulo = i18n.t("marca_recomendado") + titulo
        if r.get("antiguo"):
            titulo = titulo + i18n.t("marca_antiguo")
        productos = (r.get("productos") or "").replace(
            "Servicing Drivers", "").replace("Update and Later", "+").strip()
        return (titulo, productos, r.get("fecha", ""))

    def _tags_resultado(self, r: dict) -> tuple:
        etiquetas = []
        if r.get("recomendado"):
            etiquetas.append("recomendado")
        if r.get("antiguo"):
            etiquetas.append("antiguo")
        return tuple(etiquetas)

    def _procesar_cola(self):
        try:
            while True:
                tipo, datos = self.cola.get_nowait()
                if tipo == "estado":
                    self._log(*datos)
                elif tipo == "estado_clave":
                    if len(datos) == 3:
                        clave, color, kwargs = datos
                    else:
                        clave, color = datos
                        kwargs = {}
                    self._log_t(clave, color, **kwargs)
                elif tipo == "hardware":
                    self._mostrar_hardware(datos)
                elif tipo == "fin_deteccion":
                    self._detectando = False
                elif tipo == "resultados":
                    self._mostrar_resultados(datos)
                elif tipo == "progreso":
                    recibidos, total = datos
                    self.barra["value"] = (recibidos / total * 100) if total else 0
                elif tipo == "descargado":
                    self.barra["value"] = 100
                    self._log_t("log_guardado", COLOR_OK, datos=datos, extra="")
                    # ya no hay nada en marcha: el chip vuelve a "listo" (verde)
                    self._chip_por_color(COLOR_OK, "chip_listo")
                elif tipo == "error":
                    clave_error, kwargs_error = _error_traducido(datos)
                    self._log_t("log_error", COLOR_ERROR,
                                motivo=(clave_error, kwargs_error))
                elif tipo == "error_clave":
                    self._log_t(datos[0], COLOR_ERROR)
        except queue.Empty:
            pass
        self.root.after(100, self._procesar_cola)

    # ------------------------------------------------------------- acciones
    def _toggle_instalar(self):
        """Al activar la instalacion automatica: pide admin si no lo somos."""
        if self.instalar_var.get() and not installer.es_admin():
            if messagebox.askyesno(
                    i18n.t("msg_admin_titulo"),
                    i18n.t("msg_admin_cuerpo")):
                self.root.after(100, self.root.destroy)
                installer.reiniciar_como_admin()
                return
            self.instalar_var.set(False)

    def _instalar_archivo(self, ruta: str, instalar: bool,
                          switches=()) -> tuple[bool, str, dict]:
        """Instala un .cab, un .zip, un .msu o un Visual C++ descargado.

        Devuelve (ok, clave, kwargs). Cada tipo de paquete tiene su instalador:
        un .msu NO es un ejecutable, asi que va con wusa.exe. Y un .exe que no
        es un Visual C++ NO se ejecuta: se avisa al usuario.
        """
        if not instalar:
            return True, "", {}
        self._cola_estado("log_instalando", nombre=os.path.basename(ruta)[:45])
        extension = ruta.lower()
        if extension.endswith(".cab"):
            return installer.instalar_driver_cab(ruta)
        if extension.endswith(".zip"):
            return installer.instalar_driver_zip(ruta)
        if extension.endswith(".msu"):
            return installer.instalar_driver_msu(ruta)
        if not switches:
            # un .exe sin parametros de Visual C++ no se puede instalar solo
            return False, "inst_no_instalable", {"nombre": os.path.basename(ruta)}
        return installer.instalar_redistribuible(ruta, switches)

    def _elegir_carpeta(self):
        ruta = filedialog.askdirectory(initialdir=self.carpeta.get())
        if ruta:
            self.carpeta.set(ruta)

    def _accion_detectar(self):
        self._log_t("log_detectando")
        self._detectando = True

        def trabajo():
            try:
                info = hardware.detectar_hardware()
                self.cola.put(("hardware", info))
            except Exception as e:
                self.cola.put(("error", e))
            finally:
                self.cola.put(("fin_deteccion", None))

        self._ejecutar_hilo(trabajo)

    def _mostrar_hardware(self, info: dict):
        self.dispositivos = info["dispositivos"]
        self.arbol_hw.delete(*self.arbol_hw.get_children())
        for i, d in enumerate(self.dispositivos):
            marca = " ⚠" if d["error"] else ""
            self.arbol_hw.insert("", "end", iid=str(i),
                                 values=(hardware.nombre_categoria(d["categoria"]),
                                         d["nombre"] + marca))
        cpu = info.get("procesador") or i18n.t("desconocido")
        self._log_t("log_hardware", COLOR_OK, n=len(self.dispositivos), cpu=cpu)

    def _accion_buscar(self):
        sel = self.arbol_hw.selection()
        if not sel:
            messagebox.showinfo(i18n.t("msg_buscar_titulo"), i18n.t("msg_buscar_cuerpo"))
            return
        dispositivo = self.dispositivos[int(sel[0])]
        consulta = dispositivo["consulta"]
        self._log_t("log_buscando", consulta=consulta)
        self.barra["value"] = 0

        def trabajo():
            try:
                resultados = catalog.buscar_drivers(consulta)
                catalog.marcar_recomendado(resultados, consulta)
                self.cola.put(("resultados", resultados))
            except Exception as e:
                self.cola.put(("error", e))

        self._ejecutar_hilo(trabajo)

    def _mostrar_resultados(self, resultados: list):
        self.resultados = resultados
        # El recomendado va primero y resaltado
        ordenados = sorted(resultados, key=lambda r: not r.get("recomendado"))
        self.resultados = ordenados
        self._redibujar_tablas()
        if resultados:
            aviso = next((r for r in resultados if r.get("aviso")), None)
            if aviso:
                # se pasa la clave anidada para que el aviso se re-traduzca
                extra = ("aviso_catalogo_antiguo", {"antiguedad": aviso.get("antiguedad", 0)})
                self._log_t("log_con_aviso", COLOR_AVISO, n=len(resultados), aviso=extra)
            else:
                self._log_t("log_resultados", COLOR_OK, n=len(resultados))
        else:
            self._log_t("log_sin_resultados", COLOR_ERROR)

    # ------------------------------------------------------- kit completo
    def _accion_kit(self):
        """Descarga de un clic: driver recomendado de cada esencial + Visual C++."""
        if not self.dispositivos:
            self._intentos_kit = getattr(self, "_intentos_kit", 0) + 1
            if self._intentos_kit > 3:
                # no se insistirá mas veces: se avisa y se deja
                self._log_t("kit_sin_deteccion", COLOR_ERROR)
                return
            if self._detectando:
                # la deteccion anterior sigue en marcha: se espera a que acabe
                self.root.after(2000, self._accion_kit)
                return
            self._log_t("log_kit_detectando")
            self._accion_detectar()
            # reintento acotado: 3 veces como maximo, y esperando a que la
            # deteccion termine (tarda unos 4 s) para no solaparlas
            self.root.after(6000, self._accion_kit)
            return
        self._intentos_kit = 0

        kit = self._dispositivos_kit()
        vc = [p for p in extras.listar_visual_cpp()
              if p["nombre"].startswith("Visual C++ 2015-2022")]
        resumen = "\n".join(
            f"  • {hardware.nombre_categoria(d['categoria'])}: {d['nombre']}" for d in kit)
        resumen += "\n".join([""] + [f"  • {p['nombre']}" for p in vc])
        if not messagebox.askyesno(
                i18n.t("msg_kit_titulo"),
                i18n.t("msg_kit_cuerpo", n=len(kit), resumen=resumen)):
            return

        carpeta = self.carpeta.get() or CARPETA_DESCARGAS
        instalar = self.instalar_var.get()
        if instalar and not messagebox.askyesno(
                i18n.t("msg_kit_titulo"),
                i18n.t("msg_kit_instalar_cuerpo")):
            return
        self._ejecutar_hilo(self._trabajo_kit, kit, vc, carpeta, instalar)

    def _dispositivos_kit(self):
        """Un dispositivo (fisico, con ID) por consulta, priorizando categorias."""
        vistos = set()
        kit = []
        for d in self.dispositivos:
            if not d.get("ven"):  # solo hardware fisico identificable
                continue
            clave = d["consulta"].lower()
            if clave in vistos:
                continue
            vistos.add(clave)
            kit.append(d)
        return kit

    def _trabajo_kit(self, kit, visual_cpp, carpeta, instalar=False):
        total = len(kit) + len(visual_cpp)
        fallos = 0
        instalados = 0
        omitidos = 0
        descargados = 0

        def estado_clave(clave, color=COLOR_TEXTO, **kwargs):
            self._cola_estado(clave, color, **kwargs)

        n = 0
        for d in kit:
            n += 1
            try:
                estado_clave("kit_buscando", nombre=d['nombre'][:45], n=n, total=total)
                resultados = catalog.buscar_drivers(d["consulta"])
                catalog.marcar_recomendado(resultados, d["consulta"])
                elegido = next((r for r in resultados if r.get("recomendado")), None)
                if not elegido:
                    # el catalogo no tiene driver para este dispositivo: no es un
                    # fallo del kit, es un hecho. Se avisa y se sigue.
                    estado_clave("kit_sin_resultados", COLOR_AVISO,
                                 nombre=d['nombre'][:40], n=n, total=total)
                    omitidos += 1
                    continue
                url = catalog.obtener_enlace_descarga(elegido["guid"])
                if not url:
                    estado_clave("kit_sin_enlace", COLOR_AVISO,
                                 nombre=d['nombre'][:40], n=n, total=total)
                    omitidos += 1
                    continue
                estado_clave("kit_descargando", nombre=d['nombre'][:45], n=n, total=total)
                ruta = downloader.descargar(
                    url, carpeta,
                    progreso=lambda r, t: self.cola.put(("progreso", (r, t))),
                )
                descargados += 1
                if instalar:
                    ok, clave, kwargs = self._instalar_archivo(ruta, True)
                    estado_clave("kit_instalado", n=n, total=total,
                                 nombre=d['nombre'][:38],
                                 resultado=("inst_ok" if ok else "inst_fallo",
                                            {"msg": (clave, kwargs)}))
                    instalados += 1 if ok else 0
                    if not ok:
                        fallos += 1
                self.cola.put(("progreso", (n, total)))
            except Exception as e:
                clave_error, kwargs_error = _error_traducido(e)
                estado_clave("kit_error", COLOR_ERROR, motivo=(clave_error, kwargs_error),
                             n=n, total=total)
                fallos += 1

        for p in visual_cpp:
            n += 1
            try:
                estado_clave("kit_descargando", nombre=p['nombre'], n=n, total=total)
                ruta = downloader.descargar(
                    p["url"], carpeta, nombre=p["archivo"],
                    progreso=lambda r, t: self.cola.put(("progreso", (r, t))),
                )
                descargados += 1
                if instalar:
                    ok, clave, kwargs = self._instalar_archivo(ruta, True, p.get("switches", ()))
                    estado_clave("kit_instalado", n=n, total=total,
                                 nombre=p['nombre'][:38],
                                 resultado=("inst_ok" if ok else "inst_fallo",
                                            {"msg": (clave, kwargs)}))
                    instalados += 1 if ok else 0
                    if not ok:
                        fallos += 1
                self.cola.put(("progreso", (n, total)))
            except Exception as e:
                clave_error, kwargs_error = _error_traducido(e)
                estado_clave("kit_error", COLOR_ERROR, motivo=(clave_error, kwargs_error),
                             n=n, total=total)
                fallos += 1

        if fallos:
            self.cola.put(("estado_clave",
                           ("kit_terminado_fallos", COLOR_ERROR,
                            {"n": fallos, "omitidos": omitidos})))
        elif not instalar:
            # solo se descargo: no seInstalled nada, asi que no se dice "0 instalados"
            self.cola.put(("estado_clave",
                           ("kit_terminado_descarga", COLOR_OK,
                            {"descargados": descargados, "omitidos": omitidos,
                             "carpeta": carpeta})))
        elif omitidos:
            self.cola.put(("estado_clave",
                           ("kit_terminado_ok_sin", COLOR_OK,
                            {"instalados": instalados, "omitidos": omitidos})))
        else:
            self.cola.put(("estado_clave",
                           ("kit_terminado_ok", COLOR_OK, {"instalados": instalados})))

    def _accion_descargar(self):
        sel = self.arbol_dr.selection()
        if not sel:
            messagebox.showinfo(i18n.t("msg_descargar_titulo"),
                                i18n.t("msg_descargar_cuerpo"))
            return
        resultado = self.resultados[int(sel[0])]
        carpeta = self.carpeta.get() or CARPETA_DESCARGAS
        instalar = self.instalar_var.get()
        self._log_t("log_obteniendo_enlace")
        self.barra["value"] = 0

        def trabajo():
            try:
                url = catalog.obtener_enlace_descarga(resultado["guid"])
                if not url:
                    self.cola.put(("error_clave", ("err_sin_enlace",)))
                    return
                self.cola.put(("estado_clave",
                               ("log_descargando", COLOR_TEXTO,
                                {"titulo": resultado['titulo'][:60]})))
                ruta = downloader.descargar(
                    url, carpeta,
                    progreso=lambda r, t: self.cola.put(("progreso", (r, t))),
                )
                if instalar:
                    ok, clave, kwargs = self._instalar_archivo(ruta, True)
                    self.cola.put(("estado_clave",
                                   ("log_guardado", COLOR_OK,
                                    {"datos": ruta,
                                     "extra": ("log_guardado_extra",
                                               {"resultado": ("inst_ok" if ok else "inst_fallo",
                                                              {"msg": (clave, kwargs)})})})))
                else:
                    self.cola.put(("descargado", ruta))
            except Exception as e:
                self.cola.put(("error", e))

        self._ejecutar_hilo(trabajo)


    # ------------------------------------------------------- visual c++
    def _abrir_visual_cpp(self):
        # no se abre una segunda ventana: se enfoca la que ya hay
        existente = getattr(self, "_ventana_vcpp", None)
        if existente is not None and existente.ventana.winfo_exists():
            existente.ventana.deiconify()
            existente.ventana.lift()
            existente.ventana.focus_force()
            return
        ventana = VentanaVisualCpp(self.root, self.carpeta.get() or CARPETA_DESCARGAS)
        ventana.padre_app = self
        self._ventana_vcpp = ventana


class VentanaVisualCpp:
    """Ventana para descargar redistribuibles de Visual C++ (enlaces oficiales MS)."""

    def __init__(self, padre: tk.Tk, carpeta: str):
        self.carpeta = carpeta
        self.paquetes = extras.listar_visual_cpp()
        self.padre_app = None
        self._textos_registrados = []
        self._estado_clave = None
        self._estado_kwargs = {}
        self._estado_texto = ""
        self._cerrada = False
        # cola propia: el hilo de descarga deja aqui los mensajes y el hilo
        # principal los aplica (llamar a Tk desde un hilo no es seguro)
        self.cola = queue.Queue(maxsize=200)

        self.ventana = tk.Toplevel(padre)
        self.ventana.title(i18n.t("vcpp_ventana"))
        self.ventana.configure(bg=COLOR_FONDO)
        self.ventana.transient(padre)
        # SIN grab_set(): secuestra el raton y dejaria el selector de idioma
        # de la cabecera sin poder pulsarse
        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar)

        cabecera = tk.Frame(self.ventana, bg=COLOR_FONDO_ALT, padx=16, pady=12)
        cabecera.pack(fill="x")
        self.titulo = tk.Label(cabecera, bg=COLOR_FONDO_ALT, fg=COLOR_ACENTO_2,
                               font=(FUENTE, 14, "bold"))
        self.titulo.pack(anchor="w")
        self._registrar("titulo", "vcpp_titulo")
        self.subtitulo = tk.Label(cabecera, bg=COLOR_FONDO_ALT, fg=COLOR_TEXTO_TENUE,
                                  font=(FUENTE_MONO, 8))
        self.subtitulo.pack(anchor="w")
        self._registrar("subtitulo", "vcpp_subtitulo")
        linea_degradado(self.ventana).pack(fill="x")

        marco = tk.Frame(self.ventana, bg=COLOR_FONDO, padx=16, pady=14)
        marco.pack(fill="both", expand=True)

        tarjeta = tk.Frame(marco, bg=COLOR_PANEL, highlightbackground=COLOR_BORDE,
                           highlightthickness=1, padx=14, pady=12)
        tarjeta.pack(fill="both", expand=True)

        self.lbl_selecciona = tk.Label(tarjeta, bg=COLOR_PANEL,
                                       fg=COLOR_TEXTO_TENUE, font=(FUENTE_MONO, 8, "bold"))
        self.lbl_selecciona.pack(anchor="w", pady=(0, 6))
        self._registrar("lbl_selecciona", "vcpp_selecciona")

        self.vars = []
        for p in self.paquetes:
            var = tk.BooleanVar(value=(p["nombre"].startswith("Visual C++ 2015-2022")))
            self.vars.append(var)
            cb = tk.Checkbutton(tarjeta, text=p["nombre"], variable=var,
                                bg=COLOR_PANEL, fg=COLOR_TEXTO,
                                selectcolor=COLOR_FONDO, activebackground=COLOR_PANEL,
                                activeforeground=COLOR_TEXTO, highlightthickness=0, bd=0,
                                anchor="w", font=(FUENTE, 9))
            cb.pack(fill="x")

        botones = tk.Frame(tarjeta, bg=COLOR_PANEL)
        botones.pack(fill="x", pady=(10, 0))
        halo_todas = boton_con_halo(botones, i18n.t("vcpp_todas"), "Ghost.TButton",
                                    lambda: self._marcar(True))
        halo_todas.pack(side="left")
        halo_ninguna = boton_con_halo(botones, i18n.t("vcpp_ninguna"), "Ghost.TButton",
                                      lambda: self._marcar(False))
        halo_ninguna.pack(side="left", padx=6)
        halo_descargar = boton_con_halo(botones, i18n.t("vcpp_descargar"),
                                        "Accent.TButton", self._descargar)
        halo_descargar.pack(side="right")
        self.boton_descargar = halo_descargar.boton
        # los botones tambien se re-traducen al cambiar de idioma
        self.botones = [halo_todas.boton, halo_ninguna.boton, halo_descargar.boton]
        self._claves_botones = ["vcpp_todas", "vcpp_ninguna", "vcpp_descargar"]

        self.instalar_var = tk.BooleanVar(value=False)
        self.chk_instalar = tk.Checkbutton(
            tarjeta, variable=self.instalar_var, command=self._toggle_instalar,
            bg=COLOR_PANEL, fg=COLOR_TEXTO_TENUE, selectcolor=COLOR_FONDO,
            activebackground=COLOR_PANEL, activeforeground=COLOR_TEXTO,
            highlightthickness=0, bd=0, anchor="w", font=(FUENTE, 9))
        self.chk_instalar.pack(anchor="w", pady=(8, 0))
        self._registrar("chk_instalar", "vcpp_chk_instalar")

        self.barra = ttk.Progressbar(tarjeta, mode="determinate")
        self.barra.pack(fill="x", pady=(10, 0))
        self.estado = ttk.Label(tarjeta, style="Card.TLabel", text="")
        self.estado.pack(anchor="w", pady=(6, 0))
        self._after_id = self.ventana.after(100, self._procesar_cola)

    def _registrar(self, attr, clave):
        self._textos_registrados.append((attr, clave))
        getattr(self, attr).configure(text=i18n.t(clave))

    def aplicar_idioma(self):
        """Re-traduce la ventana al cambiar el idioma en la principal."""
        self.ventana.title(i18n.t("vcpp_ventana"))
        for attr, clave in self._textos_registrados:
            getattr(self, attr).configure(text=i18n.t(clave))
        for boton, clave in zip(self.botones, self._claves_botones):
            boton.configure(text=i18n.t(clave))
        self._estado_actual()

    def _estado_actual(self):
        clave = getattr(self, "_estado_clave", None)
        if clave:
            texto = i18n.t(clave, **getattr(self, "_estado_kwargs", {}))
        else:
            texto = getattr(self, "_estado_texto", "")
        self.estado.configure(text=texto, foreground=getattr(self, "_estado_color", COLOR_TEXTO))

    def _log(self, clave, color=COLOR_TEXTO, **kwargs):
        """Muestra un estado traducible en la ventana.

        Acepta tambien la forma antigua (clave, color, kwargs) en una tupla.
        """
        if isinstance(clave, tuple) and len(clave) == 3:
            clave, color, kwargs = clave
        self._estado_clave = clave
        self._estado_kwargs = kwargs
        self._estado_texto = i18n.t(clave, **kwargs)
        self._estado_color = color
        self.estado.configure(text=self._estado_texto, foreground=color)

    def cerrar(self):
        self._cerrada = True
        try:
            self.ventana.after_cancel(self._after_id)
        except Exception:
            pass
        if self.padre_app is not None:
            try:
                self.padre_app._ventana_vcpp = None
            except Exception:
                pass
        self.ventana.destroy()

    def _marcar(self, valor: bool):
        for v in self.vars:
            v.set(valor)

    def _toggle_instalar(self):
        from tkinter import messagebox
        if self.instalar_var.get() and not installer.es_admin():
            messagebox.showwarning(
                i18n.t("msg_vcpp_titulo"),
                i18n.t("msg_vcpp_cuerpo"),
                parent=self.ventana)
            self.instalar_var.set(False)

    def _descargar(self):
        elegidos = [p for p, v in zip(self.paquetes, self.vars) if v.get()]
        if not elegidos:
            self.estado.configure(text=i18n.t("vcpp_nada_seleccionado"),
                                  foreground=COLOR_ERROR)
            return
        self.boton_descargar.state(["disabled"])
        carpeta = self.carpeta
        instalar = self.instalar_var.get()

        def trabajo():
            """Hilo de descarga: NO toca Tk, solo deja mensajes en la cola."""
            instalados = 0
            for i, p in enumerate(elegidos, 1):
                try:
                    self.cola.put(("estado", ("vcpp_progreso", COLOR_TEXTO,
                                              {"n": i, "total": len(elegidos),
                                               "nombre": p['nombre']})))
                    ruta = downloader.descargar(
                        p["url"], carpeta, nombre=p["archivo"],
                        progreso=lambda r, t: self.cola.put(
                            ("progreso", (r / t * 100) if t else 0)),
                    )
                    if instalar:
                        self.cola.put(("estado", ("vcpp_instalando", COLOR_TEXTO,
                                                  {"n": i, "total": len(elegidos),
                                                   "nombre": p['nombre']})))
                        ok, clave, kwargs = installer.instalar_redistribuible(
                            ruta, p.get("switches", ()))
                        instalados += 1 if ok else 0
                        if not ok:
                            self.cola.put(("error",
                                           (i18n.t("vcpp_fallo_instalar",
                                                   nombre=p['nombre'],
                                                   msg=(clave, kwargs)),
                                            COLOR_ERROR)))
                except Exception as e:
                    clave_error, kwargs_error = _error_traducido(e)
                    self.cola.put(("error",
                                   (i18n.t("vcpp_error", nombre=p['nombre'],
                                           motivo=(clave_error, kwargs_error)),
                                    COLOR_ERROR)))
                    self.cola.put(("boton", True))
                    return
            self.cola.put(("progreso", 100))
            extra = i18n.t("vcpp_instalados", n=instalados) if instalar else ""
            self.cola.put(("estado", ("vcpp_completado", COLOR_OK,
                                      {"extra": extra, "carpeta": carpeta})))
            self.cola.put(("boton", True))

        threading.Thread(target=trabajo, daemon=True).start()

    def _procesar_cola(self):
        """Aplica en el hilo principal lo que deja el hilo de descarga."""
        try:
            while True:
                tipo, datos = self.cola.get_nowait()
                if tipo == "estado":
                    clave, color, kwargs = datos
                    self._log(clave, color, **kwargs)
                elif tipo == "progreso":
                    self.barra.configure(value=datos)
                elif tipo == "error":
                    texto, color = datos
                    self.estado.configure(text=texto, foreground=color)
                elif tipo == "boton":
                    self.boton_descargar.state(["!disabled"])
        except queue.Empty:
            pass
        except (tk.TclError, ValueError) as exc:
            # un mensaje mal formado no debe Tumbar la ventana
            print("aviso: mensaje de la cola descartado (%r)" % (exc,))
        if not self._cerrada:
            self._after_id = self.ventana.after(100, self._procesar_cola)


def main():
    root = tk.Tk()
    DriverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
