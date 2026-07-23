from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from quantum_engine import (
    InvalidMoveError,
    QuantumMinesweeperEngine,
)


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

game = QuantumMinesweeperEngine(
    rows=3,
    columns=3,
    mine_count=3,
    randomness=1.0,
)


class TileRequest(BaseModel):
    tile: int


class GateRequest(BaseModel):
    gate: str
    tiles: list[int]


def state_payload() -> dict:
    probabilities = game.probabilities()
    measured = game.measured_tiles

    return {
        "cells": [
            {
                "probability": float(probabilities[index]),
                "revealed": index in measured,
                "is_mine": measured.get(index),
            }
            for index in range(game.tile_count)
        ],
        "turn": game.turn,
        "remaining_mines": game.remaining_mines,
        "first_click_done": game.first_click_done,
        "power_used": game.power_used_this_turn,
        "game_over": game.game_over,
        "game_won": game.game_won,
    }


@app.get("/api/state")
def get_state() -> dict:
    return state_payload()


@app.post("/api/new")
def new_game() -> dict:
    game.reset(new_random_board=True)
    return state_payload()


@app.post("/api/measure")
def measure(request: TileRequest) -> dict:
    try:
        result = game.measure_tile(request.tile)

        response = state_payload()
        response["message"] = (
            "Mina"
            if result.is_mine
            else "Casilla segura"
        )

        response["first_safe_click"] = (
            result.was_first_safe_click
        )

        return response

    except (InvalidMoveError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.post("/api/gate")
def apply_gate(request: GateRequest) -> dict:
    try:
        gate = request.gate.upper()
        tiles = request.tiles

        if gate == "H" and len(tiles) == 2:
            game.apply_hadamard(
                tiles[0],
                tiles[1],
            )

        elif gate == "X" and len(tiles) == 2:
            game.apply_x(
                tiles[0],
                tiles[1],
            )

        # El botón Y funciona como RY inteligente.
        elif gate == "Y" and len(tiles) == 1:
            game.apply_smart_ry(
                tiles[0]
            )

        elif gate == "Z" and len(tiles) == 1:
            game.apply_z(
                tiles[0]
            )

        else:
            raise ValueError(
                "Selección de compuerta inválida."
            )

        return state_payload()

    except (InvalidMoveError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


# Debe ir después de las rutas /api.
app.mount(
    "/",
    StaticFiles(
        directory=BASE_DIR,
        html=True,
    ),
    name="static",
)
