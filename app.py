from __future__ import annotations

from pathlib import Path

from fastapi.responses import HTMLResponse
from nicegui import app, ui


# ============================================================
# RUTAS
# ============================================================

RUTA_PROYECTO = Path(__file__).resolve().parent

RUTA_PANTALLA_INICIO = (
    RUTA_PROYECTO
    / "frontend"
    / "pantalla_inicio"
)

RUTA_INDEX = (
    RUTA_PANTALLA_INICIO
    / "index.html"
)


# ============================================================
# COMPROBACIÓN DE ARCHIVOS
# ============================================================

if not RUTA_INDEX.exists():
    raise FileNotFoundError(
        "No se encontró la pantalla inicial en: "
        f"{RUTA_INDEX}"
    )


# Permite cargar styles.css, script.js y los audios
# desde frontend/pantalla_inicio.
app.add_static_files(
    "/pantalla_inicio",
    str(RUTA_PANTALLA_INICIO),
)


# Importar esta página registra la ruta /juego.
from frontend.pages import ventana_juego  # noqa: E402, F401


# ============================================================
# PANTALLA INICIAL ORIGINAL
# ============================================================

@app.get("/")
def pagina_inicio() -> HTMLResponse:
    """Devuelve el index.html original de la pantalla inicial."""

    contenido_html = RUTA_INDEX.read_text(
        encoding="utf-8"
    )

    # Hace que referencias como styles.css, script.js
    # y start.mp3 se busquen dentro de pantalla_inicio.
    if "<base " not in contenido_html.lower():

        posicion_head = contenido_html.lower().find(
            "<head"
        )

        if posicion_head != -1:
            final_head = contenido_html.find(
                ">",
                posicion_head,
            )

            if final_head != -1:
                contenido_html = (
                    contenido_html[:final_head + 1]
                    + '\n<base href="/pantalla_inicio/">'
                    + contenido_html[final_head + 1:]
                )

    return HTMLResponse(
        content=contenido_html
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ in {
    "__main__",
    "__mp_main__",
}:
    ui.run(
        title="Quantum Minesweeper",
        host="127.0.0.1",
        port=8081,
        reload=False,
        show="/",

        storage_secret=(
            "quantum-minesweeper-hackathon"
        ),
    )