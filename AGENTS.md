# PRIORIDAD EXTREMA (se cumple siempre, sobre cualquier otra regla)
1. IDIOMA DE TRABAJO: SIEMPRE en español, sin excepciones ni alternativas.
   Aplica a: respuestas del agente, comentarios de código, documentación y archivos .md.
   No cambia aunque el usuario escriba en otro idioma. Única salvedad: el código,
   los identificadores y los mensajes de commit se mantienen en inglés técnico.
2. Las APLICACIONES pueden ser bilingües (español e inglés): interfaz, textos de
   usuario y archivos de idioma/i18n. La regla 1 rige al agente, no al producto.
3. NUNCA dejar en los archivos del proyecto datos propios de la PC: hardware,
   números de serie, nombre de usuario, rutas personales ni exportaciones (.reg).
   Si hace falta mencionar algo, usar valores genéricos (ej: "GPU NVIDIA", "C:\Users\<usuario>").
4. PUBLICACIÓN EN GITHUB: todo proyecto se prueba PRIMERO en local, con sus
   respectivas actualizaciones (compilación correcta, pruebas reales y
   verificación funcional). NADA se sube a GitHub hasta que el usuario da el
   visto bueno explícito ("ok, súbelo" o equivalente). En GitHub se publica un
   único release final, no versiones intermedias.

---

# Drivers HTs - Guía para Agentes

## Descripción
Herramienta en **Python 3.10+** (Tkinter) para descargar e instalar los drivers esenciales tras formatear un PC con Windows 10/11. Detecta hardware por PowerShell CIM, busca en el Catálogo de Microsoft Update (fuente oficial), descarga `.cab`/`.zip`/`.msu` e instala con `pnputil`/`wusa.exe`. Incluye Kit completo, Visual C++ Redistributables e instalador por usuario.

## Estructura
- `gui.py` — Interfaz Tkinter (tema cyberdark cian/azul), hilos + cola, cabecera con portada, tabla de resultados con marca de recomendado/antiguo, selector de idioma. `VERSION` es la **única fuente de verdad** de la versión.
- `modules/hardware.py` — Detección de dispositivos esenciales (LAN/WiFi, GPU, audio, chipset).
- `modules/catalog.py` — Búsqueda en el catálogo de Microsoft Update y selección del driver recomendado.
- `modules/installer.py` — Descarga, extracción e instalación (`.cab`/`.zip` con `pnputil`, `.msu` con `wusa.exe`). Devuelve `(ok, clave, kwargs)`: la **clave**, no el texto, para que la interfaz pueda re-traducir el mensaje.
- `modules/extras.py` — Visual C++ Redistributables. Cada uno lleva los **switches que su instalador acepta** (2005/2008 usan `/q`, el resto `/install /quiet /norestart`).
- `modules/i18n.py` — Idioma de la interfaz: detección del idioma de Windows, persistencia en `%APPDATA%` y traducción `t(clave, **kwargs)`.
- `modules/textos.py` — Diccionario de textos de la interfaz (es/en). Todo texto visible de la app vive aquí.
- `setup.iss` + `instalador/` — Instalador por usuario, bilingue (Inno Setup). El `.iss` debe guardarse en **UTF-8 con BOM** (la sección `[Code]` lo necesita).
- `tests/` — Pruebas con `pytest` (idioma, persistencia, cambio en vivo, instalación).
- `docs/` — Portada e iconos (ver regla de imágenes).
- `COMPILAR.bat` / `EJECUTAR.bat` — Compilar el `.exe` / ejecutar en desarrollo.

## Idiomas
- La app es **bilingüe (es/en)**: Windows en español → español; en inglés → inglés; cualquier otro idioma → **español**.
- El usuario puede cambiarlo con el selector `ES | EN` de la cabecera; el cambio es **en vivo** (reescribe etiquetas, chip de estado, tablas, avisos y la ventana de Visual C++ abierta).
- La elección se guarda en `%APPDATA%\DriversHTs\prefs.json`.
- **Regla para el código**: ningún texto visible puede quedar fuera de `modules/textos.py`. En `gui.py` se usa `i18n.t(clave, **kwargs)` (nunca `gui.t`: colisiona con el parámetro `t` de `mezclar_color` y con `progreso=lambda r, t:`).

