from pathlib import Path

from nicegui import ui

from frontend.components.barra_estado import crear_barra_estado
from frontend.components.encabezado_juego import crear_encabezado
from frontend.components.panel_cuantico import crear_panel_cuantico
from frontend.components.tablero import crear_tablero


RUTA_CSS = (
    Path(__file__).resolve().parents[2]
    / 'assets'
    / 'CSS'
    / 'ventana_juego.css'
)


def volver_al_inicio() -> None:
    """Navega hacia la pantalla de inicio."""

    ui.navigate.to('/')


def reiniciar_partida() -> None:
    """Acción provisional de reinicio."""

    ui.notify(
        'La función de reinicio todavía no está conectada.',
        type='info',
    )


def seleccionar_celda(
    fila: int,
    columna: int,
) -> None:
    """Acción provisional al pulsar una celda."""

    ui.notify(
        f'Celda seleccionada: '
        f'fila {fila + 1}, columna {columna + 1}',
        type='info',
    )


def seleccionar_compuerta(
    nombre: str,
) -> None:
    """Acción provisional al seleccionar una compuerta."""

    ui.notify(
        f'Compuerta seleccionada: {nombre}',
        type='info',
    )


def ejecutar_analisis() -> None:
    """Acción provisional del análisis cuántico."""

    ui.notify(
        'La ejecución cuántica todavía no está conectada.',
        type='info',
    )


@ui.page('/juego')
def pagina_juego() -> None:
    """Construye y registra la pantalla de la partida."""

    ui.page_title('Buscaminas Cuántico | Partida')

    if not RUTA_CSS.exists():
        raise FileNotFoundError(
            f'No se encontró el CSS en: {RUTA_CSS}'
        )

    ui.add_css(
        RUTA_CSS.read_text(encoding='utf-8')
    )

    with ui.column().classes('ventana-juego'):

        crear_encabezado(
            al_volver_inicio=volver_al_inicio,
            al_reiniciar=reiniciar_partida,
        )

        with ui.element('main').classes('contenido-juego'):

            crear_tablero(
                filas=8,
                columnas=8,
                al_seleccionar_celda=seleccionar_celda,
            )

            crear_panel_cuantico(
                al_seleccionar_compuerta=seleccionar_compuerta,
                al_ejecutar_analisis=ejecutar_analisis,
            )

        crear_barra_estado()