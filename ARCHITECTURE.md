# System Architecture Document

## Project Name: Smart Chess - AI Mistake Coach

---

## 1. High-Level Architecture Overview

**Smart Chess** is structured as a decoupled client-server web application featuring a modern React SPA frontend and a high-performance Python FastAPI backend integrated with the Stockfish 16 chess engine.

```mermaid
graph TD
    Client[React 18 + TypeScript Frontend] <-->|HTTP REST / JSON| API[FastAPI Python Backend]
    API <--> Manager[GameManager - State & History]
    API <--> Classifier[MoveClassifier - CP Loss Math]
    Classifier <--> Engine[Stockfish 16 Engine Process]
```

---

## 2. Component Architecture

### 2.1 Frontend Architecture (React 18 + TypeScript)

The frontend is a single-page application built using Vite, styled with Tailwind CSS, and powered by `react-chessboard` and `chess.js`.

```mermaid
graph TD
    App[App.tsx - Master State, Header Bar & Control Loop] --> Board[ChessBoardArea.tsx - Max-Sized Board & Red Highlight]
    App --> Overlay[CoachOverlay.tsx - Pre-Commit Approval Card & Puzzle Hint Mode]
    App --> Coach[CoachPanel.tsx - Side Feedback & 3-Button Controls]
    App --> Speech[SpeechBubble.tsx - User Rating Card]
    App --> Log[MoveLog.tsx - Verbose Move History]
    App --> Translator[chessTranslator.ts - SAN to English & Turn Perspective]
    App --> Sound[soundEffects.ts - Web Audio API Sounds & Web Speech API TTS]
    App --> Service[services/api.ts - REST Client]
```

- **`App.tsx`**: Manages master game state (`gameId`, `fen`, `playerColor`, `warningActive`, `history`). Renders the top navigation bar (`You Vs Robot`, `Side Selection`, `Restart Game`, `Learner Mode: ON/OFF`, `Coach Voice: ON/OFF`, `Undo Move`) and executes pre-commit approval flow.
- **`ChessBoardArea.tsx`**: Renders the max-sized responsive chessboard grid (`85vh`), handles drag-and-drop & click-to-move input, renders legal destination dots, visual engine arrows, and applies solid red square highlights (`badMoveSquare`) on mistakes.
- **`CoachOverlay.tsx`**: Renders the pre-commit approval card over the board with 3 standard buttons: 💡 **Hint Box (Puzzle Hint Mode)**, ▶️ **Play Anyway**, and 🛡️ **Show Follow Up Moves**.
- **`soundEffects.ts`**: Web Audio API synthesizer for classic wooden piece movement/capture sounds (`chessSounds.playMove()`, `chessSounds.playCapture()`) and Web Speech API TTS (`speakCoachMessage()`).
- **`chessTranslator.ts`**: Converts SAN notation (e.g. `Nf3`, `exd5`) into natural English with automatic turn-perspective flipping for opponent reply threats.

---

### 2.2 Backend Architecture (FastAPI + Stockfish 16)

The backend is built with FastAPI (Uvicorn ASGI server) for high concurrency and asynchronous process management.

```mermaid
graph LR
    Main[app/main.py - API Endpoints] --> GM[app/game_manager.py]
    GM --> MC[app/classifier.py]
    MC --> SE[app/engine.py]
    SE --> SF[Stockfish 16 Engine Binary]
```

- **`app/main.py`**: Exposes REST endpoints for game lifecycle (`/api/game/new`, `/api/game/{id}/state`, `/api/game/{id}/undo`), move precheck (`/api/move/precheck`), move commit (`/api/move/commit`), and best engine moves (`/api/engine/best-moves`).
- **`app/engine.py`**: Spawns and manages the Stockfish 16 subprocess via `python-chess`. Runs multi-pv centipawn evaluation at depth 14+.
- **`app/classifier.py`**: Implements opening book lookup and centipawn loss calculations ($\text{CP Loss} = \text{Best Eval} - \text{Played Eval}$) to categorize moves into *Book*, *Brilliant*, *Best*, *Excellent*, *Good*, *Inaccuracy*, *Mistake*, *Blunder*, and *Miss*.
- **`app/game_manager.py`**: Stores in-memory game sessions (`Game` objects), board move stacks (`chess.Board`), move histories, and executes full-stack move popping (`undo_last_move`).

