from collections.abc import Callable

from nicegui import ui


ManejadorCompuerta = Callable[[str], None]
AccionSinParametros = Callable[[], None]


def crear_panel_cuantico(
    al_seleccionar_compuerta: ManejadorCompuerta,
    al_ejecutar_analisis: AccionSinParametros,
) -> None:
    """Construye el panel lateral de herramientas cuánticas."""

    with ui.element('aside').classes('panel-cuantico'):

        crear_cabecera_panel()
        crear_panel_compuertas(al_seleccionar_compuerta)
        crear_panel_probabilidad()
        crear_panel_circuito()

        ui.button(
            'EJECUTAR ANÁLISIS',
            icon='play_arrow',
            on_click=al_ejecutar_analisis,
        ).props(
            'unelevated no-caps'
        ).classes(
            'boton-ejecutar'
        )


def crear_cabecera_panel() -> None:
    """Crea el título del panel cuántico."""

    with ui.row().classes('cabecera-panel-cuantico'):

        ui.icon(
            'psychology'
        ).classes(
            'icono-panel-cuantico'
        )

        with ui.column().classes('gap-0'):
            ui.label(
                'Panel cuántico'
            ).classes(
                'titulo-seccion'
            )

            ui.label(
                'Herramientas de exploración'
            ).classes(
                'descripcion-seccion'
            )


def crear_panel_compuertas(
    al_seleccionar_compuerta: ManejadorCompuerta,
) -> None:
    """Crea la lista visual de compuertas disponibles."""

    compuertas = [
        ('H', 'Hadamard'),
        ('X', 'Pauli-X'),
        ('Z', 'Pauli-Z'),
        ('CX', 'CNOT'),
    ]

    with ui.element('div').classes('bloque-panel'):

        crear_titulo_bloque(
            icono='memory',
            titulo='Compuertas',
        )

        ui.label(
            'Herramientas disponibles para analizar las casillas.'
        ).classes(
            'texto-bloque'
        )

        with ui.column().classes('lista-compuertas'):
            for simbolo, nombre in compuertas:
                crear_boton_compuerta(
                    simbolo=simbolo,
                    nombre=nombre,
                    al_seleccionar=al_seleccionar_compuerta,
                )


def crear_boton_compuerta(
    simbolo: str,
    nombre: str,
    al_seleccionar: ManejadorCompuerta,
) -> None:
    """Crea un botón individual de compuerta."""

    ui.button(
        f'{simbolo}  {nombre}',
        on_click=lambda _evento, nombre_compuerta=nombre:
            al_seleccionar(nombre_compuerta),
    ).props(
        'unelevated no-caps'
    ).classes(
        'boton-compuerta'
    )


def crear_panel_probabilidad() -> None:
    """Crea la visualización provisional de probabilidad."""

    with ui.element('div').classes('bloque-panel'):

        crear_titulo_bloque(
            icono='query_stats',
            titulo='Probabilidad',
        )

        ui.label(
            'Riesgo estimado de la casilla seleccionada'
        ).classes(
            'texto-bloque'
        )

        with ui.row().classes('fila-probabilidad'):
            ui.label(
                'Sin analizar'
            ).classes(
                'valor-probabilidad'
            )

            ui.label(
                '-- %'
            ).classes(
                'porcentaje-probabilidad'
            )

        ui.linear_progress(
            value=0,
        ).props(
            'rounded'
        ).classes(
            'barra-probabilidad'
        )


def crear_panel_circuito() -> None:
    """Crea el espacio provisional para el circuito."""

    with ui.element('div').classes('bloque-panel'):

        crear_titulo_bloque(
            icono='account_tree',
            titulo='Circuito',
        )

        with ui.element('div').classes('circuito-provisional'):
            ui.icon(
                'device_hub'
            ).classes(
                'icono-circuito'
            )

            ui.label(
                'Visualización del circuito'
            ).classes(
                'texto-circuito'
            )

            ui.label(
                'Se conectará posteriormente con Qiskit'
            ).classes(
                'detalle-circuito'
            )


def crear_titulo_bloque(
    icono: str,
    titulo: str,
) -> None:
    """Crea el encabezado reutilizable de un bloque."""

    with ui.row().classes('titulo-bloque'):
        ui.icon(
            icono
        ).classes(
            'icono-bloque'
        )

        ui.label(
            titulo
        ).classes(
            'nombre-bloque'
        )