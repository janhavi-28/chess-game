from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import sys
import asyncio
import chess
import os
import razorpay
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(override=True)

razorpay_key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_TTYOP1jpVr4bFq")
razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET", "2bxfsCA8tTg4CEbNdmwSoeSH")

# Razorpay client will be instantiated per-request to avoid stale connection pools
def get_razorpay_client():
    return razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))


supabase_url: str = os.getenv("SUPABASE_URL", "https://ipwanamxxugjtpksotxq.supabase.co")
supabase_key: str = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlwd2FuYW14eHVnanRwa3NvdHhxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc1ODAzNzYsImV4cCI6MjEwMzE1NjM3Nn0.qUDvpcGryR07yaAXPkxZYUfadM9C37wDRInEYOoSf-U")
supabase: Client = create_client(supabase_url, supabase_key)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from .engine import StockfishEngine
from .classifier import MoveClassifier
from .game_manager import GameManager
from .schemas import (
    NewGameRequest, PreMoveCheckRequest, PreMoveCheckResponse,
    CommitMoveRequest, CommitMoveResponse, GameStateResponse,
    StartPuzzleRequest, PuzzleAttemptRequest, PuzzleStateResponse,
    CreateOrderRequest, VerifyPaymentRequest,
)

from .puzzle_manager import PuzzleManager

engine: StockfishEngine = None
opponent_engine: StockfishEngine = None
manager: GameManager = None
puzzle_manager = PuzzleManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, opponent_engine, manager
    engine = StockfishEngine(depth=14)
    opponent_engine = StockfishEngine(depth=14)
    classifier = MoveClassifier(engine)
    manager = GameManager(engine, opponent_engine, classifier)
    yield
    engine.close()
    opponent_engine.close()


app = FastAPI(title="Chess Mistake Coach API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend's origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/game/new")
def new_game(req: NewGameRequest):
    game_id = manager.new_game(req.starting_fen, req.opponent_rating)
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


@app.get("/api/engine/robot-move/{game_id}")
def robot_move(game_id: str):
    """Returns the opponent's move, played at the game's configured
    rating -- separate from the full-strength analysis engine."""
    try:
        return manager.get_robot_move(game_id)
    except KeyError:
        raise HTTPException(404, "Game not found")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/puzzles/start")
def start_puzzle(req: StartPuzzleRequest):
    try:
        return puzzle_manager.start_puzzle(req.level)
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.post("/api/puzzles/attempt")
def attempt_puzzle(req: PuzzleAttemptRequest):
    try:
        return puzzle_manager.attempt_move(req.session_id, req.move_uci)
    except KeyError:
        raise HTTPException(404, "Puzzle session not found")

@app.get("/api/puzzles/hint/{session_id}")
def puzzle_hint(session_id: str):
    square = puzzle_manager.get_hint_square(session_id)
    return {"hint_square": square}

@app.get("/api/puzzles/random")
def random_puzzle(level: int = 1):
    puzzle_id, fen, moves_str = puzzle_manager._query_random_puzzle(level)
    
    uci_moves = moves_str.split()
    board = chess.Board(fen)
    classified_moves = []
    
    for i, uci in enumerate(uci_moves):
        move = chess.Move.from_uci(uci)
        ply = board.ply()
        
        try:
            classification = manager.classifier.classify_move(board, move, ply)
            label = classification["label"]
        except Exception as e:
            label = "Best Move"
            
        board.push(move)
        
        classified_moves.append({
            "uci": uci,
            "classification": label
        })

    return {
        "puzzle_id": puzzle_id,
        "fen": fen,
        "moves": classified_moves
    }

@app.post("/api/payment/create-order")
def create_order(req: CreateOrderRequest):
    try:
        data = {
            "amount": 100, # 1 INR in paise
            "currency": "INR",
            "receipt": req.user_id,
        }
        client = get_razorpay_client()
        order = client.order.create(data=data)
        return {"order_id": order["id"], "amount": 100, "currency": "INR"}
    except Exception as e:
        print("RAZORPAY ERROR:", e)
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e))

@app.post("/api/payment/verify")
def verify_payment(req: VerifyPaymentRequest):
    try:
        client = get_razorpay_client()
        client.utility.verify_payment_signature({
            'razorpay_order_id': req.razorpay_order_id,
            'razorpay_payment_id': req.razorpay_payment_id,
            'razorpay_signature': req.razorpay_signature
        })
        
        return {"status": "success"}
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
    except Exception as e:
        raise HTTPException(500, str(e))
