from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import cos, pi, sin, sqrt

import numpy as np
from numpy.typing import NDArray


ComplexVector = NDArray[np.complex128]
ComplexMatrix = NDArray[np.complex128]


class QuantumEngineError(Exception):
    """Error base del motor cuántico."""


class InvalidBoardError(QuantumEngineError, ValueError):
    """Configuración inválida del tablero."""


class InvalidMoveError(QuantumEngineError, RuntimeError):
    """Movimiento no permitido durante la partida."""


@dataclass(frozen=True, slots=True)
class MeasurementResult:
    """Información producida al medir una casilla."""

    tile: int
    is_mine: bool
    probability_before: float
    was_first_safe_click: bool
    turn_finished: int


@dataclass(frozen=True, slots=True)
class BoardSnapshot:
    """Estado del tablero preparado para conectarlo con la interfaz."""

    probabilities: tuple[float, ...]
    measured_tiles: dict[int, bool]

    exact_mine_count: int
    remaining_mines: int

    turn: int
    power_used_this_turn: bool
    first_click_done: bool

    active_layouts: int
    game_won: bool
    game_over: bool


class QuantumMinesweeperEngine:
    """Motor principal de Quantum Minesweeper.

    Parameters
    ----------
    rows:
        Número de filas.

    columns:
        Número de columnas.

    mine_count:
        Número exacto de minas del tablero.

    seed:
        Semilla opcional para reproducir una partida.

    randomness:
        Controla cuánto varían las probabilidades iniciales.

        0.0:
            Todas las casillas empiezan prácticamente iguales.

        1.0:
            Existe mayor diferencia entre las probabilidades iniciales.

    Game rules
    ----------
    - El primer clic siempre es seguro.
    - Antes del primer clic no se puede usar ningún poder.
    - Después del primer clic se puede usar como máximo un poder por turno.
    - El turno termina cuando se mide una casilla.
    - Medir una casilla colapsa el estado global.
    - Una mina medida termina la partida.
    """

    ATOL = 1e-12

    def __init__(
        self,
        rows: int = 3,
        columns: int = 3,
        mine_count: int = 3,
        *,
        seed: int | None = None,
        randomness: float = 0.75,
    ) -> None:

        if not isinstance(rows, int) or rows <= 0:
            raise InvalidBoardError(
                "rows debe ser un entero positivo."
            )

        if not isinstance(columns, int) or columns <= 0:
            raise InvalidBoardError(
                "columns debe ser un entero positivo."
            )

        self.rows = rows
        self.columns = columns
        self.tile_count = rows * columns

        if not isinstance(mine_count, int):
            raise InvalidBoardError(
                "mine_count debe ser un entero."
            )

        if not 0 <= mine_count < self.tile_count:
            raise InvalidBoardError(
                "mine_count debe ser menor que el número de casillas. "
                "Debe existir al menos una casilla segura."
            )

        if not 0.0 <= randomness <= 1.0:
            raise InvalidBoardError(
                "randomness debe estar entre 0 y 1."
            )

        self.mine_count = mine_count
        self.randomness = float(randomness)

        self._rng = np.random.default_rng(seed)

        # Configuraciones posibles con exactamente mine_count minas.
        self._basis_masks = self._create_fixed_mine_basis()

        self._index_by_mask = {
            mask: index
            for index, mask in enumerate(self._basis_masks)
        }

        # Estado cuántico global.
        self._state = self._create_random_state()
        self._initial_state = self._state.copy()

        # Estado de la partida.
        self._measured_tiles: dict[int, bool] = {}
        self._history: list[str] = []

        self.turn = 0
        self.power_used_this_turn = False
        self.first_click_done = False
        self.game_over = False

    # ================================================================
    # CREACIÓN DEL ESTADO CUÁNTICO
    # ================================================================

    def _create_fixed_mine_basis(self) -> tuple[int, ...]:
        """Genera todas las distribuciones con exactamente N minas."""

        masks: list[int] = []

        for mine_positions in combinations(
            range(self.tile_count),
            self.mine_count,
        ):
            mask = 0

            for tile in mine_positions:
                mask |= 1 << tile

            masks.append(mask)

        return tuple(masks)

    def _create_random_state(self) -> ComplexVector:
        """Crea amplitudes complejas aleatorias para cada distribución.

        Cada distribución sigue teniendo exactamente ``mine_count`` minas,
        pero unas distribuciones comienzan siendo más probables que otras.

        Como consecuencia, cada casilla obtiene una probabilidad marginal
        distinta.
        """

        dimension = len(self._basis_masks)

        if dimension == 1:
            return np.ones(
                1,
                dtype=np.complex128,
            )

        # Pesos aleatorios para las distribuciones.
        random_weights = self._rng.gamma(
            shape=1.5,
            scale=1.0,
            size=dimension,
        )

        random_weights /= random_weights.sum()

        # Estado uniforme usado para evitar probabilidades iniciales
        # demasiado extremas.
        uniform_weights = np.full(
            dimension,
            1.0 / dimension,
        )

        probabilities = (
            (1.0 - self.randomness) * uniform_weights
            + self.randomness * random_weights
        )

        # Las fases permiten interferencia posterior.
        phases = self._rng.uniform(
            -pi,
            pi,
            size=dimension,
        )

        amplitudes = (
            np.sqrt(probabilities)
            * np.exp(1j * phases)
        )

        return self._normalize(amplitudes)

    @classmethod
    def _normalize(
        cls,
        state: ComplexVector,
    ) -> ComplexVector:
        """Normaliza un vector de estado."""

        norm = float(np.linalg.norm(state))

        if norm <= cls.ATOL:
            raise InvalidMoveError(
                "El estado cuántico no puede tener norma cero."
            )

        return np.asarray(
            state / norm,
            dtype=np.complex128,
        )

    # ================================================================
    # UTILIDADES
    # ================================================================

    @staticmethod
    def _contains_mine(
        mask: int,
        tile: int,
    ) -> bool:
        """Comprueba si una distribución contiene una mina."""

        return bool((mask >> tile) & 1)

    def _validate_tile(self, tile: int) -> None:
        if (
            not isinstance(tile, int)
            or not 0 <= tile < self.tile_count
        ):
            raise InvalidBoardError(
                f"La casilla debe estar entre "
                f"0 y {self.tile_count - 1}."
            )

    def index(
        self,
        row: int,
        column: int,
    ) -> int:
        """Convierte fila y columna en índice lineal."""

        if not 0 <= row < self.rows:
            raise InvalidBoardError(
                "Fila fuera del tablero."
            )

        if not 0 <= column < self.columns:
            raise InvalidBoardError(
                "Columna fuera del tablero."
            )

        return row * self.columns + column

    def coordinates(
        self,
        tile: int,
    ) -> tuple[int, int]:
        """Convierte un índice lineal en fila y columna."""

        self._validate_tile(tile)

        row = tile // self.columns
        column = tile % self.columns

        return row, column

    # ================================================================
    # INFORMACIÓN PÚBLICA DEL TABLERO
    # ================================================================

    @property
    def measured_tiles(self) -> dict[int, bool]:
        """Copia de las casillas medidas.

        False:
            Casilla segura.

        True:
            Mina.
        """

        return dict(self._measured_tiles)

    @property
    def history(self) -> tuple[str, ...]:
        """Historial inmutable de acciones."""

        return tuple(self._history)

    @property
    def state_dimension(self) -> int:
        """Cantidad de configuraciones cuánticas posibles."""

        return len(self._basis_masks)

    @property
    def active_layouts(self) -> int:
        """Configuraciones que todavía tienen amplitud no nula."""

        return int(
            np.count_nonzero(
                np.abs(self._state) > self.ATOL
            )
        )

    @property
    def can_use_power(self) -> bool:
        """Indica si el jugador puede usar un poder ahora."""

        return (
            self.first_click_done
            and not self.power_used_this_turn
            and not self.game_over
        )

    @property
    def remaining_mines(self) -> int:
        """Número exacto de minas todavía no reveladas."""

        revealed_mines = sum(
            self._measured_tiles.values()
        )

        return self.mine_count - revealed_mines

    @property
    def game_won(self) -> bool:
        """Victoria al revelar todas las casillas seguras."""

        revealed_safe_tiles = sum(
            not result
            for result in self._measured_tiles.values()
        )

        total_safe_tiles = (
            self.tile_count - self.mine_count
        )

        return revealed_safe_tiles == total_safe_tiles

    def tile_probability(
        self,
        tile: int,
    ) -> float:
        """Probabilidad actual de que una casilla sea mina."""

        self._validate_tile(tile)

        layout_probabilities = (
            np.abs(self._state) ** 2
        )

        probability = 0.0

        for layout_probability, mask in zip(
            layout_probabilities,
            self._basis_masks,
        ):
            if self._contains_mine(mask, tile):
                probability += float(layout_probability)

        return float(
            np.clip(
                probability,
                0.0,
                1.0,
            )
        )

    def probabilities(self) -> NDArray[np.float64]:
        """Probabilidades de mina de todas las casillas."""

        return np.array(
            [
                self.tile_probability(tile)
                for tile in range(self.tile_count)
            ],
            dtype=np.float64,
        )

    def expected_mines(self) -> float:
        """Suma de probabilidades marginales.

        Debido a la construcción del estado, siempre debe ser igual a
        ``mine_count``.
        """

        return float(
            np.sum(self.probabilities())
        )

    def snapshot(self) -> BoardSnapshot:
        """Crea una representación preparada para la UI."""

        return BoardSnapshot(
            probabilities=tuple(
                float(probability)
                for probability in self.probabilities()
            ),
            measured_tiles=dict(self._measured_tiles),
            exact_mine_count=self.mine_count,
            remaining_mines=self.remaining_mines,
            turn=self.turn,
            power_used_this_turn=self.power_used_this_turn,
            first_click_done=self.first_click_done,
            active_layouts=self.active_layouts,
            game_won=self.game_won,
            game_over=self.game_over,
        )

    # ================================================================
    # CONTROL DE TURNOS
    # ================================================================

    def _prepare_power(
        self,
        *tiles: int,
    ) -> None:
        """Comprueba que un poder pueda utilizarse."""

        if self.game_over:
            raise InvalidMoveError(
                "La partida ya terminó."
            )

        if not self.first_click_done:
            raise InvalidMoveError(
                "Primero debes revelar la casilla inicial segura."
            )

        if self.power_used_this_turn:
            raise InvalidMoveError(
                "Ya utilizaste un poder este turno. "
                "Ahora debes medir una casilla."
            )

        for tile in tiles:
            self._validate_tile(tile)

            if tile in self._measured_tiles:
                raise InvalidMoveError(
                    "No puedes aplicar un poder sobre "
                    "una casilla ya medida."
                )

    def _finish_power(
        self,
        description: str,
    ) -> None:
        """Registra el uso de un poder."""

        self.power_used_this_turn = True

        self._history.append(
            f"T{self.turn}:POWER:{description}"
        )

    # ================================================================
    # PODERES
    # ================================================================

    def apply_z(self, tile: int) -> None:
        """Aplica una fase de 180°.

        No modifica inmediatamente la probabilidad de la casilla.
        Su efecto aparece posteriormente mediante interferencia.
        """

        self._prepare_power(tile)

        for index, mask in enumerate(
            self._basis_masks
        ):
            if self._contains_mine(mask, tile):
                self._state[index] *= -1

        self._finish_power(
            f"Z@{tile}"
        )

    def apply_s(self, tile: int) -> None:
        """Aplica una fase de 90°."""

        self._prepare_power(tile)

        for index, mask in enumerate(
            self._basis_masks
        ):
            if self._contains_mine(mask, tile):
                self._state[index] *= 1j

        self._finish_power(
            f"S@{tile}"
        )

    def _apply_pair_matrix(
        self,
        tile_a: int,
        tile_b: int,
        matrix: ComplexMatrix,
        *,
        label: str,
    ) -> None:
        """Aplica una puerta sobre el subespacio |01>, |10>.

        Esto permite modificar probabilidades sin cambiar el número total
        de minas.
        """

        self._prepare_power(
            tile_a,
            tile_b,
        )

        if tile_a == tile_b:
            raise InvalidMoveError(
                "El poder necesita dos casillas distintas."
            )

        visited_masks: set[int] = set()

        bit_a = 1 << tile_a
        bit_b = 1 << tile_b

        for mask_01 in self._basis_masks:
            if mask_01 in visited_masks:
                continue

            tile_a_is_mine = bool(
                mask_01 & bit_a
            )

            tile_b_is_mine = bool(
                mask_01 & bit_b
            )

            # Buscamos la configuración |01>:
            # A segura y B mina.
            if tile_a_is_mine or not tile_b_is_mine:
                continue

            # Cambiamos 01 por 10.
            mask_10 = (
                mask_01
                ^ bit_a
                ^ bit_b
            )

            index_01 = self._index_by_mask[mask_01]
            index_10 = self._index_by_mask[mask_10]

            old_pair = np.array(
                [
                    self._state[index_01],
                    self._state[index_10],
                ],
                dtype=np.complex128,
            )

            new_pair = matrix @ old_pair

            self._state[index_01] = new_pair[0]
            self._state[index_10] = new_pair[1]

            visited_masks.add(mask_01)
            visited_masks.add(mask_10)

        self._state = self._normalize(
            self._state
        )

        self._finish_power(
            f"{label}@({tile_a},{tile_b})"
        )

    def apply_risk_swap(
        self,
        tile_a: int,
        tile_b: int,
    ) -> None:
        """Intercambia el riesgo cuántico de dos casillas.

        Es el equivalente jugable de una puerta X que no altera el número
        total de minas.
        """

        matrix = np.array(
            [
                [0, 1],
                [1, 0],
            ],
            dtype=np.complex128,
        )

        self._apply_pair_matrix(
            tile_a,
            tile_b,
            matrix,
            label="RISK_SWAP",
        )

    def apply_risk_rotation(
        self,
        tile_a: int,
        tile_b: int,
        angle_radians: float = pi / 8,
    ) -> None:
        """Redistribuye probabilidad de mina entre dos casillas."""

        theta = float(angle_radians)

        matrix = np.array(
            [
                [
                    cos(theta),
                    -sin(theta),
                ],
                [
                    sin(theta),
                    cos(theta),
                ],
            ],
            dtype=np.complex128,
        )

        self._apply_pair_matrix(
            tile_a,
            tile_b,
            matrix,
            label=f"RISK_ROTATION[{theta:.3f}]",
        )

    def apply_pair_hadamard(
        self,
        tile_a: int,
        tile_b: int,
    ) -> None:
        """Hadamard que conserva el número de minas.

        Opera sobre:

            |01>
            |10>

        Puede provocar interferencia constructiva o destructiva.
        """

        matrix = np.array(
            [
                [1, 1],
                [1, -1],
            ],
            dtype=np.complex128,
        ) / sqrt(2.0)

        self._apply_pair_matrix(
            tile_a,
            tile_b,
            matrix,
            label="PAIR_H",
        )

    # ================================================================
    # MEDICIÓN Y COLAPSO GLOBAL
    # ================================================================

    def measure_tile(
        self,
        tile: int,
    ) -> MeasurementResult:
        """Mide una casilla y colapsa todo el tablero."""

        if self.game_over:
            raise InvalidMoveError(
                "La partida ya terminó."
            )

        self._validate_tile(tile)

        if tile in self._measured_tiles:
            raise InvalidMoveError(
                "Esa casilla ya fue medida."
            )

        probability_before = self.tile_probability(
            tile
        )

        was_first_click = (
            not self.first_click_done
        )

        if was_first_click:
            # Regla de diseño:
            # el primer clic siempre es seguro.
            is_mine = False

        else:
            is_mine = bool(
                self._rng.random()
                < probability_before
            )

        # Conservamos únicamente las distribuciones compatibles
        # con el resultado observado.
        compatible_layouts = np.array(
            [
                self._contains_mine(mask, tile)
                == is_mine
                for mask in self._basis_masks
            ],
            dtype=bool,
        )

        collapsed_state = np.where(
            compatible_layouts,
            self._state,
            0.0 + 0.0j,
        )

        if (
            np.linalg.norm(collapsed_state)
            <= self.ATOL
        ):
            raise InvalidMoveError(
                "El resultado de la medición no tiene "
                "amplitud disponible."
            )

        self._state = self._normalize(
            collapsed_state
        )

        self._measured_tiles[tile] = is_mine

        finished_turn = self.turn

        self._history.append(
            f"T{finished_turn}:MEASURE@"
            f"{tile}->{int(is_mine)}"
        )

        self.first_click_done = True

        # La medición termina el turno.
        self.turn += 1
        self.power_used_this_turn = False

        if is_mine or self.game_won:
            self.game_over = True

        return MeasurementResult(
            tile=tile,
            is_mine=is_mine,
            probability_before=probability_before,
            was_first_safe_click=was_first_click,
            turn_finished=finished_turn,
        )

    # ================================================================
    # REPRESENTACIÓN EN TERMINAL
    # ================================================================

    def format_grid(
        self,
        precision: int = 1,
    ) -> str:
        """Muestra probabilidades actuales como cuadrícula."""

        probabilities = self.probabilities()
        lines: list[str] = []

        for row in range(self.rows):
            cells: list[str] = []

            for column in range(self.columns):
                tile = self.index(
                    row,
                    column,
                )

                if tile in self._measured_tiles:
                    text = (
                        "MINE"
                        if self._measured_tiles[tile]
                        else "SAFE"
                    )

                else:
                    text = (
                        f"{100 * probabilities[tile]:"
                        f".{precision}f}%"
                    )

                cells.append(
                    f"{text:>8}"
                )

            lines.append(
                " ".join(cells)
            )

        return "\n".join(lines)

    # ================================================================
    # REINICIO
    # ================================================================

    def reset(
        self,
        *,
        new_random_board: bool = False,
    ) -> None:
        """Reinicia la partida.

        Parameters
        ----------
        new_random_board:
            False:
                Restaura exactamente el tablero original.

            True:
                Genera probabilidades iniciales nuevas.
        """

        if new_random_board:
            self._state = self._create_random_state()
            self._initial_state = self._state.copy()

        else:
            self._state = self._initial_state.copy()

        self._measured_tiles.clear()
        self._history.clear()

        self.turn = 0
        self.power_used_this_turn = False
        self.first_click_done = False
        self.game_over = False
