from __future__ import annotations

from collections.abc import Callable

from nicegui import ui


ManejadorCompuerta = Callable[[str], None]
AccionSinParametros = Callable[[], None]


def crear_panel_cuantico(
    al_seleccionar_compuerta: ManejadorCompuerta,
    al_ejecutar_analisis: AccionSinParametros,
    probabilidad: float | None = None,
    operacion: str | None = None,
    detalle_operacion: str | None = None,
) -> None:
    """Construye el panel lateral de herramientas cuánticas."""

    with ui.element("aside").classes(
        "panel-cuantico"
    ):
        crear_cabecera_panel()

        crear_panel_compuertas(
            al_seleccionar_compuerta
        )

        crear_panel_probabilidad(
            probabilidad
        )

        crear_panel_operacion(
            operacion=operacion,
            detalle=detalle_operacion,
        )

        ui.button(
            "EJECUTAR ANÁLISIS",
            icon="play_arrow",
            on_click=al_ejecutar_analisis,
        ).props(
            "unelevated no-caps"
        ).classes(
            "boton-ejecutar"
        )


def crear_cabecera_panel() -> None:
    """Crea el título del panel cuántico."""

    with ui.row().classes(
        "cabecera-panel-cuantico"
    ):
        ui.icon(
            "psychology"
        ).classes(
            "icono-panel-cuantico"
        )

        with ui.column().classes(
            "gap-0"
        ):
            ui.label(
                "Panel cuántico"
            ).classes(
                "titulo-seccion"
            )

            ui.label(
                "Herramientas de exploración"
            ).classes(
                "descripcion-seccion"
            )


def crear_panel_compuertas(
    al_seleccionar_compuerta: ManejadorCompuerta,
) -> None:
    """Crea la lista visual de compuertas."""

    compuertas = [
        (
            "H",
            "Hadamard",
        ),
        (
            "X",
            "Pauli-X",
        ),
        (
            "RX",
            "Rotación-X",
        ),
        (
            "RY",
            "Rotación-Y",
        ),
        (
            "CX",
            "CNOT",
        ),
    ]

    with ui.element("div").classes(
        "bloque-panel"
    ):
        crear_titulo_bloque(
            icono="memory",
            titulo="Compuertas",
        )

        ui.label(
            "Selecciona una compuerta y luego "
            "las casillas necesarias."
        ).classes(
            "texto-bloque"
        )

        with ui.column().classes(
            "lista-compuertas"
        ):
            for simbolo, nombre in compuertas:
                crear_boton_compuerta(
                    simbolo=simbolo,
                    nombre=nombre,
                    al_seleccionar=(
                        al_seleccionar_compuerta
                    ),
                )


def crear_boton_compuerta(
    simbolo: str,
    nombre: str,
    al_seleccionar: ManejadorCompuerta,
) -> None:
    """Crea un botón individual de compuerta."""

    ui.button(
        f"{simbolo}  {nombre}",
        on_click=(
            lambda _evento,
            nombre_compuerta=nombre:
            al_seleccionar(
                nombre_compuerta
            )
        ),
    ).props(
        "unelevated no-caps"
    ).classes(
        "boton-compuerta"
    )


def crear_panel_probabilidad(
    probabilidad: float | None,
) -> None:
    """Muestra la probabilidad de la última casilla seleccionada."""

    if probabilidad is None:
        descripcion = "Sin casilla seleccionada"
        porcentaje = "-- %"
        progreso = 0.0

    else:
        progreso = max(
            0.0,
            min(
                1.0,
                float(probabilidad),
            ),
        )

        descripcion = "Casilla seleccionada"
        porcentaje = f"{100 * progreso:.0f}%"

    with ui.element("div").classes(
        "bloque-panel"
    ):
        crear_titulo_bloque(
            icono="query_stats",
            titulo="Probabilidad",
        )

        ui.label(
            "Probabilidad actual de que la casilla "
            "seleccionada contenga una mina."
        ).classes(
            "texto-bloque"
        )

        with ui.row().classes(
            "fila-probabilidad"
        ):
            ui.label(
                descripcion
            ).classes(
                "valor-probabilidad"
            )

            ui.label(
                porcentaje
            ).classes(
                "porcentaje-probabilidad"
            )

        ui.linear_progress(
            value=progreso,
        ).props(
            "rounded"
        ).classes(
            "barra-probabilidad"
        )


def crear_panel_operacion(
    operacion: str | None,
    detalle: str | None,
) -> None:
    """Muestra la compuerta y la selección actual."""

    nombre_operacion = (
        operacion
        if operacion is not None
        else "Sin operación"
    )

    texto_detalle = (
        detalle
        if detalle is not None
        else (
            "Selecciona una compuerta "
            "para preparar el análisis."
        )
    )

    with ui.element("div").classes(
        "bloque-panel"
    ):
        crear_titulo_bloque(
            icono="account_tree",
            titulo="Operación",
        )

        with ui.element("div").classes(
            "operacion-vacia"
        ):
            ui.icon(
                "device_hub"
            ).classes(
                "icono-operacion"
            )

            ui.label(
                nombre_operacion
            ).classes(
                "texto-operacion"
            )

            ui.label(
                texto_detalle
            ).classes(
                "detalle-operacion"
            )


def crear_titulo_bloque(
    icono: str,
    titulo: str,
) -> None:
    """Crea el encabezado reutilizable de un bloque."""

    with ui.row().classes(
        "titulo-bloque"
    ):
        ui.icon(
            icono
        ).classes(
            "icono-bloque"
        )

        ui.label(
            titulo
        ).classes(
            "nombre-bloque"
        )