"""
Thin wrapper around the Stockfish UCI engine using python-chess.

Requires a Stockfish binary installed on the machine:
  - Ubuntu/Debian: sudo apt-get install stockfish
  - macOS:         brew install stockfish
  - Or download directly from https://stockfishchess.org/download/

Set the STOCKFISH_PATH env var to point at the binary if it's not
on your PATH (e.g. STOCKFISH_PATH=/usr/games/stockfish).
"""

import os
import chess
import chess.engine
from pathlib import Path
from typing import List, Optional

def _find_stockfish() -> str:
    """Return STOCKFISH_PATH env var if set, otherwise look for stockfish.exe
    next to this file or in the parent directory, then fall back to PATH."""
    if "STOCKFISH_PATH" in os.environ:
        return os.environ["STOCKFISH_PATH"]
    # Look for stockfish binary beside engine.py or one level up (Backend/)
    here = Path(__file__).parent
    candidates = [
        here / "stockfish.exe",
        here / "stockfish",
        here.parent / "stockfish.exe",
        here.parent / "stockfish",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return "stockfish"  # fall back to PATH

STOCKFISH_PATH = _find_stockfish()
CP_MATE = 100_000


import threading

class StockfishEngine:
    def __init__(self, path: str = STOCKFISH_PATH, depth: int = 14,
                 threads: int = 2, hash_mb: int = 128):
        self.path = path
        self.depth = depth
        self.threads = threads
        self.hash_mb = hash_mb
        self.lock = threading.Lock()
        self._start_engine()

    def _start_engine(self):
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.path)
            self.engine.configure({"Threads": self.threads, "Hash": self.hash_mb})
        except FileNotFoundError as e:
            raise RuntimeError(
                f"Could not find Stockfish binary at '{self.path}'. "
                f"Install Stockfish and/or set the STOCKFISH_PATH env var."
            ) from e

    def _safe_analyse(self, board: chess.Board, limit: chess.engine.Limit, multipv: Optional[int] = None):
        """Thread-safe engine analysis with automatic process recovery."""
        with self.lock:
            try:
                if multipv:
                    return self.engine.analyse(board, limit, multipv=multipv)
                return self.engine.analyse(board, limit)
            except Exception as e:
                try:
                    self.engine.quit()
                except Exception:
                    pass
                self._start_engine()
                if multipv:
                    return self.engine.analyse(board, limit, multipv=multipv)
                return self.engine.analyse(board, limit)

    def close(self):
        with self.lock:
            try:
                self.engine.quit()
            except Exception:
                pass

    def best_moves(self, board: chess.Board, n: int = 3, depth: Optional[int] = None) -> List[dict]:
        """Top-N candidate moves with evaluation, from the mover's perspective."""
        limit = chess.engine.Limit(depth=depth or self.depth)
        multipv = min(n, board.legal_moves.count()) or 1
        infos = self._safe_analyse(board, limit, multipv=multipv)
        if isinstance(infos, dict):
            infos = [infos]

        results = []
        for info in infos:
            if not isinstance(info, dict) or "score" not in info:
                continue
            pv = info.get("pv", [])
            move = pv[0] if pv else None
            score = info["score"].pov(board.turn)
            results.append({
                "move": move.uci() if move else None,
                "san": board.san(move) if move and move in board.legal_moves else (move.uci() if move else None),
                "score_cp": score.score(mate_score=CP_MATE),
                "is_mate": score.is_mate(),
                "mate_in": score.mate() if score.is_mate() else None,
                "pv": [m.uci() for m in pv[:5]],
            })
        return results

    def score_after_move(self, board: chess.Board, move: chess.Move,
                          depth: Optional[int] = None) -> chess.engine.PovScore:
        """Evaluate the resulting position, from the perspective of the player
        who just moved (so we can compare it directly to their pre-move best score)."""
        new_board = board.copy()
        new_board.push(move)
        limit = chess.engine.Limit(depth=depth or self.depth)
        info = self._safe_analyse(new_board, limit)
        return info["score"].pov(board.turn)

    def threat_preview(self, board: chess.Board, move: chess.Move,
                        depth: Optional[int] = None) -> dict:
        """Simulate playing `move`, then find the opponent's best reply --
        this is the 'here's how you could get punished' preview."""
        new_board = board.copy()
        new_board.push(move)
        limit = chess.engine.Limit(depth=depth or self.depth)
        info = self._safe_analyse(new_board, limit)
        pv = info.get("pv", [])
        reply = pv[0] if pv else None
        score = info["score"].pov(board.turn)  # from original mover's perspective
        return {
            "opponent_best_reply": reply.uci() if reply else None,
            "opponent_best_reply_san": new_board.san(reply) if reply else None,
            "resulting_pv": [m.uci() for m in pv[:6]],
            "score_after_reply_cp": score.score(mate_score=CP_MATE),
            "is_mate_threat": score.is_mate(),
            "mate_in": score.mate() if score.is_mate() else None,
        }
