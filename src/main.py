from __future__ import annotations

import re
import shlex
from math import radians
from typing import Any

import numpy as np

from quantum_engine import (
    InvalidMoveError,
    QuantumMinesweeperEngine,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

ROWS = 3
COLUMNS = 3
MINE_COUNT = 3

# None crea una partida diferente cada vez.
# Usa un número como 42 para repetir el mismo tablero.
SEED: int | None = None

RANDOMNESS = 1.0


HELP_TEXT = """
============================================================
QUANTUM MINESWEEPER — COMANDOS
============================================================

MEDIR
  M <casilla>
  MEASURE <casilla>

  Ejemplo:
      M B2

  La primera medición siempre es segura.
  Medir termina el turno.

PUERTAS DE UNA CASILLA
  Z <casilla>
  S <casilla>

  Ejemplos:
      Z A1
      S C3

PUERTAS LÓGICAS DE DOS CASILLAS
  X <casilla A> <casilla B>
  H <casilla A> <casilla B>

  Ejemplos:
      X A1 A2
      H B1 B2

ROTACIONES INTELIGENTES
  RX <casilla objetivo>
  RY <casilla objetivo>

  Ejemplos:
      RX A2
      RY C1

  El motor elige automáticamente:
      - una casilla partner;
      - el mejor ángulo;
      - una redistribución visible del riesgo.

ROTACIÓN RZ
  RZ <casilla A> <casilla B> [ángulo]

  Ejemplos:
      RZ A1 A2
      RZ A1 A2 180

  Si no escribes un ángulo, se utilizan 90 grados.

CNOT LÓGICO
  CNOT <control A> <control B> <target A> <target B>

  Ejemplo:
      CNOT A1 A2 C1 C2

TABLERO
  B
  BOARD
      Mostrar el tablero.

  STATUS
      Mostrar el estado del turno.

  HISTORY
      Mostrar el historial de operaciones.

CONTROL
  RESET
      Reiniciar el mismo tablero.

  NEW
      Crear un tablero aleatorio nuevo.

  HELP
      Mostrar esta ayuda.

  QUIT
      Salir del juego.

REGLAS
  - La primera medición siempre es segura.
  - Solo puedes usar un poder por turno.
  - Después de usar un poder, debes medir una casilla.
  - El número total de minas permanece constante.
============================================================
"""


# ============================================================
# CREACIÓN DEL JUEGO
# ============================================================

def create_game(*, seed: int | None = SEED,) -> QuantumMinesweeperEngine:
    """Crea una nueva instancia del juego."""

    try:
        return QuantumMinesweeperEngine(rows=ROWS, columns=COLUMNS, mine_count=MINE_COUNT, seed=seed, randomness=RANDOMNESS,)

    except TypeError:
        # Compatibilidad si eliminaste randomness del constructor.
        return QuantumMinesweeperEngine(rows=ROWS, columns=COLUMNS, mine_count=MINE_COUNT, seed=seed,)


# ============================================================
# COORDENADAS
# ============================================================

def coordinate_to_tile(game: QuantumMinesweeperEngine, coordinate: str,) -> int:
    """Convierte A1, B2, C3, etc. en un índice."""

    cleaned = coordinate.strip().upper()

    match = re.fullmatch(r"([A-Z])(\d+)", cleaned,)

    if match is None:
        raise ValueError(f"Coordenada inválida: {coordinate!r}. " 
                         "Usa A1, B2, C3, etc.")

    row = ord(match.group(1)) - ord("A")
    column = int(match.group(2)) - 1

    if not 0 <= row < game.rows:
        last_row = chr(
            ord("A") + game.rows - 1
        )

        raise ValueError(f"La fila debe estar entre A y {last_row}.")

    if not 0 <= column < game.columns:
        raise ValueError(f"La columna debe estar entre 1 y {game.columns}.")

    return game.index(row, column,)


def tile_to_coordinate(game: QuantumMinesweeperEngine, tile: int,) -> str:
    """Convierte un índice en A1, B2, C3, etc."""

    row, column = game.coordinates(tile)

    row_letter = chr(ord("A") + row)

    return f"{row_letter}{column + 1}"

# ============================================================
# VISUALIZACIÓN
# ============================================================

def print_board(game: QuantumMinesweeperEngine,) -> None:
    """Muestra el tablero y sus probabilidades."""

    probabilities = game.probabilities()
    measured = game.measured_tiles
    cell_width = 12
    print()
    header = " " * 5
    for column in range(game.columns):
        header += f"{column + 1:^{cell_width}}"
    print(header)
    print(" " * 4 + "-" * (cell_width * game.columns))

    for row in range(game.rows): 
        row_letter = chr(
            ord("A") + row
        )

        line = f" {row_letter} |"

        for column in range(game.columns):
            tile = game.index(row, column,)

            if tile in measured:
                if measured[tile]:
                    text = "MINE"
                else:
                    text = "SAFE"

            else:
                text = (f"{100 * probabilities[tile]:.1f}%")

            line += f"{text:^{cell_width}}"

        print(line)

    print()

    print("Expected mines:", f"{game.expected_mines():.10f}",)
    print("Remaining mines:", game.remaining_mines,)
    print("Active layouts:", game.active_layouts,)

def print_status(game: QuantumMinesweeperEngine,) -> None:
    """Muestra el estado actual del turno."""

    print()
    print("STATUS")
    print("-" * 48)

    print("Turn:",game.turn,)

    print(
        "First click completed:",
        game.first_click_done,
    )

    print(
        "Power used this turn:",
        game.power_used_this_turn,
    )

    print(
        "Game over:",
        game.game_over,
    )

    print(
        "Game won:",
        game.game_won,
    )

    if game.game_over:
        print(
            "Next action: RESET, NEW, or QUIT."
        )

    elif not game.first_click_done:
        print(
            "Next action: measure a tile. "
            "The first click is protected."
        )

    elif game.power_used_this_turn:
        print(
            "Next action: measure a tile "
            "to finish the turn."
        )

    else:
        print(
            "Next action: use one power "
            "or measure directly."
        )


def print_history(
    game: QuantumMinesweeperEngine,
) -> None:
    """Muestra las operaciones realizadas."""

    print()
    print("HISTORY")
    print("-" * 48)

    if not game.history:
        print("No operations yet.")
        return

    for operation in game.history:
        print(operation)


def print_probability_changes(
    game: QuantumMinesweeperEngine,
    before: np.ndarray,
    after: np.ndarray,
) -> None:
    """Muestra las casillas cuya probabilidad cambió."""

    print()
    print("PROBABILITY CHANGES")
    print("-" * 64)

    found_change = False

    for tile in range(game.tile_count):
        change = float(
            after[tile] - before[tile]
        )

        if abs(change) <= 1e-10:
            continue

        found_change = True

        coordinate = tile_to_coordinate(
            game,
            tile,
        )

        print(
            f"{coordinate}: "
            f"{100 * before[tile]:6.2f}% -> "
            f"{100 * after[tile]:6.2f}% "
            f"({100 * change:+6.2f} points)"
        )

    if not found_change:
        print(
            "No visible probability changed. "
            "The gate may have changed phases "
            "or correlations."
        )

    print(
        "Probability sum:",
        f"{game.expected_mines():.10f}",
    )


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def require_arguments(
    arguments: list[str],
    allowed_counts: tuple[int, ...],
    usage: str,
) -> None:
    """Comprueba la cantidad de argumentos."""

    if len(arguments) not in allowed_counts:
        raise ValueError(
            f"Uso correcto: {usage}"
        )


def call_first_available(
    game: QuantumMinesweeperEngine,
    method_names: tuple[str, ...],
    *arguments: Any,
) -> Any:
    """Ejecuta el primer método disponible.

    Permite que main.py funcione con nombres antiguos y nuevos
    del quantum engine.
    """

    for method_name in method_names:
        method = getattr(
            game,
            method_name,
            None,
        )

        if callable(method):
            return method(*arguments)

    raise AttributeError(
        "Falta un método en quantum_engine.py. "
        "Se esperaba alguno de estos: "
        + ", ".join(method_names)
    )


# ============================================================
# MEDICIÓN
# ============================================================

def handle_measurement(
    game: QuantumMinesweeperEngine,
    arguments: list[str],
) -> None:
    """Procesa el comando M."""

    require_arguments(
        arguments,
        allowed_counts=(1,),
        usage="M <casilla>",
    )

    tile = coordinate_to_tile(
        game,
        arguments[0],
    )

    coordinate = tile_to_coordinate(
        game,
        tile,
    )

    before = game.probabilities()

    result = game.measure_tile(tile)

    after = game.probabilities()

    print()
    print("=" * 56)

    if result.was_first_safe_click:
        print(
            f"{coordinate}: SAFE "
            "— protected first click"
        )

    elif result.is_mine:
        print(
            f"{coordinate}: MINE"
        )

    else:
        print(
            f"{coordinate}: SAFE"
        )

    print(
        "Probability before measurement:",
        f"{100 * result.probability_before:.2f}%",
    )

    print("=" * 56)

    print_probability_changes(
        game,
        before,
        after,
    )

    print_board(game)

    if result.is_mine:
        print()
        print("GAME OVER — a mine was measured.")

    elif game.game_won:
        print()
        print("VICTORY — all safe tiles were revealed.")


# ============================================================
# Z Y S
# ============================================================

def handle_phase_gate(
    game: QuantumMinesweeperEngine,
    command: str,
    arguments: list[str],
) -> None:
    """Procesa Z y S."""

    require_arguments(
        arguments,
        allowed_counts=(1,),
        usage=f"{command} <casilla>",
    )

    tile = coordinate_to_tile(
        game,
        arguments[0],
    )

    before = game.probabilities()

    if command == "Z":
        call_first_available(
            game,
            ("apply_z",),
            tile,
        )

    elif command == "S":
        call_first_available(
            game,
            ("apply_s",),
            tile,
        )

    else:
        raise ValueError(
            f"Puerta desconocida: {command}"
        )

    after = game.probabilities()

    print(
        f"\nApplied {command} to "
        f"{tile_to_coordinate(game, tile)}."
    )

    print_probability_changes(
        game,
        before,
        after,
    )


# ============================================================
# X Y HADAMARD
# ============================================================

def handle_pair_gate(
    game: QuantumMinesweeperEngine,
    command: str,
    arguments: list[str],
) -> None:
    """Procesa X y H."""

    require_arguments(
        arguments,
        allowed_counts=(2,),
        usage=f"{command} <casilla A> <casilla B>",
    )

    tile_a = coordinate_to_tile(
        game,
        arguments[0],
    )

    tile_b = coordinate_to_tile(
        game,
        arguments[1],
    )

    if tile_a == tile_b:
        raise ValueError(
            "Debes seleccionar dos casillas diferentes."
        )

    before = game.probabilities()

    if command == "X":
        call_first_available(
            game,
            (
                "apply_x",
                "apply_x_pair",
                "apply_risk_swap",
            ),
            tile_a,
            tile_b,
        )

    elif command == "H":
        call_first_available(
            game,
            (
                "apply_hadamard",
                "apply_h_pair",
                "apply_pair_hadamard",
            ),
            tile_a,
            tile_b,
        )

    else:
        raise ValueError(
            f"Puerta desconocida: {command}"
        )

    after = game.probabilities()

    coordinate_a = tile_to_coordinate(
        game,
        tile_a,
    )

    coordinate_b = tile_to_coordinate(
        game,
        tile_b,
    )

    print(
        f"\nApplied {command} to "
        f"({coordinate_a}, {coordinate_b})."
    )

    print_probability_changes(
        game,
        before,
        after,
    )


# ============================================================
# RX Y RY INTELIGENTES
# ============================================================

def handle_smart_rotation(
    game: QuantumMinesweeperEngine,
    command: str,
    arguments: list[str],
) -> None:
    """Procesa RX y RY con partner y ángulo automáticos."""

    require_arguments(
        arguments,
        allowed_counts=(1,),
        usage=f"{command} <casilla objetivo>",
    )

    target_tile = coordinate_to_tile(
        game,
        arguments[0],
    )

    before = game.probabilities()

    if command == "RX":
        result = call_first_available(
            game,
            ("apply_smart_rx",),
            target_tile,
        )

    elif command == "RY":
        result = call_first_available(
            game,
            ("apply_smart_ry",),
            target_tile,
        )

    else:
        raise ValueError(
            f"Rotación desconocida: {command}"
        )

    after = game.probabilities()

    target_coordinate = tile_to_coordinate(
        game,
        result.target_tile,
    )

    partner_coordinate = tile_to_coordinate(
        game,
        result.partner_tile,
    )

    print()
    print(
        f"{result.gate} SMART ROTATION"
    )
    print("-" * 56)

    print(
        "Target:",
        target_coordinate,
    )

    print(
        "Entangled partner:",
        partner_coordinate,
    )

    print(
        "Selected angle:",
        f"{result.angle_degrees:.1f}°",
    )

    print(
        "Target risk:",
        f"{100 * result.target_before:.2f}% "
        f"-> {100 * result.target_after:.2f}%",
    )

    print(
        "Partner risk:",
        f"{100 * result.partner_before:.2f}% "
        f"-> {100 * result.partner_after:.2f}%",
    )

    if result.reduced_target:
        reduction = (
            result.target_before
            - result.target_after
        )

        print(
            "Target reduction:",
            f"{100 * reduction:.2f} points",
        )

    else:
        print(
            "The target could not be reduced. "
            "The strongest visible redistribution "
            "was used instead."
        )

    print(
        "Selection mode:",
        result.selection_mode,
    )

    print_probability_changes(
        game,
        before,
        after,
    )


# ============================================================
# RZ
# ============================================================

def handle_rz(
    game: QuantumMinesweeperEngine,
    arguments: list[str],
) -> None:
    """Procesa RZ sobre un par lógico."""

    require_arguments(
        arguments,
        allowed_counts=(2, 3),
        usage=(
            "RZ <casilla A> "
            "<casilla B> [ángulo]"
        ),
    )

    tile_a = coordinate_to_tile(
        game,
        arguments[0],
    )

    tile_b = coordinate_to_tile(
        game,
        arguments[1],
    )

    if tile_a == tile_b:
        raise ValueError(
            "Debes seleccionar dos casillas diferentes."
        )

    angle_degrees = 90.0

    if len(arguments) == 3:
        try:
            angle_degrees = float(
                arguments[2]
            )

        except ValueError as error:
            raise ValueError(
                "El ángulo debe ser numérico."
            ) from error

    angle_radians = radians(
        angle_degrees
    )

    before = game.probabilities()

    call_first_available(
        game,
        (
            "apply_rz",
            "apply_rz_pair",
        ),
        tile_a,
        tile_b,
        angle_radians,
    )

    after = game.probabilities()

    coordinate_a = tile_to_coordinate(
        game,
        tile_a,
    )

    coordinate_b = tile_to_coordinate(
        game,
        tile_b,
    )

    print(
        f"\nApplied RZ({angle_degrees:.1f}°) "
        f"to ({coordinate_a}, {coordinate_b})."
    )

    print_probability_changes(
        game,
        before,
        after,
    )


# ============================================================
# CNOT
# ============================================================

def handle_cnot(
    game: QuantumMinesweeperEngine,
    arguments: list[str],
) -> None:
    """Procesa CNOT lógico."""

    require_arguments(
        arguments,
        allowed_counts=(4,),
        usage=(
            "CNOT <control A> <control B> "
            "<target A> <target B>"
        ),
    )

    tiles = [
        coordinate_to_tile(
            game,
            coordinate,
        )
        for coordinate in arguments
    ]

    if len(set(tiles)) != 4:
        raise ValueError(
            "CNOT necesita cuatro casillas diferentes."
        )

    (
        control_a,
        control_b,
        target_a,
        target_b,
    ) = tiles

    before = game.probabilities()

    call_first_available(
        game,
        ("apply_cnot",),
        control_a,
        control_b,
        target_a,
        target_b,
    )

    after = game.probabilities()

    print()
    print("Applied logical CNOT")

    print(
        "Control:",
        tile_to_coordinate(
            game,
            control_a,
        ),
        tile_to_coordinate(
            game,
            control_b,
        ),
    )

    print(
        "Target:",
        tile_to_coordinate(
            game,
            target_a,
        ),
        tile_to_coordinate(
            game,
            target_b,
        ),
    )

    print_probability_changes(
        game,
        before,
        after,
    )


# ============================================================
# BUCLE PRINCIPAL
# ============================================================

def main() -> None:
    game = create_game()

    print()
    print("=" * 64)
    print("QUANTUM MINESWEEPER — TERMINAL")
    print("=" * 64)

    print(
        "La primera acción debe ser una medición."
    )

    print(
        "Ejemplo: M B2"
    )

    print(
        "Escribe HELP para ver los comandos."
    )

    print_board(game)
    print_status(game)

    while True:
        try:
            raw_command = input(
                "\nquantum-minesweeper> "
            ).strip()

        except (
            EOFError,
            KeyboardInterrupt,
        ):
            print()
            print("Closing game.")
            break

        if not raw_command:
            continue

        try:
            parts = shlex.split(
                raw_command
            )

        except ValueError as error:
            print()
            print(
                f"Command parsing error: {error}"
            )
            continue

        command = parts[0].upper()
        arguments = parts[1:]

        try:
            # ----------------------------------------------------
            # CONTROL
            # ----------------------------------------------------

            if command in {
                "QUIT",
                "EXIT",
                "Q",
            }:
                print("Closing game.")
                break

            if command in {
                "HELP",
                "?",
            }:
                print(HELP_TEXT)
                continue

            if command in {
                "BOARD",
                "B",
                "SHOW",
            }:
                print_board(game)
                continue

            if command == "STATUS":
                print_status(game)
                continue

            if command == "HISTORY":
                print_history(game)
                continue

            if command == "RESET":
                game.reset(
                    new_random_board=False
                )

                print()
                print(
                    "The same quantum board was reset."
                )

                print_board(game)
                print_status(game)
                continue

            if command == "NEW":
                game = create_game(
                    seed=None
                )

                print()
                print(
                    "A new random quantum board "
                    "was created."
                )

                print_board(game)
                print_status(game)
                continue

            # ----------------------------------------------------
            # MEDICIÓN
            # ----------------------------------------------------

            if command in {
                "M",
                "MEASURE",
                "CLICK",
            }:
                handle_measurement(
                    game,
                    arguments,
                )
                continue

            # ----------------------------------------------------
            # PUERTAS
            # ----------------------------------------------------

            if command in {
                "Z",
                "S",
            }:
                handle_phase_gate(
                    game,
                    command,
                    arguments,
                )

            elif command in {
                "X",
                "H",
            }:
                handle_pair_gate(
                    game,
                    command,
                    arguments,
                )

            elif command in {
                "RX",
                "RY",
            }:
                handle_smart_rotation(
                    game,
                    command,
                    arguments,
                )

            elif command == "RZ":
                handle_rz(
                    game,
                    arguments,
                )

            elif command in {
                "CNOT",
                "CX",
            }:
                handle_cnot(
                    game,
                    arguments,
                )

            else:
                print()
                print(
                    f"Unknown command: {command!r}. "
                    "Type HELP to see the commands."
                )
                continue

            print_board(game)
            print_status(game)

        except (
            InvalidMoveError,
            ValueError,
            AttributeError,
        ) as error:
            print()
            print(
                f"Invalid action: {error}"
            )


if __name__ == "__main__":
    main()
