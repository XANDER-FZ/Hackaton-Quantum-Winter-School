from pathlib import Path

from fastapi import HTTPException
from nicegui import app, ui
from pydantic import BaseModel

# Importar este módulo registra la página:
#
# /juego
from frontend.pages import ventana_juego  # noqa: F401


# ============================================================
# IMPORTACIÓN DEL MOTOR CUÁNTICO
# ============================================================

# El código admite dos organizaciones:
#
# 1. src/quantum_engine.py
# 2. quantum_engine.py en la raíz
#
# Primero intenta buscarlo dentro de src/.

try:
    from src.quantum_engine import (
        InvalidMoveError,
        QuantumMinesweeperEngine,
    )

except ModuleNotFoundError as error:
    # Solo usa la segunda ruta cuando lo que no se encontró
    # fue exactamente src o src.quantum_engine.
    #
    # Si falta otra dependencia interna, el error se conserva.

    if error.name not in {
        'src',
        'src.quantum_engine',
    }:
        raise

    from quantum_engine import (
        InvalidMoveError,
        QuantumMinesweeperEngine,
    )


# ============================================================
# RUTAS DE ARCHIVOS
# ============================================================

# Carpeta raíz:
#
# Hackaton-Quantum/
RUTA_PROYECTO = Path(__file__).resolve().parent

# Pantalla HTML:
#
# frontend/pantalla_inicio/
RUTA_INICIO = (
    RUTA_PROYECTO
    / 'frontend'
    / 'pantalla_inicio'
)


# Archivos necesarios para que funcione la pantalla inicial.
ARCHIVOS_INICIO = (
    RUTA_INICIO / 'index.html',
    RUTA_INICIO / 'styles.css',
    RUTA_INICIO / 'script.js',
    RUTA_INICIO / 'start.mp3',
    RUTA_INICIO / 'secaudio.mp3',
)


def verificar_archivos_inicio() -> None:
    """Comprueba que exista la pantalla de inicio."""

    if not RUTA_INICIO.is_dir():
        raise FileNotFoundError(
            'No se encontró la carpeta de la pantalla '
            'de inicio en:\n'
            f'{RUTA_INICIO}'
        )

    for ruta_archivo in ARCHIVOS_INICIO:
        if not ruta_archivo.is_file():
            raise FileNotFoundError(
                'No se encontró el archivo requerido:\n'
                f'{ruta_archivo}'
            )


verificar_archivos_inicio()


# ============================================================
# MOTOR DEL JUEGO
# ============================================================

game = QuantumMinesweeperEngine(
    rows=3,
    columns=3,
    mine_count=3,
    randomness=1.0,
)


# ============================================================
# MODELOS DE LAS PETICIONES
# ============================================================

class TileRequest(BaseModel):
    """Datos enviados para medir una casilla."""

    tile: int


class GateRequest(BaseModel):
    """Datos enviados para aplicar una compuerta."""

    gate: str
    tiles: list[int]


# ============================================================
# ESTADO DEL JUEGO
# ============================================================

def state_payload() -> dict:
    """Convierte el estado actual en datos JSON."""

    probabilities = game.probabilities()
    measured = game.measured_tiles

    cells = [
        {
            'probability': float(probabilities[index]),
            'revealed': index in measured,
            'is_mine': measured.get(index),
        }
        for index in range(game.tile_count)
    ]

    return {
        'cells': cells,
        'turn': game.turn,
        'remaining_mines': game.remaining_mines,
        'first_click_done': game.first_click_done,
        'power_used': game.power_used_this_turn,
        'game_over': game.game_over,
        'game_won': game.game_won,
    }


# ============================================================
# API: CONSULTAR ESTADO
# ============================================================

@app.get('/api/state')
def get_state() -> dict:
    """Devuelve el estado actual del juego."""

    return state_payload()


# ============================================================
# API: NUEVA PARTIDA
# ============================================================

@app.post('/api/new')
def new_game() -> dict:
    """Reinicia el tablero con una nueva distribución."""

    game.reset(
        new_random_board=True,
    )

    return state_payload()


# ============================================================
# API: MEDIR UNA CASILLA
# ============================================================

@app.post('/api/measure')
def measure(request: TileRequest) -> dict:
    """Mide la casilla seleccionada."""

    try:
        result = game.measure_tile(
            request.tile
        )

        response = state_payload()

        response['message'] = (
            'Mina'
            if result.is_mine
            else 'Casilla segura'
        )

        response['first_safe_click'] = (
            result.was_first_safe_click
        )

        return response

    except (InvalidMoveError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


# ============================================================
# API: APLICAR COMPUERTA
# ============================================================

@app.post('/api/gate')
def apply_gate(request: GateRequest) -> dict:
    """Aplica una compuerta sobre las casillas indicadas."""

    try:
        gate = request.gate.strip().upper()
        tiles = request.tiles

        if gate == 'H' and len(tiles) == 2:
            game.apply_hadamard(
                tiles[0],
                tiles[1],
            )

        elif gate == 'X' and len(tiles) == 2:
            game.apply_x(
                tiles[0],
                tiles[1],
            )

        # El botón Y se implementa mediante RY inteligente.
        elif gate == 'Y' and len(tiles) == 1:
            game.apply_smart_ry(
                tiles[0],
            )

        elif gate == 'Z' and len(tiles) == 1:
            game.apply_z(
                tiles[0],
            )

        else:
            raise ValueError(
                'Selección de compuerta inválida. '
                'H y X requieren dos casillas; '
                'Y y Z requieren una casilla.'
            )

        return state_payload()

    except (InvalidMoveError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


# ============================================================
# ARCHIVOS ESTÁTICOS
# ============================================================

# Publica:
#
# /inicio/index.html
# /inicio/styles.css
# /inicio/script.js
# /inicio/start.mp3
# /inicio/secaudio.mp3

app.add_static_files(
    url_path='/inicio',
    local_directory=str(RUTA_INICIO),
)


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@ui.page('/')
def pagina_principal() -> None:
    """Abre la pantalla de inicio HTML."""

    ui.navigate.to(
        '/inicio/index.html'
    )


# La página /juego no se define aquí.
#
# Se registra al importar:
#
# frontend.pages.ventana_juego


# ============================================================
# EJECUTAR SERVIDOR
# ============================================================

if __name__ in {
    '__main__',
    '__mp_main__',
}:
    ui.run(
        title='Buscaminas Quaktico',
        host='127.0.0.1',
        port=8081,
        reload=False,
        show='/',
    )