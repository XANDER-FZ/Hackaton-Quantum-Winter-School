from __future__ import annotations

from nicegui import ui


def crear_barra_estado(
    turno: int,
    minas: int,
    riesgo_medio: str,
    casillas_activas: int,
    estado: str,
) -> None:
    """Crea la barra inferior con los datos de la partida."""

    indicadores = [
        (
            "sync",
            "Turno",
            str(turno),
        ),
        (
            "warning",
            "Minas restantes",
            str(minas),
        ),
        (
            "percent",
            "Riesgo medio",
            riesgo_medio,
        ),
        (
            "grid_view",
            "Casillas activas",
            str(casillas_activas),
        ),
        (
            "radio_button_checked",
            "Estado",
            estado,
        ),
    ]

    with ui.element("footer").classes(
        "barra-estado"
    ):
        for icono, etiqueta, valor in indicadores:
            crear_indicador(
                icono=icono,
                etiqueta=etiqueta,
                valor=valor,
            )


def crear_indicador(
    icono: str,
    etiqueta: str,
    valor: str,
) -> None:
    """Crea un indicador individual."""

    with ui.row().classes(
        "indicador-estado"
    ):
        ui.icon(
            icono
        ).classes(
            "icono-estado"
        )

        with ui.column().classes(
            "texto-indicador"
        ):
            ui.label(
                etiqueta
            ).classes(
                "etiqueta-estado"
            )

            ui.label(
                valor
            ).classes(
                "valor-estado"
            )