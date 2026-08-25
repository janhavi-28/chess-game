# System Architecture Document

## Project Name: Smart Chess - AI Mistake Coach

---

## 1. High-Level Architecture Overview

**Smart Chess** is structured as a decoupled client-server web application featuring a modern React SPA frontend and a high-performance Python FastAPI backend integrated with the Stockfish 16 chess engine.

```mermaid
graph TD
    Client[React 18 + TypeScript Frontend] <-->|HTTP REST / JSON| API[FastAPI Python Backend]
    Client <-->|OAuth / JWT| Supabase[Supabase - Auth & Profiles]
    Client <-->|Popup / Scripts| Razorpay[Razorpay - Payment Gateway]
    API <-->|Create Order| RazorpayAPI[Razorpay API]
    API <--> Manager[GameManager - State & Rating]
    API <--> Classifier[MoveClassifier - CP Loss Math]
    Classifier <--> Engine[Stockfish 16 Analysis Engine]
    Manager <--> OpponentEngine[Stockfish 16 Opponent Engine - UCI_Elo 1320-3190]
```

---

## 2. Component Architecture

### 2.1 Frontend Architecture (React 18 + TypeScript)

The frontend is a single-page application built using Vite, styled with Tailwind CSS, and powered by `react-chessboard` and `chess.js`.

```mermaid
graph TD
    App[App.tsx - Master State, Header Bar & Control Loop] --> Board[ChessBoardArea.tsx - Max-Sized Board, Illegal Flash & Arrows]
    App --> Overlay[CoachOverlay.tsx - Pre-Commit Approval Card & Action Buttons]
    App --> Payment[PaymentOverlay.tsx - Razorpay Checkout & Paywall]
    App --> Log[MoveLog.tsx - Verbose Move History & Badges]
    App --> Translator[chessTranslator.ts - SAN to English & Turn Perspective]
    App --> Sound[soundEffects.ts - Web Audio API Sounds]
    App --> Voice[coachVoice.ts - Web Speech API TTS Narration]
    App --> Service[services/api.ts - REST Client with Auto-Retry]
```

- **`App.tsx`**: Manages master game state (`gameId`, `fen`, `playerColor`, `warningActive`, `history`, `isRobotThinking`, `isConnecting`). Renders the top navigation bar (`Game Mode`, `Side Selection`, `Restart Game`, `Learner Mode: ON/OFF`, `Coach Voice: ON/OFF`, `Undo Move`), handles startup auto-retry (3 attempts, 2s delay), and executes pre-commit approval flow. Integrates with `useSession` to trigger the paywall (`PaymentOverlay.tsx`) if a non-premium user tries to play.
- **`ChessBoardArea.tsx`**: Renders the max-sized responsive chessboard grid (`85vh`), handles drag-and-drop & click-to-move input, renders legal destination dots, visual engine arrows, orange-red flash on illegal/pinned moves (`illegalFlashSquare`), and solid red square highlights (`badMoveSquare`) on mistakes.
- **`CoachOverlay.tsx`**: Renders the pre-commit approval card over the board with 3 standard buttons: 💡 **Hint Box**, ▶️ **Play Anyway**, and 🛡️ **Show Follow Up Moves**.
- **`PaymentOverlay.tsx`**: Renders the paywall screen. Handles the frontend logic for initiating a Razorpay order via the backend, displaying the Razorpay checkout script, and directly updating the user's `is_premium` status in Supabase upon successful payment.
- **`coachVoice.ts`**: Web Speech API Text-to-Speech narration layer. Audio lines are 100% synchronized with the committed classification badge in `commitAndFinalize`.
- **`soundEffects.ts`**: Web Audio API synthesizer for classic wooden piece movement/capture sounds (`playMoveSoundForUci()`).
- **`chessTranslator.ts`**: Converts SAN notation (e.g. `Nf3`, `exd5`) into natural English with automatic turn-perspective flipping for opponent reply threats.

---

### 2.1b Authentication & Payments Architecture

The application relies on a combination of Supabase and Razorpay to gate gameplay behind a premium paywall.

