# Product Requirements Document (PRD)

## Project Name: Smart Chess - AI Mistake Coach

---

## 1. Executive Summary & Vision

**Smart Chess** is an interactive, real-time AI-assisted chess application designed to bridge the gap between playing chess and actively improving your game. Unlike traditional chess platforms that only analyze your game after it is finished, Smart Chess acts as a live **AI Mistake Coach**. It evaluates moves instantly using Stockfish 16, provides human-perspective feedback (e.g., *Book*, *Brilliant*, *Best*, *Excellent*, *Good*, *Inaccuracy*, *Mistake*, *Blunder*), highlights problematic moves in red, and offers an interactive pre-commit approval flow (*Play Anyway*, *Hint Box*, *Show Follow Up Moves*) so learners can analyze threats or retry moves before the bot responds.

---

## 2. Target Audience

1. **Beginner to Intermediate Chess Players (Rating 400 - 1600)**:
   - Players who want to understand *why* a move was bad right when they play it, rather than waiting for post-game analysis.
   - Learners who benefit from visual arrows, square highlights, and plain-English move translations (e.g., *White Pawn to e4*).

2. **Self-Paced Chess Students & Coaches**:
   - Students looking for an interactive sandbox where they can retry moves, explore Stockfish-recommended lines, and see immediate punishment paths (*Show Follow Up Moves*).

3. **Casual Players Seeking Learner Assistance**:
   - Players who prefer an option to toggle **Learner Mode** on or off depending on whether they want visual assist arrows and piece suggestions.

---

## 3. Core Features & Functional Requirements

### 3.1 Interactive Board & Max-Sized Responsive Sizing
- **Max-Sized 8x8 Chessboard**: Scales up to `85vh` (up to `88vh` on 2K/4K displays), eliminating empty margin dead space.
- **Visual Styling**: Built with modern dark aesthetic (`#4a4a4a` / `#8a8a8a` square pattern), crisp bold black SVG coordinate labels (`a-h`, `1-8`), and smooth 150ms piece movement animations.
- **Dual Control Options**: Supports both **Drag-and-Drop** piece dragging and **Click-to-Move** (click source piece $\rightarrow$ green target dots $\rightarrow$ click destination).
- **Side Selection**: Toggle between **⚪ White** and **⚫ Black** side; board flips automatically and Stockfish engine plays the opposing color.
- **Clean Header Navigation Bar**: Top navigation bar displaying **Game Mode Selection** (*You Vs Robot*, *Robot Vs Robot*, *You Vs Friend*), **Side Selection**, **Restart Game**, **Learner Mode: ON/OFF**, **Coach Voice: ON/OFF**, and **Undo Move**.

### 3.2 Real-Time Stockfish 16 Engine Integration
- **Engine Analysis**: Backend communicates with Stockfish 16 at depth 14 with a **1.5-second time cap** per analysis line for millisecond centipawn evaluation (`score_cp`) and mate calculations without UI hangs.
- **Board Status Validation**: `_safe_analyse` pre-checks board validity (`board.status() == STATUS_VALID`) to prevent invalid FEN states from crashing the Stockfish UCI process.
- **Centipawn Loss Calculation**:
  $$\text{Centipawn Loss} = \text{Best Engine Move Eval} - \text{Played Move Eval}$$

### 3.3 Move Classification System
Every move played by the user is evaluated against Stockfish thresholds and labeled from the **User's Perspective**:

| Classification | Centipawn Loss Range / Criteria | UI Representation |
| :--- | :--- | :--- |
| **Book** | Known opening theory (Plies 1-3) | Neutral Badge |
| **Brilliant** | Tactical sacrifice yielding high evaluation | Bright Cyan Badge |
| **Best** | Matches Stockfish's top move ($0$ CP loss) | Green Badge |
| **Excellent** | $0 \le \text{CP Loss} \le 10$ | Green Badge |
| **Good** | $11 \le \text{CP Loss} \le 25$ | Soft Green Badge |
| **Inaccuracy** | $26 \le \text{CP Loss} \le 60$ | Yellow Badge + Orange/Red Destination Square |
| **Mistake** | $61 \le \text{CP Loss} \le 150$ | Orange Badge + Red Destination Square |
| **Blunder** | $> 150$ CP Loss | Red Badge + Red Destination Square |
| **Worst Move** | Blunder resulting in heavy material/mate loss | Dark Red Badge + Red Destination Square |

### 3.4 Coach Feedback & Red Square Highlight
- **Coach Feedback Header**: Displays move classification immediately after a move attempt.
- **Red Move Square Highlight**: When a move is classified as a *Mistake*, *Blunder*, or *Worst Move*, the destination square of the move is highlighted in **solid red** on the board.
- **Illegal Move Feedback**: Attempting an illegal move (e.g. moving a pinned piece) briefly pulses the target square in orange-red and displays a coach explanation (*"🔒 That piece is pinned! Moving it would expose your king to check."*).

