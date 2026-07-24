from nicegui import ui


def crear_barra_estado(
    *,
    turno: int,
    minas_restantes: int,
    estados_activos: int,
    analisis_realizados: int,
    puede_usar_compuerta: bool,
    esperando_medicion: bool,
    partida_terminada: bool,
    partida_ganada: bool,
) -> None:
    """
    Crea la barra inferior con información real de la partida.

    Este componente solo muestra datos. No modifica directamente
    el motor cuántico.
    """

    estado_texto, estado_icono = obtener_estado_partida(
        puede_usar_compuerta=puede_usar_compuerta,
        esperando_medicion=esperando_medicion,
        partida_terminada=partida_terminada,
        partida_ganada=partida_ganada,
    )

    with ui.element("footer").classes("barra-estado"):

        crear_indicador_estado(
            icono="schedule",
            etiqueta="Turno",
            valor=str(turno),
        )

        crear_indicador_estado(
            icono="warning",
            etiqueta="Minas restantes",
            valor=str(minas_restantes),
        )

        crear_indicador_estado(
            icono="hub",
            etiqueta="Estados activos",
            valor=str(estados_activos),
        )

        crear_indicador_estado(
            icono="analytics",
            etiqueta="Análisis realizados",
            valor=str(analisis_realizados),
        )

        crear_indicador_estado(
            icono=estado_icono,
            etiqueta="Estado",
            valor=estado_texto,
        )


def crear_indicador_estado(
    *,
    icono: str,
    etiqueta: str,
    valor: str,
) -> None:
    """Crea un indicador individual de la barra inferior."""

    with ui.row().classes("indicador-estado"):

        ui.icon(
            icono
        ).classes(
            "icono-estado"
        )

        with ui.column().classes("texto-indicador"):

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


def obtener_estado_partida(
    *,
    puede_usar_compuerta: bool,
    esperando_medicion: bool,
    partida_terminada: bool,
    partida_ganada: bool,
) -> tuple[str, str]:
    """
    Determina el mensaje y el icono correspondientes al estado
    actual de la partida.
    """

    if partida_terminada:
        if partida_ganada:
            return (
                "Victoria",
                "emoji_events",
            )

        return (
            "Mina encontrada",
            "dangerous",
        )

    if esperando_medicion:
        return (
            "Medición pendiente",
            "center_focus_strong",
        )

    if puede_usar_compuerta:
        return (
            "Compuerta disponible",
            "bolt",
        )

    return (
        "Inicio protegido",
        "shield",
    )