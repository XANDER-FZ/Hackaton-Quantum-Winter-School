from nicegui import ui

from Fronted.pages.ventana_juego import construir_ventana_juego


@ui.page('/')
def pagina_inicio_temporal() -> None:
    """
    Pantalla provisional.

    Posteriormente esta página será reemplazada por
    la pantalla de inicio creada por tu compañera.
    """

    ui.page_title('Buscaminas Cuántico')

    with ui.column().classes(
        'w-full min-h-screen items-center '
        'justify-center gap-5 bg-slate-950 text-white'
    ):
        ui.icon('blur_on').classes(
            'text-7xl text-cyan-400'
        )

        ui.label(
            'Pantalla de inicio temporal'
        ).classes(
            'text-3xl font-bold'
        )

        ui.label(
            'Esta pantalla será reemplazada por '
            'el diseño de tu compañera.'
        ).classes(
            'text-slate-400'
        )

        ui.button(
            'Iniciar partida',
            icon='play_arrow',
            on_click=lambda: ui.navigate.to('/juego'),
        ).props(
            'unelevated no-caps'
        ).classes(
            'bg-cyan-700 px-6 py-2'
        )


@ui.page('/juego')
def pagina_juego() -> None:
    """Registra la segunda pantalla en la ruta /juego."""

    construir_ventana_juego()


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='Buscaminas Cuántico',
        host='127.0.0.1',
        port=8081,
        reload=False,
        show='/juego',
    )