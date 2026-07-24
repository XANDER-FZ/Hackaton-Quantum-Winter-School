from pathlib import Path

from nicegui import app, ui


RUTA_PROYECTO = Path(__file__).resolve().parent

RUTA_PANTALLA_INICIO = (
    RUTA_PROYECTO
    / 'frontend'
    / 'pantalla_inicio'
)


ARCHIVOS_PANTALLA_INICIO = (
    RUTA_PANTALLA_INICIO / 'index.html',
    RUTA_PANTALLA_INICIO / 'styles.css',
    RUTA_PANTALLA_INICIO / 'script.js',
    RUTA_PANTALLA_INICIO / 'start.mp3',
    RUTA_PANTALLA_INICIO / 'secaudio.mp3',
)


def verificar_estructura() -> None:
    """Comprueba los archivos necesarios de la pantalla inicial."""

    if not RUTA_PANTALLA_INICIO.is_dir():
        raise FileNotFoundError(
            'No se encontró la carpeta de la pantalla de inicio:\n'
            f'{RUTA_PANTALLA_INICIO}'
        )

    faltantes = [
        archivo
        for archivo in ARCHIVOS_PANTALLA_INICIO
        if not archivo.is_file()
    ]

    if faltantes:
        lista = '\n'.join(str(archivo) for archivo in faltantes)

        raise FileNotFoundError(
            'Faltan archivos de la pantalla de inicio:\n'
            f'{lista}'
        )


verificar_estructura()


app.add_static_files(
    url_path='/inicio',
    local_directory=str(RUTA_PANTALLA_INICIO),
)


from frontend.pages import ventana_juego  # noqa: E402, F401


@ui.page('/')
def pagina_principal() -> None:
    """Abre la pantalla HTML de inicio."""

    ui.navigate.to('/inicio/index.html')


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='Buscaminas Quaktico',
        host='127.0.0.1',
        port=8081,
        reload=False,
        show=True,
    )