---

## 3. Data Flow & Pre-Commit Approval Lifecycle

### 3.1 Player Move Lifecycle Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Player
    participant Frontend as React SPA (App.tsx)
    participant Backend as FastAPI Server
    participant Classifier as MoveClassifier
    participant Stockfish as Stockfish 16 Engine

    Player->>Frontend: Plays move (Drag or Click)
    Frontend->>Backend: POST /api/move/precheck {game_id, move_uci}
    Backend->>Classifier: classify_move(board, move)
    Classifier->>Stockfish: best_moves(depth=14, n=3)
    Stockfish-->>Classifier: Returns top 3 engine lines & eval_cp
    Classifier->>Stockfish: score_after_move(board, move)
    Stockfish-->>Classifier: Returns played move eval_cp
    Classifier-->>Backend: Returns classification & threat preview
    Backend-->>Frontend: Returns PreMoveCheckResponse (rating, threat, alternatives)
    
    Frontend->>Frontend: Display "User - [Rating]" in Coach Feedback
    
    alt Move is Good / Best / Book / Excellent
        Frontend->>Backend: POST /api/move/commit {game_id, move_uci}
        Frontend->>Frontend: Update Board FEN & Ready Status
        Frontend->>Backend: GET /api/engine/best-moves (Opponent Turn)
        Backend->>Stockfish: Get bot reply move
        Stockfish-->>Backend: Return bot UCI move
        Backend-->>Frontend: Update Board FEN with Bot Move
    else Move is Inaccuracy / Mistake / Blunder / Miss
        Frontend->>Frontend: Highlight destination square in RED & Enter Action Pending State
        
        alt Player clicks "Play Anyway"
            Player->>Frontend: Clicks "Play Anyway" button
            Frontend->>Backend: POST /api/move/commit {game_id, move_uci}
            Frontend->>Frontend: Update Board FEN
            Frontend->>Backend: GET /api/engine/best-moves (Opponent Turn)
            Stockfish-->>Frontend: Bot plays reply move
        else Player clicks "Undo Move" (Top Header)
            Player->>Frontend: Clicks "Undo Move" button
            Frontend->>Backend: POST /api/game/{game_id}/undo
            Backend->>Backend: Pop move pair from board.move_stack & history
            Backend-->>Frontend: Return previous FEN & history
            Frontend->>Frontend: Reset board to previous turn position
        end
    end
```

---

## 4. API Specification & Interface Contracts

### 4.1 `POST /api/game/new`
- **Request Body**: `{ "starting_fen": "rnbqkbnr/..." }` (Optional)
- **Response**: `GameStateResponse` (`game_id`, `fen`, `turn`, `move_history`)

### 4.2 `POST /api/move/precheck`
- **Request Body**: `{ "game_id": "uuid", "move_uci": "e2e4" }`
- **Response**: `PreMoveCheckResponse` (`label`, `cp_loss`, `top_alternatives`, `threat_preview`)

### 4.3 `POST /api/move/commit`
- **Request Body**: `{ "game_id": "uuid", "move_uci": "e2e4" }`
- **Response**: `CommitMoveResponse` (`fen`, `san`, `classification`, `is_game_over`, `result`)

### 4.4 `POST /api/game/{game_id}/undo`
- **Response**: `GameStateResponse` (pops last turn pair from move stack and returns updated FEN and history).

---

## 5. Deployment Architecture (Vercel Serverless)

```mermaid
graph TD
    User[Web User / Browser] --> VercelCDN[Vercel Global Edge CDN]
    VercelCDN --> Static[Vercel Static Hosting - React SPA]
    VercelCDN --> Serverless[Vercel Serverless Function - api/index.py]
    Serverless --> Binary[Stockfish Linux x86_64 Executable]
```

- **Frontend**: Hosted on Vercel Static CDN for instant global delivery.
- **Backend API**: Packaged as a Python serverless function (`api/index.py`) powered by `vercel.json`.
- **Stockfish Binary**: Executable in `Backend/bin/stockfish` for Linux x86_64 Lambda execution.
