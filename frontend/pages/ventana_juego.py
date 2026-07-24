from __future__ import annotations

from pathlib import Path

from nicegui import ui

from src.core.quantum_engine import (
    InvalidMoveError,
    QuantumMinesweeperEngine,
)

from frontend.components.barra_estado import (
    crear_barra_estado,
)
from frontend.components.encabezado_juego import (
    crear_encabezado,
)
from frontend.components.panel_cuantico import (
    crear_panel_cuantico,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

RUTA_CSS = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "CSS"
    / "ventana_juego.css"
)


DIMENSIONES = {
    3: "3 × 3",
    4: "4 × 4",
    5: "5 × 5",
}


MINAS_POR_DIMENSION = {
    3: 3,
    4: 3,
    5: 3,
}


RANDOMNESS = 1.0


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def crear_juego(
    dimension: int,
) -> QuantumMinesweeperEngine:
    """Crea una partida con la dimensión indicada."""

    if dimension not in DIMENSIONES:
        raise ValueError(
            f"Dimensión no permitida: {dimension}"
        )

    return QuantumMinesweeperEngine(
        rows=dimension,
        columns=dimension,
        mine_count=MINAS_POR_DIMENSION[dimension],
        randomness=RANDOMNESS,
    )


def convertir_nombre_compuerta(
    nombre: str,
) -> str:
    """Convierte el nombre visual al usado por el motor."""

    equivalencias = {
        "Hadamard": "H",
        "Pauli-X": "X",
        "Rotación-X": "RX",
        "Rotación-Y": "RY",
        "CNOT": "CNOT",
    }

    return equivalencias.get(
        nombre,
        nombre.upper(),
    )


def cantidad_casillas(
    compuerta: str,
) -> int:
    """Devuelve la cantidad de casillas de una compuerta."""

    if compuerta in {
        "H",
        "X",
    }:
        return 2

    if compuerta in {
        "RX",
        "RY",
    }:
        return 1

    if compuerta == "CNOT":
        return 4

    raise ValueError(
        f"Compuerta desconocida: {compuerta}"
    )


# ============================================================
# PÁGINA DEL JUEGO
# ============================================================