1. **Authentication**: Users log in via Google OAuth directly from the frontend (`AuthForm.tsx`). Supabase manages the session via JWTs and creates a corresponding record in the `profiles` table via a database trigger.
2. **Payments (Order Creation)**: When a user clicks to pay, the backend (`/api/payment/create-order`) securely communicates with Razorpay using secret keys to generate an `order_id`.
3. **Payments (Checkout & Fulfillment)**: The frontend consumes the `order_id` to render the Razorpay popup. Upon a successful transaction, the frontend directly sets `is_premium = true` in Supabase to instantly unlock the game.

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
- **`app/engine.py`**: Spawns and manages the Stockfish 16 subprocess via `python-chess`. Runs multi-pv centipawn evaluation at depth 14 with a **1.5-second time cap** (`Limit(depth=14, time=1.5)`). Pre-validates `board.status() == STATUS_VALID` in `_safe_analyse` to prevent Stockfish process crashes on corrupted FEN states.
- **`app/classifier.py`**: Implements opening book lookup and centipawn loss calculations ($\text{CP Loss} = \text{Best Eval} - \text{Played Eval}$) to categorize moves into *Book*, *Brilliant*, *Best*, *Excellent*, *Good*, *Inaccuracy*, *Mistake*, *Blunder*, and *Worst Move*.
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
    Classifier->>Stockfish: best_moves(depth=14, time=1.5)
    Stockfish-->>Classifier: Returns top 3 engine lines & eval_cp
    Classifier->>Stockfish: score_after_move(board, move)
    Stockfish-->>Classifier: Returns played move eval_cp
    Classifier-->>Backend: Returns classification & threat preview
    Backend-->>Frontend: Returns PreMoveCheckResponse (rating, threat, alternatives)
    
    alt Move is Good / Best / Book / Excellent
        Frontend->>Backend: POST /api/move/commit {game_id, move_uci}
        Backend-->>Frontend: Returns CommitMoveResponse (fen, classification, is_game_over)
        Frontend->>Frontend: Update Board FEN & Play Synchronized Voice
        
        alt Is Checkmate or Draw
            Frontend->>Frontend: Display Winner Announcement ("🏆 Checkmate! White/Black wins")
        else Game Continues
            Frontend->>Backend: GET /api/engine/best-moves (Opponent Turn)
            Backend->>Stockfish: Get bot reply move
            Stockfish-->>Backend: Return bot UCI move
            Backend-->>Frontend: Update Board FEN with Bot Move
        end
    else Move is Mistake / Blunder / Worst Move
        Frontend->>Frontend: Highlight destination square in RED & Enter Action Pending State
        
        alt Player clicks "Play Anyway"
            Player->>Frontend: Clicks "Play Anyway" button
            Frontend->>Backend: POST /api/move/commit {game_id, move_uci}
            Frontend->>Frontend: Update Board FEN & Play Synchronized Voice
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

## 4. Arrow & Learner Mode Rules

```mermaid
flowchart TD
    A[Board Arrow Request] --> B{Is followUpArrows set?}
    B -- Yes (User clicked 'Show Follow Up Moves') --> C[Animate Refutation Sequence & Highlight Opponent Threat]
    B -- No --> D{Is Learner Mode ON?}
    D -- OFF --> E[Suppress All Automatic Arrows]
    D -- ON --> F{Is warningActive true?}
    F -- Yes --> G[Render Red Threat & Green Alternative Arrows]
    F -- No --> H[Render Piece Selection Hints squareSuggestions]
```

---

## 5. API Specification & Interface Contracts

### 5.1 `POST /api/game/new`
- **Request Body**: `{ "starting_fen": "rnbqkbnr/..." }` (Optional)
- **Response**: `GameStateResponse` (`game_id`, `fen`, `turn`, `move_history`)

### 5.2 `POST /api/move/precheck`
- **Request Body**: `{ "game_id": "uuid", "move_uci": "e2e4" }`
- **Response**: `PreMoveCheckResponse` (`label`, `cp_loss`, `top_alternatives`, `refutation_sequence`, `threat_preview`, `is_box_tier`)

### 5.3 `POST /api/move/commit`
- **Request Body**: `{ "game_id": "uuid", "move_uci": "e2e4" }`
- **Response**: `CommitMoveResponse` (`fen`, `san`, `classification`, `is_game_over`, `result`)

### 5.4 `POST /api/game/{game_id}/undo`
- **Response**: `GameStateResponse` (pops last turn pair from move stack and returns updated FEN and history).

---

## 6. Deployment Architecture (Vercel Serverless)

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
