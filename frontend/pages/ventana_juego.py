from pathlib import Path

from nicegui import ui

from frontend.components.barra_estado import crear_barra_estado
from frontend.components.encabezado_juego import crear_encabezado
from frontend.components.panel_cuantico import crear_panel_cuantico
from frontend.components.tablero import crear_tablero


# ============================================================
# RUTA DEL ARCHIVO CSS
# ============================================================

# ventana_juego.py está ubicado en:
#
# frontend/pages/ventana_juego.py
#
# parents[2] permite llegar a:
#
# Hackaton-Quantum/
RUTA_CSS = (
    Path(__file__).resolve().parents[2]
    / 'assets'
    / 'CSS'
    / 'ventana_juego.css'
)


# ============================================================
# EVENTOS GENERALES
# ============================================================

def volver_al_inicio() -> None:
    """Regresa a la pantalla de inicio del juego."""

    ui.navigate.to('/')


def reiniciar_partida() -> None:
    """Acción provisional para reiniciar la partida."""

    ui.notify(
        'La función de reinicio todavía no está conectada.',
        type='info',
    )


def seleccionar_celda(
    fila: int,
    columna: int,
) -> None:
    """Acción provisional al seleccionar una casilla."""

    ui.notify(
        (
            'Celda seleccionada: '
            f'fila {fila + 1}, columna {columna + 1}'
        ),
        type='info',
    )


def seleccionar_compuerta(nombre: str) -> None:
    """Acción provisional al seleccionar una compuerta."""

    ui.notify(
        f'Compuerta seleccionada: {nombre}',
        type='info',
    )


def ejecutar_analisis() -> None:
    """Acción provisional para ejecutar el análisis cuántico."""

    ui.notify(
        'La ejecución cuántica todavía no está conectada.',
        type='info',
    )


# ============================================================
# PÁGINA DEL JUEGO
# ============================================================

@ui.page('/juego')
def pagina_juego() -> None:
    """Construye la pantalla principal de la partida."""

    ui.page_title('Buscaminas Quaktico | Partida')

    # Verificar que el archivo CSS exista.
    if not RUTA_CSS.exists():
        raise FileNotFoundError(
            'No se encontró el archivo CSS de la ventana en:\n'
            f'{RUTA_CSS}'
        )

    # Cargar los estilos de la ventana.
    ui.add_css(
        RUTA_CSS.read_text(encoding='utf-8')
    )

    # --------------------------------------------------------
    # ESTADO LOCAL DEL TABLERO
    # --------------------------------------------------------

    # El estado se crea dentro de la página para evitar
    # compartirlo accidentalmente entre distintos jugadores.
    estado_tablero = {
        'dimension': 3,
    }

    def cambiar_dimension(nueva_dimension: int) -> None:
        """
        Cambia la dimensión del tablero.

        Las dimensiones permitidas son 3, 4 y 5.
        """

        if nueva_dimension not in {3, 4, 5}:
            ui.notify(
                'La dimensión debe ser 3×3, 4×4 o 5×5.',
                type='warning',
            )
            return

        estado_tablero['dimension'] = nueva_dimension

        # Reconstruye solamente la sección del tablero.
        mostrar_tablero.refresh()

    @ui.refreshable
    def mostrar_tablero() -> None:
        """Construye únicamente el componente del tablero."""

        crear_tablero(
            dimension=estado_tablero['dimension'],
            al_seleccionar_celda=seleccionar_celda,
            al_cambiar_dimension=cambiar_dimension,
        )

    # --------------------------------------------------------
    # CONSTRUCCIÓN DE LA VENTANA
    # --------------------------------------------------------

    with ui.column().classes('ventana-juego'):

        crear_encabezado(
            al_volver_inicio=volver_al_inicio,
            al_reiniciar=reiniciar_partida,
        )

        with ui.element('main').classes('contenido-juego'):

            # Sección izquierda: tablero.
            mostrar_tablero()

            # Sección derecha: herramientas cuánticas.
            crear_panel_cuantico(
                al_seleccionar_compuerta=seleccionar_compuerta,
                al_ejecutar_analisis=ejecutar_analisis,
            )

        crear_barra_estado()