### 3.5 Pre-Commit Approval & Move Controls
- **Good / Best / Book / Excellent Moves**: Commit immediately, updating the board FEN, speaking synchronized positive coach feedback, and playing move/capture sounds.
- **Mistake / Blunder / Worst Moves**: Pause in an **`Action Pending`** state with a red square highlight until the user decides.
- **Move Controls (3 Standardized Buttons)**:
  1. 💡 **Hint Box**: Highlights the starting square of the top-ranked engine move.
  2. ▶️ **Play Anyway**: Finalizes the pending move, commits to the backend engine, and triggers opponent response.
  3. 🛡️ **Show Follow Up Moves**: Displays color-coded engine candidate arrows on the board (Green for 1st, Amber for 2nd, Red for 3rd choice).
- **Top Header Undo Button**: **`Undo Move`** executes a full-stack rollback to retry your move.

### 3.6 Formatted Move Log
- **Human-Readable Moves**: Displays move history translated into verbose English with classification badges (e.g. `1. e4 Classic Opening | Pawn moves to e4`, `2. Nf3 Best Move 🌟 | Knight jumps to f3`).

### 3.7 Learner Mode Toggle & Arrow Visibility Rules
- **Learner Mode: ON**:
  - Automatically displays green recommendation dots/arrows on piece selection.
  - Automatically shows threat and alternative arrows when a Coach warning occurs.
- **Learner Mode: OFF**:
  - Suppresses all automatic arrows (piece selection and warning arrows are hidden).
  - **Arrows ONLY appear when the user explicitly clicks "Show Follow Up Moves"**.

### 3.8 Audio & Voice Features
- 🔊 **Classic Wooden Chess Sound Effects**: Powered by Web Audio API synthesizers (`playMoveSoundForUci()`) for piece placement and wooden captures.
- 🎙️ **Synchronized Coach Voice Narration**: Uses Web Speech API Text-to-Speech (`speakMoveCategory()`). Spoken audio is 100% synchronized with the committed Move Log badge classification (e.g., *Good* badge plays *"Good move."*, *Best* badge plays *"Best move on the board."*).

### 3.9 End-of-Game & Checkmate Announcements
- **Checkmate Detection**: Automatically detects checkmate states and displays a clear winner announcement: `🏆 Checkmate! [White/Black] wins the game!`.
- **Draw / Stalemate Detection**: Displays `🤝 Game Over! The game ended in a draw.`.
- **Post-Game Interaction**: Suppresses turn-attempt toasts after game over and prompts the user to start a new game.

### 3.10 Startup Auto-Retry & Resiliency
- **Auto-Retry Connection**: Frontend attempts up to 3 automatic retries (2-second interval) on startup to connect to the backend.
- **Interactive Connection Overlay**: If the backend is unreachable, a clean full-board overlay appears with a **🔄 Retry Connection** button instead of failing silently.

---

## 4. Technical Stack & System Architecture

### 4.1 Technology Stack

- **Frontend**:
  - Framework: **React 18** + **TypeScript**
  - Build Tool: **Vite**
  - Styling: **Tailwind CSS** (Dark Mode Theme) + Vanilla CSS Overrides
  - Chess Board Render: **`react-chessboard`**
  - Game Logic Utilities: **`chess.js`**
  - Audio & Voice: **Web Audio API Synthesizer** + **Web Speech API TTS**
  - Icons: **Lucide React**

- **Backend**:
  - Framework: **FastAPI** (Python 3.10+)
  - Server: **Uvicorn** (Asynchronous ASGI)
  - Engine Wrapper: **`python-chess`**
  - Chess Engine: **Stockfish 16** (Windows `.exe` / Linux x86_64 binary)

### 4.2 Folder Structure

```
Smart_Chess/
├── PRD.md
├── ARCHITECTURE.md
├── Backend/
│   ├── app/
│   │   ├── main.py            # FastAPI endpoints (/api/game, /api/move/commit, /api/game/undo)
│   │   ├── engine.py          # Stockfish process wrapper, 1.5s time cap & safe analysis
│   │   ├── classifier.py      # Move classification & CP loss math
│   │   ├── game_manager.py    # Game state memory, move history, & stack undo
│   │   └── schemas.py         # Pydantic request/response schemas
│   └── requirements.txt
├── Frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChessBoardArea.tsx  # Max-sized board rendering, illegal move flash & arrows
│   │   │   ├── CoachOverlay.tsx    # Pre-commit approval card & action buttons
│   │   │   └── MoveLog.tsx         # Verbose English move log & classification badges
│   │   ├── services/
│   │   │   └── api.ts              # REST API client
│   │   ├── utils/
│   │   │   ├── chessTranslator.ts  # SAN to verbose English translator
│   │   │   ├── soundEffects.ts     # Web Audio API sound synthesizer
│   │   │   └── coachVoice.ts       # Web Speech API TTS voice narration
│   │   ├── App.tsx                 # Master application state, header controls & retry loop
│   │   └── index.css               # Global CSS & dark theme styling
│   ├── package.json
│   └── vite.config.ts
└── vercel.json                     # Vercel Serverless deployment config
```

---

## 5. Deployment Strategy (Vercel Ready)

The project is structured for single-repo Vercel deployment:
- **Frontend**: Deployed as Vite static SPA on Vercel CDN.
- **Backend**: Deployed as a Python Serverless Function (`api/index.py`) using `vercel.json` with a Linux x86_64 Stockfish binary or JS Stockfish fallback.
