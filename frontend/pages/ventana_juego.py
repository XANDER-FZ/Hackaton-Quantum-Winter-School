from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from nicegui import ui

from frontend.components.barra_estado import crear_barra_estado
from frontend.components.encabezado_juego import crear_encabezado
from frontend.components.panel_cuantico import crear_panel_cuantico
from frontend.components.tablero import crear_tablero

from src.core.quantum_engine import (
    InvalidMoveError,
    QuantumMinesweeperEngine,
)


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

FILAS = 3
COLUMNAS = 3
CANTIDAD_MINAS = 3
ALEATORIEDAD = 1.0


# ventana_juego.py está ubicado en:
#
# frontend/pages/ventana_juego.py
#
# parents[2] permite llegar a la raíz del repositorio.
RUTA_CSS = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "CSS"
    / "ventana_juego.css"
)


# ============================================================
# ESTADO LOCAL DE UNA PARTIDA
# ============================================================

@dataclass(slots=True)
class EstadoPartida:
    """
    Estado utilizado por una instancia de la página.

    No se declara una partida global para evitar que dos
    navegadores compartan accidentalmente el mismo tablero.
    """

    juego: QuantumMinesweeperEngine
    compuerta: str | None = None
    casillas: list[int] = field(default_factory=list)
    analisis_realizados: int = 0


def crear_motor() -> QuantumMinesweeperEngine:
    """Crea una nueva partida cuántica."""

    return QuantumMinesweeperEngine(
        rows=FILAS,
        columns=COLUMNAS,
        mine_count=CANTIDAD_MINAS,
        randomness=ALEATORIEDAD,
    )


# ============================================================
# INFORMACIÓN DE COMPUERTAS
# ============================================================

def cantidad_casillas_requeridas(
    compuerta: str,
) -> int:
    """Devuelve cuántas casillas requiere una compuerta."""

    cantidades = {
        "H": 2,
        "X": 2,
        "RX": 1,
        "RY": 1,
        "CNOT": 4,
    }

    codigo = compuerta.strip().upper()

    if codigo not in cantidades:
        raise ValueError(
            f"Compuerta desconocida: {codigo}"
        )

    return cantidades[codigo]


def convertir_coordenada(
    juego: QuantumMinesweeperEngine,
    casilla: int,
) -> str:
    """Convierte un índice en una coordenada como A1 o B3."""

    fila, columna = juego.coordinates(casilla)

    letra_fila = chr(
        ord("A") + fila
    )

    return f"{letra_fila}{columna + 1}"


# ============================================================
# PÁGINA DEL JUEGO
# ============================================================

