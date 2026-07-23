from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import cos, pi, sin, sqrt
from typing import Mapping

import numpy as np
from numpy.typing import NDArray


ComplexVector = NDArray[np.complex128]
ComplexMatrix = NDArray[np.complex128]


# =====================================================================
# EXCEPCIONES
# =====================================================================


class QuantumEngineError(Exception):
    """Error base del motor cuántico."""


class InvalidBoardError(QuantumEngineError, ValueError):
    """Configuración inválida del tablero."""


class InvalidMoveError(QuantumEngineError, RuntimeError):
    """Acción no permitida en el estado actual de la partida."""


# =====================================================================
# RESULTADOS
# =====================================================================


@dataclass(frozen=True, slots=True)
class MeasurementResult:
    """Resultado de medir una casilla."""

    tile: int
    is_mine: bool
    probability_before: float
    was_first_safe_click: bool
    turn_finished: int


@dataclass(frozen=True, slots=True)
class SmartRotationResult:
    """Resultado de una rotación RX o RY optimizada."""

    gate: str

    target_tile: int
    partner_tile: int

    angle_radians: float
    angle_degrees: float

    target_before: float
    target_after: float

    partner_before: float
    partner_after: float

    target_change: float
    reduced_target: bool

    selection_mode: str


@dataclass(frozen=True, slots=True)
class BoardSnapshot:
    """Copia inmutable del estado público del tablero."""

    probabilities: tuple[float, ...]
    measured_tiles: Mapping[int, bool]

    exact_mine_count: int
    remaining_mines: int

    turn: int
    power_used_this_turn: bool
    first_click_done: bool

    active_layouts: int

    game_won: bool
    game_over: bool

    history: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _RotationCandidate:
    """Candidato interno durante la optimización de RX y RY."""

    partner_tile: int

    angle_radians: float
    state: ComplexVector

    target_after: float
    partner_after: float

    reduction: float
    visible_change: float


# =====================================================================
# MOTOR
# =====================================================================