@ui.page("/juego")
def pagina_juego() -> None:
    """Construye la pantalla completa de la partida."""

    ui.page_title(
        "Buscaminas Cuántico | Partida"
    )

    if not RUTA_CSS.exists():
        raise FileNotFoundError(
            "No se encontró el CSS del juego en: "
            f"{RUTA_CSS}"
        )

    ui.add_css(
        RUTA_CSS.read_text(
            encoding="utf-8"
        )
    )

    # El estado queda asociado a esta página/navegador.
    dimension_actual = 3

    juego = crear_juego(
        dimension_actual
    )

    compuerta_seleccionada: str | None = None
    casillas_seleccionadas: list[int] = []

    # ========================================================
    # ESTADO Y NAVEGACIÓN
    # ========================================================

    def limpiar_seleccion() -> None:
        """Limpia la operación y las casillas elegidas."""

        nonlocal compuerta_seleccionada
        nonlocal casillas_seleccionadas

        compuerta_seleccionada = None
        casillas_seleccionadas = []

    def volver_al_inicio() -> None:
        """Regresa a la pantalla inicial original."""

        ui.navigate.to("/")

    def reiniciar_partida() -> None:
        """Reinicia manteniendo el tamaño actual."""

        nonlocal juego

        juego = crear_juego(
            dimension_actual
        )

        limpiar_seleccion()
        contenido_actualizable.refresh()

        ui.notify(
            (
                "Nueva partida "
                f"{dimension_actual} × "
                f"{dimension_actual} creada."
            ),
            type="positive",
        )

    def cambiar_dimension(
        evento,
    ) -> None:
        """Crea una nueva partida con otra dimensión."""

        nonlocal dimension_actual
        nonlocal juego

        try:
            nueva_dimension = int(
                evento.value
            )

        except (
            TypeError,
            ValueError,
        ):
            ui.notify(
                "La dimensión seleccionada no es válida.",
                type="negative",
            )
            return

        if nueva_dimension not in DIMENSIONES:
            ui.notify(
                (
                    "Solo están disponibles "
                    "3×3, 4×4 y 5×5."
                ),
                type="warning",
            )
            return

        if nueva_dimension == dimension_actual:
            return

        dimension_actual = nueva_dimension

        juego = crear_juego(
            dimension_actual
        )

        limpiar_seleccion()
        contenido_actualizable.refresh()

        ui.notify(
            (
                "Nuevo tablero de "
                f"{dimension_actual} × "
                f"{dimension_actual}."
            ),
            type="positive",
        )

    # ========================================================
    # COMPUERTAS
    # ========================================================

    def seleccionar_compuerta(
        nombre: str,
    ) -> None:
        """Selecciona una compuerta cuántica."""

        nonlocal compuerta_seleccionada
        nonlocal casillas_seleccionadas

        if juego.game_over:
            ui.notify(
                "La partida ya terminó.",
                type="warning",
            )
            return

        if not juego.first_click_done:
            ui.notify(
                (
                    "Primero selecciona una casilla. "
                    "El primer clic es seguro."
                ),
                type="warning",
            )
            return

        if juego.power_used_this_turn:
            ui.notify(
                (
                    "Ya utilizaste una compuerta. "
                    "Ahora debes medir una casilla."
                ),
                type="warning",
            )
            return

        try:
            nueva_compuerta = (
                convertir_nombre_compuerta(
                    nombre
                )
            )

            necesarias = cantidad_casillas(
                nueva_compuerta
            )

        except ValueError as error:
            ui.notify(
                str(error),
                type="negative",
            )
            return

        compuerta_seleccionada = nueva_compuerta
        casillas_seleccionadas = []

        contenido_actualizable.refresh()

        ui.notify(
            (
                f"{compuerta_seleccionada}: "
                f"selecciona {necesarias} "
                "casilla(s)."
            ),
            type="info",
        )

    # ========================================================
    # MEDICIÓN
    # ========================================================

    def medir_casilla(
        tile: int,
    ) -> None:
        """Mide una casilla del tablero."""

        try:
            resultado = juego.measure_tile(
                tile
            )

            limpiar_seleccion()
            contenido_actualizable.refresh()

            if resultado.is_mine:
                ui.notify(
                    "💥 Encontraste una mina.",
                    type="negative",
                    timeout=5000,
                )

            elif juego.game_won:
                ui.notify(
                    "🏆 Victoria cuántica.",
                    type="positive",
                    timeout=5000,
                )

            elif resultado.was_first_safe_click:
                ui.notify(
                    (
                        "Primer clic protegido: "
                        "casilla segura."
                    ),
                    type="positive",
                )

            else:
                ui.notify(
                    "Casilla segura.",
                    type="positive",
                )

        except (
            InvalidMoveError,
            ValueError,
        ) as error:
            ui.notify(
                str(error),
                type="negative",
            )

    # ========================================================
    # CLIC SOBRE EL TABLERO
    # ========================================================

    def seleccionar_celda(
        fila: int,
        columna: int,
    ) -> None:
        """Procesa la selección de una casilla."""

        nonlocal casillas_seleccionadas

        try:
            tile = juego.index(
                fila,
                columna,
            )

        except (
            IndexError,
            InvalidMoveError,
            ValueError,
        ) as error:
            ui.notify(
                str(error),
                type="negative",
            )
            return

        if juego.game_over:
            ui.notify(
                (
                    "La partida terminó. "
                    "Reinicia para continuar."
                ),
                type="warning",
            )
            return

        if tile in juego.measured_tiles:
            ui.notify(
                "Esa casilla ya fue medida.",
                type="warning",
            )
            return

        # El primer clic se mide automáticamente.
        if not juego.first_click_done:
            medir_casilla(
                tile
            )
            return

        # Después de aplicar una compuerta,
        # el siguiente clic realiza la medición.
        if juego.power_used_this_turn:
            medir_casilla(
                tile
            )
            return

        # Sin compuerta, el clic mide directamente.
        if compuerta_seleccionada is None:
            medir_casilla(
                tile
            )
            return

        necesarias = cantidad_casillas(
            compuerta_seleccionada
        )

        # Permite deseleccionar una casilla.
        if tile in casillas_seleccionadas:
            casillas_seleccionadas.remove(
                tile
            )

        else:
            if len(casillas_seleccionadas) >= necesarias:
                ui.notify(
                    (
                        f"La compuerta "
                        f"{compuerta_seleccionada} "
                        f"solo necesita {necesarias} "
                        "casilla(s)."
                    ),
                    type="warning",
                )
                return

            casillas_seleccionadas.append(
                tile
            )

        contenido_actualizable.refresh()

        if len(casillas_seleccionadas) == necesarias:
            ui.notify(
                (
                    "Selección completa. "
                    "Pulsa EJECUTAR ANÁLISIS."
                ),
                type="positive",
            )

        else:
            ui.notify(
                (
                    "Casillas seleccionadas: "
                    f"{len(casillas_seleccionadas)}"
                    f"/{necesarias}"
                ),
                type="info",
            )

    # ========================================================
    # EJECUCIÓN DE COMPUERTAS
    # ========================================================

    def tile_a_coordenada(
        tile: int,
    ) -> str:
        """Convierte un índice a una coordenada como A1."""

        fila, columna = juego.coordinates(
            tile
        )

        letra = chr(
            ord("A") + fila
        )

        return f"{letra}{columna + 1}"

    def ejecutar_analisis() -> None:
        """Ejecuta la compuerta seleccionada."""

        if juego.game_over:
            ui.notify(
                "La partida ya terminó.",
                type="warning",
            )
            return

        if juego.power_used_this_turn:
            ui.notify(
                (
                    "Ya utilizaste una compuerta. "
                    "Ahora debes medir."
                ),
                type="warning",
            )
            return

        if compuerta_seleccionada is None:
            ui.notify(
                "Selecciona una compuerta.",
                type="warning",
            )
            return

        necesarias = cantidad_casillas(
            compuerta_seleccionada
        )

        if len(casillas_seleccionadas) != necesarias:
            ui.notify(
                (
                    f"Selecciona {necesarias} "
                    "casilla(s)."
                ),
                type="warning",
            )
            return

        try:
            gate = compuerta_seleccionada
            tiles = casillas_seleccionadas.copy()

            mensaje_extra = ""

            if gate == "H":
                juego.apply_hadamard(
                    tiles[0],
                    tiles[1],
                )

                mensaje_extra = (
                    "Interferencia aplicada entre "
                    "las dos casillas."
                )

            elif gate == "X":
                juego.apply_x(
                    tiles[0],
                    tiles[1],
                )

                mensaje_extra = (
                    "El riesgo fue intercambiado "
                    "entre las dos casillas."
                )

            elif gate == "RX":
                resultado = juego.apply_smart_rx(
                    tiles[0]
                )

                mensaje_extra = (
                    "Partner automático: "
                    f"{tile_a_coordenada(resultado.partner_tile)}. "
                    "Ángulo: "
                    f"{resultado.angle_degrees:.1f}°. "
                    "Riesgo: "
                    f"{100 * resultado.target_before:.1f}% → "
                    f"{100 * resultado.target_after:.1f}%."
                )

            elif gate == "RY":
                resultado = juego.apply_smart_ry(
                    tiles[0]
                )

                mensaje_extra = (
                    "Partner automático: "
                    f"{tile_a_coordenada(resultado.partner_tile)}. "
                    "Ángulo: "
                    f"{resultado.angle_degrees:.1f}°. "
                    "Riesgo: "
                    f"{100 * resultado.target_before:.1f}% → "
                    f"{100 * resultado.target_after:.1f}%."
                )

            elif gate == "CNOT":
                juego.apply_cnot(
                    tiles[0],
                    tiles[1],
                    tiles[2],
                    tiles[3],
                )

                mensaje_extra = (
                    "Los dos primeros qubits forman "
                    "el control y los dos últimos "
                    "forman el objetivo."
                )

            else:
                raise ValueError(
                    f"Compuerta desconocida: {gate}"
                )

            limpiar_seleccion()
            contenido_actualizable.refresh()

            ui.notify(
                (
                    f"Compuerta {gate} aplicada. "
                    f"{mensaje_extra} "
                    "Ahora selecciona una casilla "
                    "para medir."
                ),
                type="positive",
                timeout=6000,
            )

        except (
            InvalidMoveError,
            ValueError,
            AttributeError,
        ) as error:
            ui.notify(
                str(error),
                type="negative",
                timeout=5000,
            )

    # ========================================================
    # INFORMACIÓN VISUAL
    # ========================================================

    def obtener_mensaje_tablero() -> str:
        """Devuelve la instrucción actual."""

        if juego.game_won:
            return (
                "Ganaste la partida. "
                "Reinicia para jugar nuevamente."
            )

        if juego.game_over:
            return (
                "Partida terminada. "
                "Reinicia para continuar."
            )

        if not juego.first_click_done:
            return (
                "Selecciona una casilla. "
                "El primer clic es seguro."
            )

        if juego.power_used_this_turn:
            return (
                "Selecciona una casilla para medir."
            )

        if compuerta_seleccionada is not None:
            necesarias = cantidad_casillas(
                compuerta_seleccionada
            )

            return (
                f"{compuerta_seleccionada}: "
                f"{len(casillas_seleccionadas)}"
                f"/{necesarias} seleccionadas."
            )

        return (
            "Selecciona una compuerta "
            "o mide directamente."
        )

    def obtener_estado_partida() -> str:
        """Devuelve un estado corto para la barra."""

        if juego.game_won:
            return "Victoria"

        if juego.game_over:
            return "Derrota"

        if not juego.first_click_done:
            return "Preparado"

        if juego.power_used_this_turn:
            return "Medición"

        if compuerta_seleccionada is not None:
            return "Configurando"

        return "En curso"

    def obtener_probabilidad_seleccionada() -> float | None:
        """Obtiene el riesgo de la última casilla seleccionada."""

        if not casillas_seleccionadas:
            return None

        probabilidades = juego.probabilities()

        ultima_casilla = casillas_seleccionadas[-1]

        return float(
            probabilidades[ultima_casilla]
        )

    def obtener_detalle_operacion() -> str | None:
        """Describe la selección de la compuerta actual."""

        if compuerta_seleccionada is None:
            return None

        necesarias = cantidad_casillas(
            compuerta_seleccionada
        )

        return (
            f"{len(casillas_seleccionadas)}"
            f"/{necesarias} casillas seleccionadas"
        )

    # ========================================================
    # TABLERO
    # ========================================================

    def crear_tablero_real() -> None:
        """Construye el tablero usando el motor cuántico."""

        probabilidades = juego.probabilities()
        medidas = juego.measured_tiles

        with ui.element("section").classes(
            "panel-tablero"
        ):
            with ui.row().classes(
                "cabecera-panel"
            ):
                with ui.column().classes(
                    "gap-0"
                ):
                    ui.label(
                        "Campo cuántico"
                    ).classes(
                        "titulo-seccion"
                    )

                    ui.label(
                        obtener_mensaje_tablero()
                    ).classes(
                        "descripcion-seccion"
                    )

                ui.select(
                    options=DIMENSIONES,
                    value=dimension_actual,
                    on_change=cambiar_dimension,
                ).props(
                    "outlined dense"
                ).classes(
                    "selector-dimension"
                )

            with ui.element("div").classes(
                "contenedor-tablero"
            ):
                with ui.element("div").classes(
                    "tablero-demostracion"
                ).style(
                    (
                        "grid-template-columns: "
                        f"repeat({dimension_actual}, "
                        "minmax(0, 1fr));"
                    )
                ):
                    for fila in range(
                        dimension_actual
                    ):
                        for columna in range(
                            dimension_actual
                        ):
                            tile = juego.index(
                                fila,
                                columna,
                            )

                            if tile in medidas:
                                texto = (
                                    "💥"
                                    if medidas[tile]
                                    else "✓"
                                )

                            else:
                                texto = (
                                    f"{100 * probabilidades[tile]:.0f}%"
                                )

                            clases = (
                                "celda-demostracion"
                            )

                            if tile in casillas_seleccionadas:
                                clases += (
                                    " celda-seleccionada"
                                )

                            boton = ui.button(
                                texto,
                                on_click=(
                                    lambda _evento,
                                    f=fila,
                                    c=columna:
                                    seleccionar_celda(
                                        f,
                                        c,
                                    )
                                ),
                            ).props(
                                "unelevated dense"
                            ).classes(
                                clases
                            ).tooltip(
                                (
                                    f"Fila {fila + 1}, "
                                    f"columna {columna + 1}"
                                )
                            )

                            if tile in medidas:
                                boton.disable()

    # ========================================================
    # CONTENIDO ACTUALIZABLE
    # ========================================================

    @ui.refreshable
    def contenido_actualizable() -> None:
        """Reconstruye el contenido que cambia."""

        total_casillas = (
            dimension_actual
            * dimension_actual
        )

        casillas_activas = (
            total_casillas
            - len(juego.measured_tiles)
        )

        if casillas_activas > 0:
            riesgo_medio_valor = (
                juego.expected_mines()
                / casillas_activas
            )

            riesgo_medio = (
                f"{100 * riesgo_medio_valor:.1f}%"
            )

        else:
            riesgo_medio = "0.0%"

        with ui.element("main").classes(
            "contenido-juego"
        ):
            with ui.column().classes(
                "columna-tablero"
            ):
                crear_tablero_real()

                crear_barra_estado(
                    turno=juego.turn,
                    minas=juego.remaining_mines,
                    riesgo_medio=riesgo_medio,
                    casillas_activas=casillas_activas,
                    estado=obtener_estado_partida(),
                )

            crear_panel_cuantico(
                al_seleccionar_compuerta=(
                    seleccionar_compuerta
                ),
                al_ejecutar_analisis=(
                    ejecutar_analisis
                ),
                probabilidad=(
                    obtener_probabilidad_seleccionada()
                ),
                operacion=compuerta_seleccionada,
                detalle_operacion=(
                    obtener_detalle_operacion()
                ),
            )

    # ========================================================
    # ESTRUCTURA DE LA PÁGINA
    # ========================================================

    with ui.column().classes(
        "ventana-juego"
    ):
        crear_encabezado(
            al_volver_inicio=volver_al_inicio,
            al_reiniciar=reiniciar_partida,
        )

        contenido_actualizable()