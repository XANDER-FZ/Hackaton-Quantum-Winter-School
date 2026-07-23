from collections.abc import Callable

from nicegui import ui


ManejadorCelda = Callable[[int, int], None]
ManejadorDimension = Callable[[int], None]


def crear_tablero(
    al_seleccionar_celda: ManejadorCelda,
    al_cambiar_dimension: ManejadorDimension,
    dimension: int = 3,
) -> None:
    """Crea el panel visual y la cuadrícula del tablero."""

    with ui.element('section').classes('panel-tablero'):

        crear_cabecera_tablero(
            dimension=dimension,
            al_cambiar_dimension=al_cambiar_dimension,
        )

        with ui.element('div').classes('contenedor-tablero'):
            crear_cuadricula(
                filas=dimension,
                columnas=dimension,
                al_seleccionar_celda=al_seleccionar_celda,
            )


def crear_cabecera_tablero(
    dimension: int,
    al_cambiar_dimension: ManejadorDimension,
) -> None:
    """Crea el título y el selector de dimensión."""

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

        ui.select(
            options={
                3: '3 × 3',
                4: '4 × 4',
                5: '5 × 5',
            },
            value=dimension,
            on_change=lambda evento:
                al_cambiar_dimension(int(evento.value)),
        ).props(
            'outlined dense'
        ).classes(
            'selector-dimension'
        )


def crear_cuadricula(
    filas: int,
    columnas: int,
    al_seleccionar_celda: ManejadorCelda,
) -> None:
    """Crea únicamente las casillas del tablero."""

    with ui.element('div').classes(
    'tablero-demostracion'
    ).style(
        f'grid-template-columns: repeat({columnas}, minmax(0, 1fr));'
    ):

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