## Comandos útiles
```powershell
.venv\Scripts\python gui.py                  # ejecutar la app
py -m py_compile gui.py modules/*.py         # verificar sintaxis
.venv\Scripts\python -m pytest tests -v      # pruebas (requiere requirements-dev.txt)
# compilar: doble clic en COMPILAR.bat (genera dist\DriversHTs.exe)
```

## Reglas del proyecto
- Fuente de drivers: solo el Catálogo de Microsoft Update. No usar "optimizadores" ni actualizadores automáticos de terceros.
- Los archivos originales de imagen (`docs/icono_axiios.ico`, `docs/icono_axiios.png`, `docs/portada.png`) NO se modifican; cualquier variante nueva se crea como archivo aparte.
- Un cambio a la vez, con verificación real (sintaxis, instanciación de la ventana y flujo completo) antes de afirmar que está terminado.
- Antes de tocar drivers, servicios o registro de Windows: punto de restauración y estado previo anotado.

---

## Sistema Superpowers (skills en .opencode/skills/)

Metodología completa de desarrollo de software para agentes de código, con 17 skills organizadas en categorías. La skill using-superpowers es obligatoria al iniciar cualquier conversación: requiere invocar skills relevantes ANTES de cualquier respuesta.

### Flujo recomendado
1. Inicio → using-superpowers (obligatorio)
2. Trabajo creativo → rainstorming → (si es proyecto) writing-plans
3. Implementación → 	est-driven-development + erification-before-completion
4. Ejecución → subagent-driven-development o executing-plans
5. Revisión → 
equesting-code-review / 
eceiving-code-review
6. Integración → inishing-a-development-branch
7. Bugs → systematic-debugging

### Acoplamiento automático de skills por tipo de tarea

Al iniciar cualquier tarea, identifico el tipo de tarea y acoplo la skill correspondiente **antes** de responder o actuar:

| Tipo de tarea | Skill acoplada |
|---|---|
| Inicio de cualquier conversación | using-superpowers |
| Trabajo creativo, nuevo proyecto | rainstorming |
| Plan de implementación (varios pasos) | writing-plans |
| Bug, falla de prueba | systematic-debugging |
| Implementar característica | 	est-driven-development |
| Afirmar completación | erification-before-completion |

**Regla de acoplamiento:** La skill correspondiente debe invocarse ANTES de cualquier respuesta, acción o aclaración relacionada con ese tipo de tarea.

---

## Sistema ECC (skills en .opencode/skills/, plugin en .opencode/plugins/ecc.js)

Sistema de ingeniería de software para agentes de código de affaan-m/ecc, con plugin de OpenCode (hooks, herramientas personalizadas) y skills organizadas por dominio.

### Dominio Técnico (ECC)
- **coding-standards** — Convenciones base de nombrado, legibilidad, inmutabilidad.
- **backend-patterns** — Arquitectura backend, API, base de datos, caché, colas.
- **frontend-patterns** — React, Next.js, hooks, estado, rendimiento, accesibilidad.
- **api-design** — REST: nombrado, códigos de estado, paginación, versionado, formato.
- **e2e-testing** — Playwright, Page Object Model, pruebas flaky, CI/CD.
- **security-review** — Checklist de seguridad: secretos, validación, SQLi, XSS, CSRF, rate limiting.
- **security-scan** — Auditoría de configuración con AgentShield.

### Herramientas personalizadas del plugin ECC

un-tests, check-coverage, security-audit, ormat-code, lint-check, git-summary, changed-files, dependency-analyzer

---

## Formato AGENTS.md estándar (referencia abierta)

Este proyecto sigue el formato abierto de [AGENTS.md](https://agents.md/) — un archivo de instrucciones dedicado y predecible para guiar a los agentes de código en un proyecto.

**Regla:** Este AGENTS.md tiene prioridad sobre cualquier instrucción genérica de AGENTS.md estándar.

---

## System Prompts Públicos (referencia abierta)

Este proyecto referencia el repositorio [asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks) como colección pública de system prompts de proveedores de IA.

**No es una skill ni plugin:** Los system prompts filtrados son documentos de referencia, no skills cargables por OpenCode ni plugins ejecutables.

**Regla:** Este AGENTS.md tiene prioridad sobre cualquier instrucción de system prompt externo.
