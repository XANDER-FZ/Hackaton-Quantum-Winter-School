from collections.abc import Callable

from nicegui import ui


ManejadorCelda = Callable[[int, int], None]


def crear_tablero(
    al_seleccionar_celda: ManejadorCelda,
    filas: int = 8,
    columnas: int = 8,
) -> None:
    """Crea el panel visual y la cuadrícula del tablero."""

    with ui.element('section').classes('panel-tablero'):

        crear_cabecera_tablero(
            filas=filas,
            columnas=columnas,
        )

        with ui.element('div').classes('contenedor-tablero'):
            crear_cuadricula(
                filas=filas,
                columnas=columnas,
                al_seleccionar_celda=al_seleccionar_celda,
            )


def crear_cabecera_tablero(
    filas: int,
    columnas: int,
) -> None:
    """Crea el título y la dimensión del tablero."""

    with ui.row().classes('cabecera-panel'):

        with ui.column().classes('gap-0'):
            ui.label(
                'Campo cuántico'
            ).classes(
                'titulo-seccion'
            )

            ui.label(
                'Selecciona una casilla para explorarla'
            ).classes(
                'descripcion-seccion'
            )

        ui.label(
            f'{filas} × {columnas}'
        ).classes(
            'etiqueta-dimension'
        )


def crear_cuadricula(
    filas: int,
    columnas: int,
    al_seleccionar_celda: ManejadorCelda,
) -> None:
    """Crea únicamente las casillas del tablero."""

    with ui.element('div').classes('tablero-demostracion'):

        for fila in range(filas):
            for columna in range(columnas):
                ui.button(
                    '',
                    on_click=lambda _evento, f=fila, c=columna:
                        al_seleccionar_celda(f, c),
                ).props(
                    'unelevated dense'
                ).classes(
                    'celda-demostracion'
                ).tooltip(
                    f'Fila {fila + 1}, columna {columna + 1}'
                )