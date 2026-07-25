from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from .engine import StockfishEngine
from .classifier import MoveClassifier
from .game_manager import GameManager
from .schemas import (
    NewGameRequest, PreMoveCheckRequest, PreMoveCheckResponse,
    CommitMoveRequest, CommitMoveResponse, GameStateResponse,
)

engine: StockfishEngine = None
manager: GameManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, manager
    engine = StockfishEngine(depth=14)
    classifier = MoveClassifier(engine)
    manager = GameManager(engine, classifier)
    yield
    engine.close()


app = FastAPI(title="Chess Mistake Coach API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend's origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/game/new")
def new_game(req: NewGameRequest):
    game_id = manager.new_game(req.starting_fen)
    return manager.get_state(game_id)


@app.get("/api/game/{game_id}/state", response_model=GameStateResponse)
def get_state(game_id: str):
    try:
        return manager.get_state(game_id)
    except KeyError:
        raise HTTPException(404, "Game not found")


@app.post("/api/game/{game_id}/undo")
def undo_move(game_id: str, plies: int = 2):
    try:
        return manager.undo_last_move(game_id, plies=plies)
    except KeyError:
        raise HTTPException(404, "Game not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/move/precheck", response_model=PreMoveCheckResponse)
def precheck_move(req: PreMoveCheckRequest):
    """Core feature: call this BEFORE committing a move. Returns the move's
    classification (Book / Best / Brilliant / Inaccuracy / Mistake / Blunder...),
    and if it's a bad move, a threat preview + alternatives so the UI can
    warn the player before they confirm."""
    try:
        return manager.precheck_move(req.game_id, req.move_uci)
    except KeyError:
        raise HTTPException(404, "Game not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/move/commit", response_model=CommitMoveResponse)
def commit_move(req: CommitMoveRequest):
    """Call this once the player has confirmed they want to play the move
    (whether or not they heeded the warning)."""
    try:
        return manager.commit_move(req.game_id, req.move_uci)
    except KeyError:
        raise HTTPException(404, "Game not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/engine/best-moves/{game_id}")
def best_moves(game_id: str, n: int = 3):
    """Standalone 'show me good options' endpoint -- independent of any
    specific move the player is considering."""
    try:
        game = manager.get_game(game_id)
    except KeyError:
        raise HTTPException(404, "Game not found")
    return {"moves": engine.best_moves(game.board, n=n)}


@app.get("/health")
def health():
    return {"status": "ok"}
