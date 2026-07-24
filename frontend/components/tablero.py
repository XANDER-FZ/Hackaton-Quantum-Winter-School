from collections.abc import Callable, Collection

from nicegui import ui

from src.core.quantum_engine import QuantumMinesweeperEngine


# Función que recibe:
# - fila
# - columna
ManejadorCelda = Callable[[int, int], None]


def crear_tablero(
    *,
    juego: QuantumMinesweeperEngine,
    casillas_seleccionadas: Collection[int],
    mensaje_estado: str,
    al_seleccionar_celda: ManejadorCelda,
) -> None:
    """
    Construye el tablero visual a partir del estado del motor.

    Este componente solamente muestra información y comunica
    qué casilla fue pulsada. No aplica compuertas ni realiza
    mediciones directamente.
    """

    probabilidades = juego.probabilities()
    casillas_medidas = juego.measured_tiles

    with ui.element("section").classes("panel-tablero"):

        crear_cabecera_tablero(
            juego=juego,
            mensaje_estado=mensaje_estado,
        )

        with ui.element("div").classes("contenedor-tablero"):
            crear_cuadricula(
                juego=juego,
                probabilidades=probabilidades,
                casillas_medidas=casillas_medidas,
                casillas_seleccionadas=casillas_seleccionadas,
                al_seleccionar_celda=al_seleccionar_celda,
            )

        crear_resumen_tablero(juego)


def crear_cabecera_tablero(
    *,
    juego: QuantumMinesweeperEngine,
    mensaje_estado: str,
) -> None:
    """Muestra el título, las instrucciones y la dimensión."""

    with ui.row().classes("cabecera-panel"):

        with ui.column().classes("gap-0"):
            ui.label(
                "Campo cuántico"
            ).classes(
                "titulo-seccion"
            )

            ui.label(
                mensaje_estado
            ).classes(
                "descripcion-seccion"
            )

        ui.label(
            f"{juego.rows} × {juego.columns}"
        ).classes(
            "etiqueta-dimension"
        )


def crear_cuadricula(
    *,
    juego: QuantumMinesweeperEngine,
    probabilidades,
    casillas_medidas: dict[int, bool],
    casillas_seleccionadas: Collection[int],
    al_seleccionar_celda: ManejadorCelda,
) -> None:
    """Construye las celdas del tablero."""

    with ui.element("div").classes(
        "tablero-demostracion"
    ).style(
        (
            "grid-template-columns: "
            f"repeat({juego.columns}, minmax(0, 1fr));"
        )
    ):

        for fila in range(juego.rows):
            for columna in range(juego.columns):

                indice = juego.index(
                    fila,
                    columna,
                )

                probabilidad = float(
                    probabilidades[indice]
                )

                texto, clases_adicionales = obtener_apariencia_celda(
                    indice=indice,
                    probabilidad=probabilidad,
                    casillas_medidas=casillas_medidas,
                    casillas_seleccionadas=casillas_seleccionadas,
                )

                clases = (
                    "celda-demostracion "
                    f"{clases_adicionales}"
                ).strip()

                boton = ui.button(
                    texto,
                    on_click=lambda _evento, f=fila, c=columna:
                        al_seleccionar_celda(f, c),
                ).props(
                    "unelevated dense no-caps"
                ).classes(
                    clases
                ).tooltip(
                    crear_tooltip_celda(
                        fila=fila,
                        columna=columna,
                        indice=indice,
                        probabilidad=probabilidad,
                        casillas_medidas=casillas_medidas,
                    )
                )

                # Una casilla medida no puede volver a pulsarse.
                # Cuando termina la partida, se bloquea el tablero.
                if (
                    indice in casillas_medidas
                    or juego.game_over
                ):
                    boton.disable()


def obtener_apariencia_celda(
    *,
    indice: int,
    probabilidad: float,
    casillas_medidas: dict[int, bool],
    casillas_seleccionadas: Collection[int],
) -> tuple[str, str]:
    """
    Devuelve el texto y las clases CSS de una celda.

    Una celda puede estar:
    - oculta;
    - seleccionada;
    - medida como segura;
    - medida como mina.
    """

    if indice in casillas_medidas:
        es_mina = casillas_medidas[indice]

        if es_mina:
            return (
                "💥",
                "celda-medida celda-mina",
            )

        return (
            "✓",
            "celda-medida celda-segura",
        )

    clases = "celda-oculta"

    if indice in casillas_seleccionadas:
        clases += " celda-seleccionada"

    return (
        f"{probabilidad * 100:.0f}%",
        clases,
    )


def crear_tooltip_celda(
    *,
    fila: int,
    columna: int,
    indice: int,
    probabilidad: float,
    casillas_medidas: dict[int, bool],
) -> str:
    """Genera el texto emergente de cada casilla."""

    coordenada = (
        f"Fila {fila + 1}, "
        f"columna {columna + 1}"
    )

    if indice in casillas_medidas:
        resultado = (
            "mina"
            if casillas_medidas[indice]
            else "segura"
        )

        return (
            f"{coordenada} — "
            f"Casilla medida: {resultado}"
        )

    return (
        f"{coordenada} — "
        f"Riesgo estimado: {probabilidad * 100:.1f}%"
    )


def crear_resumen_tablero(
    juego: QuantumMinesweeperEngine,
) -> None:
    """Muestra información básica debajo del tablero."""

    with ui.row().classes("resumen-tablero"):

        crear_dato_tablero(
            etiqueta="Turno",
            valor=str(juego.turn),
        )

        crear_dato_tablero(
            etiqueta="Minas restantes",
            valor=str(juego.remaining_mines),
        )

        crear_dato_tablero(
            etiqueta="Minas esperadas",
            valor=f"{juego.expected_mines():.2f}",
        )

        crear_dato_tablero(
            etiqueta="Estados activos",
            valor=str(juego.active_layouts),
        )


def crear_dato_tablero(
    *,
    etiqueta: str,
    valor: str,
) -> None:
    """Crea uno de los datos del resumen inferior."""

    with ui.column().classes("dato-tablero"):
        ui.label(
            etiqueta
        ).classes(
            "etiqueta-dato-tablero"
        )

        ui.label(
            valor
        ).classes(
            "valor-dato-tablero"
        )