@ui.page("/juego")
def pagina_juego() -> None:
    """Construye la segunda pantalla del juego."""

    ui.page_title(
        "Buscaminas Quaktico | Partida"
    )

    if not RUTA_CSS.is_file():
        raise FileNotFoundError(
            "No se encontró el archivo CSS de la ventana:\n"
            f"{RUTA_CSS}"
        )

    ui.add_css(
        RUTA_CSS.read_text(
            encoding="utf-8",
        )
    )

    # Cada ejecución de pagina_juego crea su propio estado.
    estado = EstadoPartida(
        juego=crear_motor(),
    )


    # ========================================================
    # FUNCIONES AUXILIARES DEL ESTADO
    # ========================================================

    def obtener_mensaje_tablero() -> str:
        """Genera la instrucción mostrada sobre el tablero."""

        juego = estado.juego

        if juego.game_over:
            if juego.game_won:
                return (
                    "Victoria cuántica. "
                    "Reinicia para jugar nuevamente."
                )

            return (
                "Partida terminada. "
                "Reinicia para intentarlo otra vez."
            )

        if not juego.first_click_done:
            return (
                "Selecciona una casilla. "
                "El primer clic está protegido."
            )

        if juego.power_used_this_turn:
            return (
                "La compuerta fue aplicada. "
                "Selecciona una casilla para medir."
            )

        if estado.compuerta is not None:
            necesarias = cantidad_casillas_requeridas(
                estado.compuerta
            )

            return (
                f"Compuerta {estado.compuerta}: "
                f"{len(estado.casillas)}/{necesarias} "
                "casillas seleccionadas."
            )

        return (
            "Selecciona una compuerta o pulsa "
            "una casilla para medir directamente."
        )


    def obtener_riesgo_seleccionado() -> float | None:
        """
        Devuelve el riesgo de la última casilla seleccionada.

        Si todavía no existe una selección, devuelve None.
        """

        if not estado.casillas:
            return None

        ultima_casilla = estado.casillas[-1]

        return estado.juego.tile_probability(
            ultima_casilla
        )


    # ========================================================
    # NAVEGACIÓN Y REINICIO
    # ========================================================

    def volver_al_inicio() -> None:
        """Regresa a la pantalla HTML inicial."""

        ui.navigate.to("/")


    def reiniciar_partida() -> None:
        """Crea una partida totalmente nueva."""

        estado.juego = crear_motor()
        estado.compuerta = None
        estado.casillas.clear()
        estado.analisis_realizados = 0

        contenido_actualizable.refresh()

        ui.notify(
            "Nueva partida creada.",
            type="positive",
        )


    # ========================================================
    # SELECCIÓN DE COMPUERTA
    # ========================================================

    def seleccionar_compuerta(
        codigo: str,
    ) -> None:
        """Selecciona o deselecciona una compuerta."""

        juego = estado.juego
        codigo_normalizado = codigo.strip().upper()

        try:
            necesarias = cantidad_casillas_requeridas(
                codigo_normalizado
            )

        except ValueError as error:
            ui.notify(
                str(error),
                type="negative",
            )
            return

        if juego.game_over:
            ui.notify(
                "La partida ya terminó.",
                type="warning",
            )
            return

        if not juego.first_click_done:
            ui.notify(
                "Primero debes realizar la medición inicial.",
                type="warning",
            )
            return

        if juego.power_used_this_turn:
            ui.notify(
                "Ya utilizaste una compuerta. "
                "Ahora debes medir una casilla.",
                type="warning",
            )
            return

        # Pulsar nuevamente la misma compuerta cancela
        # la selección actual.
        if estado.compuerta == codigo_normalizado:
            estado.compuerta = None
            estado.casillas.clear()

            contenido_actualizable.refresh()

            ui.notify(
                "Selección de compuerta cancelada.",
                type="info",
            )
            return

        estado.compuerta = codigo_normalizado
        estado.casillas.clear()

        contenido_actualizable.refresh()

        ui.notify(
            (
                f"Compuerta {codigo_normalizado} seleccionada. "
                f"Elige {necesarias} casilla(s)."
            ),
            type="info",
        )


    # ========================================================
    # MEDICIÓN
    # ========================================================

    def medir_casilla(
        casilla: int,
    ) -> None:
        """Mide una casilla y actualiza toda la interfaz."""

        juego = estado.juego

        try:
            resultado = juego.measure_tile(
                casilla
            )

            estado.compuerta = None
            estado.casillas.clear()

            contenido_actualizable.refresh()

            if resultado.is_mine:
                ui.notify(
                    "💥 Encontraste una mina.",
                    type="negative",
                    timeout=5000,
                )
                return

            if juego.game_won:
                ui.notify(
                    "🏆 Victoria cuántica.",
                    type="positive",
                    timeout=5000,
                )
                return

            if resultado.was_first_safe_click:
                ui.notify(
                    (
                        "Primer clic protegido: "
                        "la casilla fue segura."
                    ),
                    type="positive",
                )
                return

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
                timeout=5000,
            )


    # ========================================================
    # CLIC EN UNA CASILLA
    # ========================================================

    def seleccionar_celda(
        fila: int,
        columna: int,
    ) -> None:
        """
        Procesa un clic realizado sobre el tablero.

        Dependiendo del estado:
        - realiza la primera medición;
        - mide directamente;
        - selecciona casillas para una compuerta;
        - mide después de aplicar una compuerta.
        """

        juego = estado.juego

        try:
            casilla = juego.index(
                fila,
                columna,
            )

        except ValueError as error:
            ui.notify(
                str(error),
                type="negative",
            )
            return

        if juego.game_over:
            ui.notify(
                "La partida terminó. Reinicia para jugar.",
                type="warning",
            )
            return

        if casilla in juego.measured_tiles:
            ui.notify(
                "Esa casilla ya fue medida.",
                type="warning",
            )
            return

        # La primera selección se mide automáticamente
        # y el motor garantiza que sea segura.
        if not juego.first_click_done:
            medir_casilla(casilla)
            return

        # Después de utilizar una compuerta, el siguiente
        # clic debe ser una medición.
        if juego.power_used_this_turn:
            medir_casilla(casilla)
            return

        # Sin compuerta seleccionada, una casilla se mide
        # directamente.
        if estado.compuerta is None:
            medir_casilla(casilla)
            return

        necesarias = cantidad_casillas_requeridas(
            estado.compuerta
        )

        # Pulsar una casilla seleccionada la deselecciona.
        if casilla in estado.casillas:
            estado.casillas.remove(casilla)

            contenido_actualizable.refresh()

            ui.notify(
                (
                    "Casilla deseleccionada. "
                    f"{len(estado.casillas)}/{necesarias}"
                ),
                type="info",
            )
            return

        # Evita seleccionar más casillas de las requeridas.
        if len(estado.casillas) >= necesarias:
            ui.notify(
                (
                    f"La compuerta {estado.compuerta} "
                    f"solo requiere {necesarias} casilla(s)."
                ),
                type="warning",
            )
            return

        estado.casillas.append(casilla)

        contenido_actualizable.refresh()

        if len(estado.casillas) == necesarias:
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
                    "Casilla seleccionada. "
                    f"{len(estado.casillas)}/{necesarias}"
                ),
                type="info",
            )


    # ========================================================
    # EJECUTAR COMPUERTA
    # ========================================================

    def ejecutar_analisis() -> None:
        """Aplica la compuerta seleccionada al motor."""

        juego = estado.juego
        compuerta = estado.compuerta

        if compuerta is None:
            ui.notify(
                "Selecciona una compuerta.",
                type="warning",
            )
            return

        if not juego.can_use_power:
            ui.notify(
                "No puedes utilizar una compuerta ahora.",
                type="warning",
            )
            return

        necesarias = cantidad_casillas_requeridas(
            compuerta
        )

        if len(estado.casillas) != necesarias:
            ui.notify(
                (
                    f"La compuerta {compuerta} requiere "
                    f"{necesarias} casilla(s)."
                ),
                type="warning",
            )
            return

        casillas = estado.casillas.copy()

        try:
            mensaje_extra = ""

            if compuerta == "H":
                juego.apply_hadamard(
                    casillas[0],
                    casillas[1],
                )

                mensaje_extra = (
                    "Se aplicó interferencia entre "
                    "las dos casillas."
                )

            elif compuerta == "X":
                juego.apply_x(
                    casillas[0],
                    casillas[1],
                )

                mensaje_extra = (
                    "Se intercambió el riesgo entre "
                    "las dos casillas."
                )

            elif compuerta == "RX":
                resultado = juego.apply_smart_rx(
                    casillas[0]
                )

                pareja = convertir_coordenada(
                    juego,
                    resultado.partner_tile,
                )

                mensaje_extra = (
                    f"Casilla asociada: {pareja}. "
                    f"Ángulo: {resultado.angle_degrees:.1f}°. "
                    f"Riesgo: "
                    f"{resultado.target_before * 100:.1f}% → "
                    f"{resultado.target_after * 100:.1f}%."
                )

            elif compuerta == "RY":
                resultado = juego.apply_smart_ry(
                    casillas[0]
                )

                pareja = convertir_coordenada(
                    juego,
                    resultado.partner_tile,
                )

                mensaje_extra = (
                    f"Casilla asociada: {pareja}. "
                    f"Ángulo: {resultado.angle_degrees:.1f}°. "
                    f"Riesgo: "
                    f"{resultado.target_before * 100:.1f}% → "
                    f"{resultado.target_after * 100:.1f}%."
                )

            elif compuerta == "CNOT":
                juego.apply_cnot(
                    casillas[0],
                    casillas[1],
                    casillas[2],
                    casillas[3],
                )

                mensaje_extra = (
                    "Las dos primeras casillas forman "
                    "el control y las dos últimas el objetivo."
                )

            else:
                raise ValueError(
                    f"Compuerta desconocida: {compuerta}"
                )

            estado.compuerta = None
            estado.casillas.clear()
            estado.analisis_realizados += 1

            contenido_actualizable.refresh()

            ui.notify(
                (
                    f"Compuerta {compuerta} aplicada. "
                    f"{mensaje_extra} "
                    "Ahora selecciona una casilla para medir."
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
    # CONTENIDO ACTUALIZABLE
    # ========================================================

    @ui.refreshable
    def contenido_actualizable() -> None:
        """
        Reconstruye el tablero y el panel cuántico.

        El encabezado no se vuelve a crear en cada interacción.
        """

        juego = estado.juego

        with ui.element("main").classes(
            "contenido-juego"
        ):
            crear_tablero(
                juego=juego,
                casillas_seleccionadas=tuple(
                    estado.casillas
                ),
                mensaje_estado=obtener_mensaje_tablero(),
                al_seleccionar_celda=seleccionar_celda,
            )

            crear_panel_cuantico(
                compuerta_seleccionada=estado.compuerta,
                casillas_seleccionadas=tuple(
                    estado.casillas
                ),
                puede_usar_compuerta=juego.can_use_power,
                esperando_medicion=(
                    juego.power_used_this_turn
                ),
                partida_terminada=juego.game_over,
                riesgo_seleccionado=(
                    obtener_riesgo_seleccionado()
                ),
                al_seleccionar_compuerta=(
                    seleccionar_compuerta
                ),
                al_ejecutar_analisis=(
                    ejecutar_analisis
                ),
            )


    # ========================================================
    # CONSTRUCCIÓN FINAL DE LA PÁGINA
    # ========================================================

    with ui.column().classes(
        "ventana-juego"
    ):
        crear_encabezado(
            al_volver_inicio=volver_al_inicio,
            al_reiniciar=reiniciar_partida,
        )

        contenido_actualizable()