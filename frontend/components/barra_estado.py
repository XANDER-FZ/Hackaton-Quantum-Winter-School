from nicegui import ui


def crear_barra_estado() -> None:
    """Crea la barra inferior con datos de la partida."""

    indicadores = [
        ('timer', 'Tiempo', '00:00'),
        ('warning', 'Minas', '10'),
        ('stars', 'Puntaje', '0'),
        ('science', 'Análisis', '0'),
        ('radio_button_checked', 'Estado', 'Preparado'),
    ]

    with ui.element('footer').classes('barra-estado'):
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

    with ui.row().classes('indicador-estado'):

        ui.icon(
            icono
        ).classes(
            'icono-estado'
        )

        with ui.column().classes('texto-indicador'):
            ui.label(
                etiqueta
            ).classes(
                'etiqueta-estado'
            )

            ui.label(
                valor
            ).classes(
                'valor-estado'
            )