class QuantumMinesweeperEngine:
    """Motor global de Quantum Minesweeper.

    Reglas
    ------
    - La primera medición siempre es segura.
    - No se puede usar un poder antes de la primera medición.
    - Solo se puede usar un poder por turno.
    - Medir una casilla termina el turno.
    - Medir colapsa el estado cuántico completo.
    - Medir una mina termina la partida.
    - El número total de minas permanece constante.
    """

    ATOL = 1e-12

    def __init__(
        self,
        rows: int = 3,
        columns: int = 3,
        mine_count: int = 3,
        *,
        seed: int | None = None,
        randomness: float = 0.85,
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
                "mine_count debe cumplir "
                "0 <= mine_count < rows * columns."
            )

        if not 0.0 <= randomness <= 1.0:
            raise InvalidBoardError(
                "randomness debe estar entre 0 y 1."
            )

        self.mine_count = mine_count
        self.randomness = float(randomness)

        self._rng = np.random.default_rng(seed)

        # Todas las configuraciones que contienen exactamente N minas.
        self._basis_masks = self._create_fixed_mine_basis()

        self._index_by_mask = {
            mask: index
            for index, mask in enumerate(self._basis_masks)
        }

        self._state = self._create_random_state()
        self._initial_state = self._state.copy()

        self._measured_tiles: dict[int, bool] = {}
        self._history: list[str] = []

        self.turn = 0
        self.power_used_this_turn = False
        self.first_click_done = False
        self.game_over = False

    # =================================================================
    # CONSTRUCCIÓN DEL ESTADO
    # =================================================================

    def _create_fixed_mine_basis(self) -> tuple[int, ...]:
        """Genera configuraciones con exactamente mine_count minas."""

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

    @classmethod
    def _normalize(
        cls,
        state: ComplexVector,
    ) -> ComplexVector:
        """Normaliza un vector de estado."""

        vector = np.asarray(
            state,
            dtype=np.complex128,
        )

        if not np.all(np.isfinite(vector.real)):
            raise InvalidMoveError(
                "El estado contiene valores reales inválidos."
            )

        if not np.all(np.isfinite(vector.imag)):
            raise InvalidMoveError(
                "El estado contiene valores imaginarios inválidos."
            )

        norm = float(
            np.linalg.norm(vector)
        )

        if norm <= cls.ATOL:
            raise InvalidMoveError(
                "El estado cuántico tiene norma cero."
            )

        return np.asarray(
            vector / norm,
            dtype=np.complex128,
        )

    def _create_random_state(self) -> ComplexVector:
        """Crea un estado aleatorio estructurado.

        La probabilidad se concentra en algunas configuraciones dominantes
        para que las puertas produzcan efectos visibles.

        También se mantiene una pequeña probabilidad uniforme sobre todas
        las configuraciones. Esto permite que cualquier casilla pueda ser
        segura durante el primer clic protegido.
        """

        dimension = len(self._basis_masks)

        if dimension == 1:
            return np.ones(
                1,
                dtype=np.complex128,
            )

        # Preferencia aleatoria de cada casilla por contener una mina.
        tile_biases = self._rng.normal(
            loc=0.0,
            scale=1.0,
            size=self.tile_count,
        )

        layout_scores = np.zeros(
            dimension,
            dtype=np.float64,
        )

        for index, mask in enumerate(self._basis_masks):
            score = 0.0

            for tile in range(self.tile_count):
                if self._contains_mine(mask, tile):
                    score += float(tile_biases[tile])

            # Pequeña perturbación para evitar empates exactos.
            score += float(
                self._rng.normal(
                    loc=0.0,
                    scale=0.08,
                )
            )

            layout_scores[index] = score

        # Mayor randomness produce mayor concentración.
        temperature = max(
            0.20,
            0.85 - 0.50 * self.randomness,
        )

        scaled_scores = (
            layout_scores / temperature
        )

        scaled_scores -= np.max(
            scaled_scores
        )

        softmax_weights = np.exp(
            scaled_scores
        )

        softmax_weights /= np.sum(
            softmax_weights
        )

        # Número de configuraciones dominantes.
        dominant_limit = min(
            dimension,
            max(
                8,
                int(
                    round(
                        24 - 12 * self.randomness
                    )
                ),
            ),
        )

        strongest_indices = np.argpartition(
            softmax_weights,
            -dominant_limit,
        )[-dominant_limit:]

        concentrated = np.zeros(
            dimension,
            dtype=np.float64,
        )

        concentrated[strongest_indices] = (
            softmax_weights[strongest_indices]
        )

        concentrated /= np.sum(
            concentrated
        )

        # Soporte uniforme para evitar probabilidades exactamente cero.
        uniform = np.full(
            dimension,
            1.0 / dimension,
        )

        uniform_floor = (
            0.08 - 0.05 * self.randomness
        )

        probabilities = (
            (1.0 - uniform_floor) * concentrated
            + uniform_floor * uniform
        )

        probabilities /= np.sum(
            probabilities
        )

        # Fases correlacionadas por casilla.
        phase_span = (
            pi / 2.0
        ) * self.randomness

        tile_phases = self._rng.uniform(
            -phase_span,
            phase_span,
            size=self.tile_count,
        )

        phases = np.zeros(
            dimension,
            dtype=np.float64,
        )

        for index, mask in enumerate(self._basis_masks):
            phase = 0.0

            for tile in range(self.tile_count):
                if self._contains_mine(mask, tile):
                    phase += float(
                        tile_phases[tile]
                    )

            phases[index] = phase

        amplitudes = (
            np.sqrt(probabilities)
            * np.exp(1j * phases)
        )

        return self._normalize(
            amplitudes
        )

    # =================================================================
    # VALIDACIÓN Y COORDENADAS
    # =================================================================

    @staticmethod
    def _contains_mine(
        mask: int,
        tile: int,
    ) -> bool:
        """Indica si una configuración tiene mina en una casilla."""

        return bool(
            (mask >> tile) & 1
        )

    def _validate_tile(
        self,
        tile: int,
    ) -> None:

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
        """Convierte fila y columna en índice."""

        if (
            not isinstance(row, int)
            or not 0 <= row < self.rows
        ):
            raise InvalidBoardError(
                "Fila fuera del tablero."
            )

        if (
            not isinstance(column, int)
            or not 0 <= column < self.columns
        ):
            raise InvalidBoardError(
                "Columna fuera del tablero."
            )

        return (
            row * self.columns
            + column
        )

    def coordinates(
        self,
        tile: int,
    ) -> tuple[int, int]:
        """Convierte un índice en fila y columna."""

        self._validate_tile(tile)

        return divmod(
            tile,
            self.columns,
        )

    # =================================================================
    # INFORMACIÓN PÚBLICA
    # =================================================================

    @property
    def measured_tiles(self) -> dict[int, bool]:
        """Casillas medidas.

        False representa una casilla segura.
        True representa una mina.
        """

        return dict(
            self._measured_tiles
        )

    @property
    def history(self) -> tuple[str, ...]:
        """Historial de acciones."""

        return tuple(
            self._history
        )

    @property
    def state_dimension(self) -> int:
        """Número total de configuraciones posibles."""

        return len(
            self._basis_masks
        )

    @property
    def active_layouts(self) -> int:
        """Configuraciones con amplitud distinta de cero."""

        return int(
            np.count_nonzero(
                np.abs(self._state)
                > self.ATOL
            )
        )

    @property
    def can_use_power(self) -> bool:
        """Indica si se puede usar un poder."""

        return (
            self.first_click_done
            and not self.power_used_this_turn
            and not self.game_over
        )

    @property
    def remaining_mines(self) -> int:
        """Número exacto de minas aún no reveladas."""

        revealed_mines = sum(
            self._measured_tiles.values()
        )

        return (
            self.mine_count
            - revealed_mines
        )

    @property
    def game_won(self) -> bool:
        """Victoria al revelar todas las casillas seguras."""

        revealed_safe_tiles = sum(
            not is_mine
            for is_mine
            in self._measured_tiles.values()
        )

        total_safe_tiles = (
            self.tile_count
            - self.mine_count
        )

        return (
            revealed_safe_tiles
            == total_safe_tiles
        )

    def tile_probability(
        self,
        tile: int,
    ) -> float:
        """Probabilidad actual de que una casilla sea una mina."""

        return self._tile_probability_from_state(
            self._state,
            tile,
        )

    def probabilities(
        self,
    ) -> NDArray[np.float64]:
        """Probabilidad de mina de cada casilla."""

        return np.array(
            [
                self.tile_probability(tile)
                for tile
                in range(self.tile_count)
            ],
            dtype=np.float64,
        )

    def expected_mines(self) -> float:
        """Suma de las probabilidades marginales.

        Siempre debe ser aproximadamente mine_count.
        """

        return float(
            np.sum(
                self.probabilities()
            )
        )

    def snapshot(self) -> BoardSnapshot:
        """Devuelve una copia inmutable para la interfaz."""

        return BoardSnapshot(
            probabilities=tuple(
                float(probability)
                for probability
                in self.probabilities()
            ),
            measured_tiles=dict(
                self._measured_tiles
            ),
            exact_mine_count=self.mine_count,
            remaining_mines=self.remaining_mines,
            turn=self.turn,
            power_used_this_turn=(
                self.power_used_this_turn
            ),
            first_click_done=(
                self.first_click_done
            ),
            active_layouts=self.active_layouts,
            game_won=self.game_won,
            game_over=self.game_over,
            history=self.history,
        )

    def _tile_probability_from_state(
        self,
        state: ComplexVector,
        tile: int,
    ) -> float:
        """Probabilidad marginal usando un estado temporal."""

        self._validate_tile(tile)

        layout_probabilities = (
            np.abs(state) ** 2
        )

        probability = 0.0

        for layout_probability, mask in zip(
            layout_probabilities,
            self._basis_masks,
        ):
            if self._contains_mine(mask, tile):
                probability += float(
                    layout_probability
                )

        return float(
            np.clip(
                probability,
                0.0,
                1.0,
            )
        )

    # =================================================================
    # CONTROL DE TURNOS
    # =================================================================

    def _prepare_power(
        self,
        *tiles: int,
    ) -> None:
        """Valida que un poder pueda utilizarse."""

        if self.game_over:
            raise InvalidMoveError(
                "La partida ya terminó."
            )

        if not self.first_click_done:
            raise InvalidMoveError(
                "Primero debes medir la casilla inicial protegida."
            )

        if self.power_used_this_turn:
            raise InvalidMoveError(
                "Ya usaste un poder este turno. "
                "Ahora debes medir una casilla."
            )

        for tile in tiles:
            self._validate_tile(tile)

            if tile in self._measured_tiles:
                raise InvalidMoveError(
                    "No se puede aplicar un poder "
                    "a una casilla medida."
                )

    def _finish_power(
        self,
        description: str,
    ) -> None:
        """Marca el poder del turno como utilizado."""

        self.power_used_this_turn = True

        self._history.append(
            f"T{self.turn}:POWER:{description}"
        )

    # =================================================================
    # PUERTAS DE FASE: Z Y S
    # =================================================================

    def apply_z(
        self,
        tile: int,
    ) -> None:
        """Aplica Z sobre una casilla física.

        Cambia el signo de las ramas donde esa casilla contiene una mina.
        """

        self._prepare_power(tile)

        for index, mask in enumerate(
            self._basis_masks
        ):
            if self._contains_mine(mask, tile):
                self._state[index] *= -1.0

        self._finish_power(
            f"Z@{tile}"
        )

    def apply_s(
        self,
        tile: int,
    ) -> None:
        """Aplica una fase de +90° sobre las ramas donde tile = 1."""

        self._prepare_power(tile)

        for index, mask in enumerate(
            self._basis_masks
        ):
            if self._contains_mine(mask, tile):
                self._state[index] *= 1j

        self._finish_power(
            f"S@{tile}"
        )

    # =================================================================
    # PUERTAS LÓGICAS DE DOS CASILLAS
    # =================================================================

    @staticmethod
    def _validate_pair_matrix(
        matrix: ComplexMatrix,
    ) -> ComplexMatrix:
        """Valida una matriz unitaria 2x2."""

        gate = np.asarray(
            matrix,
            dtype=np.complex128,
        )

        if gate.shape != (2, 2):
            raise InvalidMoveError(
                "Una puerta lógica debe ser una matriz 2x2."
            )

        identity = np.eye(
            2,
            dtype=np.complex128,
        )

        if not np.allclose(
            gate.conj().T @ gate,
            identity,
            atol=1e-10,
        ):
            raise InvalidMoveError(
                "La matriz de la puerta debe ser unitaria."
            )

        return gate

    def _transform_pair_state(
        self,
        state: ComplexVector,
        tile_a: int,
        tile_b: int,
        matrix: ComplexMatrix,
    ) -> ComplexVector:
        """Aplica una puerta sobre el subespacio |01>, |10>.

        Los estados |00> y |11> permanecen sin cambios. Esto garantiza
        que el número exacto de minas se conserve.
        """

        self._validate_tile(tile_a)
        self._validate_tile(tile_b)

        if tile_a == tile_b:
            raise InvalidMoveError(
                "La puerta necesita dos casillas diferentes."
            )

        gate = self._validate_pair_matrix(
            matrix
        )

        transformed_state = np.asarray(
            state,
            dtype=np.complex128,
        ).copy()

        bit_a = 1 << tile_a
        bit_b = 1 << tile_b

        for mask_01 in self._basis_masks:
            a_is_mine = bool(
                mask_01 & bit_a
            )

            b_is_mine = bool(
                mask_01 & bit_b
            )

            # Procesamos únicamente el estado |01>.
            # De esta manera cada pareja |01>, |10> se procesa una vez.
            if a_is_mine or not b_is_mine:
                continue

            mask_10 = (
                mask_01
                ^ bit_a
                ^ bit_b
            )

            index_01 = self._index_by_mask[
                mask_01
            ]

            index_10 = self._index_by_mask[
                mask_10
            ]

            old_pair = np.array(
                [
                    state[index_01],
                    state[index_10],
                ],
                dtype=np.complex128,
            )

            new_pair = gate @ old_pair

            transformed_state[index_01] = (
                new_pair[0]
            )

            transformed_state[index_10] = (
                new_pair[1]
            )

        return self._normalize(
            transformed_state
        )

    def _apply_pair_matrix(
        self,
        tile_a: int,
        tile_b: int,
        matrix: ComplexMatrix,
        *,
        label: str,
    ) -> None:
        """Aplica una puerta lógica y consume el poder del turno."""

        self._prepare_power(
            tile_a,
            tile_b,
        )

        self._state = self._transform_pair_state(
            self._state,
            tile_a,
            tile_b,
            matrix,
        )

        self._finish_power(
            f"{label}@({tile_a},{tile_b})"
        )

    # -----------------------------------------------------------------
    # X
    # -----------------------------------------------------------------

    def apply_x(
        self,
        tile_a: int,
        tile_b: int,
    ) -> None:
        """X lógica.

        Intercambia:

            |01> <-> |10>

        Esto mueve la amplitud de mina entre ambas casillas.
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
            label="X",
        )

    # -----------------------------------------------------------------
    # HADAMARD
    # -----------------------------------------------------------------

    def apply_hadamard(
        self,
        tile_a: int,
        tile_b: int,
    ) -> None:
        """Hadamard lógica sobre |01>, |10>."""

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
            label="H",
        )

    # -----------------------------------------------------------------
    # MATRICES RX, RY Y RZ
    # -----------------------------------------------------------------

    @staticmethod
    def _logical_rotation_matrix(
        gate: str,
        angle_radians: float,
    ) -> ComplexMatrix:
        """Construye una rotación lógica."""

        gate = gate.upper()

        theta = float(
            angle_radians
        )

        cosine = cos(
            theta / 2.0
        )

        sine = sin(
            theta / 2.0
        )

        if gate == "RX":
            return np.array(
                [
                    [
                        cosine,
                        -1j * sine,
                    ],
                    [
                        -1j * sine,
                        cosine,
                    ],
                ],
                dtype=np.complex128,
            )

        if gate == "RY":
            return np.array(
                [
                    [
                        cosine,
                        -sine,
                    ],
                    [
                        sine,
                        cosine,
                    ],
                ],
                dtype=np.complex128,
            )

        if gate == "RZ":
            return np.array(
                [
                    [
                        np.exp(
                            -0.5j * theta
                        ),
                        0,
                    ],
                    [
                        0,
                        np.exp(
                            0.5j * theta
                        ),
                    ],
                ],
                dtype=np.complex128,
            )

        raise InvalidMoveError(
            f"Rotación desconocida: {gate}."
        )

    def apply_rx(
        self,
        tile_a: int,
        tile_b: int,
        angle_radians: float,
    ) -> None:
        """Aplica RX lógica con un ángulo explícito."""

        matrix = self._logical_rotation_matrix(
            "RX",
            angle_radians,
        )

        self._apply_pair_matrix(
            tile_a,
            tile_b,
            matrix,
            label=(
                f"RX["
                f"{np.degrees(angle_radians):.1f}deg"
                f"]"
            ),
        )

    def apply_ry(
        self,
        tile_a: int,
        tile_b: int,
        angle_radians: float,
    ) -> None:
        """Aplica RY lógica con un ángulo explícito."""

        matrix = self._logical_rotation_matrix(
            "RY",
            angle_radians,
        )

        self._apply_pair_matrix(
            tile_a,
            tile_b,
            matrix,
            label=(
                f"RY["
                f"{np.degrees(angle_radians):.1f}deg"
                f"]"
            ),
        )

    def apply_rz(
        self,
        tile_a: int,
        tile_b: int,
        angle_radians: float,
    ) -> None:
        """Aplica RZ lógica.

        RZ normalmente cambia fases, pero no las probabilidades
        inmediatamente.
        """

        matrix = self._logical_rotation_matrix(
            "RZ",
            angle_radians,
        )

        self._apply_pair_matrix(
            tile_a,
            tile_b,
            matrix,
            label=(
                f"RZ["
                f"{np.degrees(angle_radians):.1f}deg"
                f"]"
            ),
        )

    # =================================================================
    # RX Y RY INTELIGENTES
    # =================================================================

    def _best_candidate_for_partner(
        self,
        gate: str,
        target_tile: int,
        partner_tile: int,
        *,
        maximum_angle_degrees: float,
        step_degrees: float,
    ) -> tuple[
        _RotationCandidate | None,
        _RotationCandidate | None,
    ]:
        """Encuentra el mejor ángulo para un partner.

        Retorna:
            - mejor candidato que reduce el target;
            - mejor candidato que genera un cambio visible.
        """

        target_before = self.tile_probability(
            target_tile
        )

        best_reducing: _RotationCandidate | None = None
        best_visible: _RotationCandidate | None = None

        angle_candidates = np.arange(
            -maximum_angle_degrees,
            maximum_angle_degrees
            + step_degrees / 2.0,
            step_degrees,
            dtype=np.float64,
        )

        for angle_degrees in angle_candidates:
            if (
                abs(float(angle_degrees))
                <= self.ATOL
            ):
                continue

            angle_radians = float(
                np.deg2rad(
                    angle_degrees
                )
            )

            matrix = self._logical_rotation_matrix(
                gate,
                angle_radians,
            )

            preview_state = self._transform_pair_state(
                self._state,
                target_tile,
                partner_tile,
                matrix,
            )

            target_after = (
                self._tile_probability_from_state(
                    preview_state,
                    target_tile,
                )
            )

            partner_after = (
                self._tile_probability_from_state(
                    preview_state,
                    partner_tile,
                )
            )

            reduction = (
                target_before
                - target_after
            )

            visible_change = abs(
                target_after
                - target_before
            )

            candidate = _RotationCandidate(
                partner_tile=partner_tile,
                angle_radians=angle_radians,
                state=preview_state,
                target_after=target_after,
                partner_after=partner_after,
                reduction=reduction,
                visible_change=visible_change,
            )

            # Mejor reducción de riesgo.
            if reduction > self.ATOL:
                should_replace = (
                    best_reducing is None
                    or reduction
                    > best_reducing.reduction
                    + self.ATOL
                )

                same_reduction_smaller_angle = (
                    best_reducing is not None
                    and abs(
                        reduction
                        - best_reducing.reduction
                    )
                    <= self.ATOL
                    and abs(angle_radians)
                    < abs(
                        best_reducing.angle_radians
                    )
                )

                if (
                    should_replace
                    or same_reduction_smaller_angle
                ):
                    best_reducing = candidate

            # Mayor cambio visible.
            if visible_change > self.ATOL:
                should_replace_visible = (
                    best_visible is None
                    or visible_change
                    > best_visible.visible_change
                    + self.ATOL
                )

                same_change_smaller_angle = (
                    best_visible is not None
                    and abs(
                        visible_change
                        - best_visible.visible_change
                    )
                    <= self.ATOL
                    and abs(angle_radians)
                    < abs(
                        best_visible.angle_radians
                    )
                )

                if (
                    should_replace_visible
                    or same_change_smaller_angle
                ):
                    best_visible = candidate

        return (
            best_reducing,
            best_visible,
        )

    def _choose_smart_rotation(
        self,
        gate: str,
        target_tile: int,
        *,
        maximum_angle_degrees: float = 180.0,
        step_degrees: float = 2.0,
        random_top_k: int = 3,
    ) -> tuple[
        _RotationCandidate,
        str,
    ]:
        """Elige automáticamente partner y ángulo.

        El motor:
        1. Prueba todas las casillas partner disponibles.
        2. Busca el mejor ángulo para cada partner.
        3. Selecciona aleatoriamente entre los mejores partners.
        """

        gate = gate.upper()

        if gate not in {
            "RX",
            "RY",
        }:
            raise InvalidMoveError(
                "La rotación inteligente "
                "solo admite RX y RY."
            )

        self._validate_tile(
            target_tile
        )

        if target_tile in self._measured_tiles:
            raise InvalidMoveError(
                "La casilla objetivo ya fue medida."
            )

        if maximum_angle_degrees <= 0:
            raise ValueError(
                "maximum_angle_degrees debe ser positivo."
            )

        if step_degrees <= 0:
            raise ValueError(
                "step_degrees debe ser positivo."
            )

        if random_top_k <= 0:
            raise ValueError(
                "random_top_k debe ser positivo."
            )

        available_partners = [
            tile
            for tile in range(
                self.tile_count
            )
            if (
                tile != target_tile
                and tile
                not in self._measured_tiles
            )
        ]

        if not available_partners:
            raise InvalidMoveError(
                "No hay una casilla partner disponible."
            )

        best_reducing_by_partner: list[
            _RotationCandidate
        ] = []

        best_visible_by_partner: list[
            _RotationCandidate
        ] = []

        for partner_tile in available_partners:
            (
                best_reducing,
                best_visible,
            ) = self._best_candidate_for_partner(
                gate,
                target_tile,
                partner_tile,
                maximum_angle_degrees=(
                    maximum_angle_degrees
                ),
                step_degrees=step_degrees,
            )

            if best_reducing is not None:
                best_reducing_by_partner.append(
                    best_reducing
                )

            if best_visible is not None:
                best_visible_by_partner.append(
                    best_visible
                )

        # Primera prioridad: reducir el target.
        if best_reducing_by_partner:
            candidates = sorted(
                best_reducing_by_partner,
                key=lambda candidate: (
                    candidate.reduction
                ),
                reverse=True,
            )

            selection_mode = (
                "risk_reduction"
            )

            strengths = np.array(
                [
                    candidate.reduction
                    for candidate
                    in candidates
                ],
                dtype=np.float64,
            )

        # Fallback: mayor redistribución visible.
        elif best_visible_by_partner:
            candidates = sorted(
                best_visible_by_partner,
                key=lambda candidate: (
                    candidate.visible_change
                ),
                reverse=True,
            )

            selection_mode = (
                "largest_visible_change"
            )

            strengths = np.array(
                [
                    candidate.visible_change
                    for candidate
                    in candidates
                ],
                dtype=np.float64,
            )

        else:
            raise InvalidMoveError(
                f"{gate} no produce un cambio visible "
                "en el estado cuántico actual."
            )

        finalists = candidates[
            : min(
                random_top_k,
                len(candidates),
            )
        ]

        finalist_strengths = strengths[
            : len(finalists)
        ]

        # Selección aleatoria ponderada.
        weights = np.maximum(
            finalist_strengths,
            self.ATOL,
        )

        weights /= np.sum(
            weights
        )

        selected_index = int(
            self._rng.choice(
                len(finalists),
                p=weights,
            )
        )

        return (
            finalists[selected_index],
            selection_mode,
        )

    def _apply_smart_rotation(
        self,
        gate: str,
        target_tile: int,
        *,
        maximum_angle_degrees: float = 180.0,
        step_degrees: float = 2.0,
        random_top_k: int = 3,
    ) -> SmartRotationResult:
        """Busca y aplica una RX o RY optimizada."""

        gate = gate.upper()

        self._prepare_power(
            target_tile
        )

        target_before = self.tile_probability(
            target_tile
        )

        (
            candidate,
            selection_mode,
        ) = self._choose_smart_rotation(
            gate,
            target_tile,
            maximum_angle_degrees=(
                maximum_angle_degrees
            ),
            step_degrees=step_degrees,
            random_top_k=random_top_k,
        )

        self._prepare_power(
            target_tile,
            candidate.partner_tile,
        )

        partner_before = self.tile_probability(
            candidate.partner_tile
        )

        # Aplicamos el estado previamente calculado.
        self._state = candidate.state

        angle_degrees = float(
            np.degrees(
                candidate.angle_radians
            )
        )

        self._finish_power(
            f"SMART_{gate}["
            f"{angle_degrees:.1f}deg"
            f"]@("
            f"{target_tile},"
            f"{candidate.partner_tile}"
            f")"
        )

        target_change = (
            candidate.target_after
            - target_before
        )

        return SmartRotationResult(
            gate=gate,
            target_tile=target_tile,
            partner_tile=(
                candidate.partner_tile
            ),
            angle_radians=(
                candidate.angle_radians
            ),
            angle_degrees=angle_degrees,
            target_before=target_before,
            target_after=(
                candidate.target_after
            ),
            partner_before=partner_before,
            partner_after=(
                candidate.partner_after
            ),
            target_change=target_change,
            reduced_target=(
                candidate.target_after
                < target_before
                - self.ATOL
            ),
            selection_mode=selection_mode,
        )

    def apply_smart_rx(
        self,
        target_tile: int,
    ) -> SmartRotationResult:
        """Aplica RX con partner y ángulo automáticos."""

        return self._apply_smart_rotation(
            gate="RX",
            target_tile=target_tile,
            maximum_angle_degrees=180.0,
            step_degrees=2.0,
            random_top_k=3,
        )

    def apply_smart_ry(
        self,
        target_tile: int,
    ) -> SmartRotationResult:
        """Aplica RY con partner y ángulo automáticos."""

        return self._apply_smart_rotation(
            gate="RY",
            target_tile=target_tile,
            maximum_angle_degrees=180.0,
            step_degrees=2.0,
            random_top_k=3,
        )

    # =================================================================
    # CNOT LÓGICO
    # =================================================================

    def apply_cnot(
        self,
        control_a: int,
        control_b: int,
        target_a: int,
        target_b: int,
    ) -> None:
        """Aplica CNOT lógico usando cuatro casillas.

        Codificación:

            |0_L> = |01>
            |1_L> = |10>

        Si el control se encuentra en |10>, se intercambian |01> y |10>
        en el par objetivo.
        """

        self._prepare_power(
            control_a,
            control_b,
            target_a,
            target_b,
        )

        selected_tiles = {
            control_a,
            control_b,
            target_a,
            target_b,
        }

        if len(selected_tiles) != 4:
            raise InvalidMoveError(
                "CNOT necesita cuatro casillas diferentes."
            )

        control_a_bit = (
            1 << control_a
        )

        control_b_bit = (
            1 << control_b
        )

        target_a_bit = (
            1 << target_a
        )

        target_b_bit = (
            1 << target_b
        )

        transformed_state = (
            self._state.copy()
        )

        for mask_target_01 in self._basis_masks:
            # Control lógico |1_L> = |10>.
            control_is_one = (
                bool(
                    mask_target_01
                    & control_a_bit
                )
                and not bool(
                    mask_target_01
                    & control_b_bit
                )
            )

            # Target lógico |0_L> = |01>.
            target_is_zero = (
                not bool(
                    mask_target_01
                    & target_a_bit
                )
                and bool(
                    mask_target_01
                    & target_b_bit
                )
            )

            if (
                not control_is_one
                or not target_is_zero
            ):
                continue

            mask_target_10 = (
                mask_target_01
                ^ target_a_bit
                ^ target_b_bit
            )

            index_01 = self._index_by_mask[
                mask_target_01
            ]

            index_10 = self._index_by_mask[
                mask_target_10
            ]

            transformed_state[index_01] = (
                self._state[index_10]
            )

            transformed_state[index_10] = (
                self._state[index_01]
            )

        self._state = self._normalize(
            transformed_state
        )

        self._finish_power(
            "CNOT@"
            f"control=({control_a},{control_b}),"
            f"target=({target_a},{target_b})"
        )

    # =================================================================
    # MEDICIÓN Y COLAPSO GLOBAL
    # =================================================================

    def measure_tile(
        self,
        tile: int,
    ) -> MeasurementResult:
        """Mide una casilla y colapsa el tablero completo."""

        self._validate_tile(tile)

        if self.game_over:
            raise InvalidMoveError(
                "La partida ya terminó."
            )

        if tile in self._measured_tiles:
            raise InvalidMoveError(
                "Esa casilla ya fue medida."
            )

        probability_before = (
            self.tile_probability(tile)
        )

        was_first_click = (
            not self.first_click_done
        )

        # Primer clic protegido.
        if was_first_click:
            is_mine = False

        else:
            is_mine = bool(
                self._rng.random()
                < probability_before
            )

        compatible_layouts = np.array(
            [
                self._contains_mine(mask, tile)
                == is_mine
                for mask
                in self._basis_masks
            ],
            dtype=bool,
        )

        collapsed_state = np.where(
            compatible_layouts,
            self._state,
            0.0 + 0.0j,
        )

        if (
            float(
                np.linalg.norm(
                    collapsed_state
                )
            )
            <= self.ATOL
        ):
            raise InvalidMoveError(
                "El resultado de la medición "
                "tiene amplitud cero."
            )

        self._state = self._normalize(
            collapsed_state
        )

        self._measured_tiles[tile] = (
            is_mine
        )

        finished_turn = self.turn

        self._history.append(
            f"T{finished_turn}:"
            f"MEASURE@{tile}"
            f"->{int(is_mine)}"
        )

        self.first_click_done = True

        # Medir termina el turno.
        self.turn += 1

        self.power_used_this_turn = False

        if (
            is_mine
            or self.game_won
        ):
            self.game_over = True

        return MeasurementResult(
            tile=tile,
            is_mine=is_mine,
            probability_before=(
                probability_before
            ),
            was_first_safe_click=(
                was_first_click
            ),
            turn_finished=finished_turn,
        )

    # =================================================================
    # RESET
    # =================================================================

    def reset(
        self,
        *,
        new_random_board: bool = False,
    ) -> None:
        """Reinicia la partida.

        new_random_board=False:
            Restaura exactamente el estado inicial.

        new_random_board=True:
            Genera un tablero cuántico diferente.
        """

        if new_random_board:
            self._state = (
                self._create_random_state()
            )

            self._initial_state = (
                self._state.copy()
            )

        else:
            self._state = (
                self._initial_state.copy()
            )

        self._measured_tiles.clear()
        self._history.clear()

        self.turn = 0
        self.power_used_this_turn = False
        self.first_click_done = False
        self.game_over = False

    # =================================================================
    # FORMATO PARA TERMINAL
    # =================================================================

    def format_grid(
        self,
        precision: int = 1,
    ) -> str:
        """Muestra el tablero como porcentajes."""

        probabilities = self.probabilities()

        lines: list[str] = []

        for row in range(self.rows):
            cells: list[str] = []

            for column in range(
                self.columns
            ):
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
                    text = f"{100 * probabilities[tile]:.{precision}f}%"
                    
                cells.append(
                    f"{text:>8}"
                )

            lines.append(
                " ".join(cells)
            )

        return "\n".join(lines)

    # =================================================================
    # ALIASES DE COMPATIBILIDAD
    # =================================================================

    apply_x_pair = apply_x
    apply_risk_swap = apply_x

    apply_h_pair = apply_hadamard
    apply_pair_hadamard = apply_hadamard

    apply_rx_pair = apply_rx
    apply_ry_pair = apply_ry
    apply_rz_pair = apply_rz
