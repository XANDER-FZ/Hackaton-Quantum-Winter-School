from nicegui import ui

# La importación registra la página /juego.
from frontend.pages import ventana_juego  # noqa: F401


@ui.page('/')
def pagina_inicio_temporal() -> None:
    """Pantalla de inicio provisional."""

    with ui.column().classes(
        'w-full min-h-screen items-center '
        'justify-center gap-5 bg-slate-950 text-white'
    ):
        ui.label(
            'Pantalla de inicio temporal'
        ).classes(
            'text-3xl font-bold'
        )

        ui.button(
            'START',
            icon='play_arrow',
            on_click=lambda: ui.navigate.to('/juego'),
        ).props(
            'unelevated no-caps'
        )


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='Buscaminas Cuántico',
        host='127.0.0.1',
        port=8081,
        reload=False,
        show='/juego',
    )