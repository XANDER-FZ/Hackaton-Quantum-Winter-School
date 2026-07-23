from quantum_engine import (
    InvalidMoveError,
    QuantumMinesweeperEngine,
)


def main() -> None:
    game = QuantumMinesweeperEngine(
        rows=3,
        columns=3,
        mine_count=3,
        seed=42,
        randomness=0.85,
    )

    print("TABLERO INICIAL")
    print(game.format_grid())

    print("\nSuma de probabilidades:")
    print(game.expected_mines())

    # El primer clic siempre será seguro.
    result = game.measure_tile(
        game.index(1, 1)
    )

    print("\nPRIMER CLIC")
    print(result)
    print(game.format_grid())

    # Turno 1: se utiliza un poder.
    game.apply_risk_rotation(
        game.index(0, 0),
        game.index(0, 1),
    )

    print("\nDESPUÉS DEL PODER")
    print(game.format_grid())

    # Intentar usar un segundo poder debe fallar.
    try:
        game.apply_z(
            game.index(2, 2)
        )

    except InvalidMoveError as error:
        print("\nMovimiento bloqueado:")
        print(error)

    # Medir termina el turno.
    result = game.measure_tile(
        game.index(0, 0)
    )

    print("\nSEGUNDA MEDICIÓN")
    print(result)
    print(game.format_grid())


if __name__ == "__main__":
    main()
