from collections.abc import Callable

from nicegui import ui


AccionSinParametros = Callable[[], None]


def crear_encabezado(
    al_volver_inicio: AccionSinParametros,
    al_reiniciar: AccionSinParametros,
) -> None:
    """Crea el encabezado principal de la partida."""

    with ui.element('header').classes('encabezado-juego'):

        ui.button(
            'Inicio',
            icon='arrow_back',
            on_click=al_volver_inicio,
        ).props(
            'flat no-caps'
        ).classes(
            'boton-pastilla-secundario'
        )

        with ui.column().classes('contenedor-brand'):

            with ui.row().classes('fila-brand'):
                ui.label(
                    'BUSCAMINAS'
                ).classes(
                    'titulo-brand titulo-morado'
                )

                ui.label(
                    'QUÁNTICO'
                ).classes(
                    'titulo-brand titulo-verde'
                )

            ui.label(
                'Explora el campo cuántico y evita minas '
                'mediante compuertas cuánticas.'
            ).classes(
                'subtitulo-brand'
            )

        ui.button(
            icon='restart_alt',
            on_click=al_reiniciar,
        ).props(
            'flat round'
        ).classes(
            'boton-pastilla-secundario boton-reinicio'
        ).tooltip(
            'Reiniciar partida'
        )