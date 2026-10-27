"""Pruebas del soporte bilingue (modulos i18n y textos) y de la GUI.

Los textos de UI viven en `modules/textos.py`; la mecanica en `modules/i18n.py`.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import i18n, textos


@pytest.fixture(autouse=True)
def _prefs_aisladas(tmp_path, monkeypatch):
    """Las pruebas NUNCA tocan la preferencia real del usuario en %APPDATA%."""
    monkeypatch.setattr(i18n, "RUTA_PREFS", str(tmp_path / "prefs.json"))
    yield


# --- deteccion -----------------------------------------------------------
def test_detectar_espanol(monkeypatch):
    monkeypatch.setattr(i18n, "_idioma_windows", lambda: "es")
    assert i18n.detectar_idioma() == "es"


def test_detectar_ingles(monkeypatch):
    monkeypatch.setattr(i18n, "_idioma_windows", lambda: "en")
    assert i18n.detectar_idioma() == "en"


def test_otro_idioma_cae_en_espanol(monkeypatch):
    monkeypatch.setattr(i18n, "_idioma_windows", lambda: "de")
    assert i18n.detectar_idioma() == "es"


def test_una_etiqueta_completa_tambien_se_detecta(monkeypatch):
    """Por si el sistema devuelve 'en-US' en vez de 'en'."""
    monkeypatch.setattr(i18n, "_idioma_windows", lambda: "en-US")
    assert i18n.detectar_idioma() == "en"


def test_parseo_real_de_langid():
    """El idioma primario son los 10 bits bajos: 0x0416 portugues, 0x0411 japones."""
    assert (0x080A & 0x3FF) == 0x0A          # espanol
    assert i18n._idioma_desde_langid(0x080A) == "es"
    assert i18n._idioma_desde_langid(0x0409) == "en"
    assert i18n._idioma_desde_langid(0x0416) == "es"   # portugues -> respaldo
    assert i18n._idioma_desde_langid(0x0411) == "es"   # japones  -> respaldo


# --- persistencia --------------------------------------------------------
def test_idioma_desconocido_guardado_cae_en_espanol(tmp_path, monkeypatch):
    prefs = tmp_path / "prefs.json"
    prefs.write_text(json.dumps({"idioma": "fr"}), encoding="utf-8")
    monkeypatch.setattr(i18n, "RUTA_PREFS", str(prefs))
    monkeypatch.setattr(i18n, "_idioma_windows", lambda: "de")
    assert i18n.cargar_preferencia() == "es"


def test_prefs_corruptas_no_revientan(tmp_path, monkeypatch):
    prefs = tmp_path / "prefs.json"
    prefs.write_text("{esto no es json", encoding="utf-8")
    monkeypatch.setattr(i18n, "RUTA_PREFS", str(prefs))
    assert i18n.cargar_preferencia() in ("es", "en")


def test_prefs_con_forma_inesperada_no_revientan(tmp_path, monkeypatch):
    """Un JSON valido pero que no es un dict (lista, null, texto) no debe romper."""
    for contenido in ("[]", "null", '"texto"', "3"):
        prefs = tmp_path / "prefs.json"
        prefs.write_text(contenido, encoding="utf-8")
        monkeypatch.setattr(i18n, "RUTA_PREFS", str(prefs))
        assert i18n.cargar_preferencia() in ("es", "en"), contenido


def test_cargar_preferencia_sin_archivo(tmp_path, monkeypatch):
    """Sin archivo: se detecta el idioma del sistema."""
    monkeypatch.setattr(i18n, "RUTA_PREFS", str(tmp_path / "no-existe.json"))
    monkeypatch.setattr(i18n, "_idioma_windows", lambda: "en")
    assert i18n.cargar_preferencia() == "en"


def test_guardar_y_recargar(tmp_path, monkeypatch):
    prefs = tmp_path / "prefs.json"
    monkeypatch.setattr(i18n, "RUTA_PREFS", str(prefs))
    assert i18n.guardar_preferencia("en") is True
    assert i18n.cargar_preferencia() == "en"


def test_apdata_no_escribible_no_revienta(monkeypatch):
    monkeypatch.setattr(i18n, "RUTA_PREFS", "Z:\\ruta\\imposible\\prefs.json")
    assert i18n.guardar_preferencia("en") is False


def test_guardar_en_ruta_sin_directorio_no_revienta(monkeypatch, tmp_path):
    """Una ruta sin carpeta no puede crear el directorio: no debe lanzar."""
    monkeypatch.setattr(i18n, "RUTA_PREFS", str(tmp_path / "prefs-sin-carpeta.json"))
    assert i18n.guardar_preferencia("en") is True
    monkeypatch.setattr(i18n, "RUTA_PREFS", "Z:\\ruta\\imposible\\prefs.json")
    assert i18n.guardar_preferencia("en") is False

def test_fijar_idioma_no_revienta_si_no_puede_guardar(monkeypatch):
    monkeypatch.setattr(i18n, "RUTA_PREFS", "Z:\\ruta\\imposible\\prefs.json")
    assert i18n.fijar_idioma("en") == "en"
    assert i18n.fijar_idioma("xx") == "es"   # valor invalido -> respaldo


def test_fijar_idioma_no_guarda_salvo_que_se_pida():
    """El arranque no debe persistir: el idioma de Windows se sigue detectando."""
    i18n.fijar_idioma("en")
    assert not os.path.exists(i18n.RUTA_PREFS)


def test_fijar_idioma_guarda_cuando_se_pide():
    i18n.fijar_idioma("en", guardar=True)
    assert os.path.exists(i18n.RUTA_PREFS)
    assert i18n.cargar_preferencia() == "en"


# --- traduccion ----------------------------------------------------------
def test_t_traduce_y_respalda():
    i18n.fijar_idioma("es")
    assert i18n.t("btn_detectar") == "1 \u00b7 DETECTAR HARDWARE"
    i18n.fijar_idioma("en")
    assert i18n.t("btn_detectar") == "1 \u00b7 DETECT HARDWARE"
    assert i18n.t("clave_que_no_existe") == "clave_que_no_existe"


def test_t_con_placeholders():
    i18n.fijar_idioma("es")
    assert i18n.t("log_guardado", datos="X") == "Guardado en: X"


def test_t_no_lanza_con_una_plantilla_rota():
    """Una clave con '{' sin cerrar no debe tumbar la app."""
    monkeypatch_texto = {"es": {"rota": "abre { y nada"}, "en": {"rota": "abre { y nada"}}
    original = textos.TEXTOS
    textos.TEXTOS = monkeypatch_texto
    try:
        assert isinstance(i18n.t("rota", x=1), str)
    finally:
        textos.TEXTOS = original


def test_t_resuelve_un_valor_anidado():
    """Un valor ('clave', {kwargs}) se traduce dentro de la plantilla."""
    i18n.fijar_idioma("es")
    texto = i18n.t("log_con_aviso", n=2,
                   aviso=("aviso_catalogo_antiguo", {"antiguedad": 3}))
    assert "catalogo sin versiones recientes (3 anos)" in texto
    i18n.fijar_idioma("en")
    texto = i18n.t("log_con_aviso", n=2,
                   aviso=("aviso_catalogo_antiguo", {"antiguedad": 3}))
    assert "catalog has no recent versions (3 years)" in texto


def test_cobertura_de_claves():
    assert textos.claves_faltantes() == []


def test_las_claves_existen_en_los_dos_idiomas():
    assert set(textos.TEXTOS["es"]) == set(textos.TEXTOS["en"])


def test_los_marcadores_coinciden_entre_idiomas():
    import re
    for clave, plantilla in textos.TEXTOS["es"].items():
        esperados = set(re.findall(r"\{(\w+)\}", plantilla))
        obtenidos = set(re.findall(r"\{(\w+)\}", textos.TEXTOS["en"][clave]))
        assert esperados == obtenidos, clave


def test_claves_chip_existen():
    for clave in ("chip_listo", "chip_error", "chip_activo", "chip_trabajando"):
        assert clave in textos.TEXTOS["es"]
        assert clave in textos.TEXTOS["en"]


def test_el_titulo_de_la_app_muestra_la_version_real():
    """El titulo no puede decir una version vieja: hay una sola fuente de verdad."""
    import gui
    assert gui.VERSION.startswith("1."), gui.VERSION
    i18n.fijar_idioma("es")
    assert gui.VERSION in i18n.t("app_titulo", version=gui.VERSION)
    i18n.fijar_idioma("en")
    assert gui.VERSION in i18n.t("app_titulo", version=gui.VERSION)


# --- GUI: cambio de idioma en vivo ---------------------------------------
_RAIZ = None


def _raiz():
    """Una sola raiz Tk reutilizada: crear y destruir varias seguidas rompe Tcl."""
    global _RAIZ
    if _RAIZ is None:
        import tkinter as tk
        _RAIZ = tk.Tk()
        _RAIZ.withdraw()
    return _RAIZ


def _app(monkeypatch, idioma="es"):
    """Crea la app sobre la raiz compartida, con el idioma que se indique.

    El idioma se fija SIEMPRE: la app se publica para Windows en español y en
    ingles, y las pruebas no pueden depender del idioma del equipo.
    """
    import gui
    monkeypatch.setattr(i18n, "cargar_preferencia", lambda: idioma)
    raiz = _raiz()
    app = gui.DriverGUI(raiz)
    raiz.update()
    return raiz, app


def _esperar(raiz, condicion,timeout=3.0):
    """Bombea el bucle de eventos hasta que la condicion sea cierta."""
    import time
    fin = time.time() + timeout
    while time.time() < fin:
        raiz.update()
        if condicion():
            return True
        time.sleep(0.02)
    return False


def test_arranque_usa_el_idioma_detectado(monkeypatch):
    raiz, app = _app(monkeypatch, idioma="en")
    try:
        assert app.idioma_actual == "en"
        assert app.boton_detectar.boton.cget("text") == i18n.t("btn_detectar")
    finally:
        app.cerrar()


def test_el_arranque_no_guarda_la_preferencia(monkeypatch):
    """Si el usuario nunca elige idioma, la app debe seguir al idioma de Windows."""
    raiz, app = _app(monkeypatch)
    try:
        assert not os.path.exists(i18n.RUTA_PREFS)
    finally:
        app.cerrar()


def test_el_selector_guarda_la_preferencia(monkeypatch):
    raiz, app = _app(monkeypatch)
    try:
        app._aplicar_idioma("en")
        # se lee el archivo: el helper simula cargar_preferencia()
        with open(i18n.RUTA_PREFS, encoding="utf-8") as f:
            assert json.load(f)["idioma"] == "en"
    finally:
        app.cerrar()


def test_cambio_de_idioma_reescribe_estaticos(monkeypatch):
    raiz, app = _app(monkeypatch)
    try:
        app._aplicar_idioma("es")
        raiz.update()
        assert app.boton_detectar.boton.cget("text") == "1 \u00b7 DETECTAR HARDWARE"
        assert app.etiqueta_carpeta.cget("text") == "CARPETA DE DESCARGA"
        app._aplicar_idioma("en")
        raiz.update()
        assert app.boton_detectar.boton.cget("text") == "1 \u00b7 DETECT HARDWARE"
        assert app.etiqueta_carpeta.cget("text") == "DOWNLOAD FOLDER"
        assert app.arbol_hw.heading("categoria")["text"] == "CATEGORY"
    finally:
        app.cerrar()


def test_chip_conserva_estado_al_cambiar_idioma(monkeypatch):
    """Si el chip estaba en ERROR, sigue en ERROR (traducido), no vuelve a LISTO."""
    import gui
    raiz, app = _app(monkeypatch)
    try:
        app._log(i18n.t("log_error", datos="x"), gui.COLOR_ERROR)
        raiz.update()
        assert app.chip.cget("text") == i18n.t("chip_error")
        app._aplicar_idioma("en")
        raiz.update()
        assert app.chip.cget("text") == i18n.t("chip_error")
    finally:
        app.cerrar()


def test_etiqueta_estado_se_retraduce_al_cambiar_idioma(monkeypatch):
    raiz, app = _app(monkeypatch)
    try:
        app._log_t("log_detectando")
        raiz.update()
        assert app.etiqueta_estado.cget("text") == "Detectando hardware..."
        app._aplicar_idioma("en")
        raiz.update()
        assert app.etiqueta_estado.cget("text") == "Detecting hardware..."
    finally:
        app.cerrar()


def test_el_aviso_del_catalogo_se_retraduce(monkeypatch):
    """El aviso del catalogo no puede quedar horneado en el idioma anterior."""
    raiz, app = _app(monkeypatch)
    try:
        app._mostrar_resultados([{
            "titulo": "Driver X", "productos": "Windows 11", "fecha": "2020-01-01",
            "recomendado": True, "antiguo": True, "antiguedad": 5,
            "aviso": i18n.t("aviso_catalogo_antiguo", antiguedad=5),
        }])
        raiz.update()
        app._aplicar_idioma("en")
        raiz.update()
        texto = app.etiqueta_estado.cget("text")
        assert "catalog has no recent versions (5 years)" in texto, texto
        assert "catalogo sin versiones recientes" not in texto, texto
    finally:
        app.cerrar()


def test_el_mensaje_de_instalacion_se_retraduce(monkeypatch):
    """'Instalando X...' debe re-traducirse al cambiar de idioma."""
    raiz, app = _app(monkeypatch)
    try:
        app._cola_estado("log_instalando", nombre="driver.cab")
        assert _esperar(raiz, lambda: app.etiqueta_estado.cget("text") == "Instalando driver.cab..."), \
            app.etiqueta_estado.cget("text")
        app._aplicar_idioma("en")
        raiz.update()
        assert app.etiqueta_estado.cget("text") == "Installing driver.cab..."
    finally:
        app.cerrar()


def test_tablas_se_redibujan_traducidas(monkeypatch):
    raiz, app = _app(monkeypatch)
    try:
        app.dispositivos = [
            {"categoria": "Red", "nombre": "Ethernet", "ven": "VEN_1", "error": False,
             "consulta": "Ethernet"},
        ]
        app._mostrar_hardware({"dispositivos": app.dispositivos, "procesador": "CPU"})
        raiz.update()
        app._aplicar_idioma("en")
        raiz.update()
        fila = app.arbol_hw.item("0", "values")
        assert fila[0] == i18n.t("cat_red")
    finally:
        app.cerrar()


def test_la_seleccion_de_la_tabla_se_conserva(monkeypatch):
    """Cambiar de idioma no debe deseleccionar el driver que el usuario eligio."""
    raiz, app = _app(monkeypatch)
    try:
        app.resultados = [
            {"titulo": "Driver X", "productos": "Windows 11", "fecha": "2020-01-01"},
            {"titulo": "Driver Y", "productos": "Windows 10", "fecha": "2020-02-01"},
        ]
        app._redibujar_tablas()
        raiz.update()
        app.arbol_dr.selection_set("1")
        raiz.update()
        assert app.arbol_dr.selection() == ("1",)
        app._aplicar_idioma("en")
        raiz.update()
        assert app.arbol_dr.selection() == ("1",)
    finally:
        app.cerrar()


def test_ventana_vcpp_cambia_de_idioma(monkeypatch):
    import gui
    raiz, app = _app(monkeypatch)
    try:
        vc = gui.VentanaVisualCpp(raiz, app.carpeta.get())
        app._ventana_vcpp = vc
        app._aplicar_idioma("en")
        raiz.update()
        assert vc.titulo.cget("text") == i18n.t("vcpp_titulo")
        assert vc.ventana.title() == i18n.t("vcpp_ventana")
        app._aplicar_idioma("es")
        raiz.update()
        assert vc.titulo.cget("text") == i18n.t("vcpp_titulo")
        vc.cerrar()
    finally:
        app.cerrar()


def test_los_botones_de_la_ventana_vcpp_se_retraducen(monkeypatch):
    """TODAS / NINGUNA / DESCARGAR SELECCIONADOS tambien cambian de idioma."""
    import gui
    raiz, app = _app(monkeypatch)
    try:
        vc = gui.VentanaVisualCpp(raiz, app.carpeta.get())
        app._ventana_vcpp = vc
        raiz.update()
        antes = [b.cget("text") for b in vc.botones]
        app._aplicar_idioma("en")
        raiz.update()
        despues = [b.cget("text") for b in vc.botones]
        assert antes == ["TODAS", "NINGUNA", "DESCARGAR SELECCIONADOS"], antes
        assert despues == ["ALL", "NONE", "DOWNLOAD SELECTED"], despues
        vc.cerrar()
    finally:
        app.cerrar()


def test_la_ventana_vcpp_no_se_abre_dos_veces(monkeypatch):
    """Abrirla dos veces no debe dejar una ventana huerfana sin re-traducir."""
    raiz, app = _app(monkeypatch)
    try:
        app._abrir_visual_cpp()
        primera = app._ventana_vcpp
        assert primera is not None
        app._abrir_visual_cpp()
        assert app._ventana_vcpp is primera
        primera.cerrar()
    finally:
        app.cerrar()


def test_cerrar_la_ventana_vcpp_durante_la_descarga_no_rompe(monkeypatch):
    """El hilo de descarga sobrevive al cierre: no debe lanzar TclError."""
    import gui
    raiz, app = _app(monkeypatch)
    try:
        vc = gui.VentanaVisualCpp(raiz, app.carpeta.get())
        app._ventana_vcpp = vc
        raiz.update()
        vc.cerrar()
        # el hilo intentara actualizar widgets ya destruidos: no debe romper
        vc.ventana.after(0, lambda: None)
        raiz.update()
    finally:
        app.cerrar()


def test_el_mensaje_de_guardado_separa_la_ruta_del_resultado():
    """'Guardado en: <ruta> -> OK: msg' (antes salia pegado: '<ruta>OK: msg')."""
    i18n.fijar_idioma("es")
    solo = i18n.t("log_guardado", datos="C:\\Drivers\\x.cab", extra="")
    assert solo == "Guardado en: C:\\Drivers\\x.cab", solo
    con = i18n.t("log_guardado", datos="C:\\Drivers\\x.cab",
                 extra=("log_guardado_extra",
                        {"resultado": ("inst_ok", {"msg": ("inst_ok_texto", {})})}))
    assert con == "Guardado en: C:\\Drivers\\x.cab -> OK: instalado", con


# --- kit completo: el recuento de fallos y de instalados -----------------
def test_el_kit_cuenta_los_fallos_de_instalacion(monkeypatch, tmp_path):
    """Un driver que no instala debe contar como fallo, no como instalado."""
    import gui
    from modules import catalog
    monkeypatch.setattr(catalog, "buscar_drivers", lambda consulta: [
        {"titulo": "Driver X", "guid": "g", "productos": "Windows 11",
         "fecha": "2020", "recomendado": True}])
    monkeypatch.setattr(catalog, "obtener_enlace_descarga", lambda guid: "http://x/y.cab")
    monkeypatch.setattr(gui.downloader, "descargar", lambda url, carpeta, **kw: "x.cab")
    monkeypatch.setattr(gui.installer, "instalar_driver_cab",
                        lambda r: (False, "inst_pnputil_error", {}))
    raiz, app = _app(monkeypatch)
    try:
        kit = [{"categoria": "Red", "nombre": "Ethernet", "consulta": "Ethernet",
                "ven": "VEN_1"}]
        app._trabajo_kit(kit, [], str(tmp_path), True)
        app._procesar_cola()
        raiz.update()
        texto = app.etiqueta_estado.cget("text").lower()
        assert "1 fallo" in texto, texto
    finally:
        app.cerrar()


def test_un_dispositivo_sin_driver_no_es_un_fallo_del_kit(monkeypatch, tmp_path):
    """Si el catalogo no tiene driver para un dispositivo, el kit NO debe fallar.

    Es un hecho, no un error: debe mostrarse como aviso, no en rojo.
    """
    import gui
    from modules import catalog
    monkeypatch.setattr(catalog, "buscar_drivers", lambda consulta: [])
    monkeypatch.setattr(gui.downloader, "descargar", lambda url, carpeta, **kw: "x.cab")
    monkeypatch.setattr(gui.installer, "instalar_driver_cab",
                        lambda r: (True, "inst_ok_texto", {}))
    raiz, app = _app(monkeypatch)
    try:
        kit = [{"categoria": "Red", "nombre": "Ethernet", "consulta": "Ethernet",
                "ven": "VEN_1"}]
        app._trabajo_kit(kit, [], str(tmp_path), True)
        app._procesar_cola()
        raiz.update()
        texto = app.etiqueta_estado.cget("text")
        assert "fallo" not in texto.lower(), texto
        assert "driver en el catalogo" in texto.lower(), texto
        assert "instalado" in texto.lower(), texto
    finally:
        app.cerrar()


def test_el_kit_que_falla_de_verdad_lo_dice(monkeypatch, tmp_path):
    """Si la instalacion falla de verdad, ahi si debe salir el mensaje de fallo."""
    import gui
    from modules import catalog
    monkeypatch.setattr(catalog, "buscar_drivers", lambda consulta: [
        {"titulo": "Driver X", "guid": "g", "productos": "Windows 11", "fecha": "2020",
         "recomendado": True}])
    monkeypatch.setattr(catalog, "obtener_enlace_descarga", lambda guid: "http://x/y.cab")
    monkeypatch.setattr(gui.downloader, "descargar", lambda url, carpeta, **kw: "x.cab")
    monkeypatch.setattr(gui.installer, "instalar_driver_cab",
                        lambda r: (False, "inst_pnputil_error", {}))
    raiz, app = _app(monkeypatch)
    try:
        kit = [{"categoria": "Red", "nombre": "Ethernet", "consulta": "Ethernet",
                "ven": "VEN_1"}]
        app._trabajo_kit(kit, [], str(tmp_path), True)
        app._procesar_cola()
        raiz.update()
        texto = app.etiqueta_estado.cget("text")
        assert "fallo" in texto.lower(), texto
    finally:
        app.cerrar()


# --- errores de red: mensajes entendibles, no volcados de excepcion ------
def test_un_error_de_conexion_se_muestra_traducido():
    """Un error de red no debe enseñar un HTTPSConnectionPool al usuario."""
    import requests
    import gui
    clave, kwargs = gui._error_traducido(
        requests.exceptions.ConnectionError("HTTPSConnectionPool(host='x')"))
    assert clave == "err_conexion", clave
    i18n.fijar_idioma("es")
    assert "conexion" in i18n.t(clave, **kwargs).lower()
    i18n.fijar_idioma("en")
    assert "connection" in i18n.t(clave, **kwargs).lower()


def test_un_error_de_servidor_se_muestra_traducido():
    import requests
    import gui
    clave, kwargs = gui._error_traducido(
        requests.exceptions.HTTPError("500 Server Error"))
    assert clave == "err_servidor", clave


def test_un_error_generico_muestra_el_detalle():
    import gui
    clave, kwargs = gui._error_traducido(ValueError("algo raro"))
    assert clave == "err_generico", clave
    assert "algo raro" in kwargs["msg"]


def test_el_error_del_kit_usa_el_mensaje_traducido(monkeypatch, tmp_path):
    """Un error de red en el kit debe salir traducido, no como HTTPSConnectionPool."""
    from modules import catalog
    import requests
    monkeypatch.setattr(catalog, "buscar_drivers", lambda consulta: (_ for _ in ()).throw(
        requests.exceptions.ConnectionError("HTTPSConnectionPool(host='www.catalog')")))
    raiz, app = _app(monkeypatch)
    try:
        kit = [{"categoria": "Red", "nombre": "Ethernet", "consulta": "Ethernet",
                "ven": "VEN_1"}]
        app._trabajo_kit(kit, [], str(tmp_path), True)
        # se recogen los mensajes EN ORDEN: son los que ve el usuario
        mensajes = []
        while not app.cola.empty():
            tipo, datos = app.cola.get_nowait()
            if tipo == "estado_clave":
                clave, color, kwargs = datos
                mensajes.append(i18n.t(clave, **kwargs))
        assert mensajes, "el kit no ha emitido ningun mensaje"
        assert not any("HTTPSConnectionPool" in m for m in mensajes), mensajes
        assert any("conexion" in m.lower() for m in mensajes), mensajes
    finally:
        app.cerrar()


# --- fallos que ve el usuario, encontrados en la revision final ------------
def test_el_kit_no_dice_que_instalo_cero_si_no_instala(monkeypatch):
    """Sin la casilla de instalar, el kit DESCARGA: no debe decir '0 instalados'."""
    import gui
    from modules import catalog
    monkeypatch.setattr(catalog, "buscar_drivers", lambda consulta: [
        {"titulo": "Driver X", "guid": "g", "productos": "Windows 11",
         "fecha": "2020", "recomendado": True}])
    monkeypatch.setattr(catalog, "obtener_enlace_descarga", lambda guid: "http://x/y.cab")
    monkeypatch.setattr(gui.downloader, "descargar", lambda url, carpeta, **kw: "x.cab")
    raiz, app = _app(monkeypatch)
    try:
        kit = [{"categoria": "Red", "nombre": "Ethernet", "consulta": "Ethernet",
                "ven": "VEN_1"}]
        app._trabajo_kit(kit, [], os.path.join(os.environ.get("TEMP", "."), "kit"), False)
        app._procesar_cola()
        raiz.update()
        texto = app.etiqueta_estado.cget("text").lower()
        assert "0 driver" not in texto, texto
        assert "descarg" in texto, texto
    finally:
        app.cerrar()


def test_el_kit_no_reintenta_la_deteccion_para_siempre(monkeypatch):
    """Si la deteccion no da dispositivos, no se puede reintentar en bucle."""
    raiz, app = _app(monkeypatch)
    try:
        app.dispositivos = []
        reintentos = []
        app._accion_detectar = lambda: reintentos.append(1)
        app._accion_kit()
        # se llama una vez y se avisa; no debe programar un reintento infinito
        for _ in range(5):
            raiz.update()
        assert len(reintentos) <= 1, "no debe reintentar la deteccion sin limite"
    finally:
        app.cerrar()


def test_la_ventana_vcpp_no_secuestra_el_raton(monkeypatch):
    """grab_set() bloquea el selector de idioma de la cabecera."""
    import gui
    raiz, app = _app(monkeypatch)
    try:
        vc = gui.VentanaVisualCpp(raiz, app.carpeta.get())
        raiz.update()
        # con grab_set() el raton queda capturado por la ventana secundaria
        assert raiz.grab_current() is not vc.ventana, \
            "la ventana VC++ secuestra el raton e impide cambiar el idioma"
        vc.cerrar()
    finally:
        app.cerrar()


def test_la_ventana_vcpp_no_llama_after_desde_el_hilo(monkeypatch):
    """after() desde un hilo secundario no es seguro en Tkinter."""
    import inspect
    import gui
    fuente = inspect.getsource(gui.VentanaVisualCpp._descargar)
    assert "self.ventana.after(" not in fuente, \
        "el hilo no debe llamar a after() directamente"
    assert "self.cola.put" in fuente, \
        "el hilo debe pasar por la cola del hilo principal"


def test_la_cola_vcpp_tras_cerrar_la_ventana_no_rompe(monkeypatch):
    """Los mensajes pendientes en la cola no rompen tras cerrar la ventana."""
    import gui
    raiz, app = _app(monkeypatch)
    try:
        vc = gui.VentanaVisualCpp(raiz, app.carpeta.get())
        app._ventana_vcpp = vc
        raiz.update()
        # el hilo deja mensajes en la cola y la ventana se cierra
        vc.cola.put(("estado", ("vcpp_progreso", "TEXTO", {"n": 1, "total": 2, "nombre": "X"})))
        vc.cerrar()
        raiz.update()   # no debe saltar ningun TclError
    finally:
        app.cerrar()


def test_los_mensajes_de_la_cola_vcpp_tienen_el_formato_correcto(monkeypatch):
    """Todos los mensajes 'estado' deben bring 3 valores (clave, color, kwargs)."""
    import gui
    from modules import installer
    monkeypatch.setattr(gui.downloader, "descargar",
                        lambda url, carpeta, **kw: "vc_redist_x64.exe")
    monkeypatch.setattr(installer, "instalar_redistribuible",
                        lambda r, s=(): (True, "inst_ok_texto", {}))
    raiz, app = _app(monkeypatch)
    try:
        vc = gui.VentanaVisualCpp(raiz, app.carpeta.get())
        app._ventana_vcpp = vc
        raiz.update()
        for v in vc.vars[1:]:
            v.set(False)
        vc._descargar()
        # se espera a que el hilo termine
        import time
        fin = time.time() + 20
        while time.time() < fin and vc.cola.empty():
            raiz.update()
            time.sleep(0.05)
        raiz.update()
        mensajes = []
        while not vc.cola.empty():
            tipo, datos = vc.cola.get_nowait()
            if tipo == "estado":
                assert len(datos) == 3, "un mensaje de estado debe traer 3 valores: %r" % (datos,)
                clave, color, kwargs = datos
                assert isinstance(clave, str), "la clave debe ser texto: %r" % (clave,)
                mensajes.append(clave)
        assert "vcpp_completado" in mensajes, mensajes
        vc.cerrar()
    finally:
        app.cerrar()


def test_la_suite_no_depende_del_idioma_del_sistema(monkeypatch):
    """La app se publica para Windows en ingles: las pruebas deben ser independientes."""
    monkeypatch.setattr(i18n, "_idioma_windows", lambda: "en")
    raiz, app = _app(monkeypatch, idioma="en")
    try:
        raiz.update()
        assert app.idioma_actual == "en"
        # los textos en ingles deben ser los de la clave, no los de espanol
        assert app.boton_detectar.boton.cget("text") == i18n.t("btn_detectar")
        assert app.etiqueta_carpeta.cget("text") == i18n.t("lbl_carpeta")
    finally:
        app.cerrar()


# --- modulos -------------------------------------------------------------
def test_categorias_se_traducen_pero_ordenan_igual():
    from modules import hardware
    i18n.fijar_idioma("en")
    assert hardware.nombre_categoria("Red") == i18n.t("cat_red")
    assert hardware.nombre_categoria("Otro") == i18n.t("cat_otro")
    assert hardware.CATEGORIAS == ("Red", "Video", "Audio", "Chipset", "Otro")
    i18n.fijar_idioma("es")
    assert hardware.nombre_categoria("Red") == i18n.t("cat_red")


def test_installer_mensajes_se_traducen():
    from modules import installer
    i18n.fijar_idioma("en")
    assert installer._texto("inst_ok_texto") == i18n.t("inst_ok_texto")
    assert "administrator" in installer._texto("inst_req_admin").lower()
    i18n.fijar_idioma("es")
    assert installer._texto("inst_req_admin") == "requiere administrador"


def test_un_msu_se_instala_con_wusa(monkeypatch):
    """Los .msu no son ejecutables: se instalan con wusa.exe."""
    from modules import installer
    llamadas = {}

    class Resultado:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(args, **kwargs):
        llamadas["args"] = list(args)
        return Resultado()

    monkeypatch.setattr(installer, "es_admin", lambda: True)
    monkeypatch.setattr(installer.subprocess, "run", fake_run)
    ok, clave, kwargs = installer.instalar_driver_msu("C:\\Drivers\\x.msu")
    assert llamadas["args"][0].lower().endswith("wusa.exe"), llamadas
    assert "C:\\Drivers\\x.msu" in llamadas["args"], llamadas
    assert "/quiet" in llamadas["args"], llamadas
    assert ok is True


def test_un_zip_se_extrae_y_se_instala_con_pnputil(monkeypatch, tmp_path):
    """Un .zip de drivers contiene el .inf: se extrae y se instala con pnputil."""
    import zipfile
    from modules import installer

    zip_path = tmp_path / "driver.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("driver.inf", "[Version]\nSignature=\"$WINDOWS NT$\"\n")
    ruta_zip = str(zip_path)

    llamadas = []

    class Resultado:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(args, **kwargs):
        llamadas.append(list(args))
        return Resultado()

    monkeypatch.setattr(installer, "es_admin", lambda: True)
    monkeypatch.setattr(installer.subprocess, "run", fake_run)
    ok, clave, kwargs = installer.instalar_driver_zip(ruta_zip)
    assert ok is True, (ok, clave, kwargs)
    pnputil = [c for c in llamadas if "pnputil" in c[0].lower()]
    assert pnputil, llamadas
    assert any(c.endswith(".inf") for c in pnputil[0]), pnputil[0]
    assert "/subdirs" in pnputil[0] and "/install" in pnputil[0], pnputil[0]


def test_un_zip_roto_no_rompe(monkeypatch, tmp_path):
    """Un .zip corrupto debe avisar, no reventar la app."""
    from modules import installer
    monkeypatch.setattr(installer, "es_admin", lambda: True)
    roto = tmp_path / "roto.zip"
    roto.write_bytes(b"esto no es un zip")
    ok, clave, kwargs = installer.instalar_driver_zip(str(roto))
    assert ok is False
    assert clave in ("inst_zip_invalido", "inst_sin_inf"), clave


def test_la_app_distingue_cab_msu_y_visual_cpp(monkeypatch):
    """Un .msu no debe tratarse como un Visual C++ (se ejecutaria mal)."""
    from modules import installer
    llamadas = []
    monkeypatch.setattr(installer, "instalar_driver_cab",
                        lambda r: llamadas.append("cab") or (True, "inst_ok_texto", {}))
    monkeypatch.setattr(installer, "instalar_driver_msu",
                        lambda r: llamadas.append("msu") or (True, "inst_ok_texto", {}))
    monkeypatch.setattr(installer, "instalar_redistribuible",
                        lambda r, s=(): llamadas.append("vcpp") or (True, "inst_ok_texto", {}))
    raiz, app = _app(monkeypatch)
    try:
        app._instalar_archivo("C:\\d\\driver.cab", True)
        app._instalar_archivo("C:\\d\\driver.msu", True)
        app._instalar_archivo("C:\\d\\vc_redist.exe", True, ("/q",))
        assert llamadas == ["cab", "msu", "vcpp"], llamadas
    finally:
        app.cerrar()


def test_un_exe_que_no_es_visual_cpp_no_se_ejecuta(monkeypatch):
    """Un .exe de driver no se puede instalar solo: se avisa, no se ejecuta."""
    from modules import installer
    ejecutados = []
    monkeypatch.setattr(installer, "instalar_redistribuible",
                        lambda r, s=(): ejecutados.append(r) or (True, "inst_ok_texto", {}))
    raiz, app = _app(monkeypatch)
    try:
        ok, clave, kwargs = app._instalar_archivo("C:\\d\\driver.exe", True)
        assert ok is False, "no debe instalar un exe que no es de Visual C++"
        assert clave == "inst_no_instalable", clave
        assert not ejecutados, "no debe ejecutarse"
    finally:
        app.cerrar()



def test_installer_devuelve_clave_y_no_texto_pretraducido():
    """El mensaje debe venir como (clave, kwargs) para poder re-traducirse."""
    from modules import installer
    ok, clave, kwargs = installer.instalar_driver_cab("no-existe.cab")
    assert ok is False
    assert clave == "inst_req_admin"
    assert kwargs == {}


# --- errores de pnputil: la salida real del sistema hay que entenderla ----
SALIDA_PNPUTIL_ES = [
    "Utilidad PnP de Microsoft",
    "",
    "Error al agregar el paquete de controladores: El paquete de controladores "
    "especificado falta o no es valido.",
    "",
    "Paquetes de controladores totales:  0",
    "Paquetes de controladores agregados:  0",
]

SALIDA_PNPUTIL_EN = [
    "Microsoft PnP Utility",
    "",
    "Failed to add driver package: The specified driver package is missing or invalid.",
    "",
    "Total driver packages:  0",
    "Added driver packages:  0",
]


def test_se_extrae_la_linea_de_error_real():
    """La ultima linea es un resumen: el error de verdad esta mas arriba."""
    from modules import installer
    assert "falta o no es valido" in installer._linea_error_pnputil(SALIDA_PNPUTIL_ES)
    assert "missing or invalid" in installer._linea_error_pnputil(SALIDA_PNPUTIL_EN)


def test_el_resumen_de_pnputil_no_cuenta_como_error():
    """'Paquetes de controladores agregados: 2' es un resumen, no un error."""
    from modules import installer
    salida = [
        "Utilidad PnP de Microsoft",
        "",
        "Agregando paquete de controladores:  nvdd.inf",
        "El paquete de controladores se agrego correctamente. (ya existe en el sistema)",
        "Nombre publicado:         oem22.inf",
        "",
        "Paquetes de controladores totales:  4",
        "Paquetes de controladores agregados:  0",
    ]
    detalle = installer._linea_error_pnputil(salida)
    assert "agregados" not in detalle, detalle
    assert "totales" not in detalle, detalle
    assert "Nombre publicado" not in detalle, detalle


def test_se_detecta_el_driver_ya_instalado():
    """pnputil dice 'ya existe en el sistema' y aun asi devuelve codigo != 0."""
    from modules import installer
    salida = [
        "Agregando paquete de controladores:  nvdd.inf",
        "El paquete de controladores se agrego correctamente. (ya existe en el sistema)",
        "Paquetes de controladores totales:  4",
        "Paquetes de controladores agregados:  0",
    ]
    assert installer._ya_instalado(salida) is True
    assert installer._ya_instalado(["Error al agregar el paquete: acceso denegado"]) is False


def test_instalar_un_driver_ya_instalado_no_es_error(monkeypatch, tmp_path):
    """Un driver ya presente es un exito, aunque pnputil devuelva codigo 5."""
    from modules import installer
    salida = (
        "Utilidad PnP de Microsoft\r\n"
        "\r\n"
        "Agregando paquete de controladores:  nvdd.inf\r\n"
        "El paquete de controladores se agrego correctamente. (ya existe en el sistema)\r\n"
        "Nombre publicado:         oem22.inf\r\n"
        "\r\n"
        "Paquetes de controladores totales:  4\r\n"
        "Paquetes de controladores agregados:  0\r\n"
    )

    class Resultado:
        def __init__(self, code, salida=""):
            self.returncode = code
            self.stdout = salida
            self.stderr = ""

    def fake_run(args, **kwargs):
        if args[0] == "expand":
            return Resultado(0)          # la extraccion va bien
        return Resultado(5, salida)      # pnputil: ya existe -> codigo 5

    monkeypatch.setattr(installer, "es_admin", lambda: True)
    monkeypatch.setattr(installer.subprocess, "run", fake_run)
    monkeypatch.setattr(installer.os, "walk", lambda d: [(d, [], ["x.inf"])])
    ok, clave, kwargs = installer.instalar_driver_cab(str(tmp_path / "prueba.cab"))
    assert ok is True, "un driver ya instalado no es un fallo"
    assert clave == "inst_ya_existente"



def test_si_no_hay_linea_de_error_se_toma_la_ultima_no_vacia():
    from modules import installer
    assert installer._linea_error_pnputil(["", "algo", ""]) == "algo"


@pytest.mark.parametrize("detalle,clave", [
    ("Acceso denegado.", "inst_error_admin"),
    ("Access is denied.", "inst_error_admin"),
    ("Se requiere privilegios de administrador", "inst_error_admin"),
    ("El paquete de controladores ya esta instalado", "inst_error_ya_existe"),
    ("Driver package already exists", "inst_error_ya_existe"),
    ("No se encontro hardware aplicable", "inst_error_sin_hardware"),
    ("No applicable hardware found", "inst_error_sin_hardware"),
    ("El paquete de controladores especificado falta o no es valido.", "inst_error_invalido"),
    ("The specified driver package is missing or invalid.", "inst_error_invalido"),
    ("algo completamente distinto", "inst_error_otro"),
])
def test_se_clasifica_el_error_de_pnputil(detalle, clave):
    from modules import installer
    assert installer._clasificar_error_pnputil(detalle) == clave


def test_la_clasificacion_ignora_las_tildes():
    """El mensaje real de pnputil en espanol lleva tildes: 'no es válido'."""
    from modules import installer
    real = ("Error al agregar el paquete de controladores: El paquete de "
            "controladores especificado falta o no es válido.")
    assert installer._clasificar_error_pnputil(real) == "inst_error_invalido"
    real_admin = "Error al agregar el paquete: Acceso denegado."
    assert installer._clasificar_error_pnputil(real_admin) == "inst_error_admin"



def test_el_mensaje_de_pnputil_se_traduce():
    """El motivo va traducido y el detalle tecnico se conserva."""
    i18n.fijar_idioma("es")
    msg = i18n.t("inst_pnputil_error",
                 motivo=("inst_error_admin", {}), detalle="Acceso denegado.")
    assert "administrador" in msg.lower()
    assert "Acceso denegado." in msg
    i18n.fijar_idioma("en")
    msg = i18n.t("inst_pnputil_error",
                 motivo=("inst_error_admin", {}), detalle="Access is denied.")
    assert "administrator" in msg.lower()
    assert "Access is denied." in msg


# --- instaladores de Visual C++: cada version tiene su sintaxis ----------
def test_los_instaladores_viejos_no_reciben_switches_de_2010():
    """VC++ 2005 y 2008 NO aceptan /install /quiet: solo /q.

    Con los switches equivocados, el 2005 muestra un dialogo
    'Command line option syntax error'.
    """
    from modules import extras
    por_version = {p["version"]: p for p in extras.listar_visual_cpp()
                   if p["arch"] == "x64"}
    assert por_version["2015-2022"]["switches"] == ("/install", "/quiet", "/norestart")
    assert por_version["2013"]["switches"] == ("/install", "/quiet", "/norestart")
    assert por_version["2008"]["switches"] == ("/q",)
    assert por_version["2005"]["switches"] == ("/q",)


def test_los_nombres_de_archivo_de_los_paquetes_son_unicos():
    """Todos se llamaban vcredist_x64.exe: se sobrescribian entre si."""
    from modules import extras
    paquetes = extras.listar_visual_cpp()
    nombres = [p["archivo"] for p in paquetes]
    assert len(nombres) == len(set(nombres)), nombres
    assert "vcredist_x64.exe" not in nombres


def test_la_descarga_usa_el_nombre_elegido(tmp_path):
    """El downloader debe guardar el archivo con el nombre que se le pasa."""
    from modules import downloader

    class Respuesta:
        headers = {"Content-Length": "4"}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1):
            yield b"dato"

    import modules.downloader as mod
    original = mod.requests.get
    mod.requests.get = lambda url, **kw: Respuesta()
    try:
        ruta = downloader.descargar("http://x/vcredist_x64.exe", str(tmp_path),
                                     nombre="vcredist_2010_x64.exe")
    finally:
        mod.requests.get = original
    assert ruta.endswith("vcredist_2010_x64.exe"), ruta
    assert os.path.exists(ruta)
    # y sin nombre explicito usa el de la URL
    mod.requests.get = lambda url, **kw: Respuesta()
    try:
        ruta2 = downloader.descargar("http://x/otro.cab", str(tmp_path))
    finally:
        mod.requests.get = original
    assert ruta2.endswith("otro.cab"), ruta2


def test_el_log_de_la_ventana_vcpp_acepta_la_forma_que_usa_el_codigo(monkeypatch):
    """La ventana VC++ llama a _log desde un hilo con una tupla: no debe romperse."""
    import gui
    raiz, app = _app(monkeypatch)
    try:
        vc = gui.VentanaVisualCpp(raiz, app.carpeta.get())
        app._ventana_vcpp = vc
        raiz.update()
        # exactamente como lo invoca el hilo de descarga
        vc._log(("vcpp_progreso", gui.COLOR_TEXTO,
                 {"n": 1, "total": 2, "nombre": "X"}))
        raiz.update()
        assert "1/2" in vc.estado.cget("text"), vc.estado.cget("text")
        vc.cerrar()
    finally:
        app.cerrar()




def test_aviso_catalogo_traducido():
    from modules import catalog
    i18n.fijar_idioma("en")
    assert "catalog" in catalog._texto_aviso(3).lower()
    i18n.fijar_idioma("es")
    assert "catalogo" in catalog._texto_aviso(3).lower()


# --- coherencia de las llamadas i18n.t(...) -------------------------------
def _marcadores(plantilla: str) -> set:
    import re
    return set(re.findall(r"\{(\w+)\}", plantilla))


def _ficheros_proyecto() -> list:
    import glob
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return ([os.path.join(raiz, "gui.py")]
            + sorted(glob.glob(os.path.join(raiz, "modules", "*.py"))))


def _marcadores_incorrectos(ficheros) -> list:
    """Llamadas i18n.t/_texto con clave inexistente o marcadores que no cuadran."""
    import ast
    fallos = []
    for ruta in ficheros:
        with open(ruta, "r", encoding="utf-8") as f:
            arbol = ast.parse(f.read(), filename=ruta)
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call) or not isinstance(nodo.func, ast.Attribute):
                continue
            if nodo.func.attr not in ("t", "_texto"):
                continue
            if not nodo.args or not isinstance(nodo.args[0], ast.Constant):
                continue
            clave = nodo.args[0].value
            if clave not in textos.TEXTOS["es"]:
                fallos.append("%s:%d clave inexistente: %r"
                              % (os.path.basename(ruta), nodo.lineno, clave))
                continue
            esperados = _marcadores(textos.TEXTOS["es"][clave])
            pasados = {kw.arg for kw in nodo.keywords if kw.arg}
            if esperados != pasados:
                fallos.append("%s:%d %s -> espera %s, recibe %s"
                              % (os.path.basename(ruta), nodo.lineno, clave,
                                 sorted(esperados), sorted(pasados)))
    return fallos


def test_las_llamadas_i18n_usan_los_marcadores_correctos():
    fallos = _marcadores_incorrectos(_ficheros_proyecto())
    assert not fallos, "llamadas i18n con marcadores incorrectos:\n" + "\n".join(fallos)


def test_la_comprobacion_detecta_una_clave_mal_escrita(tmp_path):
    """La comprobacion debe FALLAR si hay una clave mal escrita."""
    archivo = tmp_path / "malo.py"
    archivo.write_text("from modules import i18n\n"
                       "i18n.t('btn_detectr')\n"
                       "i18n.t('log_guardado', datos='x')\n",
                       encoding="utf-8")
    fallos = _marcadores_incorrectos([str(archivo)])
    assert any("btn_detectr" in f for f in fallos), fallos
    assert any("log_guardado" in f for f in fallos), fallos
